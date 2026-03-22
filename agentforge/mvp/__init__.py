"""
MVP builder module: generates a working prototype from the project brief.

Uses Claude to generate actual Python files, a README, requirements.txt,
basic test stubs, and a Makefile — producing a runnable skeleton project
that the developer can immediately start iterating on.
"""

from agentforge.mvp.builder import MVPBuilder, MVPResult

__all__ = ["MVPBuilder", "MVPResult"]
