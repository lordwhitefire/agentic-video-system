"""Agent Studio tests — dashboard snapshot derives REAL state.

Rules under test (WORKSPACE_REBUILD_PLAN W1): the registry is 8 primary
agents + 6 named sub-agents, matching the runtime catalog exactly; no
fabricated statuses; attention only appears while a handoff is pending;
pages and endpoints serve as specified; sub-agents are grouped under their
parent on the dashboard."""

from __future__ import annotations

import asyncio
import time

import pytest
from fastapi.testclient import TestClient

import avis.agents as agents
import avis.brain as brain
import avis.events as events
import avis.knowledge as knowledge
import avis.studio as studio
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
    """Fresh event bus per test — other test modules (e.g. test_laws) emit
    law_block events on the shared bus, which would leak into attention."""
    from avis.events import _Bus
    monkeypatch.setattr(events, "bus", _Bus())
    yield


@pytest.fixture(autouse=True)
def _isolate_workspace_store(monkeypatch):
    monkeypatch.setattr(studio, "WORKSPACES", {})
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    with TestClient(server.app) as c:
        yield c


# --------------------------------------------------------------------------
# registry integrity (W1 remap)

def test_registry_matches_runtime_catalog() -> None:
    reg = studio.registry()
    assert len(reg) == 14
    ids = [a["id"] for a in reg]
    assert len(set(ids)) == 14
    assert set(ids) == set(agents.BY_ID)
    primaries = [a for a in reg if a["tier"] == "primary"]
    subagents = [a for a in reg if a["tier"] == "subagent"]
    assert len(primaries) == 8
    assert len(subagents) == 6
    primary_ids = {a["id"] for a in primaries}
    assert primary_ids == set(agents.PRIMARY_IDS)
    for a in subagents:
        assert a["parent"] in primary_ids, \
            f"sub-agent {a['id']} must sit under a primary"
    for a in reg:
        assert a["name"] and a["description"]
        assert a["department"]
        assert a["tier"] in {"primary", "subagent"}


def test_no_pre_rebuild_ids_remain() -> None:
    legacy = {"strategist", "analyzer", "planner", "researcher", "audio-lead",
              "tts", "editor", "graphics", "animation", "animated-graphics",
              "video-effects", "clips", "images", "reviewer", "watcher-blocker",
              "investigator"}
    retired = {"recruiter"}
    assert not (legacy | retired) & set(agents.BY_ID)
    for old in legacy:
        assert agents.resolve(old) in agents.BY_ID, \
            f"alias for '{old}' must resolve to a live agent"


def test_subagents_are_grouped_under_their_parent() -> None:
    by_id = {a["id"]: a for a in agents.AGENTS}
    parents = {by_id[s]["parent"] for s in agents.SUBAGENT_IDS}
    assert parents == {"video-strategy", "scene-planning"}


# --------------------------------------------------------------------------
# idle snapshot (pure, isolated bus)

def test_dashboard_idle_snapshot() -> None:
    snap = studio.build_dashboard_snapshot()
    sys_ = snap["system"]
    assert sys_["total_agents"] == 8
    assert sys_["total_sessions"] == 0
    assert sys_["attention_agents"] == 0
    assert all(a["status"] == "idle" for a in snap["agents"])
    assert all(a["session_count"] == 0 for a in snap["agents"])
    assert snap["recent_activity"] == []
    by_id = {a["id"]: a for a in snap["agents"]}
    assert by_id["video-strategy"]["sub_agents"] == [
        "audience-analyzer", "competitor-analyzer", "market-research-analyzer"]
    assert by_id["scene-planning"]["sub_agents"] == [
        "shot-analyzer", "clip-cutter", "continuity-checker"]
    assert by_id["creative-director"]["sub_agents"] == []


def test_dashboard_never_fabricates_statuses() -> None:
    allowed = {"idle", "working", "waiting", "completed", "failed"}
    snap = studio.build_dashboard_snapshot()
    assert all(a["status"] in allowed for a in snap["agents"])


# --------------------------------------------------------------------------
# snapshot reflects a real session (server + real bus)

def _poll(client, agent_id, predicate, timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = client.get(f"/api/studio/agents/{agent_id}").json()
        if predicate(snap):
            return snap
        time.sleep(0.1)
    pytest.fail(f"timed out waiting for {agent_id} workspace state")


def test_dashboard_reflects_a_real_session(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "Scope the market for the launch film."})
    assert r.json()["ok"] is True
    _poll(client, "video-strategy",
          lambda s: s["active_session"] and s["active_session"]["status"] == "idle")

    snap = client.get("/api/studio/dashboard").json()
    sys_ = snap["system"]
    assert sys_["total_agents"] == 8
    assert sys_["total_sessions"] >= 1
    by_id = {a["id"]: a for a in snap["agents"]}
    assert by_id["video-strategy"]["session_count"] == 1
    assert by_id["video-strategy"]["last_activity_at"]
    assert snap["recent_activity"], "the real bus history shows up"
    assert all(a["session_count"] == 0 for a in snap["agents"]
               if a["id"] != "video-strategy")


def test_dashboard_attention_during_pending_handoff(client, _stub_brain) -> None:
    _stub_brain.add_text("Understood.")
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "Let's get started."})
    assert r.json()["ok"] is True
    _poll(client, "video-strategy",
          lambda s: s["active_session"] and s["active_session"]["status"] == "idle")
    r = client.post("/api/studio/agents/video-strategy/mode",
                    json={"mode": "build"})
    assert r.json()["ok"] is True

    _stub_brain.add_tools([{"name": "handoff", "arguments": {
        "target": "script-narrative", "prompt": "please take the story from here"}}])
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "The strategy is set. Take the story forward."})
    assert r.json()["ok"] is True
    _poll(client, "video-strategy",
          lambda s: s["active_session"] and s["active_session"]["status"] == "handed_off")

    snap = client.get("/api/studio/dashboard").json()
    assert snap["system"]["attention_agents"] >= 1
    by_id = {a["id"]: a for a in snap["agents"]}
    assert by_id["video-strategy"]["handoff_pending"] >= 1
    assert by_id["video-strategy"]["status"] == "handed_off"

    r = client.post("/api/studio/agents/video-strategy/handoff",
                    json={"decision": "accept"})
    assert r.json()["ok"] is True

    snap2 = client.get("/api/studio/dashboard").json()
    assert snap2["system"]["attention_agents"] == 0
    by_id2 = {a["id"]: a for a in snap2["agents"]}
    assert by_id2["video-strategy"]["handoff_pending"] == 0


# --------------------------------------------------------------------------
# pages + endpoints

def test_dashboard_is_landing_page(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Agent Dashboard" in r.text
    assert "TOTAL AGENTS" in r.text


def test_workspace_page_served(client) -> None:
    r = client.get("/workspace/video-strategy")
    assert r.status_code == 200
    assert '<div id="root">' in r.text, "the React workspace shell is served"
    assert "/workspace/assets/" in r.text
    assert client.get("/workspace/nobody").status_code == 404
    assert client.get("/workspace/strategist").status_code == 404, \
        "pre-rebuild ids are gone from the workspace routes"


def test_single_agent_endpoint(client) -> None:
    r = client.get("/api/agents/video-strategy").json()
    assert r["agent"]["name"] == "Video Strategy Agent"
    assert r["department"] == "Strategy"
    assert r["tier"] == "primary"
    sub = client.get("/api/agents/audience-analyzer").json()
    assert sub["agent"]["name"] == "Audience Analyzer"
    assert sub["agent"]["parent"] == "video-strategy"
    assert client.get("/api/agents/nobody").status_code == 404


def test_studio_events_stream(client) -> None:
    # TestClient's portal never completes open SSE connections, so drive the
    # real endpoint function directly: pre-fill the bus, call the endpoint,
    # consume one mapped event from its body iterator.
    events.bus.emit("video-strategy", "note", "video-strategy invoked")
    events.bus.emit("video-strategy", "result", "video-strategy -> ok")

    class _FakeRequest:
        async def is_disconnected(self) -> bool:
            return False

    async def _probe() -> bytes:
        resp = await server.api_studio_events(_FakeRequest())  # type: ignore[arg-type]
        first = await anext(aiter(resp.body_iterator))
        assert first
        assert "event:" in first
        return first

    first = asyncio.run(_probe())
    assert "activity_created" in first or "agent_completed" in first


def test_studio_event_mapping() -> None:
    m = studio.map_studio_event({"agent": "script-narrative", "kind": "result",
                                 "text": "script-narrative -> ok", "ts": 1.0})
    assert m["type"] == "agent_completed" and m["agent_id"] == "script-narrative"
    m = studio.map_studio_event({"agent": "video-strategy", "kind": "approval_request",
                                 "text": "approval required", "ts": 1.0})
    assert m["type"] == "agent_attention_required"
    m = studio.map_studio_event({"agent": "video-strategy", "kind": "note",
                                 "text": "video-strategy invoked", "ts": 1.0})
    assert m["type"] == "activity_created"
    m = studio.map_studio_event({"agent": "visual-design", "kind": "tool_call",
                                 "text": "assign_visual", "ts": 1.0})
    assert m["type"] == "activity_created"
    assert studio.map_studio_event({"agent": "server", "kind": "error",
                                    "text": "x", "ts": 1.0})["type"] == "agent_failed"
