"""
LLM interface — uses the locally authenticated `claude` CLI instead of API keys.

No ANTHROPIC_API_KEY needed. Works wherever Claude Code is installed.
Falls back gracefully if `claude` binary is not found.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any

from rich.console import Console

console = Console()

_CLAUDE_BIN: str | None = shutil.which("claude")


def _find_claude() -> str:
    """Locate the claude binary; raises if not found."""
    if _CLAUDE_BIN:
        return _CLAUDE_BIN
    # Common Windows paths
    import os
    candidates = [
        os.path.expanduser("~\\AppData\\Roaming\\npm\\claude.cmd"),
        os.path.expanduser("~\\AppData\\Local\\Programs\\claude\\claude.exe"),
        "claude",
    ]
    for c in candidates:
        if shutil.which(c):
            return c
    raise FileNotFoundError(
        "claude CLI not found. Install Claude Code: https://claude.ai/download"
    )


def ask(prompt: str, system: str = "", max_retries: int = 2) -> str:
    """Run a prompt through the local claude CLI via stdin and return the text response.

    Args:
        prompt: The user prompt to send.
        system: Optional system prompt prepended to the message.
        max_retries: Number of retries on transient errors.

    Returns:
        Raw text response from Claude.
    """
    import tempfile
    import os

    binary = _find_claude()

    json_instruction = "\n\nIMPORTANT: Respond ONLY with the requested output. No questions, no clarifications, no preamble."
    full_prompt = f"{system}\n\n{prompt}{json_instruction}" if system else f"{prompt}{json_instruction}"

    # Write prompt to temp file to avoid command-line length limits
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(full_prompt)
        tmp_path = f.name

    try:
        # Use stdin piping to avoid shell argument length limits
        cmd = [binary, "-p", full_prompt, "--output-format", "text"]

        for attempt in range(max_retries + 1):
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    encoding="utf-8",
                    errors="replace",
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
                if attempt < max_retries:
                    console.print(f"[yellow]Retry {attempt + 1}/{max_retries}...[/]")
                else:
                    err = result.stderr[:300] if result.stderr else "empty output"
                    raise RuntimeError(f"claude CLI failed (code {result.returncode}): {err}")
            except subprocess.TimeoutExpired:
                if attempt < max_retries:
                    console.print("[yellow]Timeout, retrying...[/]")
                else:
                    raise
    finally:
        os.unlink(tmp_path)

    return ""


def ask_json(prompt: str, system: str = "", max_retries: int = 2) -> Any:
    """Run a prompt expecting JSON output; strips markdown fences and parses.

    Args:
        prompt: The user prompt to send.
        system: Optional system prompt.
        max_retries: Number of retries on parse or API failure.

    Returns:
        Parsed Python object (dict or list).

    Raises:
        ValueError: If JSON cannot be parsed after all retries.
    """
    raw = ask(prompt, system=system, max_retries=max_retries)

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
    cleaned = cleaned.rstrip("`").strip()

    # Try to extract just the JSON portion
    for pattern in [r"(\[[\s\S]*\])", r"(\{[\s\S]*\})"]:
        match = re.search(pattern, cleaned)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Could not parse JSON from Claude response.\nRaw:\n{raw[:800]}"
        ) from exc


def is_available() -> bool:
    """Check whether the claude CLI is available."""
    try:
        _find_claude()
        return True
    except FileNotFoundError:
        return False
