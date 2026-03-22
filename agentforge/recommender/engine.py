"""
Personalized recommendation engine.

Combines Personal Ontology + ToolProfile + GapAnalysis to generate top-5
highly personalized project recommendations. Each recommendation explains
WHY it fits this specific person, estimates difficulty and timeline, and
names similar projects to differentiate from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

import anthropic
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from agentforge.config import Config
from agentforge.github.analyzer import GapAnalysis
from agentforge.ontology.builder import PersonalOntology
from agentforge.scanner.tools import ToolProfile

console = Console()

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Recommendation:
    """A single personalized project recommendation.

    Attributes:
        id: 1-based index used for user selection.
        project_name: Proposed project name.
        tagline: One-line description (max 80 chars).
        concept: 2–4 sentence description of the project.
        why_fit: Why this project fits this specific developer.
        market_opportunity_score: 1–10 market opportunity rating.
        difficulty_score: 1–10 technical difficulty (10 = hardest).
        estimated_mvp_weeks: Estimated weeks to working MVP.
        similar_projects: Names of existing similar projects to differentiate from.
        differentiation: How to stand out from existing solutions.
        tech_stack: Suggested technology stack.
        first_steps: Ordered list of first 3–5 concrete actions to take.
        monetization_path: Suggested path to monetization.
        risk_factors: List of key risks to consider.
    """

    id: int
    project_name: str
    tagline: str
    concept: str
    why_fit: str
    market_opportunity_score: int
    difficulty_score: int
    estimated_mvp_weeks: int
    similar_projects: list[str] = field(default_factory=list)
    differentiation: str = ""
    tech_stack: list[str] = field(default_factory=list)
    first_steps: list[str] = field(default_factory=list)
    monetization_path: str = ""
    risk_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def display_card(self) -> None:
        """Render this recommendation as a Rich panel."""
        opp_color = (
            "green" if self.market_opportunity_score >= 7
            else "yellow" if self.market_opportunity_score >= 5
            else "red"
        )
        diff_color = (
            "green" if self.difficulty_score <= 3
            else "yellow" if self.difficulty_score <= 6
            else "red"
        )

        lines: list[str] = [
            f"[bold]{self.tagline}[/]",
            "",
            f"[dim]{self.concept}[/]",
            "",
            f"[bold yellow]Why it fits you:[/] {self.why_fit}",
            "",
            f"[{opp_color}]Market Opportunity:[/] {self.market_opportunity_score}/10  "
            f"[{diff_color}]Difficulty:[/] {self.difficulty_score}/10  "
            f"[cyan]MVP:[/] ~{self.estimated_mvp_weeks} weeks",
            "",
            f"[bold]Tech Stack:[/] {', '.join(self.tech_stack)}",
            "",
            f"[bold]Differentiation:[/] {self.differentiation}",
        ]

        if self.similar_projects:
            lines.append(f"\n[dim]Similar to: {', '.join(self.similar_projects)}[/]")

        if self.first_steps:
            lines.append("\n[bold green]First Steps:[/]")
            lines += [f"  {i+1}. {step}" for i, step in enumerate(self.first_steps)]

        console.print(
            Panel(
                "\n".join(lines),
                title=f"[bold cyan]#{self.id} — {self.project_name}[/]",
                border_style="cyan",
            )
        )


@dataclass
class RecommendationSet:
    """Container for the full set of recommendations.

    Attributes:
        recommendations: List of personalized recommendations (typically 5).
        selection_rationale: Claude's explanation of the selection logic.
        overall_strategy: High-level strategic advice for this developer.
    """

    recommendations: list[Recommendation] = field(default_factory=list)
    selection_rationale: str = ""
    overall_strategy: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "selection_rationale": self.selection_rationale,
            "overall_strategy": self.overall_strategy,
        }

    def to_json(self) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def display(self) -> None:
        """Render all recommendations to the terminal."""
        console.print()
        console.print(
            Panel(
                self.overall_strategy,
                title="[bold]Your Strategic Context[/]",
                border_style="yellow",
            )
        )
        console.print()

        for rec in self.recommendations:
            rec.display_card()
            console.print()

    def get_by_id(self, rec_id: int) -> Recommendation | None:
        """Look up a recommendation by its 1-based ID."""
        for rec in self.recommendations:
            if rec.id == rec_id:
                return rec
        return None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an elite product strategist and startup advisor specializing in
AI-powered developer tools. Your job is to generate the top 5 personalized
project recommendations for a developer, combining their personal profile,
existing tools, and market gaps.

Return ONLY valid JSON — no markdown, no text outside the JSON object.
The JSON must conform exactly to this schema:

{
  "recommendations": [
    {
      "id": 1,
      "project_name": "string",
      "tagline": "string (max 80 chars)",
      "concept": "string (2-4 sentences)",
      "why_fit": "string (why this fits THIS specific developer)",
      "market_opportunity_score": 1-10,
      "difficulty_score": 1-10,
      "estimated_mvp_weeks": integer,
      "similar_projects": ["string", ...],
      "differentiation": "string",
      "tech_stack": ["string", ...],
      "first_steps": ["string", ...],
      "monetization_path": "string",
      "risk_factors": ["string", ...]
    },
    ... (5 total)
  ],
  "selection_rationale": "string",
  "overall_strategy": "string"
}

Rules:
- Recommendations MUST match the developer's skills, time, risk tolerance
- Each must address a real gap from the gap analysis
- Difficulty must be realistic for solo dev within the stated time budget
- Be specific: real project names, real tech stacks, actionable first steps
- Rank by (opportunity × fit) — highest combined score first
"""

_USER_PROMPT_TEMPLATE = """\
Generate 5 personalized project recommendations for this developer profile:

## Personal Ontology
{ontology_json}

## Local Tool Environment
{tool_profile_json}

## Ecosystem Gap Analysis
{gap_analysis_json}

Create recommendations that are:
1. Deeply personalized to their strengths and style
2. Realistic given their time and risk tolerance
3. Addressing real gaps in the ecosystem
4. Differentiated from what already exists
5. Immediately actionable (clear first steps)

The developer's superpower: {superpower}
Their core pain: {pain_point}
Their target market: {geo_advantage}
"""


class RecommendationEngine:
    """Generates personalized project recommendations using Claude.

    Args:
        config: AgentForge configuration with API credentials.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    def recommend(
        self,
        ontology: PersonalOntology,
        tool_profile: ToolProfile,
        gap_analysis: GapAnalysis,
    ) -> RecommendationSet:
        """Generate top-5 personalized project recommendations.

        Args:
            ontology: The developer's personal ontology from the survey.
            tool_profile: Scanned local environment profile.
            gap_analysis: Ecosystem gap analysis from GitHub data.

        Returns:
            RecommendationSet with 5 ranked, personalized recommendations.

        Raises:
            ValueError: If Claude returns malformed JSON.
        """
        console.print("\n[dim]Generating personalized recommendations with Claude...[/]\n")

        # Build compact representations
        tool_summary = {
            "python_packages_count": len(tool_profile.python_packages),
            "key_sdks": {
                "anthropic": tool_profile.has_anthropic_sdk,
                "openai": tool_profile.has_openai_sdk,
                "langchain": tool_profile.has_langchain,
            },
            "has_node": tool_profile.has_node,
            "has_docker": tool_profile.has_docker,
            "claude_skills": tool_profile.claude_skills,
            "mcp_servers": tool_profile.mcp_servers,
            "vscode_extensions_count": len(tool_profile.vscode_extensions),
            "git_repos_count": len(tool_profile.git_repos),
            "environment_summary": tool_profile.environment_summary,
        }

        gap_summary = {
            "opportunities": [
                {
                    "title": o.title,
                    "potential_score": o.potential_score,
                    "competition_level": o.competition_level,
                    "technical_complexity": o.technical_complexity,
                    "description": o.description,
                }
                for o in gap_analysis.opportunities[:6]
            ],
            "pain_themes": gap_analysis.pain_themes[:5],
            "best_entry_points": gap_analysis.best_entry_points,
            "ecosystem_summary": gap_analysis.ecosystem_summary,
        }

        prompt = _USER_PROMPT_TEMPLATE.format(
            ontology_json=ontology.to_json(),
            tool_profile_json=json.dumps(tool_summary, ensure_ascii=False, indent=2),
            gap_analysis_json=json.dumps(gap_summary, ensure_ascii=False, indent=2),
            superpower=ontology.superpower_summary,
            pain_point=ontology.pain_point_focus,
            geo_advantage=ontology.geo_advantage,
        )

        with Live(
            Spinner("dots12", text="[cyan]Claude is crafting your recommendations...[/]"),
            console=console,
            refresh_per_second=10,
        ):
            message = self._client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        raw_text: str = message.content[0].text.strip()  # type: ignore[union-attr]

        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            data: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Claude returned malformed JSON for recommendations.\nRaw:\n{raw_text}"
            ) from exc

        return self._parse_recommendation_set(data)

    def _parse_recommendation_set(self, data: dict[str, Any]) -> RecommendationSet:
        """Parse the raw Claude JSON into a RecommendationSet."""
        raw_recs: list[dict[str, Any]] = data.get("recommendations", [])
        recommendations: list[Recommendation] = []

        for i, raw in enumerate(raw_recs[:5], 1):
            recommendations.append(
                Recommendation(
                    id=raw.get("id", i),
                    project_name=raw.get("project_name", f"Project {i}"),
                    tagline=raw.get("tagline", ""),
                    concept=raw.get("concept", ""),
                    why_fit=raw.get("why_fit", ""),
                    market_opportunity_score=int(raw.get("market_opportunity_score", 5)),
                    difficulty_score=int(raw.get("difficulty_score", 5)),
                    estimated_mvp_weeks=int(raw.get("estimated_mvp_weeks", 8)),
                    similar_projects=raw.get("similar_projects", []),
                    differentiation=raw.get("differentiation", ""),
                    tech_stack=raw.get("tech_stack", []),
                    first_steps=raw.get("first_steps", []),
                    monetization_path=raw.get("monetization_path", ""),
                    risk_factors=raw.get("risk_factors", []),
                )
            )

        return RecommendationSet(
            recommendations=recommendations,
            selection_rationale=data.get("selection_rationale", ""),
            overall_strategy=data.get("overall_strategy", ""),
        )
