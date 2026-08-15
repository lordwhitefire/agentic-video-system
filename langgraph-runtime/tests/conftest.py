"""Test environment: tests must run deterministically, offline, fast.
Forces the scripted brain regardless of keys present in the shell env."""

from __future__ import annotations

import os

os.environ["AVIS_LLM_ENABLED"] = "0"
for _k in ("OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "GLM_API_KEY"):
    os.environ.pop(_k, None)