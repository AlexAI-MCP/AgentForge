"""Tests for agentforge.collector.data module."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agentforge.collector.data import GitHubIssueInsight, ProjectBrief


class TestGitHubIssueInsight:
    """Tests for GitHubIssueInsight data model."""

    def test_construction(self) -> None:
        """GitHubIssueInsight should store all provided fields."""
        insight = GitHubIssueInsight(
            repo="langchain-ai/langchain",
            title="Add support for Claude tool use",
            url="https://github.com/langchain-ai/langchain/issues/123",
            theme="missing feature",
            insight="Users want native Claude tool-use support",
        )
        assert insight.repo == "langchain-ai/langchain"
        assert insight.theme == "missing feature"

    def test_to_dict_is_serializable(self) -> None:
        """to_dict should be JSON-serializable."""
        insight = GitHubIssueInsight(
            repo="owner/repo",
            title="Test issue",
            url="https://github.com/owner/repo/issues/1",
            theme="bug / stability",
            insight="Users want better error messages",
        )
        d = insight.to_dict()
        json.dumps(d)  # must not raise


class TestProjectBrief:
    """Tests for ProjectBrief data model."""

    def _make_brief(self) -> ProjectBrief:
        return ProjectBrief(
            project_name="ClaudeSkillForge",
            tagline="The missing npm for Claude Code skills",
            concept="A CLI marketplace for Claude skills.",
            why_fit="Your deep Claude experience makes this natural.",
            tech_stack=["Python", "FastAPI", "SQLite"],
            differentiation="Claude-specific with revenue sharing",
            mvp_scope=[
                "CLI: agentskill install <name>",
                "Skill schema (YAML descriptor)",
                "FastAPI registry",
            ],
            pain_point_evidence=[
                "Claude Code users spend time rewriting the same skill prompts",
            ],
            success_metrics=["100 skills published in 3 months"],
            first_steps=["Design skill schema", "Build CLI"],
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def test_to_json_is_valid_json(self) -> None:
        """to_json should produce valid JSON."""
        brief = self._make_brief()
        json_str = brief.to_json()
        parsed = json.loads(json_str)
        assert parsed["project_name"] == "ClaudeSkillForge"

    def test_to_markdown_contains_key_sections(self) -> None:
        """to_markdown should include project name, concept, and MVP scope."""
        brief = self._make_brief()
        md = brief.to_markdown()

        assert "# ClaudeSkillForge" in md
        assert "## Concept" in md
        assert "## MVP Scope" in md
        assert "CLI: agentskill install" in md

    def test_save_creates_both_files(self, tmp_path: Path) -> None:
        """save should create both .md and .json files."""
        brief = self._make_brief()
        md_path = brief.save(tmp_path)

        assert md_path.exists()
        assert md_path.suffix == ".md"

        json_path = tmp_path / "claudeskillforge_brief.json"
        assert json_path.exists()

    def test_save_returns_markdown_path(self, tmp_path: Path) -> None:
        """save should return the path to the Markdown file."""
        brief = self._make_brief()
        result = brief.save(tmp_path)
        assert result.suffix == ".md"

    def test_safe_name_in_filename(self, tmp_path: Path) -> None:
        """Saved files should use a filesystem-safe version of the project name."""
        brief = self._make_brief()
        md_path = brief.save(tmp_path)
        assert " " not in md_path.name
        assert "/" not in md_path.name
