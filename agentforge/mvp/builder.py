"""
MVP generator: produces a complete runnable project skeleton.

Takes the ProjectBrief and PersonalOntology as input and calls Claude to
generate:
  - Full Python package structure with working code
  - README.md with setup instructions
  - requirements.txt / pyproject.toml
  - Basic pytest test stubs
  - .env.example
  - Makefile for common tasks

All files are written to a timestamped output directory so multiple runs
do not overwrite each other.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import anthropic
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.tree import Tree

from agentforge.collector.data import ProjectBrief
from agentforge.config import Config
from agentforge.ontology.builder import PersonalOntology

console = Console()

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class GeneratedFile:
    """A single generated file in the MVP.

    Attributes:
        path: Relative path within the project directory.
        content: Full file content as a string.
        description: Brief description of what this file does.
    """

    path: str
    content: str
    description: str = ""


@dataclass
class MVPResult:
    """The complete generated MVP.

    Attributes:
        project_name: Name of the generated project.
        output_dir: Absolute path to the generated project directory.
        files: List of all generated files.
        setup_instructions: Step-by-step instructions to run the MVP.
        next_steps: Suggested next development steps.
    """

    project_name: str
    output_dir: Path
    files: list[GeneratedFile] = field(default_factory=list)
    setup_instructions: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def display(self) -> None:
        """Render the generated project tree and instructions."""
        tree = Tree(
            f"[bold cyan]{self.project_name}/[/]",
            guide_style="dim",
        )
        for generated_file in self.files:
            parts = Path(generated_file.path).parts
            current = tree
            for part in parts[:-1]:
                # Find or create branch
                found = None
                for child in current.children:
                    if child.label == f"[blue]{part}/[/]":
                        found = child
                        break
                if found is None:
                    found = current.add(f"[blue]{part}/[/]")
                current = found
            current.add(f"[green]{parts[-1]}[/]  [dim]{generated_file.description}[/]")

        console.print("\n[bold]Generated Project Structure:[/]")
        console.print(tree)
        console.print()

        console.print(
            Panel(
                "\n".join(
                    f"  {i+1}. {step}"
                    for i, step in enumerate(self.setup_instructions)
                ),
                title="[bold green]Setup Instructions[/]",
                border_style="green",
            )
        )

        if self.next_steps:
            console.print("\n[bold yellow]Suggested Next Steps:[/]")
            for step in self.next_steps:
                console.print(f"  [yellow]→[/] {step}")

        console.print(
            f"\n[bold]Project saved to:[/] [cyan]{self.output_dir}[/]"
        )


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a world-class senior software engineer who generates production-quality
Python project skeletons. Your output is immediately runnable code.

Return ONLY a valid JSON object — no markdown code blocks, no explanations outside JSON.

Schema:
{
  "files": [
    {
      "path": "relative/path/to/file.py",
      "content": "full file content as string",
      "description": "brief description of this file"
    },
    ...
  ],
  "setup_instructions": ["step 1", "step 2", ...],
  "next_steps": ["next dev action 1", ...]
}

Requirements:
- Generate ALL files needed to have a WORKING prototype
- Include: main package files, CLI entry point, README.md, pyproject.toml,
  requirements.txt, .env.example, tests/ directory with at least 2 test files,
  Makefile
- Code must have proper type hints, docstrings, error handling
- README must have quick-start instructions
- Tests must use pytest and actually test something meaningful
- The CLI must be runnable: python -m <package_name> or a script entry point
- Use the Anthropic SDK for AI features (include proper API key handling)
- Make the code clean, idiomatic Python 3.11+
- Do NOT use placeholder comments like "# TODO implement this"
  — write actual working implementation code
"""

_USER_PROMPT_TEMPLATE = """\
Generate a complete, working Python MVP for this project:

## Project Brief
{brief_json}

## Developer Profile
Builder style: {builder_style}
Tech preferences: {tech_stack}
Risk profile: {risk_profile}
Superpower: {superpower}

## Requirements
1. The main package should be named: {package_name}
2. Primary tech stack: {tech_stack}
3. MVP scope (build exactly these features): {mvp_scope}
4. Make it immediately runnable with minimal setup
5. Include meaningful working code — not just stubs
6. If it uses Claude API, include a proper client wrapper with retry logic
7. Create a compelling README that explains what it does and why it matters

Generate the full working codebase now.
"""


class MVPBuilder:
    """Generates a complete MVP project from a ProjectBrief using Claude.

    Args:
        config: AgentForge configuration with API credentials and output dir.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    def build(
        self,
        brief: ProjectBrief,
        ontology: PersonalOntology,
    ) -> MVPResult:
        """Generate a complete MVP project.

        Args:
            brief: The project brief with scope, tech stack, and context.
            ontology: Developer's personal ontology for style preferences.

        Returns:
            MVPResult with all generated files written to disk.

        Raises:
            ValueError: If Claude returns malformed JSON.
        """
        console.print(
            f"\n[dim]Generating MVP for:[/] [bold cyan]{brief.project_name}[/]\n"
        )

        package_name = self._safe_package_name(brief.project_name)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_dir = self.config.output_dir / f"{package_name}_{timestamp}"

        prompt = _USER_PROMPT_TEMPLATE.format(
            brief_json=brief.to_json(),
            builder_style=ontology.builder_style,
            tech_stack=", ".join(brief.tech_stack),
            risk_profile=ontology.risk_profile,
            superpower=ontology.superpower_summary,
            package_name=package_name,
            mvp_scope="\n".join(f"  - {f}" for f in brief.mvp_scope),
        )

        with Live(
            Spinner("dots", text="[cyan]Claude is generating your MVP codebase...[/]"),
            console=console,
            refresh_per_second=10,
        ):
            message = self._client.messages.create(
                model=self.config.model,
                max_tokens=8192,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        raw_text: str = message.content[0].text.strip()  # type: ignore[union-attr]

        # Strip code fences
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            data: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the text
            data = self._extract_json_fallback(raw_text, brief, package_name)

        generated_files: list[GeneratedFile] = []
        for file_data in data.get("files", []):
            generated_files.append(
                GeneratedFile(
                    path=file_data.get("path", "unknown.txt"),
                    content=file_data.get("content", ""),
                    description=file_data.get("description", ""),
                )
            )

        # Write all files to disk
        output_dir.mkdir(parents=True, exist_ok=True)
        for gen_file in generated_files:
            file_path = output_dir / gen_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(gen_file.content, encoding="utf-8")

        # Save the brief alongside the project
        brief.save(output_dir)

        result = MVPResult(
            project_name=brief.project_name,
            output_dir=output_dir,
            files=generated_files,
            setup_instructions=data.get("setup_instructions", self._default_setup(package_name)),
            next_steps=data.get("next_steps", brief.first_steps),
        )

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_package_name(project_name: str) -> str:
        """Convert a project name to a valid Python package name."""
        name = project_name.lower()
        name = re.sub(r"[^a-z0-9_]", "_", name)
        name = re.sub(r"_+", "_", name)
        name = name.strip("_")
        return name or "my_project"

    def _default_setup(self, package_name: str) -> list[str]:
        """Return sensible default setup instructions."""
        return [
            f"cd {package_name}_*  # navigate to generated directory",
            "python -m venv .venv && source .venv/bin/activate",
            "pip install -r requirements.txt",
            "cp .env.example .env && edit .env with your API keys",
            f"python -m {package_name}",
        ]

    def _extract_json_fallback(
        self, raw_text: str, brief: ProjectBrief, package_name: str
    ) -> dict[str, Any]:
        """Attempt to extract a JSON object from raw text using regex.

        Falls back to a minimal scaffold if extraction fails.
        """
        # Try to find a JSON object in the text
        match = re.search(r"\{[\s\S]+\}", raw_text)
        if match:
            try:
                return json.loads(match.group())  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # Generate a minimal scaffold as last resort
        console.print(
            "[yellow]Warning: Could not parse Claude's JSON. "
            "Generating minimal scaffold...[/]"
        )
        return self._minimal_scaffold(brief, package_name)

    def _minimal_scaffold(
        self, brief: ProjectBrief, package_name: str
    ) -> dict[str, Any]:
        """Generate a minimal but functional project scaffold."""
        return {
            "files": [
                {
                    "path": f"{package_name}/__init__.py",
                    "content": f'"""\n{brief.project_name}\n\n{brief.tagline}\n"""\n\n__version__ = "0.1.0"\n',
                    "description": "Package init",
                },
                {
                    "path": f"{package_name}/main.py",
                    "content": (
                        f'"""\n{brief.project_name} — main entry point.\n"""\n\n'
                        "from __future__ import annotations\n\n"
                        "import os\nimport anthropic\n\n"
                        "def main() -> None:\n"
                        f'    """Run {brief.project_name}."""\n'
                        "    api_key = os.getenv('ANTHROPIC_API_KEY', '')\n"
                        "    if not api_key:\n"
                        "        print('Error: ANTHROPIC_API_KEY not set')\n"
                        "        return\n"
                        "    client = anthropic.Anthropic(api_key=api_key)\n"
                        f"    print('Welcome to {brief.project_name}!')\n"
                        f"    print('{brief.concept}')\n\n"
                        "if __name__ == '__main__':\n"
                        "    main()\n"
                    ),
                    "description": "Main entry point",
                },
                {
                    "path": "README.md",
                    "content": f"# {brief.project_name}\n\n> {brief.tagline}\n\n"
                    f"{brief.concept}\n\n"
                    "## Quick Start\n\n"
                    "```bash\npip install -r requirements.txt\n"
                    "cp .env.example .env\n"
                    f"python -m {package_name}\n```\n",
                    "description": "Project README",
                },
                {
                    "path": "requirements.txt",
                    "content": "anthropic>=0.40.0\npython-dotenv>=1.0.0\nrich>=13.0.0\nclick>=8.1.0\n",
                    "description": "Python dependencies",
                },
                {
                    "path": ".env.example",
                    "content": "ANTHROPIC_API_KEY=your_key_here\n",
                    "description": "Environment variable template",
                },
                {
                    "path": f"tests/test_{package_name}.py",
                    "content": (
                        f'"""Basic tests for {brief.project_name}."""\n\n'
                        "import pytest\n\n"
                        f"def test_import() -> None:\n"
                        f"    import {package_name}\n"
                        f"    assert {package_name}.__version__ == '0.1.0'\n"
                    ),
                    "description": "Basic test suite",
                },
            ],
            "setup_instructions": self._default_setup(package_name),
            "next_steps": brief.first_steps,
        }
