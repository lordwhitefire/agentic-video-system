"""W2 — created agents (dynamic registry).

The registry is dynamic: POST /api/studio/agents persists a real entry to
data/agents/, and the agent immediately gets a workspace page, sessions, and
tool definitions from its chosen tools. Created sub-agents are spawnable by
name via the `subagent` tool; duplicate slugs are rejected.

Exact reply text is never asserted (test doubles only).
"""

from __future__ import annotations

import os
import time
from pathlib import Path

os.environ["AVIS_LLM_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient

import avis.brain as brain
from avis import events
from avis import knowledge
from avis import studio
from avis import tools
from ui.web import server


@pytest.fixture(autouse=True)
def _stub_brain(monkeypatch):
    stub = brain.StubBrain()
    monkeypatch.setattr(brain, "stub", stub)
    return stub


@pytest.fixture(autouse=True)
def _isolate_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    yield


@pytest.fixture(autouse=True)
def _isolate_bus(monkeypatch):
    from avis.events import _Bus
    monkeypatch.setattr(events, "bus", _Bus())
    yield


@pytest.fixture(autouse=True)
def _isolate_workspace_store(monkeypatch):
    monkeypatch.setattr(studio, "WORKSPACES", {})
    yield


@pytest.fixture(autouse=True)
def _isolate_capabilities(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "CAPABILITIES_DIR", Path(tmp_path) / "capabilities")
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    with TestClient(server.app) as c:
        yield c


def _poll(client, agent_id, predicate, timeout: float = 20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = client.get(f"/api/studio/agents/{agent_id}").json()
        if predicate(snap):
            return snap
        time.sleep(0.05)
    pytest.fail(f"timed out waiting for {agent_id}")


def _primary_payload(**overrides):
    payload = {
        "name": "Brand Voice Agent",
        "slug": "brand-voice",
        "type": "primary",
        "description": "Tone and voice for the brand",
        "identity": "I shape the brand voice.",
        "capabilities": ["Tone & Style", "Voice Guidelines"],
        "skills": ["voice", "copywriting"],
        "tools": ["write_decision", "retrieve_knowledge"],
        "tool_labels": ["Research Tools", "Knowledge Base"],
    }
    payload.update(overrides)
    return payload


def test_create_primary_agent_appears_everywhere(client) -> None:
    r = client.post("/api/studio/agents", json=_primary_payload())
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["agent"]["id"] == "brand-voice"
    assert body["agent"]["name"] == "Brand Voice Agent"

    reg = client.get("/api/agents").json()["agents"]
    assert len(reg) == 15
    entry = next(a for a in reg if a["id"] == "brand-voice")
    assert entry["name"] == "Brand Voice Agent"
    assert entry["tier"] == "primary"
    assert entry["created"] is True

    snap = client.get("/api/studio/agents/brand-voice").json()
    assert snap["agent"]["name"] == "Brand Voice Agent"
    assert snap["agent"]["identity"] == "I shape the brand voice."
    tool_names = [t["name"] for t in snap["agent"]["tools"]]
    assert "write_decision" in tool_names
    assert "retrieve_knowledge" in tool_names


def test_created_primary_runs_a_real_session(client, _stub_brain) -> None:
    client.post("/api/studio/agents", json=_primary_payload())
    _stub_brain.add_text("Here is the brand voice plan.")
    r = client.post("/api/studio/agents/brand-voice/messages",
                    json={"message": "draft the voice guidelines"})
    assert r.json()["ok"] is True

    def done(snap):
        sess = snap["active_session"]
        return bool(sess and sess["status"] == "idle" and any(
            e["type"] == "assistant_message" for e in sess["conversation"]))

    snap = _poll(client, "brand-voice", done)
    assert snap["active_session"]["title"] == "draft the voice guidelines"
    assert snap["active_session"]["mode"] == "plan"


def test_created_subagent_is_registered_and_spawnable(client, _stub_brain) -> None:
    client.post("/api/studio/agents", json={
        "name": "Color Grading Specialist",
        "slug": "color-grader",
        "type": "sub",
        "parent": "visual-design",
        "description": "Color and grade guidance",
        "capabilities": ["Color Grading"],
        "skills": ["color"],
        "tools": ["retrieve_knowledge"],
    })
    snap = client.get("/api/studio/agents/color-grader").json()
    assert snap["agent"]["tier"] == "subagent"
    assert snap["agent"]["name"] == "Color Grading Specialist"

    reg = client.get("/api/agents").json()["agents"]
    sub = next(a for a in reg if a["id"] == "color-grader")
    assert sub["parent"] == "visual-design"

    _stub_brain.add_text("The parent session is open.")
    client.post("/api/studio/agents/visual-design/messages",
                json={"message": "open a session"})
    _poll(client, "visual-design",
          lambda s: s["active_session"] and s["active_session"]["status"] == "idle")
    assert client.post("/api/studio/agents/visual-design/mode",
                       json={"mode": "build"}).json()["ok"] is True

    _stub_brain.add_tools([{
        "name": "subagent",
        "arguments": {"class": "color-grader", "task": "advise on the grade"},
    }])
    _stub_brain.add_text("Advice: keep it natural.")
    _stub_brain.add_text("The grade specialist advised keeping it natural.")
    r = client.post("/api/studio/agents/visual-design/messages",
                    json={"message": "get grade advice"})
    assert r.json()["ok"] is True

    def done(snap):
        sess = snap["active_session"]
        if not sess or sess["status"] != "idle":
            return False
        conv = sess["conversation"]
        return any(e["type"] == "tool_result" and
                   e.get("tool", {}).get("name") == "subagent" for e in conv)

    snap = _poll(client, "visual-design", done)
    conv = snap["active_session"]["conversation"]
    result = next(e for e in conv if e["type"] == "tool_result" and
                  e.get("tool", {}).get("name") == "subagent")
    assert "Advice: keep it natural." in (result.get("content") or "")


def test_duplicate_slug_rejected(client) -> None:
    client.post("/api/studio/agents", json=_primary_payload())
    r = client.post("/api/studio/agents", json=_primary_payload(slug="brand-voice"))
    assert r.json()["ok"] is False
    assert "already exists" in r.json()["error"]


def test_create_validation(client) -> None:
    assert client.post("/api/studio/agents", json={}).json()["ok"] is False
    assert client.post("/api/studio/agents",
                       json=_primary_payload(type="deploy")).json()["ok"] is False
    assert client.post("/api/studio/agents",
                       json=_primary_payload(tools=["no_such_tool"])).json()["ok"] is False
    bad_parent = client.post("/api/studio/agents", json={
        "name": "Orphan", "slug": "orphan", "type": "sub",
        "parent": "nobody", "tools": []})
    assert bad_parent.json()["ok"] is False
    assert "unknown parent" in bad_parent.json()["error"]
    assert client.post("/api/studio/agents",
                       json=_primary_payload(slug="strategist")).json()["ok"] is False, \
        "legacy alias ids are reserved"


def test_created_agents_survive_reload(client) -> None:
    """Persistence: the entry is on disk, so a registry rebuild keeps it."""
    client.post("/api/studio/agents", json=_primary_payload())
    import avis.agents as agents
    agents._rebuild()
    assert "brand-voice" in agents.BY_ID
    snap = client.get("/api/studio/agents/brand-voice").json()
    assert snap["agent"]["name"] == "Brand Voice Agent"