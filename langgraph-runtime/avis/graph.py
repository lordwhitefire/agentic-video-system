"""Deterministic orchestrator. The graph structure is fixed: pipeline order is
hard-wired, legal guards sit at watchpoints, and the ONLY branches are
(1) reviewer pass/revise/branch and (2) human approval interrupts.

This mirrors the paper system: CEO (you) delegates to 5 department heads,
heads deterministically summon their workers, Watcher/Blocker patrols the
watchpoints, Investigator only fires when Watcher finds concrete evidence."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Callable, Optional

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

import avis.events as events
import avis.knowledge as knowledge
from avis.agents import AGENTS, build_node
from avis.state import AgentState

WORKERS = ["graphics", "animation", "animated-graphics", "video-effects", "clips", "images"]


def _watchpoint(compile_target: str) -> tuple[str, dict[str, str]]:
    name = f"watch->{compile_target}"
    return name, {name: compile_target}


def _watch_route(state: AgentState) -> str:
    return "investigator" if state.get("revocations") else "next"


def _gate_pipeline(state: AgentState) -> str:
    """Router: missing upstream input → stop and ask the CEO (Law 1: never
    fabricate the missing piece)."""
    ok = bool(state.get("reference_analysis") and state.get("topic"))
    events.bus.emit("orchestrator", "route", f"gate(strategist) -> {'pipeline' if ok else 'halt: awaiting CEO input'}")
    return "next" if ok else "halt"


def _gate_blueprint_router(state: AgentState) -> str:
    ok = bool(state.get("blueprint"))
    events.bus.emit("orchestrator", "route", f"gate(blueprint) -> {'planner' if ok else 'halt: no blueprint'}")
    return "next" if ok else "halt"


def _gate_blueprint(state: AgentState) -> dict[str, Any]:
    return {"note": "blueprint present" if state.get("blueprint") else "halted: no blueprint to plan from"}


def build_graph() -> tuple[Any, str]:
    g = StateGraph(AgentState)

    for a in AGENTS:
        g.add_node(a["id"], build_node(a["id"]))

    # ---------------- main deterministic pipeline ----------------
    g.add_edge(START, "strategist")
    g.add_conditional_edges("strategist", _gate_pipeline,
                            {"next": "analyzer", "halt": END})
    g.add_node("gate->blueprint", _gate_blueprint)
    g.add_edge("analyzer", "gate->blueprint")
    g.add_conditional_edges("gate->blueprint", _gate_blueprint_router,
                            {"next": "planner", "halt": END})
    g.add_edge("planner", "researcher")        # (script approval interrupt inside)
    g.add_edge("audio-lead", "tts")
    g.add_edge("tts", "editor")

    for i, worker in enumerate(WORKERS):
        prev = "editor" if i == 0 else WORKERS[i - 1]
        g.add_edge(prev, worker)

    # ---------------- review branches (the only non-pipeline branch) ----------------
    def review_route(state: AgentState) -> str:
        decision = (state.get("review_report") or {}).get("decision", "revise")
        if state.get("iterations", 0) >= 4:
            decision = "pass"  # iteration cap: deliver with known gaps, never loop forever
        events.bus.emit("reviewer", "route", f"reviewer route -> {decision}")
        return decision

    g.add_conditional_edges(
        "reviewer", review_route,
        {"pass": END, "revise": "editor", "branch": "strategist"},
    )

    # ---------------- watchpoints: patrolled deterministically ----------------
    # after sourcing and after the production pass, Watcher/Blocker scans the
    # run log for concrete evidence; violations escalate to Investigator.
    g.add_node("watch->researcher", build_node("watcher-blocker"))
    g.add_edge("researcher", "watch->researcher")
    g.add_conditional_edges(
        "watch->researcher", _watch_route,
        {"investigator": "investigator", "next": "audio-lead"},
    )
    g.add_edge("investigator", "audio-lead")

    g.add_node("watch->reviewer", build_node("watcher-blocker"))
    g.add_edge(WORKERS[-1], "watch->reviewer")  # workers -> watchpoint -> reviewer
    g.add_conditional_edges(
        "watch->reviewer", _watch_route,
        {"investigator": "investigator", "next": "reviewer"},
    )
    g.add_edge("investigator", "reviewer")

    graph = g.compile(checkpointer=InMemorySaver())

    mermaid = ""
    try:
        mermaid = graph.get_graph().draw_mermaid()
    except Exception as e:  # pragma: no cover
        mermaid = f"<!-- mermaid draw failed: {e} -->"
    return graph, mermaid


def seed_state(topic: str, reference_analysis: Optional[dict[str, Any]] = None,
               voice_profile: Optional[dict[str, Any]] = None,
               reference_file: Optional[str] = None) -> dict[str, Any]:
    """Initial state. Everything here is factual input from the user or config —
    agents never invent the rest (Law 1)."""
    if reference_analysis is None and reference_file:
        try:
            with open(reference_file) as f:
                reference_analysis = json.load(f).get("reference_analysis") or json.load(f)
        except Exception as e:
            reference_analysis = {"error": str(e)}
    profile = voice_profile or {}
    if not profile:
        p = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "voice-profile.json")
        try:
            with open(p) as f:
                profile = json.load(f)
        except Exception:
            profile = {"default_engine": "coqui_xtts_v2", "voice_sample_path": "voice-samples/my-voice-v1.wav",
                       "loudness_target_lufs": -16}
    return {
        "topic": topic,
        "reference": reference_file,
        "reference_analysis": reference_analysis or {},
        "voice_profile": profile,
        "iterations": 0,
        "mailboxes": {a["id"]: [] for a in AGENTS},
        "registry": {a["id"]: {"department": a["department"], "tier": a["tier"]} for a in AGENTS},
        "log": [],
        "decisions": [],
        "edits": [],
        "revocations": [],
        "substitutions": [],
        "blocks": [],
        "visual_assignments": [],
        "recruitments": [],
    }


class _Watchdog(RuntimeError):
    """Raised when a run exceeds the maximum stream-update budget. A run can
    never spin: the 4-iteration review cap is the first guard, this is the last."""


def run(graph: Any, state: dict[str, Any], approver: Callable[[dict[str, Any]], Any]) -> dict[str, Any]:
    """Execute with human-in-the-loop approval. Deterministic control flow;
    the only nondeterminism is the CEO's answers to interrupt() questions.
    Recursively resumes through every interrupt; returns the final state."""
    config = {"configurable": {"thread_id": uuid.uuid4().hex}}
    final: dict[str, Any] = {}
    budget = {"steps": 0, "max": 500}

    def _execute(input_: Any) -> None:
        for update in graph.stream(input_, config=config, stream_mode="updates"):
            budget["steps"] += 1
            if budget["steps"] > budget["max"]:
                events.bus.emit("orchestrator", "error",
                                f"watchdog: exceeded {budget['max']} stream updates — run aborted")
                raise _Watchdog(f"exceeded {budget['max']} stream updates")
            for node_name, values in update.items():
                if node_name == "__interrupt__":
                    for i in values:
                        question = i.value if hasattr(i, "value") else i
                        events.bus.emit("CEO", "interrupt",
                                        f"approval required: {question.get('question')}")
                        resume = approver(question)
                        events.bus.emit("CEO", "note", f"CEO answer -> {resume}")
                    _execute(Command(resume=resume))
                    return
                final.update(values or {})

    try:
        _execute(state)
    except _Watchdog:
        pass
    snapshot = graph.get_state(config)
    if snapshot and snapshot.values:
        final.update(snapshot.values)
    final["knowledge_run"] = knowledge.record_run(final)
    return final