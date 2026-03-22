"""Tests for agentforge.mvp.builder module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentforge.mvp.builder import MVPBuilder, MVPResult, GeneratedFile


class TestMVPBuilderHelpers:
    """Tests for MVPBuilder static/private helpers."""

    def test_safe_package_name_basic(self) -> None:
        """Simple names should come through with spaces replaced."""
        result = MVPBuilder._safe_package_name("ClaudeSkillForge")
        assert result == "claudeskillforge"

    def test_safe_package_name_with_spaces(self) -> None:
        """Spaces should become underscores."""
        result = MVPBuilder._safe_package_name("Agent Eval Toolkit")
        assert result == "agent_eval_toolkit"

    def test_safe_package_name_with_hyphens(self) -> None:
        """Hyphens should become underscores."""
        result = MVPBuilder._safe_package_name("my-great-tool")
        assert result == "my_great_tool"

    def test_safe_package_name_with_slashes(self) -> None:
        """Slashes should become underscores."""
        result = MVPBuilder._safe_package_name("owner/repo-name")
        assert result == "owner_repo_name"

    def test_safe_package_name_empty_fallback(self) -> None:
        """Empty or all-special-char names fall back to 'my_project'."""
        result = MVPBuilder._safe_package_name("!!!###")
        assert result == "my_project"

    def test_safe_package_name_collapses_underscores(self) -> None:
        """Multiple consecutive underscores should be collapsed."""
        result = MVPBuilder._safe_package_name("my--great---tool")
        assert "__" not in result


class TestMVPResult:
    """Tests for MVPResult data model."""

    def test_construction(self, tmp_path: Path) -> None:
        """MVPResult should store all provided fields."""
        files = [
            GeneratedFile(path="pkg/__init__.py", content="# init", description="Package init"),
            GeneratedFile(path="README.md", content="# Readme", description="Docs"),
        ]
        result = MVPResult(
            project_name="TestProject",
            output_dir=tmp_path,
            files=files,
            setup_instructions=["pip install -r requirements.txt"],
            next_steps=["Deploy to production"],
        )
        assert result.project_name == "TestProject"
        assert len(result.files) == 2
        assert result.output_dir == tmp_path


class TestGeneratedFile:
    """Tests for GeneratedFile data model."""

    def test_construction(self) -> None:
        """GeneratedFile should store path, content, and description."""
        gf = GeneratedFile(
            path="src/main.py",
            content="print('hello')",
            description="Main entry point",
        )
        assert gf.path == "src/main.py"
        assert gf.content == "print('hello')"
        assert gf.description == "Main entry point"

    def test_default_description(self) -> None:
        """description should default to empty string."""
        gf = GeneratedFile(path="x.py", content="")
        assert gf.description == ""


class TestMinimalScaffold:
    """Tests for MVPBuilder._minimal_scaffold fallback."""

    def test_scaffold_contains_required_files(self) -> None:
        """Minimal scaffold should include __init__, main, README, requirements, tests."""
        from agentforge.collector.data import ProjectBrief
        from agentforge.config import Config

        config = Config(anthropic_api_key="test", output_dir=Path("/tmp/test"))
        builder = MVPBuilder(config)

        brief = ProjectBrief(
            project_name="Test Project",
            tagline="A test",
            concept="Just a test project",
            why_fit="Fits well",
            tech_stack=["Python"],
        )
        scaffold = builder._minimal_scaffold(brief, "test_project")

        file_paths = [f["path"] for f in scaffold["files"]]
        assert any("__init__" in p for p in file_paths)
        assert any("main.py" in p for p in file_paths)
        assert any("README" in p for p in file_paths)
        assert any("requirements" in p for p in file_paths)
        assert any("test_" in p for p in file_paths)

    def test_scaffold_setup_instructions_non_empty(self) -> None:
        """Minimal scaffold should always provide setup instructions."""
        from agentforge.collector.data import ProjectBrief
        from agentforge.config import Config

        config = Config(anthropic_api_key="test", output_dir=Path("/tmp/test"))
        builder = MVPBuilder(config)

        brief = ProjectBrief(
            project_name="Test",
            tagline="test",
            concept="test",
            why_fit="test",
        )
        scaffold = builder._minimal_scaffold(brief, "test")
        assert len(scaffold["setup_instructions"]) > 0
