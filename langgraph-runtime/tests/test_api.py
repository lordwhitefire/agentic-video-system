"""Web API smoke tests — graph view, run flow (interactive + auto), RAG endpoints."""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

import avis.knowledge as knowledge
from ui.web import server


@pytest.fixture(autouse=True)
def _isolate_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    with TestClient(server.app) as c:
        yield c


def test_index_and_graph(client) -> None:
    r = client.get("/")
    assert r.status_code == 200 and "Agents at a Glance" in r.text
    g = client.get("/api/graph").json()
    assert "mermaid" in g and "strategist" in g["mermaid"]


def test_agents_and_examples(client) -> None:
    agents = client.get("/api/agents").json()["agents"]
    assert len(agents) == 17
    examples = client.get("/api/examples").json()["examples"]
    assert any("mbappe" in e for e in examples)


def test_auto_approve_run_passes(client) -> None:
    r = client.post("/api/run", json={
        "topic": "Why Mbappé shines on the biggest stage",
        "reference_analysis": "examples/reference-analysis-mbappe.json",
        "llm": False, "auto_approve": True})
    assert r.json()["ok"] is True
    for _ in range(60):
        st = client.get("/api/state").json()
        if not st["running"]:
            break
        time.sleep(0.25)
    assert st["review_decision"] == "pass"
    assert st["visual_assignments"] == 60
    assert len(client.get("/api/knowledge").json()["runs"]) >= 1


def test_interactive_approval_flow(client) -> None:
    client.post("/api/run", json={
        "topic": "t", "reference_analysis": "examples/reference-analysis-mbappe.json",
        "llm": False, "auto_approve": False})
    for _ in range(40):
        p = client.get("/api/pending").json()
        if p["resume"]:
            break
        time.sleep(0.25)
    assert p["resume"] is True
    assert "script" in p["question"] or "proposals" in p["question"]
    client.post("/api/answer", json={"resume": "approve"})
    for _ in range(40):
        p = client.get("/api/pending").json()
        if p["resume"]:
            break
        time.sleep(0.25)
    client.post("/api/answer", json={"resume": "approve"})
    for _ in range(60):
        st = client.get("/api/state").json()
        if not st["running"]:
            break
        time.sleep(0.25)
    assert st["review_decision"] == "pass"


def test_knowledge_retrieval_endpoint(client) -> None:
    client.post("/api/run", json={"topic": "t",
        "reference_analysis": "examples/reference-analysis-mbappe.json",
        "auto_approve": True, "llm": False})
    for _ in range(60):
        st = client.get("/api/state").json()
        if not st["running"]:
            break
        time.sleep(0.25)
    r = client.post("/api/knowledge/retrieve", json={"query": "asset bundle"}).json()
    assert isinstance(r["results"], list)
    assert any("bundle" in h["text"] for h in r["results"])


def test_run_rejects_path_escape(client) -> None:
    r = client.post("/api/run", json={"topic": "t",
        "reference_analysis": "../../etc/passwd"})
    assert r.json()["ok"] is False