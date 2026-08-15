"""Agent Studio Stage One tests — dashboard snapshot derives REAL state.

Rules under test: registry matches the runtime catalog exactly; no fabricated
statuses; attention only appears while a CEO interrupt is pending; pages and
endpoints serve as specified."""

from __future__ import annotations

import types
import time

import pytest
from fastapi.testclient import TestClient

import avis.agents as agents
import avis.events as events
import avis.knowledge as knowledge
import avis.studio as studio
from ui.web import server


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


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    with TestClient(server.app) as c:
        yield c


# --------------------------------------------------------------------------
# registry integrity
# --------------------------------------------------------------------------

def test_registry_matches_runtime_catalog() -> None:
    reg = studio.registry()
    assert len(reg) == 17
    ids = [a["id"] for a in reg]
    assert len(set(ids)) == 17
    assert set(ids) == set(agents.BY_ID)
    for a in reg:
        assert a["name"] and a["description"]
        assert a["department"] and a["tier"]


def test_pipeline_order_covers_all_agents() -> None:
    assert len(studio.PIPELINE_ORDER) == 17
    assert set(studio.PIPELINE_ORDER) == set(agents.BY_ID)


def test_production_stages_cover_all_agents() -> None:
    covered = [a for st in studio.PRODUCTION_STAGES for a in st["agents"]]
    assert set(covered) == set(agents.BY_ID)
    assert len(studio.PRODUCTION_STAGES) == 5


# --------------------------------------------------------------------------
# idle snapshot (pure, isolated bus)
# --------------------------------------------------------------------------

def test_dashboard_idle_snapshot() -> None:
    snap = studio.build_dashboard_snapshot({"running": False}, None)
    sys_ = snap["system"]
    assert sys_["total_agents"] == 17
    assert sys_["active_agents"] == 0
    assert sys_["idle_agents"] == 17
    assert sys_["waiting_agents"] == 0
    assert sys_["attention_agents"] == 0
    assert sys_["status"] == "healthy"
    assert all(a["status"] == "idle" for a in snap["agents"])
    assert all(a["progress"] == 0 for a in snap["agents"])
    assert snap["recent_activity"] == []
    assert snap["attention"] == []
    assert snap["heatmap"] == []
    assert all(st["status"] == "Upcoming" for st in snap["production"]["stages"])


def test_dashboard_never_fabricates_statuses() -> None:
    for st in ("idle", "working", "waiting", "completed", "failed"):
        assert st in {"idle", "working", "waiting", "completed", "failed"}
    snap = studio.build_dashboard_snapshot({"running": False}, None)
    allowed = {"idle", "working", "waiting", "completed", "failed"}
    assert all(a["status"] in allowed for a in snap["agents"])


# --------------------------------------------------------------------------
# snapshot reflects a real run (server + real bus)
# --------------------------------------------------------------------------

def _wait_run(client) -> None:
    for _ in range(80):
        st = client.get("/api/state").json()
        if not st["running"]:
            return
        time.sleep(0.25)


def test_dashboard_reflects_completed_run(client) -> None:
    r = client.post("/api/run", json={"topic": "t",
        "reference_analysis": "examples/reference-analysis-mbappe.json",
        "llm": False, "auto_approve": True})
    assert r.json()["ok"] is True
    _wait_run(client)

    snap = client.get("/api/studio/dashboard").json()
    sys_ = snap["system"]
    assert sys_["total_agents"] == 17
    assert sys_["active_agents"] == 0
    assert sys_["attention_agents"] == 0
    completed = [a for a in snap["agents"] if a["status"] == "completed"]
    assert len(completed) >= 12  # full pipeline minus recruiter-style idle tails
    for a in completed:
        assert a["progress"] == 100
    by_id = {a["id"]: a for a in snap["agents"]}
    assert by_id["strategist"]["status"] == "completed"
    assert by_id["reviewer"]["status"] == "completed"
    assert by_id["planner"]["current_task"]  # real event text
    assert snap["recent_activity"]
    assert sys_["completed_today"] >= 1
    stages = {st["name"]: st["status"] for st in snap["production"]["stages"]}
    assert stages["Strategy"] == "Complete"
    assert stages["Production"] == "Complete"


def test_dashboard_attention_during_interrupt(client) -> None:
    client.post("/api/run", json={"topic": "t",
        "reference_analysis": "examples/reference-analysis-mbappe.json",
        "llm": False, "auto_approve": False})
    for _ in range(60):
        p = client.get("/api/pending").json()
        if p["resume"]:
            break
        time.sleep(0.25)
    assert p["resume"] is True

    snap = client.get("/api/studio/dashboard").json()
    assert snap["system"]["waiting_agents"] >= 1
    assert snap["system"]["attention_agents"] >= 1
    waiting = [a for a in snap["agents"] if a["status"] == "waiting"]
    assert waiting, "a run in flight must show a waiting agent"
    assert waiting[0]["id"] in {"planner", "researcher"}
    assert waiting[0]["attention"] is True
    assert snap["attention"][0]["agent_id"] == waiting[0]["id"]
    # the in-flight agent is the waiting one (planner at interrupt #1); it is
    # reported as waiting, so "working" may legitimately be 0 here
    assert snap["system"]["active_agents"] + snap["system"]["waiting_agents"] >= 1

    client.post("/api/answer", json={"resume": "approve"})
    for _ in range(40):
        p = client.get("/api/pending").json()
        if p["resume"]:
            break
        time.sleep(0.25)
    client.post("/api/answer", json={"resume": "approve"})
    _wait_run(client)
    snap2 = client.get("/api/studio/dashboard").json()
    assert snap2["system"]["waiting_agents"] == 0
    assert snap2["system"]["attention_agents"] == 0


# --------------------------------------------------------------------------
# pages + endpoints
# --------------------------------------------------------------------------

def test_dashboard_is_landing_page(client) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "Agents at a Glance" in r.text
    assert "AVIS" in r.text


def test_graph_view_moved_to_graph_route(client) -> None:
    r = client.get("/graph")
    assert r.status_code == 200
    assert "Agentic Video System — Graph View" in r.text
    g = client.get("/api/graph").json()
    assert "strategist" in g["mermaid"]


def test_workspace_page_served(client) -> None:
    r = client.get("/workspace/strategist")
    assert r.status_code == 200
    assert "Agent Workspace" in r.text
    assert "Live Activity" not in r.text, "the old activity panel is gone"
    assert "AGENT NETWORK" in r.text
    assert "PLAN" in r.text and "BUILD" in r.text
    assert client.get("/workspace/nobody").status_code == 404


def test_single_agent_endpoint(client) -> None:
    r = client.get("/api/agents/strategist").json()
    assert r["agent"]["name"] == "Strategist"
    assert r["department"] == "Strategy"
    assert client.get("/api/agents/nobody").status_code == 404


def test_studio_events_stream(client) -> None:
    # TestClient's portal never completes open SSE connections, so drive the
    # real endpoint function directly: pre-fill the bus, call the endpoint,
    # consume one mapped event from its body iterator.
    import asyncio
    import types

    events.bus.emit("strategist", "note", "strategist invoked")
    events.bus.emit("strategist", "result", "strategist -> ok")

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
    assert "agent_status_changed" in first or "agent_completed" in first


def test_studio_event_mapping() -> None:
    m = studio.map_studio_event({"agent": "planner", "kind": "result",
                                 "text": "planner -> ok", "ts": 1.0})
    assert m["type"] == "agent_completed" and m["agent_id"] == "planner"
    m = studio.map_studio_event({"agent": "CEO", "kind": "interrupt",
                                 "text": "approval required", "ts": 1.0})
    assert m["type"] == "agent_attention_required"
    m = studio.map_studio_event({"agent": "strategist", "kind": "note",
                                 "text": "strategist invoked", "ts": 1.0})
    assert m["type"] == "agent_status_changed"
    m = studio.map_studio_event({"agent": "graphics", "kind": "tool_call",
                                 "text": "assign_visual", "ts": 1.0})
    assert m["type"] == "activity_created"
    assert studio.map_studio_event({"agent": "server", "kind": "error",
                                    "text": "x", "ts": 1.0})["type"] == "agent_failed"