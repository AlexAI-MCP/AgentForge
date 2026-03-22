"""Tests for agentforge.config module."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentforge.config import Config


class TestConfig:
    """Tests for Config model."""

    def test_default_values(self) -> None:
        """Config should have sensible defaults when no env vars are set."""
        config = Config()
        assert config.model == "claude-opus-4-6"
        assert config.anthropic_api_key == ""
        assert config.github_token == ""
        assert config.max_github_results == 30
        assert isinstance(config.output_dir, Path)

    def test_from_env_uses_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Config.from_env should read ANTHROPIC_API_KEY and GITHUB_TOKEN."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key_123")
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")
        monkeypatch.setenv("AGENTFORGE_MODEL", "claude-haiku-3-5")

        config = Config.from_env()

        assert config.anthropic_api_key == "test_key_123"
        assert config.github_token == "ghp_testtoken"
        assert config.model == "claude-haiku-3-5"

    def test_validate_for_run_missing_api_key(self) -> None:
        """validate_for_run should return an error when API key is absent."""
        config = Config(anthropic_api_key="")
        errors = config.validate_for_run()
        assert len(errors) == 1
        assert "ANTHROPIC_API_KEY" in errors[0]

    def test_validate_for_run_with_api_key(self) -> None:
        """validate_for_run should return empty list when API key is present."""
        config = Config(anthropic_api_key="sk-ant-test")
        errors = config.validate_for_run()
        assert errors == []

    def test_path_coercion(self) -> None:
        """Path fields should coerce strings to Path objects."""
        config = Config(output_dir="./my_output")  # type: ignore[arg-type]
        assert isinstance(config.output_dir, Path)
        assert str(config.output_dir) == "my_output"

    def test_ensure_output_dir_creates_directory(self, tmp_path: Path) -> None:
        """ensure_output_dir should create output_dir and survey parent."""
        config = Config(
            anthropic_api_key="test",
            output_dir=tmp_path / "new_output",
        )
        config.ensure_output_dir()
        assert config.output_dir.exists()
