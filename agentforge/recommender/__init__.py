"""
Recommender module: personalized project recommendation engine.

Combines the Personal Ontology, ToolProfile, and GapAnalysis to generate
top-5 personalized project recommendations using Claude, complete with
opportunity scores, difficulty ratings, and differentiation strategies.
"""

from agentforge.recommender.engine import RecommendationEngine, Recommendation, RecommendationSet

__all__ = ["RecommendationEngine", "Recommendation", "RecommendationSet"]
