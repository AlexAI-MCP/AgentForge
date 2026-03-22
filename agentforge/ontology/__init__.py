"""
Ontology module: survey and personal ontology construction.

This module handles the 20-question interactive survey and the Claude-powered
synthesis of answers into a structured Personal Ontology used to personalize
all downstream recommendations.
"""

from agentforge.ontology.builder import OntologyBuilder, PersonalOntology
from agentforge.ontology.survey import SurveyRunner, SurveyAnswers

__all__ = ["OntologyBuilder", "PersonalOntology", "SurveyRunner", "SurveyAnswers"]
