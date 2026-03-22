"""
Personal ontology builder: synthesizes survey answers into a structured JSON
ontology using the Claude API.

The PersonalOntology is the central data structure that drives all downstream
personalization — recommender, MVP builder, and data collector all consume it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live

from agentforge.config import Config
from agentforge.ontology.survey import SurveyAnswers

console = Console()


@dataclass
class PersonalOntology:
    """Structured representation of a developer's personal builder DNA.

    Attributes:
        strengths: Technical and domain strengths detected from survey.
        gaps: Areas where the developer has acknowledged weaknesses or low coverage.
        opportunities: High-level opportunity areas suited to this profile.
        recommended_domains: Specific technology or product domains to focus on.
        builder_style: One of 'builder', 'researcher', 'operator', 'designer', 'hacker'.
        risk_profile: One of 'conservative', 'moderate', 'aggressive'.
        time_horizon: Estimated ideal project duration given availability.
        target_persona: Who this person should build for.
        monetization_fit: Best monetization model for this profile.
        geo_advantage: Geographic / language market advantage.
        motivation_core: Core internal driver.
        superpower_summary: One-sentence summary of their unique ability.
        pain_point_focus: The pain point most worth addressing.
        ideal_project_traits: Bullet-point traits of the ideal project for this person.
        raw_claude_analysis: Full raw JSON string returned by Claude for debugging.
    """

    strengths: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    recommended_domains: list[str] = field(default_factory=list)
    builder_style: str = "builder"
    risk_profile: str = "moderate"
    time_horizon: str = "3–6 months"
    target_persona: str = ""
    monetization_fit: str = ""
    geo_advantage: str = ""
    motivation_core: str = ""
    superpower_summary: str = ""
    pain_point_focus: str = ""
    ideal_project_traits: list[str] = field(default_factory=list)
    raw_claude_analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonalOntology":
        """Deserialize from a plain dictionary.

        Unknown keys are silently dropped for forward compatibility.
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_str: str) -> "PersonalOntology":
        """Deserialize from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def display(self) -> None:
        """Pretty-print the ontology to the terminal using Rich."""
        lines: list[str] = [
            f"[bold cyan]Builder Style:[/]    {self.builder_style}",
            f"[bold cyan]Risk Profile:[/]     {self.risk_profile}",
            f"[bold cyan]Time Horizon:[/]     {self.time_horizon}",
            f"[bold cyan]Target Persona:[/]   {self.target_persona}",
            f"[bold cyan]Monetization:[/]     {self.monetization_fit}",
            f"[bold cyan]Geo Advantage:[/]    {self.geo_advantage}",
            "",
            "[bold yellow]Strengths:[/]",
        ]
        lines += [f"  + {s}" for s in self.strengths]
        lines += ["", "[bold red]Gaps:[/]"]
        lines += [f"  - {g}" for g in self.gaps]
        lines += ["", "[bold green]Opportunities:[/]"]
        lines += [f"  * {o}" for o in self.opportunities]
        lines += ["", "[bold magenta]Recommended Domains:[/]"]
        lines += [f"  > {d}" for d in self.recommended_domains]
        lines += [
            "",
            f"[bold]Superpower:[/] {self.superpower_summary}",
            f"[bold]Pain Focus:[/] {self.pain_point_focus}",
            f"[bold]Motivation:[/] {self.motivation_core}",
        ]

        console.print(
            Panel(
                "\n".join(lines),
                title="[bold]Your Personal Ontology[/]",
                border_style="cyan",
            )
        )


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert developer strategist and product advisor. Your job is to analyze
a developer's survey responses and synthesize a precise Personal Ontology — a
structured map of their strengths, gaps, opportunities, and ideal project traits.

Return ONLY valid JSON — no markdown, no explanation outside the JSON object.
The JSON must conform exactly to this schema:

{
  "strengths": ["string", ...],          // 3–6 concrete technical/domain strengths
  "gaps": ["string", ...],               // 3–5 honest gaps or weak points
  "opportunities": ["string", ...],      // 4–6 specific market/tech opportunities for this profile
  "recommended_domains": ["string", ...],// 3–5 specific product/tech domains to focus on
  "builder_style": "builder|researcher|operator|designer|hacker",
  "risk_profile": "conservative|moderate|aggressive",
  "time_horizon": "string",             // e.g. "2–4 weeks", "3–6 months", "1 year+"
  "target_persona": "string",           // 1–2 sentence description of ideal user
  "monetization_fit": "string",         // best monetization model and brief rationale
  "geo_advantage": "string",            // geographic / language market advantage
  "motivation_core": "string",          // 1 sentence on what really drives this person
  "superpower_summary": "string",       // 1 sentence unique superpower
  "pain_point_focus": "string",         // the highest-leverage pain point to address
  "ideal_project_traits": ["string", ...]  // 4–6 bullet traits of the perfect project
}
"""

_USER_PROMPT_TEMPLATE = """\
Here are my survey answers. Please synthesize my Personal Ontology as JSON:

{survey_json}
"""


class OntologyBuilder:
    """Calls Claude to synthesize survey answers into a PersonalOntology.

    Args:
        config: AgentForge config with API credentials and model selection.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    def build(self, answers: SurveyAnswers) -> PersonalOntology:
        """Build a PersonalOntology from survey answers using Claude.

        Args:
            answers: Completed SurveyAnswers from the survey runner.

        Returns:
            PersonalOntology synthesized by Claude.

        Raises:
            ValueError: If Claude returns malformed JSON.
            anthropic.APIError: On API-level failures.
        """
        console.print("\n[dim]Synthesizing your Personal Ontology with Claude...[/]\n")

        prompt = _USER_PROMPT_TEMPLATE.format(survey_json=answers.to_json())

        with Live(
            Spinner("dots", text="[cyan]Claude is analyzing your answers...[/]"),
            console=console,
            refresh_per_second=10,
        ):
            message = self._client.messages.create(
                model=self.config.model,
                max_tokens=2048,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        raw_text: str = message.content[0].text.strip()  # type: ignore[union-attr]

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            data: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Claude returned malformed JSON. Raw response:\n{raw_text}"
            ) from exc

        ontology = PersonalOntology.from_dict(data)
        ontology.raw_claude_analysis = raw_text
        return ontology
