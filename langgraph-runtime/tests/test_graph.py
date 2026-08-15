"""Graph topology + full pipeline runs (deterministic scripted brain, in-memory)."""

from __future__ import annotations

import json
import os

import pytest

import avis.knowledge as knowledge
from avis.agents import AGENTS, BY_ID
from avis.graph import build_graph, run, seed_state

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "examples", "reference-analysis-mbappe.json")


def test_seventeen_agents_registered() -> None:
    assert len(AGENTS) == 17
    heads = [a for a in AGENTS if a["tier"] == "head"]
    workers = [a for a in AGENTS if a["tier"] == "worker"]
    assert len(heads) == 5 and len(workers) == 12
    for a in AGENTS:
        assert a["id"] in BY_ID
        if a["tier"] == "worker":
            assert a["head"] in BY_ID


def test_graph_builds_with_all_nodes() -> None:
    graph, mermaid = build_graph()
    nodes = {n for n in graph.get_graph().nodes if not n.startswith("__")}
    expected = {a["id"] for a in AGENTS} | {"gate->blueprint", "watch->researcher", "watch->reviewer"}
    assert expected <= nodes
    assert "__start__" in graph.get_graph().nodes


def test_seed_state_has_facts_only() -> None:
    state = seed_state("topic-x", reference_file=EXAMPLES)
    assert state["topic"] == "topic-x"
    assert state["reference_analysis"]["form"] == "long-form"
    assert len(state["reference_analysis"]["segments"]) == 10
    assert set(state["registry"].keys()) == {a["id"] for a in AGENTS}


def test_full_run_auto_approve_passes(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    graph, _ = build_graph()
    state = seed_state("Why Mbappé shines on the biggest stage", reference_file=EXAMPLES)
    final = run(graph, state, lambda q: "approve")

    assert (final.get("review_report") or {}).get("decision") == "pass"
    assert final.get("iterations", 0) >= 1
    assert len(final.get("visual_assignments", [])) >= 10
    assert final.get("revocations", []) == []
    assert final.get("knowledge_run")


def test_full_run_rejection_stops_pipeline(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    graph, _ = build_graph()
    state = seed_state("Why Mbappé shines on the biggest stage", reference_file=EXAMPLES)
    final = run(graph, state, lambda q: "rejected: no")

    # the script never gets produced (planner blocked), and the pipeline runs
    # out the revise loop to the iteration cap instead of fabricating output
    assert final.get("script") is None
    assert final.get("manifest") is None
    assert final.get("iterations", 0) >= 1
    assert final.get("visual_assignments", []) == []


def test_watchdog_never_spins(tmp_path, monkeypatch) -> None:
    """A pathological reviewer loop is capped by iterations; the watchdog is a
    second guard. Force 'revise' forever by patching the registered scorer."""
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    import avis.tools as tools

    graph, _ = build_graph()
    state = seed_state("t", reference_file=EXAMPLES)

    original = tools.REGISTRY["score_fidelity"]["fn"]
    tools.REGISTRY["score_fidelity"]["fn"] = lambda s, a: {"review_report": {
        "checks": {}, "missing_assets": [], "decision": "revise"}}
    try:
        final = run(graph, state, lambda q: "approve")
    finally:
        tools.REGISTRY["score_fidelity"]["fn"] = original

    assert final.get("iterations", 0) >= 4  # iteration cap fired — run ended
    assert final.get("review_report", {}).get("decision") == "revise"  # last report
    # the run terminated: a forever-looping reviewer would never return at all