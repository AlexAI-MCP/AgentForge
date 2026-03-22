"""
Shared pytest fixtures for AgentForge tests.

Provides a Windows-compatible tmp_path replacement that writes to a
known-writable directory inside the project, avoiding Windows AppData
temp permission issues.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

# Use a tmp directory inside the project tree — always writable
_TMP_BASE = Path(__file__).parent.parent / ".test_tmp"


@pytest.fixture
def tmp_path() -> Path:  # type: ignore[override]
    """Provide a unique temporary directory inside the project tree.

    Cleans up after the test regardless of pass/fail status.
    """
    test_dir = _TMP_BASE / str(uuid.uuid4())
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir  # type: ignore[misc]
    shutil.rmtree(test_dir, ignore_errors=True)
