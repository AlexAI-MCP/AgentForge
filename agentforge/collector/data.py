"""
Automated data collection for the chosen project concept.

Fetches supporting research including:
- GitHub issues from competing/similar projects
- Trending discussions in the target domain
- Related API documentation pointers
- Example datasets or data sources
- Competitive landscape snapshot

All collected data is compiled into a project_brief.md that serves as
context for the MVP builder.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

import anthropic
import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.spinner import Spinner

from agentforge.config import Config
from agentforge.ontology.builder import PersonalOntology
from agentforge.recommender.engine import Recommendation

console = Console()

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class GitHubIssueInsight:
    """Distilled insight from a GitHub issue thread.

    Attributes:
        repo: Repository where this issue appears.
        title: Issue title.
        url: Direct link to the issue.
        theme: Categorized theme (e.g., 'missing feature', 'bug', 'docs').
        insight: One-sentence extracted insight.
    """

    repo: str
    title: str
    url: str
    theme: str
    insight: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


@dataclass
class ProjectBrief:
    """Comprehensive brief for the chosen project, ready for MVP generation.

    Attributes:
        project_name: Name of the chosen project.
        tagline: One-line description.
        concept: Full concept description.
        why_fit: Why this fits the developer.
        tech_stack: Proposed technology stack.
        differentiation: How to stand out.
        github_insights: Insights from competing project issues.
        pain_point_evidence: Evidence of real user pain points.
        competitive_landscape: Analysis of similar existing tools.
        integration_opportunities: APIs or services to integrate with.
        mvp_scope: Precise MVP scope and feature list.
        success_metrics: How to measure success.
        risks_and_mitigations: Key risks with mitigation strategies.
        first_steps: Ordered list of immediate first actions.
        created_at: ISO timestamp when brief was created.
    """

    project_name: str
    tagline: str
    concept: str
    why_fit: str
    tech_stack: list[str] = field(default_factory=list)
    differentiation: str = ""
    github_insights: list[GitHubIssueInsight] = field(default_factory=list)
    pain_point_evidence: list[str] = field(default_factory=list)
    competitive_landscape: list[dict[str, str]] = field(default_factory=list)
    integration_opportunities: list[str] = field(default_factory=list)
    mvp_scope: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    risks_and_mitigations: list[dict[str, str]] = field(default_factory=list)
    first_steps: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        d = asdict(self)
        return d

    def to_json(self) -> str:
        """Serialize to a formatted JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """Render the brief as a Markdown document."""
        lines: list[str] = [
            f"# {self.project_name}",
            f"> {self.tagline}",
            f"\n**Created:** {self.created_at}",
            "\n---\n",
            "## Concept",
            self.concept,
            "\n## Why This Fits You",
            self.why_fit,
            "\n## Proposed Tech Stack",
        ]
        lines += [f"- {tech}" for tech in self.tech_stack]

        lines += ["\n## Differentiation", self.differentiation]

        if self.mvp_scope:
            lines += ["\n## MVP Scope"]
            lines += [f"- [ ] {feature}" for feature in self.mvp_scope]

        if self.pain_point_evidence:
            lines += ["\n## Evidence of Pain Points"]
            lines += [f"- {e}" for e in self.pain_point_evidence]

        if self.github_insights:
            lines += ["\n## GitHub Issue Insights"]
            for insight in self.github_insights[:10]:
                lines += [
                    f"\n### [{insight.repo}] {insight.title}",
                    f"**Theme:** {insight.theme}",
                    f"**Insight:** {insight.insight}",
                    f"**URL:** {insight.url}",
                ]

        if self.competitive_landscape:
            lines += ["\n## Competitive Landscape"]
            for comp in self.competitive_landscape:
                name = comp.get("name", "")
                weakness = comp.get("weakness", "")
                lines.append(f"- **{name}**: {weakness}")

        if self.integration_opportunities:
            lines += ["\n## Integration Opportunities"]
            lines += [f"- {opp}" for opp in self.integration_opportunities]

        if self.success_metrics:
            lines += ["\n## Success Metrics"]
            lines += [f"- {m}" for m in self.success_metrics]

        if self.risks_and_mitigations:
            lines += ["\n## Risks & Mitigations"]
            for risk in self.risks_and_mitigations:
                r = risk.get("risk", "")
                m = risk.get("mitigation", "")
                lines.append(f"- **Risk:** {r}  \n  **Mitigation:** {m}")

        if self.first_steps:
            lines += ["\n## Immediate First Steps"]
            lines += [f"{i+1}. {step}" for i, step in enumerate(self.first_steps)]

        return "\n".join(lines)

    def save(self, output_dir: Path) -> Path:
        """Save the brief as both JSON and Markdown.

        Args:
            output_dir: Directory in which to save the files.

        Returns:
            Path to the saved Markdown file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self.project_name.lower().replace(" ", "_").replace("/", "_")

        md_path = output_dir / f"{safe_name}_brief.md"
        json_path = output_dir / f"{safe_name}_brief.json"

        md_path.write_text(self.to_markdown(), encoding="utf-8")
        json_path.write_text(self.to_json(), encoding="utf-8")

        return md_path


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

_GITHUB_API_BASE = "https://api.github.com"

_BRIEF_SYSTEM_PROMPT = """\
You are a senior product manager and technical researcher. Your job is to create
a comprehensive project brief that will guide MVP development.

Return ONLY valid JSON — no markdown, no text outside the JSON.

{
  "mvp_scope": ["string", ...],               // 5–8 specific MVP features
  "pain_point_evidence": ["string", ...],     // 4–6 evidence statements of real pain
  "competitive_landscape": [
    {"name": "string", "weakness": "string"},
    ...
  ],
  "integration_opportunities": ["string", ...],  // 3–5 APIs/services to integrate
  "success_metrics": ["string", ...],            // 4–6 measurable success criteria
  "risks_and_mitigations": [
    {"risk": "string", "mitigation": "string"},
    ...
  ]
}
"""

_BRIEF_USER_TEMPLATE = """\
Create a comprehensive project brief for this AI agent era project:

## Project
Name: {project_name}
Tagline: {tagline}
Concept: {concept}
Tech Stack: {tech_stack}
Differentiation: {differentiation}
Similar Projects: {similar_projects}

## Developer Profile
{ontology_summary}

## GitHub Insights Collected
{github_insights_json}

Produce a detailed, actionable project brief with:
1. Precise MVP scope (what to build first, what to defer)
2. Evidence of real pain points this addresses
3. Honest competitive analysis with specific weaknesses to exploit
4. Integration opportunities with existing ecosystem tools
5. Clear, measurable success metrics
6. Key risks with concrete mitigation strategies
"""


class DataCollector:
    """Collects supporting research data for the chosen project recommendation.

    Args:
        config: AgentForge configuration with API credentials and output settings.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self._client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        self._http_headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if config.github_token:
            self._http_headers["Authorization"] = f"Bearer {config.github_token}"

    def collect(
        self,
        recommendation: Recommendation,
        ontology: PersonalOntology,
    ) -> ProjectBrief:
        """Collect all research data and build a ProjectBrief.

        Args:
            recommendation: The chosen project recommendation.
            ontology: Developer's personal ontology for context.

        Returns:
            Fully populated ProjectBrief ready for MVP generation.
        """
        console.print(
            f"\n[dim]Collecting research data for:[/] [bold]{recommendation.project_name}[/]\n"
        )

        github_insights = asyncio.run(
            self._collect_github_insights(recommendation.similar_projects)
        )

        brief_data = self._generate_brief(recommendation, ontology, github_insights)

        brief = ProjectBrief(
            project_name=recommendation.project_name,
            tagline=recommendation.tagline,
            concept=recommendation.concept,
            why_fit=recommendation.why_fit,
            tech_stack=recommendation.tech_stack,
            differentiation=recommendation.differentiation,
            github_insights=github_insights,
            pain_point_evidence=brief_data.get("pain_point_evidence", []),
            competitive_landscape=brief_data.get("competitive_landscape", []),
            integration_opportunities=brief_data.get("integration_opportunities", []),
            mvp_scope=brief_data.get("mvp_scope", []),
            success_metrics=brief_data.get("success_metrics", []),
            risks_and_mitigations=brief_data.get("risks_and_mitigations", []),
            first_steps=recommendation.first_steps,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        return brief

    async def _collect_github_insights(
        self, similar_repos: list[str]
    ) -> list[GitHubIssueInsight]:
        """Fetch recent issues from similar repos for pain-point research."""
        insights: list[GitHubIssueInsight] = []

        if not similar_repos:
            return insights

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(
                "[cyan]Fetching GitHub issues...", total=len(similar_repos)
            )

            async with httpx.AsyncClient(
                headers=self._http_headers, timeout=20.0, follow_redirects=True
            ) as client:
                for repo_hint in similar_repos[:5]:
                    progress.update(task, description=f"[cyan]Checking: {repo_hint}...")
                    repo_issues = await self._fetch_repo_issues(client, repo_hint)
                    insights.extend(repo_issues)
                    progress.advance(task)
                    await asyncio.sleep(0.3)

        return insights[:20]  # cap at 20 insights

    async def _fetch_repo_issues(
        self, client: httpx.AsyncClient, repo_hint: str
    ) -> list[GitHubIssueInsight]:
        """Fetch open issues for a single repo, identified by name hint."""
        # Try to find repo by searching if not in owner/repo format
        if "/" not in repo_hint:
            search_url = f"{_GITHUB_API_BASE}/search/repositories"
            try:
                resp = await client.get(
                    search_url,
                    params={"q": f"{repo_hint} language:python stars:>100", "per_page": 1},
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    if items:
                        repo_hint = items[0]["full_name"]
                    else:
                        return []
                else:
                    return []
            except httpx.HTTPError:
                return []

        issues_url = f"{_GITHUB_API_BASE}/repos/{repo_hint}/issues"
        cutoff = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

        try:
            resp = await client.get(
                issues_url,
                params={
                    "state": "open",
                    "per_page": 10,
                    "sort": "comments",
                    "direction": "desc",
                    "since": cutoff,
                },
            )
            if resp.status_code != 200:
                return []

            issues: list[dict[str, Any]] = resp.json()
            insights: list[GitHubIssueInsight] = []

            for issue in issues[:8]:
                title: str = issue.get("title", "")
                # Classify theme based on keywords
                title_lower = title.lower()
                if any(kw in title_lower for kw in ["feature", "request", "add", "support"]):
                    theme = "missing feature"
                elif any(kw in title_lower for kw in ["bug", "error", "fail", "broken"]):
                    theme = "bug / stability"
                elif any(kw in title_lower for kw in ["doc", "example", "tutorial", "guide"]):
                    theme = "documentation gap"
                elif any(kw in title_lower for kw in ["performance", "slow", "timeout", "memory"]):
                    theme = "performance issue"
                else:
                    theme = "general improvement"

                insights.append(
                    GitHubIssueInsight(
                        repo=repo_hint,
                        title=title,
                        url=issue.get("html_url", ""),
                        theme=theme,
                        insight=f"Users of {repo_hint} want: {title}",
                    )
                )

            return insights

        except (httpx.HTTPError, json.JSONDecodeError):
            return []

    def _generate_brief(
        self,
        recommendation: Recommendation,
        ontology: PersonalOntology,
        github_insights: list[GitHubIssueInsight],
    ) -> dict[str, Any]:
        """Use Claude to synthesize collected data into a structured brief."""
        console.print("\n[dim]Synthesizing project brief with Claude...[/]\n")

        ontology_summary = (
            f"Strengths: {', '.join(ontology.strengths[:3])}\n"
            f"Builder style: {ontology.builder_style}\n"
            f"Risk profile: {ontology.risk_profile}\n"
            f"Time horizon: {ontology.time_horizon}\n"
            f"Superpower: {ontology.superpower_summary}"
        )

        insights_data = [i.to_dict() for i in github_insights[:10]]

        prompt = _BRIEF_USER_TEMPLATE.format(
            project_name=recommendation.project_name,
            tagline=recommendation.tagline,
            concept=recommendation.concept,
            tech_stack=", ".join(recommendation.tech_stack),
            differentiation=recommendation.differentiation,
            similar_projects=", ".join(recommendation.similar_projects),
            ontology_summary=ontology_summary,
            github_insights_json=json.dumps(insights_data, ensure_ascii=False, indent=2),
        )

        with Live(
            Spinner("dots", text="[cyan]Claude is synthesizing your project brief...[/]"),
            console=console,
            refresh_per_second=10,
        ):
            message = self._client.messages.create(
                model=self.config.model,
                max_tokens=3000,
                system=_BRIEF_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

        raw_text: str = message.content[0].text.strip()  # type: ignore[union-attr]

        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                line for line in lines if not line.startswith("```")
            ).strip()

        try:
            return json.loads(raw_text)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            # Return a minimal fallback rather than crashing
            return {
                "mvp_scope": recommendation.first_steps,
                "pain_point_evidence": [],
                "competitive_landscape": [
                    {"name": p, "weakness": "See GitHub issues for details"}
                    for p in recommendation.similar_projects
                ],
                "integration_opportunities": [],
                "success_metrics": [
                    "10 active users in first month",
                    "GitHub stars > 50 in 3 months",
                    "At least 1 external contributor",
                ],
                "risks_and_mitigations": [
                    {
                        "risk": r,
                        "mitigation": "Monitor early and adjust",
                    }
                    for r in recommendation.risk_factors[:3]
                ],
            }
