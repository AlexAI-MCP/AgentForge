"""Tests for agentforge.github searcher and analyzer modules."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentforge.github.searcher import GitHubSearcher, RepoInfo
from agentforge.github.analyzer import GapAnalysis, Opportunity


class TestRepoInfo:
    """Tests for RepoInfo data model."""

    def test_construction(self) -> None:
        """RepoInfo should store all provided fields."""
        repo = RepoInfo(
            name="owner/repo",
            description="A test repo",
            stars=1500,
            forks=200,
            issues_count=45,
            topics=["ai", "agents"],
            language="Python",
            last_updated="2026-03-01T00:00:00Z",
            url="https://github.com/owner/repo",
            category="agent-frameworks",
        )
        assert repo.name == "owner/repo"
        assert repo.stars == 1500
        assert "ai" in repo.topics

    def test_to_dict_is_serializable(self) -> None:
        """to_dict should produce a JSON-serializable dictionary."""
        repo = RepoInfo(
            name="owner/repo",
            description="Test",
            stars=100,
            forks=10,
            issues_count=5,
            topics=["llm"],
            language="Python",
            last_updated="2026-01-01T00:00:00Z",
            url="https://github.com/owner/repo",
            category="llm-tools",
        )
        d = repo.to_dict()
        json.dumps(d)  # must not raise


class TestGitHubSearcherParsing:
    """Tests for GitHubSearcher._parse_item."""

    def test_parse_valid_item(self) -> None:
        """_parse_item should correctly convert a GitHub API response item."""
        searcher = GitHubSearcher()
        item = {
            "full_name": "owner/repo",
            "description": "Great AI framework",
            "stargazers_count": 5000,
            "forks_count": 300,
            "open_issues_count": 87,
            "topics": ["ai", "llm", "python"],
            "language": "Python",
            "pushed_at": "2026-03-15T12:00:00Z",
            "html_url": "https://github.com/owner/repo",
            "created_at": "2024-01-01T00:00:00Z",
            "license": {"spdx_id": "MIT"},
        }
        repo = searcher._parse_item(item, "agent-frameworks")

        assert repo is not None
        assert repo.name == "owner/repo"
        assert repo.stars == 5000
        assert repo.license_name == "MIT"
        assert repo.category == "agent-frameworks"

    def test_parse_item_with_none_description(self) -> None:
        """_parse_item should handle None description gracefully."""
        searcher = GitHubSearcher()
        item = {
            "full_name": "owner/repo",
            "description": None,
            "stargazers_count": 100,
            "forks_count": 10,
            "open_issues_count": 5,
            "topics": [],
            "language": None,
            "pushed_at": "2026-01-01T00:00:00Z",
            "html_url": "https://github.com/owner/repo",
            "created_at": "2025-01-01T00:00:00Z",
            "license": None,
        }
        repo = searcher._parse_item(item, "llm-tools")
        assert repo is not None
        assert repo.description == ""
        assert repo.language == ""
        assert repo.license_name == ""

    def test_parse_item_missing_key_returns_none(self) -> None:
        """_parse_item should return None on KeyError (malformed response)."""
        searcher = GitHubSearcher()
        item = {"description": "missing full_name key"}
        result = searcher._parse_item(item, "automation")
        assert result is None


class TestGapAnalysis:
    """Tests for GapAnalysis data model."""

    def test_default_construction(self) -> None:
        """GapAnalysis should initialise with empty defaults."""
        analysis = GapAnalysis()
        assert analysis.opportunities == []
        assert analysis.pain_themes == []
        assert analysis.ecosystem_summary == ""

    def test_opportunity_construction(self) -> None:
        """Opportunity should store all fields correctly."""
        opp = Opportunity(
            title="Missing evaluation toolkit",
            description="No good way to evaluate agent outputs",
            affected_repos=["langchain-ai/langchain"],
            potential_score=8,
            competition_level="low",
            technical_complexity="medium",
            suggested_approach="Build pytest-like framework for agent outputs",
        )
        assert opp.potential_score == 8
        assert opp.competition_level == "low"

    def test_to_json_round_trip(self) -> None:
        """GapAnalysis should serialize and deserialize correctly."""
        analysis = GapAnalysis(
            pain_themes=["missing evaluation", "poor documentation"],
            ecosystem_summary="The ecosystem is fragmented",
            best_entry_points=["agent evaluation", "skill sharing"],
        )
        json_str = analysis.to_json()
        parsed = json.loads(json_str)

        assert parsed["ecosystem_summary"] == "The ecosystem is fragmented"
        assert len(parsed["pain_themes"]) == 2
