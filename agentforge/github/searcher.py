"""
GitHub API searcher for trending AI/agent repositories.

Searches multiple categories (agent-frameworks, llm-tools, automation,
developer-tools, data-pipelines) and returns rich RepoInfo objects with
star counts, topics, issue counts, and metadata needed for gap analysis.

Works without a GitHub token (60 req/hr) but benefits greatly from one
(5000 req/hr). Configure via GITHUB_TOKEN env var.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.parse import quote

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RepoInfo:
    """Metadata for a GitHub repository.

    Attributes:
        name: Full repository name (owner/repo).
        description: Repository description.
        stars: Star count (stargazers_count).
        forks: Fork count.
        issues_count: Open issues count.
        topics: List of topic tags.
        language: Primary programming language.
        last_updated: ISO 8601 datetime string of latest push.
        url: HTML URL of the repository.
        category: Search category this repo was found under.
        created_at: ISO 8601 datetime string of repository creation.
        license_name: SPDX license identifier or empty string.
        readme_excerpt: First 500 chars of README if fetched, else empty.
    """

    name: str
    description: str
    stars: int
    forks: int
    issues_count: int
    topics: list[str]
    language: str
    last_updated: str
    url: str
    category: str
    created_at: str = ""
    license_name: str = ""
    readme_excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Search categories
# ---------------------------------------------------------------------------

SEARCH_CATEGORIES: dict[str, list[str]] = {
    "agent-frameworks": [
        "topic:ai-agents language:python stars:>500",
        "topic:llm-agent language:python stars:>500",
        "agent framework llm python stars:>1000",
        "multi-agent orchestration stars:>500",
    ],
    "llm-tools": [
        "topic:llm-tools language:python stars:>500",
        "topic:langchain stars:>500",
        "llm prompt engineering library stars:>800",
        "topic:openai-api stars:>500",
    ],
    "automation": [
        "topic:automation ai agent stars:>500",
        "workflow automation llm stars:>500",
        "rpa ai python stars:>300",
        "computer use agent automation stars:>200",
    ],
    "developer-tools": [
        "topic:developer-tools ai assistant stars:>500",
        "code generation ai tool python stars:>500",
        "topic:claude-api stars:>200",
        "aider coding assistant stars:>500",
    ],
    "data-pipelines": [
        "topic:data-pipeline llm stars:>300",
        "rag retrieval augmented generation python stars:>500",
        "vector database embedding python stars:>500",
        "knowledge graph llm stars:>200",
    ],
}

_GITHUB_API_BASE = "https://api.github.com"
_SEARCH_ENDPOINT = f"{_GITHUB_API_BASE}/search/repositories"


# ---------------------------------------------------------------------------
# Searcher
# ---------------------------------------------------------------------------


class GitHubSearcher:
    """Searches GitHub for trending AI/agent repositories.

    Args:
        token: GitHub personal access token. Without one, requests are
            rate-limited to 60/hour. With a token, 5000/hour.
        max_per_category: Maximum repositories to return per category.
        days_lookback: Only include repos pushed within this many days.
    """

    def __init__(
        self,
        token: str = "",
        max_per_category: int = 10,
        days_lookback: int = 90,
    ) -> None:
        self.token = token
        self.max_per_category = max_per_category
        self.days_lookback = days_lookback
        self._headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def search_all(self) -> list[RepoInfo]:
        """Search all categories and return deduplicated repo list.

        Returns:
            Deduplicated list of RepoInfo objects sorted by star count descending.
        """
        console.print("\n[dim]Searching GitHub for trending AI/agent repositories...[/]\n")
        return asyncio.run(self._search_all_async())

    async def _search_all_async(self) -> list[RepoInfo]:
        """Async implementation that fetches all categories concurrently."""
        seen: set[str] = set()
        all_repos: list[RepoInfo] = []

        async with httpx.AsyncClient(
            headers=self._headers, timeout=30.0, follow_redirects=True
        ) as client:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                categories = list(SEARCH_CATEGORIES.keys())
                task = progress.add_task(
                    "[cyan]Fetching GitHub data...", total=len(categories)
                )

                for category in categories:
                    progress.update(
                        task, description=f"[cyan]Searching: {category}..."
                    )
                    queries = SEARCH_CATEGORIES[category]
                    repos = await self._search_category(client, category, queries)

                    for repo in repos:
                        if repo.name not in seen:
                            seen.add(repo.name)
                            all_repos.append(repo)

                    progress.advance(task)
                    # Be polite to the GitHub API
                    await asyncio.sleep(0.5)

        all_repos.sort(key=lambda r: r.stars, reverse=True)
        return all_repos

    async def _search_category(
        self,
        client: httpx.AsyncClient,
        category: str,
        queries: list[str],
    ) -> list[RepoInfo]:
        """Run one or more queries for a category, returning combined results."""
        repos: list[RepoInfo] = []
        seen_in_category: set[str] = set()
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.days_lookback)

        for query in queries:
            if len(repos) >= self.max_per_category:
                break
            try:
                batch = await self._run_query(client, query, category, cutoff)
                for repo in batch:
                    if repo.name not in seen_in_category:
                        seen_in_category.add(repo.name)
                        repos.append(repo)
                        if len(repos) >= self.max_per_category:
                            break
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 403:
                    console.print(
                        "[yellow]GitHub rate limit hit. Add GITHUB_TOKEN for more requests.[/]"
                    )
                    break
                # Other errors: log and continue
                console.print(f"[red]GitHub API error for query '{query}': {exc}[/]")

        return repos

    async def _run_query(
        self,
        client: httpx.AsyncClient,
        query: str,
        category: str,
        cutoff: datetime,
    ) -> list[RepoInfo]:
        """Execute a single GitHub search query and parse results."""
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        full_query = f"{query} pushed:>{cutoff_str}"

        params = {
            "q": full_query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(self.max_per_category, 15),
        }

        response = await client.get(_SEARCH_ENDPOINT, params=params)
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        items: list[dict[str, Any]] = data.get("items", [])

        repos: list[RepoInfo] = []
        for item in items:
            repo = self._parse_item(item, category)
            if repo:
                repos.append(repo)

        return repos

    def _parse_item(self, item: dict[str, Any], category: str) -> RepoInfo | None:
        """Parse a GitHub API repository item into a RepoInfo."""
        try:
            license_data = item.get("license") or {}
            return RepoInfo(
                name=item["full_name"],
                description=item.get("description") or "",
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                issues_count=item.get("open_issues_count", 0),
                topics=item.get("topics", []),
                language=item.get("language") or "",
                last_updated=item.get("pushed_at", ""),
                url=item.get("html_url", ""),
                category=category,
                created_at=item.get("created_at", ""),
                license_name=license_data.get("spdx_id", ""),
            )
        except KeyError:
            return None

    def display_results(self, repos: list[RepoInfo], limit: int = 20) -> None:
        """Display top repos in a Rich table."""
        table = Table(
            title=f"Top {min(limit, len(repos))} Trending AI/Agent Repos",
            border_style="dim",
            show_lines=False,
        )
        table.add_column("Repo", style="cyan", no_wrap=True, max_width=35)
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Category", style="green")
        table.add_column("Issues", justify="right")
        table.add_column("Description", max_width=50)

        for repo in repos[:limit]:
            table.add_row(
                repo.name,
                f"{repo.stars:,}",
                repo.category,
                str(repo.issues_count),
                repo.description[:80] + "..." if len(repo.description) > 80 else repo.description,
            )

        console.print(table)
