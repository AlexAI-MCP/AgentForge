"""
Local environment scanner.

Detects installed Python packages, Claude Code skills, VS Code extensions,
npm global packages, MCP server configurations, and nearby git repositories
to build a complete ToolProfile of what the developer already has available.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ToolProfile:
    """Complete snapshot of a developer's local toolchain.

    Attributes:
        python_packages: Names of installed Python packages (pip list).
        python_version: Active Python interpreter version string.
        node_version: Node.js version if installed, else empty string.
        npm_global_packages: npm globally installed package names.
        vscode_extensions: VS Code extension IDs.
        claude_skills: Skill names found in Claude Code skills directory.
        mcp_servers: MCP server names from Claude configuration.
        git_repos: Paths to nearby git repositories.
        has_anthropic_sdk: Whether the anthropic Python package is installed.
        has_openai_sdk: Whether the openai Python package is installed.
        has_langchain: Whether langchain is installed.
        has_docker: Whether docker CLI is available.
        has_git: Whether git CLI is available.
        has_node: Whether node is available.
        environment_summary: Human-readable summary of the environment.
    """

    python_packages: list[str] = field(default_factory=list)
    python_version: str = ""
    node_version: str = ""
    npm_global_packages: list[str] = field(default_factory=list)
    vscode_extensions: list[str] = field(default_factory=list)
    claude_skills: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    git_repos: list[str] = field(default_factory=list)
    has_anthropic_sdk: bool = False
    has_openai_sdk: bool = False
    has_langchain: bool = False
    has_docker: bool = False
    has_git: bool = False
    has_node: bool = False
    environment_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def display(self) -> None:
        """Render the tool profile as a Rich table."""
        table = Table(title="Local Environment Scan Results", border_style="dim")
        table.add_column("Category", style="cyan", no_wrap=True)
        table.add_column("Details", style="white")

        table.add_row("Python Version", self.python_version or "unknown")
        table.add_row("Python Packages", f"{len(self.python_packages)} installed")
        table.add_row(
            "AI SDKs",
            ", ".join(
                filter(
                    None,
                    [
                        "anthropic" if self.has_anthropic_sdk else "",
                        "openai" if self.has_openai_sdk else "",
                        "langchain" if self.has_langchain else "",
                    ],
                )
            )
            or "none detected",
        )
        table.add_row("Node.js", self.node_version or "not found")
        table.add_row(
            "npm Global Packages",
            f"{len(self.npm_global_packages)} installed"
            if self.npm_global_packages
            else "none",
        )
        table.add_row(
            "VS Code Extensions",
            f"{len(self.vscode_extensions)} installed"
            if self.vscode_extensions
            else "none / VS Code not found",
        )
        table.add_row(
            "Claude Skills",
            ", ".join(self.claude_skills) if self.claude_skills else "none found",
        )
        table.add_row(
            "MCP Servers",
            ", ".join(self.mcp_servers) if self.mcp_servers else "none configured",
        )
        table.add_row(
            "Nearby Git Repos",
            f"{len(self.git_repos)} found"
            if self.git_repos
            else "none in common locations",
        )
        table.add_row(
            "CLI Tools",
            ", ".join(
                filter(
                    None,
                    [
                        "git" if self.has_git else "",
                        "docker" if self.has_docker else "",
                        "node" if self.has_node else "",
                    ],
                )
            )
            or "minimal",
        )

        console.print(table)


# ---------------------------------------------------------------------------
# Scanner implementation
# ---------------------------------------------------------------------------


class ToolScanner:
    """Scans the local environment and builds a ToolProfile.

    Runs a series of non-destructive discovery commands. All subprocess calls
    have short timeouts and fail silently — this scanner must never crash the
    main pipeline.
    """

    _CLAUDE_SKILL_DIRS: list[Path] = [
        Path.home() / ".claude" / "skills",
        Path.home() / ".config" / "claude" / "skills",
        Path("skills"),
    ]

    _CLAUDE_CONFIG_PATHS: list[Path] = [
        Path.home() / ".claude" / "claude_desktop_config.json",
        Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        Path.home() / ".config" / "claude" / "config.json",
    ]

    _COMMON_REPO_DIRS: list[Path] = [
        Path.home() / "workspace",
        Path.home() / "projects",
        Path.home() / "dev",
        Path.home() / "code",
        Path.home() / "src",
        Path.cwd(),
        Path.cwd().parent,
    ]

    def scan(self) -> ToolProfile:
        """Run all environment discovery routines and return a ToolProfile.

        Returns:
            Fully populated ToolProfile.
        """
        profile = ToolProfile()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Scanning local environment...", total=8)

            profile.python_version = self._get_python_version()
            profile.python_packages = self._get_python_packages()
            progress.advance(task)

            self._detect_ai_sdks(profile)
            progress.advance(task)

            profile.node_version = self._get_node_version()
            profile.has_node = bool(profile.node_version)
            profile.npm_global_packages = self._get_npm_global_packages()
            progress.advance(task)

            profile.vscode_extensions = self._get_vscode_extensions()
            progress.advance(task)

            profile.claude_skills = self._get_claude_skills()
            progress.advance(task)

            profile.mcp_servers = self._get_mcp_servers()
            progress.advance(task)

            profile.git_repos = self._get_git_repos()
            profile.has_git = bool(shutil.which("git"))
            progress.advance(task)

            profile.has_docker = bool(shutil.which("docker"))
            profile.environment_summary = self._build_summary(profile)
            progress.advance(task)

        return profile

    # ------------------------------------------------------------------
    # Individual scanners
    # ------------------------------------------------------------------

    def _run(self, cmd: list[str], timeout: int = 10) -> str:
        """Run a subprocess and return stdout, returning empty string on failure."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return ""

    def _get_python_version(self) -> str:
        """Return the active Python version string."""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _get_python_packages(self) -> list[str]:
        """Return list of installed Python package names via pip."""
        output = self._run([sys.executable, "-m", "pip", "list", "--format=columns"])
        if not output:
            return []
        lines = output.splitlines()[2:]  # Skip header rows
        return [line.split()[0].lower() for line in lines if line.strip()]

    def _detect_ai_sdks(self, profile: ToolProfile) -> None:
        """Set boolean flags for key AI SDKs in the installed packages."""
        packages_lower = {p.lower() for p in profile.python_packages}
        profile.has_anthropic_sdk = "anthropic" in packages_lower
        profile.has_openai_sdk = "openai" in packages_lower
        profile.has_langchain = any(
            p.startswith("langchain") for p in packages_lower
        )

    def _get_node_version(self) -> str:
        """Return node version string, or empty string if not installed."""
        output = self._run(["node", "--version"])
        return output.lstrip("v") if output.startswith("v") else output

    def _get_npm_global_packages(self) -> list[str]:
        """Return list of globally installed npm package names."""
        output = self._run(["npm", "list", "-g", "--depth=0", "--parseable"])
        if not output:
            return []
        packages: list[str] = []
        for line in output.splitlines():
            path = Path(line)
            name = path.name
            if name and name != "lib" and not name.startswith("."):
                packages.append(name)
        return packages

    def _get_vscode_extensions(self) -> list[str]:
        """Return list of installed VS Code extension IDs."""
        output = self._run(["code", "--list-extensions"])
        if not output:
            # Try code-insiders
            output = self._run(["code-insiders", "--list-extensions"])
        if not output:
            return []
        return [line.strip() for line in output.splitlines() if line.strip()]

    def _get_claude_skills(self) -> list[str]:
        """Return list of Claude Code skill names from known skill directories."""
        skills: list[str] = []
        for skill_dir in self._CLAUDE_SKILL_DIRS:
            if skill_dir.exists() and skill_dir.is_dir():
                for item in skill_dir.iterdir():
                    if item.suffix in {".md", ".yaml", ".yml", ".json", ".py"}:
                        skills.append(item.stem)
                    elif item.is_dir():
                        skills.append(item.name)
        return list(dict.fromkeys(skills))  # deduplicate preserving order

    def _get_mcp_servers(self) -> list[str]:
        """Return list of configured MCP server names from Claude config files."""
        servers: list[str] = []
        for config_path in self._CLAUDE_CONFIG_PATHS:
            if not config_path.exists():
                continue
            try:
                data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
                mcp_config = data.get("mcpServers", {})
                if isinstance(mcp_config, dict):
                    servers.extend(mcp_config.keys())
            except (json.JSONDecodeError, OSError):
                continue
        return list(dict.fromkeys(servers))

    def _get_git_repos(self) -> list[str]:
        """Return paths of git repositories in common workspace directories."""
        found: list[str] = []
        checked: set[str] = set()

        for base_dir in self._COMMON_REPO_DIRS:
            if not base_dir.exists() or not base_dir.is_dir():
                continue
            key = str(base_dir.resolve())
            if key in checked:
                continue
            checked.add(key)

            try:
                for child in base_dir.iterdir():
                    if child.is_dir() and (child / ".git").exists():
                        found.append(str(child))
            except PermissionError:
                continue

        return found[:20]  # cap at 20 to avoid overwhelming the output

    def _build_summary(self, profile: ToolProfile) -> str:
        """Compose a concise environment summary string."""
        parts: list[str] = [f"Python {profile.python_version}"]
        if profile.has_anthropic_sdk:
            parts.append("Anthropic SDK")
        if profile.has_openai_sdk:
            parts.append("OpenAI SDK")
        if profile.has_langchain:
            parts.append("LangChain")
        if profile.has_node:
            parts.append(f"Node {profile.node_version}")
        if profile.has_docker:
            parts.append("Docker")
        if profile.claude_skills:
            parts.append(f"{len(profile.claude_skills)} Claude skills")
        if profile.mcp_servers:
            parts.append(f"MCP: {', '.join(profile.mcp_servers[:3])}")
        return " | ".join(parts)
