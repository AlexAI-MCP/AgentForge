"""Tests for agentforge.ontology.survey module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentforge.ontology.survey import SurveyAnswers, QUESTIONS


class TestSurveyAnswers:
    """Tests for SurveyAnswers data model."""

    def test_default_construction(self) -> None:
        """SurveyAnswers should initialise with empty defaults."""
        answers = SurveyAnswers()
        assert answers.q1_primary_language == ""
        assert answers.q3_ai_tools == []
        assert answers.raw_responses == {}

    def test_to_dict_round_trip(self) -> None:
        """to_dict and from_dict should produce equivalent objects."""
        answers = SurveyAnswers(
            q1_primary_language="Python",
            q2_experience_years="5–10년 (5–10 years)",
            q3_ai_tools=["Claude / Claude Code", "GitHub Copilot"],
            q20_superpower="I ship very fast prototypes",
        )
        d = answers.to_dict()
        restored = SurveyAnswers.from_dict(d)

        assert restored.q1_primary_language == "Python"
        assert restored.q3_ai_tools == ["Claude / Claude Code", "GitHub Copilot"]
        assert restored.q20_superpower == "I ship very fast prototypes"

    def test_to_json_is_valid_json(self) -> None:
        """to_json should produce valid JSON."""
        answers = SurveyAnswers(q7_pain_point="반복적인 코드 작성")
        json_str = answers.to_json()
        parsed = json.loads(json_str)
        assert parsed["q7_pain_point"] == "반복적인 코드 작성"

    def test_from_json_round_trip(self) -> None:
        """from_json should restore an object serialized with to_json."""
        answers = SurveyAnswers(
            q15_geo_market="한국 (Korea — Korean language first)",
            q17_build_motivation="경제적 자유를 얻고 싶어서 (Financial freedom)",
        )
        restored = SurveyAnswers.from_json(answers.to_json())
        assert restored.q15_geo_market == answers.q15_geo_market
        assert restored.q17_build_motivation == answers.q17_build_motivation

    def test_save_and_load(self, tmp_path: Path) -> None:
        """save/load should round-trip through the filesystem."""
        answers = SurveyAnswers(
            q20_superpower="I automate everything",
            q18_past_project="Built a Telegram bot that processes 1M msgs/day",
        )
        path = tmp_path / "survey.json"
        answers.save(path)
        loaded = SurveyAnswers.load(path)

        assert loaded.q20_superpower == answers.q20_superpower
        assert loaded.q18_past_project == answers.q18_past_project


class TestQuestions:
    """Tests for the QUESTIONS constant structure."""

    def test_exactly_20_questions(self) -> None:
        """There must be exactly 20 questions."""
        assert len(QUESTIONS) == 20

    def test_question_ids_are_sequential(self) -> None:
        """Question IDs should be 1 through 20 with no gaps."""
        ids = [q["id"] for q in QUESTIONS]
        assert ids == list(range(1, 21))

    def test_all_questions_have_required_keys(self) -> None:
        """Every question must have id, field, title, subtitle, type."""
        required_keys = {"id", "field", "title", "subtitle", "type"}
        for question in QUESTIONS:
            missing = required_keys - set(question.keys())
            assert not missing, f"Q{question['id']} missing keys: {missing}"

    def test_choice_questions_have_choices(self) -> None:
        """Questions of type 'choice' or 'multi_choice' must have a choices list."""
        for question in QUESTIONS:
            if question["type"] in ("choice", "multi_choice"):
                assert "choices" in question, f"Q{question['id']} missing choices"
                assert len(question["choices"]) >= 2

    def test_free_text_questions_have_no_choices(self) -> None:
        """Free-text questions should not have a choices list."""
        for question in QUESTIONS:
            if question["type"] == "free_text":
                assert "choices" not in question, (
                    f"Q{question['id']} free_text should not have choices"
                )

    def test_field_names_are_unique(self) -> None:
        """Each question must map to a unique field name."""
        fields = [q["field"] for q in QUESTIONS]
        assert len(fields) == len(set(fields)), "Duplicate field names found"

    def test_q8_and_q18_and_q20_are_free_text(self) -> None:
        """Questions 8, 18, and 20 are designed as free-text entries."""
        free_text_ids = {q["id"] for q in QUESTIONS if q["type"] == "free_text"}
        assert 8 in free_text_ids
        assert 18 in free_text_ids
        assert 20 in free_text_ids
