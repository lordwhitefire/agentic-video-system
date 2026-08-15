"""Stage Two acceptance tests: the Agent Workspace.

Each test exercises the REAL single-node graph and node functions. Nothing in
this module invents events, outcomes, or artifacts — they are read from the
real bus that the workspace run pumps.
"""

from __future__ import annotations

import asyncio
import json
import os
import time

os.environ["AVIS_LLM_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient

from avis.agents import BY_ID
from avis import events
from avis import knowledge
from ui.web import server


@pytest.fixture(autouse=True)
def _isolate_knowledge(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    yield


@pytest.fixture(autouse=True)
def _isolate_bus(monkeypatch):
    from avis.events import _Bus
    monkeypatch.setattr(events, "bus", _Bus())
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    with TestClient(server.app) as c:
        yield c


def _poll(client, agent_id, predicate, timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = client.get(f"/api/studio/agents/{agent_id}").json()
        if predicate(snap):
            return snap
        time.sleep(0.1)
    pytest.fail(f"timed out waiting for {agent_id} workspace state")


def _run_done(snap):
    run = snap["current_run"]
    return run is None or run["status"] not in ("working", "pending")


def _start_run(client, agent_id: str, message: str):
    r = client.post(
        f"/api/studio/agents/{agent_id}/messages", json={"message": message}
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    return _poll(client, agent_id, _run_done)


# --------------------------------------------------------------------------
# snapshot + routing


def test_workspace_snapshot_reports_real_agent(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    agent = snap["agent"]
    assert agent["id"] == "strategist"
    assert agent["name"] == BY_ID["strategist"]["id"].capitalize()
    assert agent["department"] == BY_ID["strategist"]["department"]
    assert agent["status"] == "idle"
    assert agent["current_task"] is None or agent["current_task"] == "Awaiting your instruction"
    assert agent["progress"] == 0
    assert agent["capabilities"]
    assert snap["messages"] == []
    assert snap["handoff"] is None


def test_unknown_agent_returns_404(client) -> None:
    assert client.get("/api/studio/agents/nobody").status_code == 404
    assert (
        client.post(
            "/api/studio/agents/nobody/messages", json={"message": "hi"}
        ).status_code
        == 404
    )


def test_empty_message_rejected(client) -> None:
    r = client.post("/api/studio/agents/strategist/messages", json={"message": "  "})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# the real run loop


def test_workspace_message_runs_real_node_chain_to_handoff(client) -> None:
    snap = _start_run(client, "strategist", "Work through the initial strategy.")

    assert snap["current_run"]["status"] == "completed"

    assert len(snap["messages"]) >= 2
    assert snap["messages"][0]["role"] == "human"
    agent_msg = [m for m in snap["messages"] if m["role"] == "agent"]
    assert agent_msg, "agent should have produced a real result message"

    types = {e["type"] for e in snap["events"] if e["agent_id"] == "strategist"}
    assert "run_started" in types
    assert "run_completed" in types
    assert "action_started" in types

    assert snap["handoff"] is not None
    assert snap["handoff"]["next_agent_id"] == "analyzer"
    assert snap["handoff"]["reason"]


def test_workspace_history_survives_refresh(client) -> None:
    snap = _start_run(client, "strategist", "Update the strategy with the latest constraints.")
    assert len(snap["messages"]) >= 2

    # Conversation is persisted server-side: reloading the workspace (a second
    # GET — the same round trip a page refresh performs) returns the same
    # messages and the same terminal run, not a wiped timeline.
    reloaded = client.get("/api/studio/agents/strategist").json()
    assert reloaded["messages"] == snap["messages"]
    assert reloaded["current_run"]["id"] == snap["current_run"]["id"]
    assert reloaded["current_run"]["status"] == "completed"
    rel_types = {e["type"] for e in reloaded["events"]}
    snap_types = {e["type"] for e in snap["events"]}
    assert "run_started" in rel_types and "run_completed" in rel_types
    assert snap_types <= rel_types


# --------------------------------------------------------------------------
# workspace SSE — pre-fill the store, then drive the endpoint function
# directly (TestClient's portal never completes open SSE connections).


def test_workspace_sse_streams_real_events(client) -> None:
    _start_run(client, "strategist", "Map the market.")

    class _FakeRequest:
        async def is_disconnected(self) -> bool:
            return False

    async def _probe() -> list[str]:
        resp = await server.api_workspace_events("strategist", _FakeRequest())  # type: ignore[arg-type]
        types = []
        async for chunk in resp.body_iterator:
            text = chunk.decode() if isinstance(chunk, bytes) else chunk
            if "event: " not in text:
                continue
            if "event: keepalive" in text:
                continue
            types.append(text.split("event: ")[1].splitlines()[0])
            if any("run_completed" in t or "run_failed" in t for t in types):
                break
        return types

    types = asyncio.run(_probe())
    assert "run_started" in types
    assert any(
        t in types for t in ("action_started", "tool_call_started", "plan_created")
    )
    assert "run_completed" in types


# --------------------------------------------------------------------------
# handoff control


def test_handoff_approve_returns_next_workspace(client) -> None:
    snap = _start_run(client, "strategist", "Draft the initial strategy plan.")
    run_id = snap["current_run"]["id"]

    r = client.post(
        "/api/studio/agents/strategist/handoff",
        json={"decision": "approve", "target_agent_id": "analyzer", "run_id": run_id},
    )
    body = r.json()
    assert r.status_code == 200
    assert body["approved"] is True
    assert body["target_agent_id"] == "analyzer"
    assert body["workspace_url"] == "/workspace/analyzer"

    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["handoff"] is None


def test_handoff_redirect_validates_and_switches(client) -> None:
    snap = _start_run(client, "strategist", "Shape the market analysis approach.")
    run_id = snap["current_run"]["id"]

    r = client.post(
        "/api/studio/agents/strategist/handoff",
        json={"decision": "redirect", "target_agent_id": "planner", "run_id": run_id},
    )
    assert r.status_code == 200
    assert r.json()["workspace_url"] == "/workspace/planner"

    bad = client.post(
        "/api/studio/agents/strategist/handoff",
        json={
            "decision": "redirect",
            "target_agent_id": "not-a-real-agent",
            "run_id": run_id,
        },
    )
    assert bad.status_code == 400


def test_handoff_continue_records_and_dismisses(client) -> None:
    snap = _start_run(client, "strategist", "Refine the draft.")
    run_id = snap["current_run"]["id"]

    r = client.post(
        "/api/studio/agents/strategist/handoff",
        json={"decision": "continue", "target_agent_id": None, "run_id": run_id},
    )
    assert r.status_code == 200

    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["handoff"] is None
    decisions = [e for e in snap["events"]
                 if e["type"] in ("handoff_redirected", "handoff_approved", "decision_created")]
    assert decisions


# --------------------------------------------------------------------------
# hygiene


def test_workspace_secrets_are_not_exposed(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    raw = json.dumps(snap)
    assert "api_key" not in raw
    assert "password" not in raw
    assert "GLM_API_KEY" not in raw