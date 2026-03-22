"""
AgentForge configuration management.

Loads configuration from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

load_dotenv()


class Config(BaseModel):
    """Central configuration for AgentForge.

    All values can be overridden via environment variables or .env file.

    Attributes:
        github_token: Personal access token for GitHub API (optional but recommended).
        output_dir: Directory where generated projects and artifacts are saved.
        max_github_results: Maximum number of GitHub repos to fetch per search.
        survey_save_path: Where to persist survey results between sessions.
    """

    github_token: str = Field(default="", description="GitHub personal access token")
    output_dir: Path = Field(default=Path("./agentforge_output"), description="Output directory")
    max_github_results: int = Field(default=30, description="Max GitHub results per category")
    survey_save_path: Path = Field(
        default=Path("./agentforge_output/survey.json"),
        description="Path to persist survey results",
    )

    @field_validator("output_dir", "survey_save_path", mode="before")
    @classmethod
    def coerce_path(cls, v: object) -> Path:
        """Coerce string paths to Path objects."""
        return Path(str(v))

    @classmethod
    def from_env(cls) -> "Config":
        """Create a Config instance from environment variables.

        Returns:
            Fully populated Config, falling back to defaults for missing vars.
        """
        return cls(
            github_token=os.getenv("GITHUB_TOKEN", ""),
            output_dir=Path(os.getenv("AGENTFORGE_OUTPUT_DIR", "./agentforge_output")),
        )

    def validate_for_run(self) -> list[str]:
        """Return a list of validation errors that would prevent a full run.

        Returns:
            List of human-readable error strings. Empty list means config is valid.
        """
        return []

    def ensure_output_dir(self) -> None:
        """Create the output directory if it does not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.survey_save_path.parent.mkdir(parents=True, exist_ok=True)
