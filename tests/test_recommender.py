"""Tests for agentforge.recommender.engine module."""

from __future__ import annotations

import json

import pytest

from agentforge.recommender.engine import (
    Recommendation,
    RecommendationSet,
)


class TestRecommendation:
    """Tests for the Recommendation data model."""

    def _make_rec(self, rec_id: int = 1) -> Recommendation:
        return Recommendation(
            id=rec_id,
            project_name="ClaudeSkillForge",
            tagline="The missing npm for Claude Code skills",
            concept="A marketplace CLI for sharing and installing Claude skills.",
            why_fit="Your daily Claude Code usage gives you unique insight.",
            market_opportunity_score=9,
            difficulty_score=5,
            estimated_mvp_weeks=6,
            similar_projects=["npm", "pip"],
            differentiation="Claude-specific with revenue sharing",
            tech_stack=["Python", "FastAPI", "SQLite"],
            first_steps=["Design skill schema", "Build CLI installer"],
            monetization_path="5% revenue share on paid skills",
            risk_factors=["Anthropic may build this natively"],
        )

    def test_to_dict_is_serializable(self) -> None:
        """to_dict should produce JSON-serializable output."""
        rec = self._make_rec()
        d = rec.to_dict()
        json.dumps(d)  # must not raise

    def test_all_fields_preserved(self) -> None:
        """to_dict should preserve all fields."""
        rec = self._make_rec(rec_id=3)
        d = rec.to_dict()

        assert d["id"] == 3
        assert d["project_name"] == "ClaudeSkillForge"
        assert d["market_opportunity_score"] == 9
        assert d["difficulty_score"] == 5
        assert "Python" in d["tech_stack"]


class TestRecommendationSet:
    """Tests for the RecommendationSet container."""

    def _make_set(self) -> RecommendationSet:
        recs = [
            Recommendation(
                id=i,
                project_name=f"Project {i}",
                tagline=f"Tagline {i}",
                concept="A concept.",
                why_fit="It fits.",
                market_opportunity_score=8,
                difficulty_score=4,
                estimated_mvp_weeks=6,
            )
            for i in range(1, 6)
        ]
        return RecommendationSet(
            recommendations=recs,
            selection_rationale="These best match your profile.",
            overall_strategy="Start with #1, pivot if needed.",
        )

    def test_get_by_id_found(self) -> None:
        """get_by_id should return the correct recommendation."""
        rec_set = self._make_set()
        rec = rec_set.get_by_id(3)
        assert rec is not None
        assert rec.id == 3
        assert rec.project_name == "Project 3"

    def test_get_by_id_not_found(self) -> None:
        """get_by_id should return None for unknown IDs."""
        rec_set = self._make_set()
        assert rec_set.get_by_id(99) is None
        assert rec_set.get_by_id(0) is None

    def test_to_json_round_trip(self) -> None:
        """to_json should produce valid JSON with all recommendations."""
        rec_set = self._make_set()
        json_str = rec_set.to_json()
        parsed = json.loads(json_str)

        assert len(parsed["recommendations"]) == 5
        assert parsed["selection_rationale"] == "These best match your profile."
        assert parsed["overall_strategy"] == "Start with #1, pivot if needed."

    def test_to_dict_contains_all_fields(self) -> None:
        """to_dict should include recommendations, rationale, and strategy."""
        rec_set = self._make_set()
        d = rec_set.to_dict()

        assert "recommendations" in d
        assert "selection_rationale" in d
        assert "overall_strategy" in d
        assert len(d["recommendations"]) == 5
