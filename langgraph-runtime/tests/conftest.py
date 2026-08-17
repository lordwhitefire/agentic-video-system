"""Test environment: tests must run deterministically, offline, fast.
Forces the scripted brain regardless of keys present in the shell env."""

from __future__ import annotations

import os
from pathlib import Path

os.environ["AVIS_LLM_ENABLED"] = "0"
for _k in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "GLM_API_KEY"):
    os.environ.pop(_k, None)

import pytest


@pytest.fixture(autouse=True)
def _isolate_created_agents(tmp_path, monkeypatch):
    """W2 — created agents persist under data/agents/; tests isolate that
    directory and restore the real registry state afterwards."""
    import avis.agents as agents

    original = agents.CREATED_DIR
    monkeypatch.setattr(agents, "CREATED_DIR", Path(tmp_path) / "agents")
    agents._rebuild()
    yield
    agents.CREATED_DIR = original
    agents._rebuild()