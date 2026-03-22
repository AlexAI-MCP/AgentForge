"""Tests for agentforge.ontology.builder module."""

from __future__ import annotations

import json

import pytest

from agentforge.ontology.builder import PersonalOntology


class TestPersonalOntology:
    """Tests for PersonalOntology data model."""

    def test_default_construction(self) -> None:
        """PersonalOntology should have sensible defaults."""
        onto = PersonalOntology()
        assert onto.builder_style == "builder"
        assert onto.risk_profile == "moderate"
        assert onto.strengths == []
        assert onto.recommended_domains == []

    def test_to_json_is_valid(self) -> None:
        """to_json should produce valid JSON."""
        onto = PersonalOntology(
            strengths=["Python", "Anthropic API"],
            builder_style="hacker",
            superpower_summary="I ship extremely fast",
        )
        json_str = onto.to_json()
        parsed = json.loads(json_str)

        assert parsed["builder_style"] == "hacker"
        assert "Python" in parsed["strengths"]

    def test_from_dict_round_trip(self) -> None:
        """from_dict should restore an ontology from a dictionary."""
        original = PersonalOntology(
            strengths=["Python", "Claude API"],
            gaps=["Marketing", "Frontend"],
            opportunities=["Developer tools", "Korean market"],
            recommended_domains=["AI tooling"],
            builder_style="builder",
            risk_profile="moderate",
            time_horizon="3–6 months",
            target_persona="AI developers",
            monetization_fit="Open-core",
            geo_advantage="Korean developer community",
            motivation_core="Scratch own itch",
            superpower_summary="Ship fast, iterate faster",
            pain_point_focus="Repetitive boilerplate code",
            ideal_project_traits=["Solves my own problem", "< 2 month MVP"],
        )
        d = original.to_dict()
        restored = PersonalOntology.from_dict(d)

        assert restored.builder_style == "builder"
        assert restored.geo_advantage == "Korean developer community"
        assert "Python" in restored.strengths
        assert len(restored.ideal_project_traits) == 2

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """from_dict should silently ignore keys not in the dataclass."""
        data = {
            "strengths": ["Python"],
            "builder_style": "researcher",
            "unknown_future_field": "some_value",
        }
        onto = PersonalOntology.from_dict(data)
        assert onto.builder_style == "researcher"
        assert onto.strengths == ["Python"]

    def test_from_json_round_trip(self) -> None:
        """from_json(to_json()) should produce an equivalent object."""
        original = PersonalOntology(
            superpower_summary="Deep financial domain + AI",
            pain_point_focus="Manual report generation",
            risk_profile="aggressive",
        )
        restored = PersonalOntology.from_json(original.to_json())

        assert restored.superpower_summary == original.superpower_summary
        assert restored.pain_point_focus == original.pain_point_focus
        assert restored.risk_profile == "aggressive"

    def test_to_dict_all_fields_present(self) -> None:
        """to_dict should include all declared fields."""
        onto = PersonalOntology()
        d = onto.to_dict()

        expected_fields = [
            "strengths", "gaps", "opportunities", "recommended_domains",
            "builder_style", "risk_profile", "time_horizon", "target_persona",
            "monetization_fit", "geo_advantage", "motivation_core",
            "superpower_summary", "pain_point_focus", "ideal_project_traits",
            "raw_claude_analysis",
        ]
        for field in expected_fields:
            assert field in d, f"Missing field: {field}"
