"""Graph state. A LangGraph TypedDict — the single source of truth every agent
node reads and writes. All orchestration is deterministic: hard-wired edges,
law guards, and human approvals are the only branching."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


def append_list(a: Optional[list[dict[str, Any]]], b: Optional[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return (a or []) + (b or [])


class AgentState(TypedDict, total=False):
    # --- run context -------------------------------------------------------
    topic: str
    reference: Optional[str]              # reference video path / analysis seed
    reference_analysis: dict[str, Any]    # structural template facts (from Analyzer or seed)

    # --- artifact chain ----------------------------------------------------
    blueprint: dict[str, Any]             # Analyzer output
    script: dict[str, Any]                # Planner output (markdown + segments)
    manifest: dict[str, Any]              # resource manifest (Planner)
    asset_bundle: dict[str, Any]          # Researcher output (user-confirmed)
    cut_spec: dict[str, Any]              # Editor output (timeline)
    visual_assignments: Annotated[list[dict[str, Any]], append_list]  # worker nodes
    tts_plan: dict[str, Any]              # Audio Lead output
    voice_track: dict[str, Any]           # TTS spec
    review_report: dict[str, Any]         # Reviewer output

    # --- control -----------------------------------------------------------
    pending_input: Optional[dict[str, Any]]   # question written by interrupt
    branch: Optional[str]                 # 'main-temporal-001' etc.
    iterations: int
    halted: bool

    # --- memory / mailbox --------------------------------------------------
    decisions: Annotated[list[dict[str, Any]], append_list]
    edits: Annotated[list[dict[str, Any]], append_list]
    log: Annotated[list[dict[str, Any]], append_list]
    mailboxes: dict[str, list[dict[str, Any]]]
    recruitments: Annotated[list[dict[str, Any]], append_list]
    registry: dict[str, Any]

    # --- law enforcement ---------------------------------------------------
    revocations: Annotated[list[dict[str, Any]], append_list]
    substitutions: Annotated[list[dict[str, Any]], append_list]   # user-approved substitutions
    blocks: Annotated[list[dict[str, Any]], append_list]

    # --- review loop -------------------------------------------------------
    review_decision: Optional[str]        # pass | revise | branch