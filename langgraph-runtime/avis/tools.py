"""Tool registry — deterministic, executable, observable.

Every tool call is emitted to the event bus so both UIs show exactly what each
agent does. Tools are pure functions over state; no tool hides anything.

RAG-style knowledge retrieval is included (`retrieve_memory`): a deterministic
keyword retrieval over the run's decisions/edits/mailbox — the knowledge
repository of the system."""

from __future__ import annotations

import re
import threading
from typing import Any, Callable

import avis.events as events
import avis.knowledge as knowledge

ToolFn = Callable[[dict[str, Any], list[Any]], dict[str, Any]]

# Tool call outputs are staged here for the current node invocation; the node
# wrapper merges them into the graph state update (append-reducers keep lists).
_pending = threading.local()

# Plan Mode execution gate. Tools that mutate state are rejected while the
# gate is on — Plan Mode has no execution authority (runtime-enforced, not a
# prompt instruction). Read-only inspection tools stay available.
_execution_gate = threading.local()

READ_ONLY_TOOLS = {"read_state", "retrieve_memory", "retrieve_knowledge",
                   "score_fidelity", "pass_through"}


def set_execution_blocked(flag: bool) -> None:
    """Turn the Plan-Mode gate on/off for the current thread."""
    _execution_gate.blocked = bool(flag)


def execution_blocked() -> bool:
    return getattr(_execution_gate, "blocked", False)


def drain_pending() -> dict[str, Any]:
    out = getattr(_pending, "updates", {})
    _pending.updates = {}
    return out


def _register(tools: dict[str, dict[str, Any]]):
    return lambda f: tools.setdefault(f.__name__, {"fn": f, "doc": (f.__doc__ or "").strip()}) or tools


REGISTRY: dict[str, dict[str, Any]] = {}


@_register(REGISTRY)
def read_state(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """read_state(field, ...) — read one or more state fields. Fails loudly (Law 12) if missing."""
    missing = [f for f in args if f not in state]
    if missing:
        return {"error": f"fields not produced upstream: {missing} (Law 12)"}
    return {f: state[f] for f in args}


@_register(REGISTRY)
def write_decision(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """write_decision(agent, text) — persist a decision to memory."""
    agent, text = args
    record = {"agent": agent, "text": text}
    return {"decisions": [record], "note": f"decision recorded by {agent}"}


@_register(REGISTRY)
def write_edit(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """write_edit(agent, file, change) — persist an edit to memory."""
    agent, file, change = args
    return {"edits": [{"agent": agent, "file": file, "change": change}]}


@_register(REGISTRY)
def retrieve_memory(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """retrieve_memory(query) — deterministic RAG-style retrieval over decisions, edits,
    mailboxes, and revocations. Splits the query into keywords; scores corpus entries
    by keyword overlap; returns the top matches. All facts come from the system's own
    knowledge repository — nothing invented (Law 1)."""
    query = args[0]
    tokens = {t for t in re.split(r"\W+", query.lower()) if len(t) > 2}
    corpus: list[tuple[str, str]] = []
    for rec in state.get("decisions", []):
        corpus.append(("decision", rec.get("text", "")))
    for rec in state.get("edits", []):
        corpus.append(("edit", f"{rec.get('file', '')} {rec.get('change', '')}"))
    for mb_name, items in (state.get("mailboxes") or {}).items():
        for m in items:
            corpus.append(("mailbox", f"{mb_name}: {m.get('text', '')}"))
    for rec in state.get("revocations", []):
        corpus.append(("revocation", f"Law {rec.get('law', '')} {rec.get('law_name', '')} {rec.get('reason', '')}"))

    scored = []
    for kind, text in corpus:
        text_tokens = {t for t in re.split(r"\W+", text.lower()) if len(t) > 2}
        overlap = len(tokens & text_tokens)
        if overlap:
            scored.append((overlap, kind, text))
    scored.sort(key=lambda x: -x[0])
    top = [{"kind": k, "text": t} for _, k, t in scored[:5]]
    return {"retrieved": top, "note": f"retrieved {len(top)} knowledge entries for query '{query}'"}


@_register(REGISTRY)
def retrieve_knowledge(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """retrieve_knowledge(query) — RAG over the persisted knowledge repository
    (every completed run). BM25 keyword ranking; deterministic; facts come only
    from recorded runs — nothing invented (Law 1)."""
    query = args[0]
    results = knowledge.retrieve(query)
    return {"retrieved_knowledge": results,
            "note": f"knowledge base: {len(results)} hit(s) for '{query}'"}


@_register(REGISTRY)
def propose_source(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """propose_source(kind, description, url, license_tbd, content_verified) — Researcher
    candidate. `content_verified` must be False unless concretely verified (Law 1)."""
    kind, description, url, license_tbd, content_verified = args
    return {"sourcing_proposals": [{
        "kind": kind, "description": description, "url": url,
        "license": "NOT_VERIFIED" if license_tbd else "VERIFIED",
        "content_verified": bool(content_verified)}],
        "note": "proposal flagged: license/content not verified until user confirms"}


@_register(REGISTRY)
def approve_source(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """approve_source(index_in_proposals) — user-verified source becomes part of the bundle."""
    idx = int(args[0])
    proposals = state.get("sourcing_proposals", [])
    if not (0 <= idx < len(proposals)):
        return {"error": "no proposal at that index (Law 12)"}
    return {"asset_bundle": {"assets": [proposals[idx], *state.get("asset_bundle", {}).get("assets", [])]},
            "note": "source approved as part of the Asset Bundle"}


@_register(REGISTRY)
def assign_visual(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """assign_visual(agent, segment, asset_id, kind, image_ref?) — a production worker
    appends a visual assignment. Law 8/9/10 enforced by the caller via `guard`."""
    agent, segment, asset_id, kind = args[:4]
    record: dict[str, Any] = {"agent": agent, "segment": segment, "asset_id": asset_id, "kind": kind}
    if len(args) > 4 and args[4]:
        record["image_ref"] = args[4]
    return {"visual_assignments": [record]}


@_register(REGISTRY)
def score_fidelity(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """score_fidelity() — Reviewer: deterministic fidelity scoring of the cut spec
    against the blueprint, asset bundle, and TTS plan."""
    blueprint = state.get("blueprint", {})
    bundle = state.get("asset_bundle", {}).get("assets", [])
    spec = state.get("cut_spec", {})
    tts = state.get("voice_track", {})

    template_count = len(blueprint.get("segments", [])) if isinstance(blueprint.get("segments"), list) else 0
    cut_count = len(spec.get("shots", []))
    owned = {a.get("id") for a in bundle}
    used = {s.get("asset_id") for s in spec.get("shots", [])}
    assigned = state.get("visual_assignments", [])

    missing_assets = sorted(used - owned)
    images_no_overlay = [a.get("segment") for a in assigned
                         if (a.get("kind") or "").startswith("graphic") and not a.get("image_ref")]
    per_kind: dict[str, list[str]] = {}
    for a in assigned:
        per_kind.setdefault(a.get("kind") or "", []).append(a.get("asset_id"))
    reuse = sum(len(v) - len(set(v)) for v in per_kind.values())
    tts_ok = len(tts.get("segments", [])) == cut_count if cut_count else False

    target = blueprint.get("target_duration_s") or 0
    pacing = spec.get("estimated_duration_s", 0) - target

    checks = {
        "structure_fidelity": cut_count == template_count,
        "pacing_within_tolerance": abs(pacing) <= max(1, 0.05 * target),
        "all_assets_exist": not missing_assets,
        "graphics_have_images": not images_no_overlay,
        "no_image_reuse": reuse == 0,
        "tts_coverage": tts_ok,
    }
    passed = all(checks.values())
    return {"review_report": {
        "checks": checks,
        "missing_assets": missing_assets,
        "decision": "pass" if passed else ("revise" if missing_assets or not tts_ok else "branch")}}


@_register(REGISTRY)
def tts_plan(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """tts_plan(engine, voice_sample) — Audio Lead picks the engine from voice-profile;
    switching engines demands explicit authorization (Law 7)."""
    engine, voice_sample = args
    profile = state.get("voice_profile", {})
    default = profile.get("default_engine")
    if engine and engine != default:
        authorized = profile.get("authorized_engines") or []
        if engine not in authorized:
            return {"error": f"engine switch to {engine} not authorized (Law 7)"}
    return {"tts_plan": {
        "engine": engine or default,
        "voice_sample": voice_sample or profile.get("voice_sample_path"),
        "loudness_target_lufs": profile.get("loudness_target_lufs", -16),
        "segments": [{"segment": i, "wav": f"segment_{i:02d}.wav"} for i in range(1, 11)]}}


@_register(REGISTRY)
def pass_through(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """pass_through() — deterministic no-op for nodes whose work is pure state routing."""
    return {"note": "no state mutation this visit"}


def call(state: dict[str, Any], agent_id: str, tool: str, *args: Any) -> dict[str, Any]:
    if tool not in REGISTRY:
        events.bus.emit(agent_id, "tool_result", f"tool '{tool}' not found (Law 12)", error=True)
        return {"error": f"unknown tool {tool}"}
    if execution_blocked() and tool not in READ_ONLY_TOOLS:
        # Plan Mode has no execution authority: the tool is observed but never
        # run, never staged, never mutated. The error is real and visible.
        events.bus.emit(agent_id, "tool_call", f"{tool}({', '.join(str(a) for a in args)})",
                        tool=tool, args=list(args), blocked=True)
        events.bus.emit(agent_id, "tool_result",
                        f"{tool} blocked: Plan Mode has no execution authority (read-only inspection only)",
                        tool=tool, error=True, blocked=True)
        return {"error": f"blocked: Plan Mode has no execution authority ({tool})"}
    events.bus.emit(agent_id, "tool_call", f"{tool}({', '.join(str(a) for a in args)})", tool=tool, args=list(args))
    try:
        result = REGISTRY[tool]["fn"](state, list(args))
    except Exception as e:
        result = {"error": f"{tool} failed: {e}"}
    # stage every non-error output key for the current node's state update
    if "error" not in result:
        staged = getattr(_pending, "updates", None) or {}
        updates = dict(staged)
        for k, v in result.items():
            if k in ("note", "error"):
                continue
            cur = updates.get(k)
            if isinstance(cur, list) and isinstance(v, list):
                cur = cur + v
            else:
                cur = v
            updates[k] = cur
        _pending.updates = updates
    events.bus.emit(agent_id, "tool_result", f"{tool} -> {result.get('note') or result}",
                    tool=tool)
    return result