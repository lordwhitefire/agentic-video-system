"""The 12 laws — deterministic guards, not suggestions. Every agent node runs
through `guard()` before it acts. The Watcher/Blocker re-runs the same checks
over the run log at watchpoints. Violations produce a revocation record and
block the offending action."""

from __future__ import annotations

from typing import Any, Callable

import avis.events as events

LAWS: list[dict[str, Any]] = [
    {"id": 1, "name": "No Inference",
     "rule": "never guess, gap-fill, fabricate, or silently assume anything not present in state",
     "check": lambda s, a, d: d.get("guessy", False)},
    {"id": 2, "name": "No Inference About Inference",
     "rule": "the watcher must prove a violation from the log; suspicion is not evidence",
     "check": lambda s, a, d: d.get("unproven", False)},
    {"id": 3, "name": "No Silent Substitution",
     "rule": "replacing a sourced asset requires an explicit user-approved substitution record",
     "check": lambda s, a, d: d.get("substitution", False)
           and not any(x.get("id") == d.get("substitution_id") for x in s.get("substitutions", []))},
    {"id": 4, "name": "No Auto-Correction",
     "rule": "no agent fixes work beyond the exact correction the user specified",
     "check": lambda s, a, d: bool(d.get("auto_correct", "")) and d["auto_correct"].get("authorized", False) is False},
    {"id": 5, "name": "No Carrying Over",
     "rule": "reference video content (frames, clips, opinions) never carries into the new video",
     "check": lambda s, a, d: bool(d.get("carry_over", []))},
    {"id": 6, "name": "No Effect Substitution",
     "rule": "effects come from the blueprint's visual vocabulary, not improvised alternatives",
     "check": lambda s, a, d: bool(d.get("effect_off_blueprint"))},
    {"id": 7, "name": "No Silent Engine Switching",
     "rule": "switching the TTS engine requires explicit user authorization in voice-profile",
     "check": lambda s, a, d: bool(d.get("engine_switch"))},
    {"id": 8, "name": "Graphics Must Contain Images",
     "rule": "every graphic overlay must reference a real sourced image",
     "check": lambda s, a, d: bool(d.get("graphic_without_image"))},
    {"id": 9, "name": "No Image Reusing",
     "rule": "an image may be assigned to at most one segment",
     "check": lambda s, a, d: bool(d.get("reused_image"))},
    {"id": 10, "name": "No Watermarked Images",
     "rule": "images flagged watermarked must be rejected, not cleaned or cropped",
     "check": lambda s, a, d: bool(d.get("watermarked"))},
    {"id": 11, "name": "No Silent Runtime Swap",
     "rule": "changing the rendering runtime (Colab/local/cloud) requires user confirmation",
     "check": lambda s, a, d: bool(d.get("runtime_swap"))},
    {"id": 12, "name": "No Assuming Context",
     "rule": "an agent only uses state fields that exist and were produced upstream",
     "check": lambda s, a, d: bool(d.get("assuming_context"))},
]

BY_ID: dict[int, dict[str, Any]] = {law["id"]: law for law in LAWS}


def guard(state: dict[str, Any], agent_id: str, action: dict[str, Any]) -> dict[str, Any]:
    """Run every law against an action. Returns a revocation record (or None).
    Deterministic: same state + action -> same verdict."""
    for law in LAWS:
        try:
            violated = law["check"](state, agent_id, action)
        except Exception:
            violated = False
        if violated:
            record = {"law": law["id"], "law_name": law["name"], "agent": agent_id,
                      "reason": law["rule"], "action": action, "blocked": True}
            events.bus.emit("watcher-blocker", "law_block",
                            f"[Law {law['id']}] {law['name']} — {law['rule']}",
                            law_id=law["id"], violator=agent_id)
            return record
    return {}


def describe() -> str:
    return "\n".join(f"  L{law['id']:>2} — {law['name']}: {law['rule']}" for law in LAWS)