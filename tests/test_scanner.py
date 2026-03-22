"""Tests for agentforge.scanner.tools module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agentforge.scanner.tools import ToolScanner, ToolProfile


class TestToolProfile:
    """Tests for ToolProfile data model."""

    def test_default_construction(self) -> None:
        """ToolProfile defaults should all be empty/False."""
        profile = ToolProfile()
        assert profile.python_packages == []
        assert profile.claude_skills == []
        assert not profile.has_anthropic_sdk
        assert not profile.has_docker

    def test_to_json_round_trip(self) -> None:
        """to_json/from_dict should round-trip correctly."""
        profile = ToolProfile(
            python_version="3.12.1",
            python_packages=["anthropic", "click", "rich"],
            has_anthropic_sdk=True,
            has_docker=False,
            environment_summary="Python 3.12.1 | Anthropic SDK",
        )
        json_str = profile.to_json()
        data = json.loads(json_str)
        restored = ToolProfile(**data)

        assert restored.python_version == "3.12.1"
        assert restored.has_anthropic_sdk is True
        assert "anthropic" in restored.python_packages

    def test_to_dict_is_serializable(self) -> None:
        """to_dict output must be JSON-serializable."""
        profile = ToolProfile(
            python_packages=["numpy", "pandas"],
            claude_skills=["code-review"],
        )
        d = profile.to_dict()
        json.dumps(d)  # must not raise


class TestToolScanner:
    """Tests for ToolScanner logic (mocked subprocess calls)."""

    def test_python_version_returns_string(self) -> None:
        """_get_python_version should return a non-empty version string."""
        scanner = ToolScanner()
        version = scanner._get_python_version()
        assert isinstance(version, str)
        assert "." in version  # e.g. "3.12.1"

    def test_get_python_packages_parses_output(self) -> None:
        """_get_python_packages should parse pip list output correctly."""
        scanner = ToolScanner()
        mock_output = (
            "Package    Version\n"
            "---------- -------\n"
            "anthropic  0.40.0\n"
            "click      8.1.7\n"
            "rich       13.7.0\n"
        )
        with patch.object(scanner, "_run", return_value=mock_output):
            packages = scanner._get_python_packages()

        assert "anthropic" in packages
        assert "click" in packages
        assert "rich" in packages

    def test_detect_ai_sdks_sets_flags(self) -> None:
        """_detect_ai_sdks should correctly set has_anthropic_sdk etc."""
        scanner = ToolScanner()
        profile = ToolProfile(python_packages=["anthropic", "openai", "numpy"])
        scanner._detect_ai_sdks(profile)

        assert profile.has_anthropic_sdk is True
        assert profile.has_openai_sdk is True
        assert profile.has_langchain is False

    def test_detect_langchain_prefix(self) -> None:
        """_detect_ai_sdks should detect langchain-* packages."""
        scanner = ToolScanner()
        profile = ToolProfile(python_packages=["langchain-core", "langchain-openai"])
        scanner._detect_ai_sdks(profile)
        assert profile.has_langchain is True

    def test_get_claude_skills_returns_list(self, tmp_path: Path) -> None:
        """_get_claude_skills should find files in the skills directory."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "code-review.md").write_text("# Review skill")
        (skills_dir / "refactor.yaml").write_text("name: refactor")

        scanner = ToolScanner()
        scanner._CLAUDE_SKILL_DIRS = [skills_dir]  # type: ignore[attr-defined]
        skills = scanner._get_claude_skills()

        assert "code-review" in skills
        assert "refactor" in skills

    def test_get_mcp_servers_parses_config(self, tmp_path: Path) -> None:
        """_get_mcp_servers should read mcpServers from Claude config."""
        config_file = tmp_path / "claude_config.json"
        config_file.write_text(
            json.dumps({
                "mcpServers": {
                    "filesystem": {"command": "mcp-server-filesystem"},
                    "github": {"command": "mcp-server-github"},
                }
            }),
            encoding="utf-8",
        )

        scanner = ToolScanner()
        scanner._CLAUDE_CONFIG_PATHS = [config_file]  # type: ignore[attr-defined]
        servers = scanner._get_mcp_servers()

        assert "filesystem" in servers
        assert "github" in servers

    def test_get_mcp_servers_handles_missing_file(self) -> None:
        """_get_mcp_servers should not crash when config file is missing."""
        scanner = ToolScanner()
        scanner._CLAUDE_CONFIG_PATHS = [Path("/nonexistent/path/config.json")]  # type: ignore[attr-defined]
        servers = scanner._get_mcp_servers()
        assert servers == []

    def test_get_git_repos_caps_at_20(self, tmp_path: Path) -> None:
        """_get_git_repos should return at most 20 repos."""
        # Create 25 fake git repos
        for i in range(25):
            repo = tmp_path / f"repo{i}"
            repo.mkdir()
            (repo / ".git").mkdir()

        scanner = ToolScanner()
        scanner._COMMON_REPO_DIRS = [tmp_path]  # type: ignore[attr-defined]
        repos = scanner._get_git_repos()

        assert len(repos) <= 20

    def test_build_summary_includes_key_info(self) -> None:
        """_build_summary should produce a non-empty descriptive string."""
        scanner = ToolScanner()
        profile = ToolProfile(
            python_version="3.11.8",
            has_anthropic_sdk=True,
            has_docker=True,
            claude_skills=["code-review", "refactor"],
        )
        summary = scanner._build_summary(profile)

        assert "3.11.8" in summary
        assert "Anthropic SDK" in summary
        assert "Docker" in summary
