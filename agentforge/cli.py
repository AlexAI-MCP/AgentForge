"""
AgentForge CLI — the main entry point.

Commands:
    run         Full pipeline: survey → scan → search → analyze → recommend → build
    survey      Run the 20-question personal ontology survey only
    scan        Scan local development environment only
    search      Search GitHub for trending AI/agent repos only
    recommend   Generate recommendations (requires a saved survey)
    build       Build MVP for a specific recommendation ID
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

from agentforge.config import Config

console = Console()

# ---------------------------------------------------------------------------
# ASCII art banner
# ---------------------------------------------------------------------------

BANNER = r"""
    _                    _   _____
   / \   __ _  ___ _ __ | |_|  ___|__  _ __ __ _  ___
  / _ \ / _` |/ _ \ '_ \| __| |_ / _ \| '__/ _` |/ _ \
 / ___ \ (_| |  __/ | | | |_|  _| (_) | | | (_| |  __/
/_/   \_\__, |\___|_| |_|\__|_|  \___/|_|  \__, |\___|
        |___/                               |___/
"""

TAGLINE = "What to Build in the Agent Era — AI 에이전트 시대의 선택장애 해결"


def _print_banner() -> None:
    console.print(f"[cyan]{BANNER}[/]")
    console.print(f"  [bold]{TAGLINE}[/]\n")


# ---------------------------------------------------------------------------
# Shared state helpers
# ---------------------------------------------------------------------------


def _get_config() -> Config:
    """Load config and validate required credentials."""
    config = Config.from_env()
    errors = config.validate_for_run()
    if errors:
        for error in errors:
            console.print(f"[red]Config Error:[/] {error}")
        console.print(
            "\n[dim]Copy .env.example to .env and add your API key.[/]"
        )
        sys.exit(1)
    config.ensure_output_dir()
    return config


def _load_ontology(config: Config) -> "PersonalOntology":  # type: ignore[name-defined]
    """Load saved ontology or exit with guidance."""
    from agentforge.ontology.builder import PersonalOntology

    ontology_path = config.output_dir / "ontology.json"
    if not ontology_path.exists():
        console.print(
            "[red]No saved ontology found.[/] Run [bold]agentforge survey[/] first."
        )
        sys.exit(1)
    return PersonalOntology.from_json(ontology_path.read_text(encoding="utf-8"))


def _load_recommendations(config: Config) -> "RecommendationSet":  # type: ignore[name-defined]
    """Load saved recommendations or exit with guidance."""
    from agentforge.recommender.engine import RecommendationSet

    recs_path = config.output_dir / "recommendations.json"
    if not recs_path.exists():
        console.print(
            "[red]No saved recommendations found.[/] Run [bold]agentforge recommend[/] first."
        )
        sys.exit(1)
    data = json.loads(recs_path.read_text(encoding="utf-8"))
    rec_set = RecommendationSet()
    from agentforge.recommender.engine import Recommendation

    for r in data.get("recommendations", []):
        rec_set.recommendations.append(Recommendation(**r))
    rec_set.selection_rationale = data.get("selection_rationale", "")
    rec_set.overall_strategy = data.get("overall_strategy", "")
    return rec_set


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version="0.1.0", prog_name="agentforge")
def main() -> None:
    """AgentForge: overcome decision paralysis about what to build in the AI era."""
    pass


# ---------------------------------------------------------------------------
# agentforge run
# ---------------------------------------------------------------------------


@main.command()
@click.option("--skip-scan", is_flag=True, default=False, help="Skip local environment scan")
@click.option("--skip-github", is_flag=True, default=False, help="Skip GitHub search")
@click.option("--auto-build", is_flag=True, default=False, help="Automatically build top recommendation")
def run(skip_scan: bool, skip_github: bool, auto_build: bool) -> None:
    """Run the full AgentForge pipeline end-to-end.

    Steps: survey → scan → GitHub search → gap analysis → recommend → build
    """
    _print_banner()
    config = _get_config()

    # Step 1: Survey
    console.print(Rule("[bold cyan]Step 1/6: Personal Ontology Survey[/]"))
    _run_survey_internal(config)

    # Step 2: Scan
    if not skip_scan:
        console.print(Rule("[bold cyan]Step 2/6: Environment Scan[/]"))
        _run_scan_internal(config)

    # Step 3 + 4: GitHub + Gap Analysis
    if not skip_github:
        console.print(Rule("[bold cyan]Step 3–4/6: GitHub Trend Search & Gap Analysis[/]"))
        _run_search_internal(config)

    # Step 5: Recommend
    console.print(Rule("[bold cyan]Step 5/6: Personalized Recommendations[/]"))
    _run_recommend_internal(config)

    # Step 6: Build
    console.print(Rule("[bold cyan]Step 6/6: Build Your MVP[/]"))

    rec_set = _load_recommendations(config)
    rec_set.display()

    if auto_build:
        rec_id = 1
        console.print(f"\n[dim]Auto-building top recommendation (#{rec_id})...[/]")
    else:
        rec_id = click.prompt(
            "\nWhich recommendation do you want to build? (Enter number 1-5)",
            type=int,
            default=1,
        )

    _run_build_internal(config, rec_id)


# ---------------------------------------------------------------------------
# agentforge survey
# ---------------------------------------------------------------------------


@main.command()
def survey() -> None:
    """Run the 20-question personal ontology survey and build your Personal Ontology."""
    _print_banner()
    config = _get_config()
    console.print(Rule("[bold cyan]Personal Ontology Survey[/]"))
    _run_survey_internal(config)


def _run_survey_internal(config: Config) -> None:
    """Internal survey runner used by both `survey` and `run` commands."""
    from agentforge.ontology.survey import SurveyRunner
    from agentforge.ontology.builder import OntologyBuilder

    runner = SurveyRunner(save_path=config.survey_save_path)
    answers = runner.run()

    console.print(Rule("[dim]Building ontology...[/]"))
    builder = OntologyBuilder(config)
    ontology = builder.build(answers)

    ontology.display()

    # Persist
    ontology_path = config.output_dir / "ontology.json"
    ontology_path.write_text(ontology.to_json(), encoding="utf-8")
    console.print(f"\n[green]Ontology saved to:[/] {ontology_path}")


# ---------------------------------------------------------------------------
# agentforge scan
# ---------------------------------------------------------------------------


@main.command()
def scan() -> None:
    """Scan your local development environment and display what was found."""
    _print_banner()
    config = _get_config()
    console.print(Rule("[bold cyan]Local Environment Scan[/]"))
    _run_scan_internal(config)


def _run_scan_internal(config: Config) -> None:
    """Internal scanner used by both `scan` and `run` commands."""
    from agentforge.scanner.tools import ToolScanner

    scanner = ToolScanner()
    profile = scanner.scan()
    profile.display()

    # Persist
    profile_path = config.output_dir / "tool_profile.json"
    profile_path.write_text(profile.to_json(), encoding="utf-8")
    console.print(f"\n[green]Tool profile saved to:[/] {profile_path}")


# ---------------------------------------------------------------------------
# agentforge search
# ---------------------------------------------------------------------------


@main.command()
@click.option("--days", default=90, help="Look back N days for active repos (default: 90)")
@click.option("--limit", default=10, help="Max repos per category (default: 10)")
def search(days: int, limit: int) -> None:
    """Search GitHub for trending AI/agent repos and run gap analysis."""
    _print_banner()
    config = _get_config()
    console.print(Rule("[bold cyan]GitHub Trend Search & Gap Analysis[/]"))
    _run_search_internal(config, days=days, limit=limit)


def _run_search_internal(
    config: Config, days: int = 90, limit: int = 10
) -> None:
    """Internal search+analysis used by both `search` and `run` commands."""
    from agentforge.github.searcher import GitHubSearcher
    from agentforge.github.analyzer import GapAnalyzer

    searcher = GitHubSearcher(
        token=config.github_token,
        max_per_category=limit,
        days_lookback=days,
    )
    repos = searcher.search_all()
    console.print(f"\n[green]Found {len(repos)} unique repositories.[/]")
    searcher.display_results(repos, limit=15)

    # Persist raw repo list
    repos_path = config.output_dir / "github_repos.json"
    repos_path.write_text(
        json.dumps([r.to_dict() for r in repos], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Gap analysis
    analyzer = GapAnalyzer(config)
    gap_analysis = analyzer.analyze(repos)
    gap_analysis.display()

    # Persist gap analysis
    gap_path = config.output_dir / "gap_analysis.json"
    gap_path.write_text(gap_analysis.to_json(), encoding="utf-8")
    console.print(f"\n[green]Gap analysis saved to:[/] {gap_path}")


# ---------------------------------------------------------------------------
# agentforge recommend
# ---------------------------------------------------------------------------


@main.command()
def recommend() -> None:
    """Generate personalized recommendations (requires prior survey and search)."""
    _print_banner()
    config = _get_config()
    console.print(Rule("[bold cyan]Personalized Recommendations[/]"))
    _run_recommend_internal(config)
    rec_set = _load_recommendations(config)
    rec_set.display()


def _run_recommend_internal(config: Config) -> None:
    """Internal recommender used by both `recommend` and `run` commands."""
    from agentforge.ontology.builder import PersonalOntology
    from agentforge.scanner.tools import ToolProfile
    from agentforge.github.analyzer import GapAnalysis, Opportunity
    from agentforge.recommender.engine import RecommendationEngine

    ontology = _load_ontology(config)

    # Load tool profile (run scan first if missing)
    profile_path = config.output_dir / "tool_profile.json"
    if profile_path.exists():
        tool_profile = ToolProfile(**json.loads(profile_path.read_text(encoding="utf-8")))
    else:
        console.print("[yellow]No tool profile found — running quick scan...[/]")
        from agentforge.scanner.tools import ToolScanner
        scanner = ToolScanner()
        tool_profile = scanner.scan()
        profile_path.write_text(tool_profile.to_json(), encoding="utf-8")

    # Load gap analysis (run search first if missing)
    gap_path = config.output_dir / "gap_analysis.json"
    if gap_path.exists():
        gap_data = json.loads(gap_path.read_text(encoding="utf-8"))
        opps = [
            Opportunity(
                title=o.get("title", ""),
                description=o.get("description", ""),
                affected_repos=o.get("affected_repos", []),
                potential_score=o.get("potential_score", 5),
                competition_level=o.get("competition_level", "medium"),
                technical_complexity=o.get("technical_complexity", "medium"),
                suggested_approach=o.get("suggested_approach", ""),
            )
            for o in gap_data.get("opportunities", [])
        ]
        gap_analysis = GapAnalysis(
            opportunities=opps,
            pain_themes=gap_data.get("pain_themes", []),
            saturated_areas=gap_data.get("saturated_areas", []),
            fast_moving_areas=gap_data.get("fast_moving_areas", []),
            ecosystem_summary=gap_data.get("ecosystem_summary", ""),
            best_entry_points=gap_data.get("best_entry_points", []),
        )
    else:
        console.print("[yellow]No gap analysis found — running GitHub search...[/]")
        _run_search_internal(config)
        return _run_recommend_internal(config)

    engine = RecommendationEngine(config)
    rec_set = engine.recommend(ontology, tool_profile, gap_analysis)

    # Persist
    recs_path = config.output_dir / "recommendations.json"
    recs_path.write_text(rec_set.to_json(), encoding="utf-8")
    console.print(f"\n[green]Recommendations saved to:[/] {recs_path}")


# ---------------------------------------------------------------------------
# agentforge build
# ---------------------------------------------------------------------------


@main.command()
@click.argument("rec_id", type=int, required=False)
def build(rec_id: Optional[int]) -> None:
    """Build the MVP for recommendation #REC_ID.

    If REC_ID is omitted, you will be prompted to choose.
    """
    _print_banner()
    config = _get_config()
    console.print(Rule("[bold cyan]MVP Builder[/]"))

    rec_set = _load_recommendations(config)
    rec_set.display()

    if rec_id is None:
        rec_id = click.prompt(
            "Which recommendation do you want to build? (Enter number 1-5)",
            type=int,
            default=1,
        )

    _run_build_internal(config, rec_id)


def _run_build_internal(config: Config, rec_id: int) -> None:
    """Internal build routine used by both `build` and `run` commands."""
    from agentforge.collector.data import DataCollector
    from agentforge.mvp.builder import MVPBuilder

    ontology = _load_ontology(config)
    rec_set = _load_recommendations(config)
    recommendation = rec_set.get_by_id(rec_id)

    if recommendation is None:
        console.print(f"[red]Recommendation #{rec_id} not found.[/] Valid IDs: 1–{len(rec_set.recommendations)}")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]{recommendation.project_name}[/]\n{recommendation.tagline}",
            title=f"[bold cyan]Building MVP: #{rec_id}[/]",
            border_style="cyan",
        )
    )

    # Collect research data
    collector = DataCollector(config)
    brief = collector.collect(recommendation, ontology)

    # Save brief
    brief_path = brief.save(config.output_dir)
    console.print(f"\n[green]Project brief saved to:[/] {brief_path}")

    # Build MVP
    builder = MVPBuilder(config)
    result = builder.build(brief, ontology)
    result.display()

    console.print(
        Panel(
            f"[bold green]MVP generated successfully![/]\n\n"
            f"[dim]Project:[/] {result.project_name}\n"
            f"[dim]Location:[/] {result.output_dir}\n"
            f"[dim]Files generated:[/] {len(result.files)}\n\n"
            "[bold]Run:[/] [cyan]cd "
            + str(result.output_dir)
            + " && pip install -r requirements.txt[/]",
            title="[bold green]Done![/]",
            border_style="green",
        )
    )
