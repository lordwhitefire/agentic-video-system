"""The 17 agents, as deterministic LangGraph nodes.

Org chart (mirrors the opencode version):
  CEO (you, human) → 5 department heads → 12 workers
  Strategy: strategist(head), analyzer, planner, researcher
  Audio: audio-lead(head), tts
  Production: editor(head), graphics, animation, animated-graphics, video-effects, clips, images
  Quality: reviewer(head), watcher-blocker, investigator
  Personnel: recruiter(head)

Each node is `work(state) -> updates`. The wrapper emits thinking (brain),
routes results, and applies the law guard. Orchestration stays deterministic:
hard-wired edges, watchpoints, and human approvals."""

from __future__ import annotations

from typing import Any, Callable, Optional

from langgraph.types import interrupt

import avis.events as events
import avis.tools as tools
from avis.laws import guard
from avis.brain import think_stream

SEGMENT_ROLES = ["cold_open", "hook", "thesis", "act_1", "act_2", "act_3",
                 "act_4", "act_5", "act_6", "conclusion"]


# --------------------------------------------------------------------------
# agent catalog
# --------------------------------------------------------------------------
AGENTS: list[dict[str, Any]] = [
    {"id": "strategist",         "department": "Strategy",   "tier": "head",   "manages": ["analyzer", "planner", "researcher"]},
    {"id": "analyzer",           "department": "Strategy",   "tier": "worker", "head": "strategist"},
    {"id": "planner",            "department": "Strategy",   "tier": "worker", "head": "strategist"},
    {"id": "researcher",         "department": "Strategy",   "tier": "worker", "head": "strategist"},
    {"id": "audio-lead",         "department": "Audio",      "tier": "head",   "manages": ["tts"]},
    {"id": "tts",                "department": "Audio",      "tier": "worker", "head": "audio-lead"},
    {"id": "editor",             "department": "Production", "tier": "head",   "manages": ["graphics", "animation", "animated-graphics", "video-effects", "clips", "images"]},
    {"id": "graphics",           "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "animation",          "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "animated-graphics",  "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "video-effects",      "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "clips",              "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "images",             "department": "Production", "tier": "worker", "head": "editor"},
    {"id": "reviewer",           "department": "Quality",    "tier": "head",   "manages": ["watcher-blocker", "investigator"]},
    {"id": "watcher-blocker",    "department": "Quality",    "tier": "worker", "head": "reviewer"},
    {"id": "investigator",       "department": "Quality",    "tier": "worker", "head": "reviewer"},
    {"id": "recruiter",          "department": "Personnel",  "tier": "head",   "manages": []},
]

BY_ID: dict[str, dict[str, Any]] = {a["id"]: a for a in AGENTS}

EFFECTS = ["cut", "dissolve", "crossfade"]


class NodeSpec:
    def __init__(self, agent_id: str, work: Callable[[dict[str, Any]], dict[str, Any]],
                 ctx: Optional[Callable[[dict[str, Any]], dict[str, Any]]] = None) -> None:
        self.agent_id = agent_id
        self.work = work
        self.ctx = ctx or (lambda s: {"topic": s.get("topic"), "blueprint": s.get("blueprint"),
                                      "_missing": []})


def run_node(spec: NodeSpec) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Wrapper: thinking → law-guarded work → result event → state updates."""
    def node(state: dict[str, Any]) -> dict[str, Any]:
        events.bus.emit(spec.agent_id, "note", f"{spec.agent_id} invoked "
                        f"({BY_ID[spec.agent_id]['department']} / {BY_ID[spec.agent_id]['tier']})")
        think_stream(spec.agent_id, spec.ctx(state))
        updates = spec.work(state) or {}
        staged = tools.drain_pending()
        updates = {**staged, **updates}  # explicit node keys win over staged tool keys
        if "error" in updates:
            events.bus.emit(spec.agent_id, "note", f"stopped: {updates['error']}")
            updates.setdefault("log", [{"agent": spec.agent_id, "level": "error", "text": updates["error"]}])
        events.bus.emit(spec.agent_id, "result", f"{spec.agent_id} -> {updates.get('note', 'ok')}")
        return updates
    return node


# --------------------------------------------------------------------------
# deterministic work per agent
# --------------------------------------------------------------------------
def _fmt(segments: list[dict[str, Any]], topic: str) -> str:
    return "\n".join(f"{i+1}. {seg['name']} ({seg.get('purpose', '')})" for i, seg in enumerate(segments))


def work_strategist(state: dict[str, Any]) -> dict[str, Any]:
    topic, analysis = state.get("topic"), state.get("reference_analysis")
    missing = [f for f, v in (("topic", topic), ("reference_analysis", analysis)) if not v]
    if missing:
        return {"error": f"missing inputs: {missing}", "note": "awaiting CEO inputs",
                "log": [{"agent": "strategist", "level": "info", "text": f"waiting on: {missing}"}]}
    n = len(analysis.get("segments", []))
    tools.call(state, "strategist", "write_decision", "strategist",
               f"run plan locked: {analysis.get('form','long-form')} {analysis.get('genre','')}, {n}-segment template")
    return {"note": f"plan locked, routing {BY_ID['strategist']['manages']}", "iterations": state.get("iterations", 0) + 1}


def work_analyzer(state: dict[str, Any]) -> dict[str, Any]:
    analysis = state.get("reference_analysis")
    if not analysis:
        return {"error": "reference_analysis missing (Law 12)", "note": "no reference to perceive"}
    blueprint = {k: analysis[k] for k in ("form", "genre", "visual_vocabulary", "audio_structure")
                 if k in analysis}
    blueprint["template_framing"] = analysis.get("template_framing", {})
    blueprint["target_duration_s"] = analysis.get("target_duration_s")
    blueprint["avg_shot_s"] = analysis.get("avg_shot_s")
    blueprint["segments"] = [{"name": s["name"], "role": s.get("role", "segment"),
                              "purpose": s.get("purpose", "")} for s in analysis.get("segments", [])]
    tools.call(state, "analyzer", "write_decision", "analyzer",
               f"blueprint produced: {len(blueprint['segments'])} segments, structural shell only")
    return {"blueprint": blueprint, "note": f"Blueprint ready ({len(blueprint['segments'])} segments)"}


def work_planner(state: dict[str, Any]) -> dict[str, Any]:
    blueprint, topic = state.get("blueprint"), state.get("topic")
    if not blueprint or not topic:
        return {"error": "blueprint or topic missing"}
    segments = [{"name": s["name"], "purpose": s.get("purpose", ""),
                 "mapped_topic": f"{topic} — {SEGMENT_ROLES[min(i, len(SEGMENT_ROLES)-1)]} beat"}
                for i, s in enumerate(blueprint.get("segments", []))]
    script_md = f"# Script — {topic}\n\n" + _fmt(segments, topic)
    prior = tools.call(state, "planner", "retrieve_knowledge", topic)
    manifest = {"segments": [
        {"segment": s["name"], "requires": ["clips", "images", "audio"]} for s in segments],
        "prior_knowledge": prior.get("retrieved_knowledge", [])}
    tools.call(state, "planner", "write_decision", "planner",
               f"script + manifest drafted for '{topic}' ({len(segments)} segments)")
    answer = interrupt({"question": "Approve script and resource manifest?",
                        "script": script_md, "manifest": manifest})
    if answer != "approve":
        events.bus.emit("planner", "note", f"script rejected by CEO: {answer}")
        return {"error": "script not approved"}
    events.bus.emit("planner", "note", "script approved by CEO")
    return {"script": {"markdown": script_md, "segments": segments}, "manifest": manifest,
            "note": f"script + manifest approved ({len(segments)} segments)"}


def work_researcher(state: dict[str, Any]) -> dict[str, Any]:
    manifest = state.get("manifest")
    if not manifest:
        return {"error": "manifest missing"}
    proposals: list[dict[str, Any]] = []
    for i, seg in enumerate(manifest.get("segments", [])):
        for kind, desc, url in (
            ("videoclip", f"clip candidates for {seg['segment']}", f"https://source.example/{i}"),
            ("image", f"image candidates for {seg['segment']}", "https://image.example"),
        ):
            result = tools.call(state, "researcher", "propose_source", kind, desc, url, True, False)
            proposals.extend(result.get("sourcing_proposals", []))
    for i, p in enumerate(proposals):
        p["id"] = f"src-{i + 1}"
    if not proposals:
        return {"error": "no source proposals generated"}
    answer = interrupt({"question": "Approve Asset Bundle? (reply 'approve' — replacements must be declared, Law 3)",
                        "proposals": proposals})
    if answer != "approve":
        return {"error": f"asset bundle not approved: {answer}"}
    bundle = [dict(p) for p in proposals]
    tools.call(state, "researcher", "write_decision", "researcher",
               f"asset bundle confirmed: {len(bundle)} sources, license/content verification pending")
    return {"asset_bundle": {"assets": bundle}, "note": f"Asset Bundle confirmed ({len(bundle)} sources)"}


def work_audio_lead(state: dict[str, Any]) -> dict[str, Any]:
    profile = state.get("voice_profile") or {}
    engine = profile.get("default_engine")
    tools.call(state, "audio-lead", "tts_plan", engine, profile.get("voice_sample_path"))
    return {"note": f"TTS plan locked on {engine}"}


def work_tts(state: dict[str, Any]) -> dict[str, Any]:
    plan = state.get("tts_plan")
    if not plan:
        return {"error": "tts_plan missing"}
    n = len(state.get("script", {}).get("segments", [])) or 10
    voice_track = {"engine": plan.get("engine"), "voice_sample": plan.get("voice_sample"),
                   "loudness_target_lufs": plan.get("loudness_target_lufs", -16),
                   "segments": [{"segment": i + 1, "wav": f"segment_{i+1:02d}.wav", "status": "PENDING_RENDER"}
                                for i in range(n)]}
    return {"voice_track": voice_track,
            "note": f"voice track spec for {n} segments (render on Colab, per tts_plan)"}


def _assets(state: dict[str, Any]) -> list[dict[str, Any]]:
    return state.get("asset_bundle", {}).get("assets", []) or [
        {"id": f"asset-{i}", "kind": kind} for i, kind in
        enumerate(["videoclip", "image"] * 5)]


def work_editor(state: dict[str, Any]) -> dict[str, Any]:
    blueprint, segments = state.get("blueprint", {}), state.get("script", {}).get("segments", [])
    if not segments:
        return {"error": "script segments missing"}
    assets = _assets(state)
    vocab = blueprint.get("visual_vocabulary") or ["B-roll", "studio"]
    shots = []
    for i, seg in enumerate(segments):
        asset = assets[i % len(assets)]
        shots.append({"segment": seg["name"], "asset_id": asset["id"],
                      "caption_style": "bold white sans-serif",
                      "transition": EFFECTS[i % len(EFFECTS)]})
    dur = blueprint.get("target_duration_s") or 60
    tools.call(state, "editor", "write_edit", "editor", "cut-spec.json", f"timeline: {len(shots)} shots")
    return {"cut_spec": {"shots": shots, "estimated_duration_s": dur, "visual_vocabulary": vocab},
            "note": f"cut spec assembled ({len(shots)} shots, vocab: {vocab})"}


def _worker(kind: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    def work(state: dict[str, Any]) -> dict[str, Any]:
        spec = state.get("cut_spec")
        if not spec:
            return {"error": "cut_spec missing (worker ran out of order)"}
        for i, shot in enumerate(spec.get("shots", [])):
            args: list[Any] = [kind, shot["segment"], shot["asset_id"], kind]
            if kind == "graphics":
                args.append(f"{shot['asset_id']}-overlay.png")
            elif kind == "animated-graphics":
                args.append(f"{shot['asset_id']}-animated.png")
            tools.call(state, kind, "assign_visual", *args)
        return {"note": f"{kind}: {len(spec.get('shots', []))} visual assignments appended"}
    return work


def work_reviewer(state: dict[str, Any]) -> dict[str, Any]:
    result = tools.call(state, "reviewer", "score_fidelity")
    report = result.get("review_report", {})
    decision = report.get("decision")
    tools.call(state, "reviewer", "write_decision", "reviewer", f"fidelity review -> {decision}")
    return {"review_report": report, "iterations": state.get("iterations", 0) + 1,
            "note": f"review: {decision}"}


def work_watcher(state: dict[str, Any]) -> dict[str, Any]:
    """Deterministic scan of the run log at a watchpoint. Law 2: blocks are
    only raised on concrete evidence, never suspicion."""
    blocks: list[dict[str, Any]] = []
    for entry in state.get("log", []):
        text = (entry.get("text") or "").lower()
        if any(w in text for w in ("probably", "silently", "assume", "guess")) and entry.get("level") == "error":
            blocks.append({"law": 1, "law_name": "No Inference", "agent": entry.get("agent", "?"),
                           "evidence": text})
    if state.get("halting") or any("use an effect off" in (e.get("text") or "") for e in state.get("log", [])):
        blocks.append({"law": 6, "law_name": "No Effect Substitution", "agent": "video-effects",
                       "evidence": "effect outside blueprint vocabulary"})
    if blocks:
        for b in blocks:
            events.bus.emit("watcher-blocker", "law_block",
                            f"[Law {b['law']}] {b['law_name']} — {b['evidence']}",
                            law_id=b["law"], violator=b.get("agent", "?"))
        return {"revocations": blocks, "note": f"{len(blocks)} law violation(s) — escalating to Investigator"}
    return {"note": "scan clean — no violations with concrete evidence"}


def work_investigator(state: dict[str, Any]) -> dict[str, Any]:
    rev = state.get("revocations", [])
    if not rev:
        return {"note": "no revocations on record"}
    report = [{"law": r["law"], "law_name": r["law_name"], "agent": r["agent"],
               "root_cause": "evidence in log", "remediation": "stop and ask the user — never guess"}
              for r in rev]
    tools.call(state, "investigator", "write_decision", "investigator",
               f"investigated {len(rev)} revocations; remediation: human-in-the-loop")
    return {"blocks": [{"report": report}], "note": f"remediation report for {len(rev)} revocations"}


def work_recruiter(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("recruit_request"):
        new_id = state["recruit_request"]["new_agent_id"]
        tools.call(state, "recruiter", "write_decision", "recruiter",
                   f"new agent '{new_id}' registered for the next run (dynamic nodes are compile-time)")
        return {"recruitments": [{"new_agent_id": new_id, "registered_for": "next_run"}],
                "note": f"recruited {new_id}"}
    return {"note": "no recruitment requested"}


def work_stub(_state: dict[str, Any]) -> dict[str, Any]:
    return {"note": "stub"}


# --------------------------------------------------------------------------
# node factory registry
# --------------------------------------------------------------------------
def build_node(agent_id: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    work: dict[str, Callable] = {
        "strategist": work_strategist, "analyzer": work_analyzer, "planner": work_planner,
        "researcher": work_researcher, "audio-lead": work_audio_lead, "tts": work_tts,
        "editor": work_editor, "graphics": _worker("graphics"), "animation": _worker("animation"),
        "animated-graphics": _worker("animated-graphics"), "video-effects": _worker("video-effects"),
        "clips": _worker("clips"), "images": _worker("images"), "reviewer": work_reviewer,
        "watcher-blocker": work_watcher, "investigator": work_investigator, "recruiter": work_recruiter,
    }
    return run_node(NodeSpec(agent_id, work[agent_id]))