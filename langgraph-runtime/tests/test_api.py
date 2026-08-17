"""Web API smoke tests — registry, workspace, examples, knowledge, and the
backward-compat stubs. The old Run flow (/api/run, /api/graph, /api/state
run polling) is gone: only the human drives work now."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

import avis.agents as agents
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


def test_index_serves_dashboard(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Agent Dashboard" in r.text


def test_registry_endpoint(client) -> None:
    reg = client.get("/api/agents").json()["agents"]
    assert len(reg) == 14
    assert {a["id"] for a in reg} == set(agents.BY_ID)
    primaries = [a for a in reg if a["tier"] == "primary"]
    assert len(primaries) == 8


def test_examples_endpoint(client) -> None:
    examples = client.get("/api/examples").json()["examples"]
    assert any("mbappe" in e for e in examples)


def test_workspace_api_roundtrip(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "Hello."})
    assert r.json()["ok"] is True
    snap = None
    for _ in range(80):
        snap = client.get("/api/studio/agents/video-strategy").json()
        if snap["active_session"]["status"] != "working":
            break
        time.sleep(0.1)
    assert snap["active_session"]["status"] == "idle"
    assert snap["agent"]["id"] == "video-strategy"


def test_run_flow_endpoints_are_backward_compat_stubs(client) -> None:
    st = client.get("/api/state").json()
    assert st["running"] is False and st["review_decision"] is None
    p = client.get("/api/pending").json()
    assert p["resume"] is False


def test_knowledge_retrieval_endpoint(client) -> None:
    knowledge.record_run({"topic": "t", "decisions": [
        {"agent": "video-strategy", "text": "asset bundle confirmed for the film"}]},
        run_id="run-0001")
    r = client.post("/api/knowledge/retrieve", json={"query": "asset bundle"}).json()
    assert isinstance(r["results"], list)
    assert any("bundle" in h["text"] for h in r["results"])