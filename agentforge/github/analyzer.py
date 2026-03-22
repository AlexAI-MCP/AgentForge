"""
GitHub ecosystem gap analyzer.

Takes a list of trending repositories and uses Claude to identify:
- Common pain points and complaints in the ecosystem
- Missing features frequently requested
- Frameworks that are "good but incomplete"
- Underserved gaps ranked by opportunity size

The resulting GapAnalysis feeds directly into the recommendation engine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table

from agentforge.config import Config
from agentforge.github.searcher import RepoInfo
from agentforge.llm import ask_json

console = Console()

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Opportunity:
    """A specific market opportunity identified from gap analysis.

    Attributes:
        title: Short, punchy title for the opportunity.
        description: 2–4 sentence description of what is missing.
        affected_repos: Repos where this gap is most visible.
        potential_score: 1–10 score for market potential.
        competition_level: 'low', 'medium', or 'high'.
        technical_complexity: 'low', 'medium', or 'high'.
        suggested_approach: Brief suggestion on how to address this gap.
    """

    title: str
    description: str
    affected_repos: list[str] = field(default_factory=list)
    potential_score: int = 5
    competition_level: str = "medium"
    technical_complexity: str = "medium"
    suggested_approach: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass
class GapAnalysis:
    """Complete ecosystem gap analysis result.

    Attributes:
        opportunities: Ranked list of market opportunities.
        pain_themes: Recurring pain point themes across repos.
        saturated_areas: Areas with strong existing solutions.
        fast_moving_areas: Areas evolving too fast to build in.
        ecosystem_summary: 3–5 sentence summary of the ecosystem state.
        best_entry_points: The 3 most attractive entry points for a new project.
    """

    opportunities: list[Opportunity] = field(default_factory=list)
    pain_themes: list[str] = field(default_factory=list)
    saturated_areas: list[str] = field(default_factory=list)
    fast_moving_areas: list[str] = field(default_factory=list)
    ecosystem_summary: str = ""
    best_entry_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary, including nested opportunities."""
        d = asdict(self)
        return d

    def to_json(self) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def display(self) -> None:
        """Render the gap analysis to the terminal using Rich."""
        console.print(
            Panel(
                self.ecosystem_summary,
                title="[bold]Ecosystem Summary[/]",
                border_style="blue",
            )
        )

        if self.opportunities:
            table = Table(
                title="Top Opportunities",
                border_style="dim",
                show_lines=True,
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Opportunity", style="cyan", min_width=25)
            table.add_column("Potential", justify="center", width=8)
            table.add_column("Competition", justify="center", width=12)
            table.add_column("Complexity", justify="center", width=10)
            table.add_column("Description", max_width=50)

            for i, opp in enumerate(self.opportunities[:8], 1):
                potential_color = (
                    "green" if opp.potential_score >= 7
                    else "yellow" if opp.potential_score >= 5
                    else "red"
                )
                table.add_row(
                    str(i),
                    opp.title,
                    f"[{potential_color}]{opp.potential_score}/10[/]",
                    opp.competition_level,
                    opp.technical_complexity,
                    opp.description[:120] + "..." if len(opp.description) > 120 else opp.description,
                )
            console.print(table)

        if self.pain_themes:
            console.print("\n[bold yellow]Recurring Pain Themes:[/]")
            for theme in self.pain_themes:
                console.print(f"  [red]•[/] {theme}")

        if self.best_entry_points:
            console.print("\n[bold green]Best Entry Points:[/]")
            for entry in self.best_entry_points:
                console.print(f"  [green]→[/] {entry}")


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a world-class product strategist and open-source ecosystem analyst.
You analyze GitHub repositories to identify gaps, pain points, and opportunities
in the AI/agent/developer-tools ecosystem.

Return ONLY valid JSON — no markdown, no explanations outside the JSON.
The JSON must conform exactly to this schema:

{
  "opportunities": [
    {
      "title": "string",
      "description": "string",
      "affected_repos": ["string", ...],
      "potential_score": 1-10,
      "competition_level": "low|medium|high",
      "technical_complexity": "low|medium|high",
      "suggested_approach": "string"
    },
    ...
  ],
  "pain_themes": ["string", ...],
  "saturated_areas": ["string", ...],
  "fast_moving_areas": ["string", ...],
  "ecosystem_summary": "string",
  "best_entry_points": ["string", ...]
}

Return 5–8 opportunities, ranked by potential_score descending.
Be specific — name concrete project ideas, not vague categories.
"""

_USER_PROMPT_TEMPLATE = """\
Analyze this list of trending AI/agent repositories and identify gaps,
opportunities, and ecosystem patterns:

{repos_json}

Focus on:
1. What keeps appearing in open issues that is NOT solved?
2. What do people try to integrate that lacks a clean solution?
3. Which tools are "almost great" but missing a key feature?
4. Where is there high demand but low-quality supply?
5. What use cases have no good open-source solution?

Be specific. Name real gaps that a solo developer could address in 1–3 months.
"""


class GapAnalyzer:
    """Analyzes a list of trending repos to find ecosystem gaps using Claude.

    Args:
        config: AgentForge configuration with API credentials.
    """

    def __init__(self, config: Config) -> None:
        self.config = config

    def analyze(self, repos: list[RepoInfo]) -> GapAnalysis:
        """Run gap analysis on a list of GitHub repos.

        Args:
            repos: List of RepoInfo objects from the GitHub searcher.

        Returns:
            GapAnalysis with ranked opportunities and ecosystem insights.

        Raises:
            ValueError: If Claude returns malformed JSON.
        """
        console.print("\n[dim]Analyzing ecosystem gaps with Claude...[/]\n")

        # Build a compact representation to stay within context limits
        repo_summaries = [
            {
                "name": r.name,
                "stars": r.stars,
                "description": r.description,
                "topics": r.topics[:8],
                "issues": r.issues_count,
                "category": r.category,
                "language": r.language,
            }
            for r in repos[:40]  # Limit to top 40 to manage token count
        ]

        prompt = _USER_PROMPT_TEMPLATE.format(
            repos_json=json.dumps(repo_summaries, ensure_ascii=False, indent=2)
        )

        with Live(
            Spinner("dots2", text="[cyan]Claude is analyzing the ecosystem...[/]"),
            console=console,
            refresh_per_second=10,
        ):
            data: dict[str, Any] = ask_json(prompt, system=_SYSTEM_PROMPT)

        return self._parse_gap_analysis(data)

    def _parse_gap_analysis(self, data: dict[str, Any]) -> GapAnalysis:
        """Parse the raw Claude JSON into a GapAnalysis dataclass."""
        raw_opps: list[dict[str, Any]] = data.get("opportunities", [])
        opportunities: list[Opportunity] = []

        for opp in raw_opps:
            opportunities.append(
                Opportunity(
                    title=opp.get("title", ""),
                    description=opp.get("description", ""),
                    affected_repos=opp.get("affected_repos", []),
                    potential_score=int(opp.get("potential_score", 5)),
                    competition_level=opp.get("competition_level", "medium"),
                    technical_complexity=opp.get("technical_complexity", "medium"),
                    suggested_approach=opp.get("suggested_approach", ""),
                )
            )

        return GapAnalysis(
            opportunities=opportunities,
            pain_themes=data.get("pain_themes", []),
            saturated_areas=data.get("saturated_areas", []),
            fast_moving_areas=data.get("fast_moving_areas", []),
            ecosystem_summary=data.get("ecosystem_summary", ""),
            best_entry_points=data.get("best_entry_points", []),
        )
