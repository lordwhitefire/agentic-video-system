"""Agent Workspace acceptance tests — the conversation-first model.

Plan Mode has zero execution authority (enforced by the runtime, not by
prompting); Build Mode runs the agent's REAL node with inline human approval
and cooperative stop; greetings are conversational and never execute; there
is no auto-routing and handoffs require an explicit human decision. Nothing
in this module invents events or outcomes — everything is read from the real
bus and the workspace store.
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
from avis import tools
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
    return run is None or run["status"] not in ("working", "waiting", "stopping")


def _types(snap) -> set[str]:
    return {e["type"] for e in snap["conversation"]}


def _start_turn(client, agent_id: str, message: str):
    r = client.post(f"/api/studio/agents/{agent_id}/messages", json={"message": message})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    return _poll(client, agent_id, _run_done)


def _switch_mode(client, agent_id: str, mode: str):
    r = client.post(f"/api/studio/agents/{agent_id}/mode", json={"mode": mode})
    assert r.status_code == 200
    assert r.json()["ok"] is True


# --------------------------------------------------------------------------
# snapshot contract

def test_workspace_snapshot_reports_real_agent_and_conversation(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    agent = snap["agent"]
    assert agent["id"] == "strategist"
    assert agent["name"] == BY_ID["strategist"]["id"].capitalize()
    assert agent["department"] == BY_ID["strategist"]["department"]
    assert agent["capabilities"]
    assert agent["about"]
    assert snap["mode"] == "plan"
    assert snap["can_stop"] is False
    assert snap["pending_approval"] is None
    assert "handoff" not in snap
    # a fresh workspace opens with the conversational greeting — real, seeded
    assert snap["conversation"][0]["type"] == "assistant_message"
    assert "Hello" in snap["conversation"][0]["content"]
    # the timeline only ever uses the normalized event types (spec §11)
    assert _types(snap) <= set(server.studio.CONVERSATION_TYPES)


def test_unknown_agent_returns_404(client) -> None:
    assert client.get("/api/studio/agents/nobody").status_code == 404
    assert (
        client.post("/api/studio/agents/nobody/messages", json={"message": "hi"}).status_code
        == 404
    )
    assert (
        client.post("/api/studio/agents/nobody/mode", json={"mode": "build"}).status_code
        == 404
    )
    assert (
        client.post("/api/studio/agents/nobody/stop", json={"run_id": "x"}).status_code
        == 404
    )


def test_empty_message_rejected(client) -> None:
    r = client.post("/api/studio/agents/strategist/messages", json={"message": "  "})
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_invalid_mode_rejected(client) -> None:
    r = client.post("/api/studio/agents/strategist/mode", json={"mode": "deploy"})
    assert r.status_code == 400


# --------------------------------------------------------------------------
# CRITICAL 1: Plan Mode has zero execution authority (runtime-enforced)

def test_plan_mode_blocks_tool_execution_at_the_runtime(client) -> None:
    # the gate itself: while the gate is on, mutating tools are refused —
    # observed but never run, never staged (unit-level guarantee).
    tools.set_execution_blocked(True)
    assert tools.execution_blocked() is True
    state: dict = {}
    res = tools.call(state, "strategist", "write_edit", "topic", "Plan mode must not write")
    assert "error" in res and "blocked" in res["error"]
    assert "topic" not in state
    read = tools.call(state, "strategist", "read_state", "topic")
    assert "blocked" not in str(read), "read-only inspection stays allowed"
    tools.set_execution_blocked(False)
    assert tools.execution_blocked() is False


def test_plan_mode_turn_executes_nothing(client) -> None:
    # integration: a Plan Mode turn reasons and replies — and the conversation
    # contains zero tool events and zero mutations.
    snap = _start_turn(client, "strategist", "Create a strategy for a new product video.")

    assert snap["current_run"]["status"] == "completed"
    assert _types(snap) & {"tool_call", "tool_result"} == set()
    assert "intent" in _types(snap), "the agent states its intended action before anything"
    msgs = [e for e in snap["conversation"] if e["type"] == "assistant_message"]
    assert any("Nothing was executed" in m["content"] for m in msgs)
    assert any(e["type"] == "reasoning_summary" for e in snap["conversation"]), \
        "Plan Mode still reasons — via the real think stream"


# --------------------------------------------------------------------------
# CRITICAL 2: Build Mode executes for real

def test_build_mode_runs_the_real_node_with_tool_events(client) -> None:
    _switch_mode(client, "analyzer", "build")
    snap = _start_turn(client, "analyzer", "Produce the structural analysis.")

    assert snap["current_run"]["status"] == "completed"
    assert "tool_call" in _types(snap)
    assert "tool_result" in _types(snap)
    assert "assistant_message" in _types(snap)
    msgs = [e for e in snap["conversation"] if e["type"] == "assistant_message"]
    assert msgs[-1]["content"], "the agent's final message carries the real result"
    assert any(e["type"] == "status" and "Produced artifact" in e["content"]
               for e in snap["conversation"]), "real artifacts are announced inline"


# --------------------------------------------------------------------------
# CRITICAL 3: a greeting is conversational, zero execution

def test_hello_is_conversational_and_executes_nothing(client) -> None:
    # scope the assertion to THIS run (the agent's real timeline may carry
    # earlier bus events); the greeting turn itself must not execute.
    snap = _start_turn(client, "analyzer", "Hello.")
    assert snap["current_run"]["status"] == "completed"

    run_id = snap["current_run"]["id"]
    turn = [e for e in snap["conversation"]
            if e.get("run_id") == run_id or e["type"] == "user_message"]
    assert {e["type"] for e in turn} <= {"user_message", "assistant_message", "status"}
    msgs = [e for e in turn if e["type"] == "assistant_message"]
    assert "Hello. I'm the" in msgs[-1]["content"]


# --------------------------------------------------------------------------
# CRITICAL 4: handoff requires an explicit human decision

def test_handoff_without_human_decision_is_blocked(client) -> None:
    # no auto-routing exists: a handoff call WITHOUT an explicit human
    # decision is refused by the runtime (400).
    r = client.post("/api/studio/agents/strategist/handoff", json={})
    assert r.status_code == 400
    assert "human decision" in r.json()["detail"]

    bad = client.post(
        "/api/studio/agents/strategist/handoff",
        json={"decision": "approve", "target_agent_id": "not-a-real-agent"},
    )
    assert bad.status_code == 400


def test_handoff_with_explicit_decision_switches_workspace(client) -> None:
    r = client.post(
        "/api/studio/agents/strategist/handoff",
        json={"decision": "approve", "target_agent_id": "analyzer"},
    )
    body = r.json()
    assert r.status_code == 200
    assert body["approved"] is True
    assert body["workspace_url"] == "/workspace/analyzer"
    snap = client.get("/api/studio/agents/strategist").json()
    assert "handoff" not in snap, "no handoff state lives in the snapshot — it's a page switch"


# --------------------------------------------------------------------------
# inline human approval: the run genuinely pauses and resumes on the answer

def _seed_blueprint(client) -> None:
    """The planner only reaches its approval interrupt when a REAL blueprint
    exists — produced here by an analyzer build run (real context transfer)."""
    _switch_mode(client, "analyzer", "build")
    _start_turn(client, "analyzer", "Produce the structural analysis.")
    _switch_mode(client, "planner", "build")


def test_build_mode_approval_flow_pauses_and_resumes(client) -> None:
    _seed_blueprint(client)
    r = client.post("/api/studio/agents/planner/messages",
                    json={"message": "Script a short product segment."})
    assert r.json()["ok"] is True

    snap = _poll(client, "planner", lambda s: s["pending_approval"] is not None)
    assert snap["can_stop"] is True
    assert "approval_request" in _types(snap)
    run_id = snap["current_run"]["id"]

    r = client.post("/api/studio/agents/planner/approval",
                    json={"run_id": run_id, "answer": "approve"})
    assert r.status_code == 200 and r.json()["ok"] is True

    snap = _poll(client, "planner", lambda s: s["pending_approval"] is None and _run_done(s))
    assert snap["current_run"]["status"] == "completed"
    assert "approval_result" in _types(snap)


def test_approval_rejected_then_run_finishes(client) -> None:
    _seed_blueprint(client)
    client.post("/api/studio/agents/planner/messages",
                json={"message": "Script a short product segment."})
    snap = _poll(client, "planner", lambda s: s["pending_approval"] is not None)
    run_id = snap["current_run"]["id"]
    r = client.post("/api/studio/agents/planner/approval",
                    json={"run_id": run_id, "answer": "rejected"})
    assert r.json()["ok"] is True
    snap = _poll(client, "planner", lambda s: s["pending_approval"] is None and _run_done(s))
    # a rejected script is a real failure — the planner reports it as failed
    assert snap["current_run"]["status"] == "failed"
    assert "approval_result" in _types(snap)
    results = [e for e in snap["conversation"]
               if e["type"] == "approval_result" and e.get("approval", {}).get("status") == "rejected"]
    assert results
    assert any(e["type"] == "error" for e in snap["conversation"]), \
        "the rejection surfaces honestly as an error event"


def test_approval_without_pending_returns_ok_false(client) -> None:
    r = client.post("/api/studio/agents/strategist/approval",
                    json={"run_id": "x", "answer": "approve"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# stop is a REAL runtime cancellation, with an honest post-stop message

def test_stop_cancels_a_pending_run_with_honest_message(client) -> None:
    _seed_blueprint(client)
    client.post("/api/studio/agents/planner/messages",
                json={"message": "Script a short product segment."})
    snap = _poll(client, "planner", lambda s: s["pending_approval"] is not None)
    run_id = snap["current_run"]["id"]

    r = client.post("/api/studio/agents/planner/stop", json={"run_id": run_id})
    assert r.status_code == 200
    assert r.json()["stopping"] is True

    snap = _poll(client, "planner", lambda s: s["pending_approval"] is None and _run_done(s))
    assert snap["current_run"]["status"] == "stopped"
    msgs = [e for e in snap["conversation"] if e["type"] == "assistant_message"]
    assert any("Stopped" in m["content"] for m in msgs)
    assert any(e["type"] == "status" and "Stop requested" in e["content"]
               for e in snap["conversation"])


def test_stop_with_no_active_run_is_refused(client) -> None:
    r = client.post("/api/studio/agents/strategist/stop", json={"run_id": "stale"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# persistence + streaming

def test_conversation_survives_refresh(client) -> None:
    snap = _start_turn(client, "strategist", "Update the strategy with the latest constraints.")
    assert len(snap["conversation"]) >= 3
    run_id = snap["current_run"]["id"]

    reloaded = client.get("/api/studio/agents/strategist").json()
    assert reloaded["current_run"]["id"] == run_id
    assert [k for k in reloaded["conversation"]] == [k for k in snap["conversation"]], \
        "the same persisted timeline comes back after a page refresh"


def test_workspace_sse_streams_real_conversation_events(client) -> None:
    _start_turn(client, "strategist", "Hello.")
    _start_turn(client, "strategist", "Map the market.")

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
            if len(types) >= 12:
                break
        return types

    types = asyncio.run(_probe())
    assert "assistant_message" in types
    assert "user_message" in types
    assert "status" in types


# --------------------------------------------------------------------------
# hygiene

def test_workspace_secrets_are_not_exposed(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    raw = json.dumps(snap)
    assert "api_key" not in raw
    assert "password" not in raw
    assert "GLM_API_KEY" not in raw
