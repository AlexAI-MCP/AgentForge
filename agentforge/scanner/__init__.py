"""
Scanner module: detects the local development environment.

Scans installed tools, AI plugins, VS Code extensions, npm packages,
Claude Code skills, and MCP server configurations to build a ToolProfile
that informs personalized recommendations.
"""

from agentforge.scanner.tools import ToolScanner, ToolProfile

__all__ = ["ToolScanner", "ToolProfile"]
