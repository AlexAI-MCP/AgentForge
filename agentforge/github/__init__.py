"""
GitHub module: trend search and ecosystem gap analysis.

Fetches trending AI/agent repositories from the GitHub API and uses Claude
to identify gaps, common pain points in issues, and underserved opportunity
areas in the current open-source ecosystem.
"""

from agentforge.github.searcher import GitHubSearcher, RepoInfo
from agentforge.github.analyzer import GapAnalyzer, GapAnalysis, Opportunity

__all__ = ["GitHubSearcher", "RepoInfo", "GapAnalyzer", "GapAnalysis", "Opportunity"]
