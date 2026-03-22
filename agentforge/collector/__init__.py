"""
Collector module: automated data collection for a chosen project.

Once the user selects a recommendation, this module gathers supporting
research: related GitHub issues, similar project analysis, potential API
integrations, and generates a structured project_brief.md.
"""

from agentforge.collector.data import DataCollector, ProjectBrief

__all__ = ["DataCollector", "ProjectBrief"]
