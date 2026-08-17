"""Agent Workspace acceptance tests — the runtime governs, the LLM speaks.

The contract (WORKSPACE_CONVERSATION_REBUILD_PLAN.md):

- EVERY user message takes the SAME path: context → model → runtime
  enforcement. There is no classifier, no canned reply, no intent state.
- The conversation contains no runtime-log events (no turn started/completed,
  no mode-switch messages, no "invoked", no "produced artifact", no CEO
  notes, no "task received" brain lines).
- Plan Mode has zero execution authority (runtime-enforced); Build Mode runs
  the agent's REAL node with inline human approval and cooperative stop.
- A capability is a REAL ability: creation registers its real parts (name,
  description, knowledge, skills, tools, resources, guidance) on disk, only
  in Build Mode with explicit human approval (the model judges the words;
  the runtime enforces the mode and persists the record).
- Tests inject a StubBrain (test double) so the runtime contract is checked
  deterministically; exact reply text is NEVER asserted.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path

os.environ["AVIS_LLM_ENABLED"] = "0"

import pytest
from fastapi.testclient import TestClient

import avis.brain as brain
from avis import events
from avis import knowledge
from avis import tools
from avis.agents import BY_ID
from avis import studio
from ui.web import server


# --------------------------------------------------------------------------
# the test double: a stub brain. Test-only, never a production voice.
# --------------------------------------------------------------------------

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
    monkeypatch.setattr(server, "_workspace_store", {})
    monkeypatch.setattr(server, "_workspace_context", {})
    yield


@pytest.fixture(autouse=True)
def _isolate_capabilities(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, "CAPABILITIES_DIR", Path(tmp_path) / "capabilities")
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


def _conversation_text(snap) -> str:
    return "\n".join(e.get("content", "") for e in snap["conversation"])


# --------------------------------------------------------------------------
# the no-debug sweep: runtime-log language is banned from the conversation
# --------------------------------------------------------------------------

BANNED = ["turn started", "turn completed", "switched to", "state has topic",
          "blueprint=", "deterministic step", "invoked", "produced artifact",
          "task received"]


def _assert_no_debug_text(snap) -> None:
    text = _conversation_text(snap).lower()
    hits = [b for b in BANNED if b in text]
    assert not hits, f"runtime-log language leaked into the conversation: {hits}"


# --------------------------------------------------------------------------
# snapshot contract

def test_workspace_snapshot_reports_real_agent(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    agent = snap["agent"]
    assert agent["id"] == "strategist"
    assert agent["name"] == "Strategist"
    assert agent["about"] == BY_ID["strategist"]["identity"]
    assert agent["capabilities"]
    assert all("name" in c and "created" in c for c in agent["capabilities"])
    assert all(not c["created"] for c in agent["capabilities"]), \
        "a fresh workspace has no created capabilities"
    assert snap["mode"] == "plan"
    assert snap["can_stop"] is False
    assert snap["pending_approval"] is None
    assert snap["model_configured"] is True
    assert "handoff" not in snap
    # a fresh workspace starts EMPTY — no canned greeting, no fake voice
    assert snap["conversation"] == []
    # the timeline only ever uses the normalized event types
    assert _types(snap) <= set(studio.CONVERSATION_TYPES)


def test_snapshot_capabilities_are_real_labels_not_org_chart(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    labels = {c["name"] for c in snap["agent"]["capabilities"]}
    assert not (labels & {"Strategy", "head", "Analyzer", "Planner", "Researcher"})
    assert "Video concept development" in labels
    assert snap["agent"]["skills"]


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
# THE SAME PATH: any message — "Hello.", "How are you?", "I don't like the
# direction", a long work request — is one model call with full context.
# No special handling exists in front of the model.

@pytest.mark.parametrize("message", [
    "Hello.",
    "How are you?",
    "I don't like the direction we're taking.",
    "Create a strategy for a new product video.",
])
def test_every_message_takes_the_same_path(client, _stub_brain, message) -> None:
    snap = _start_turn(client, "strategist", message)

    assert snap["current_run"]["status"] == "completed"
    # exactly one model call, with the FULL context: identity, mode, history, capabilities
    assert len(_stub_brain.calls) == 1, "every message is exactly one model call"
    system, user = _stub_brain.calls[0]
    assert "You are Strategist" in system
    assert "PLAN MODE" in system
    assert "Video concept development" in system
    assert message in user
    # the conversation is exactly: user message + the model's reply
    assert _types(snap) <= {"user_message", "assistant_message"}
    _assert_no_debug_text(snap)
    # reply text is the MODEL's (the stub's) — never asserted for exact words


def test_no_classifier_no_reply_table_no_intent(client) -> None:
    # the puppeteer machinery is gone from the code, not just unused
    for banned in ("is_greeting", "greeting_reply", "is_status_question",
                   "status_summary", "intent_message", "plan_response",
                   "workspace_plan"):
        assert not hasattr(studio, banned), f"{banned} must not exist"
    assert "intent" not in studio.CONVERSATION_TYPES


def test_source_has_no_debug_conversation_events(client) -> None:
    # the runtime never EMITS runtime-log language into the conversation
    for path in (Path(server.__file__), Path(studio.__file__)):
        text = path.read_text().lower()
        for banned in ("turn started", "turn completed", "switched to",
                       "produced artifact", "stop requested — cancelling"):
            assert banned not in text, f"'{banned}' must not appear in {path.name}"


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
    snap = _start_turn(client, "strategist", "Create a strategy for a new product video.")

    assert snap["current_run"]["status"] == "completed"
    assert _types(snap) & {"tool_call", "tool_result"} == set()
    assert _types(snap) <= {"user_message", "assistant_message"}
    _assert_no_debug_text(snap)


# --------------------------------------------------------------------------
# CRITICAL 2: Build Mode executes for real

def test_build_mode_runs_the_real_node_with_tool_events(client) -> None:
    _switch_mode(client, "analyzer", "build")
    snap = _start_turn(client, "analyzer", "Produce the structural analysis.")

    assert snap["current_run"]["status"] == "completed"
    assert "tool_call" in _types(snap)
    assert "tool_result" in _types(snap)
    msgs = [e for e in snap["conversation"] if e["type"] == "assistant_message"]
    assert len(msgs) == 2, "action preview message + real result message"
    assert msgs[0]["content"], "the preview is the model's own words"
    assert msgs[-1]["content"], "the agent's final message carries the real result"
    _assert_no_debug_text(snap)


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
    _assert_no_debug_text(snap)


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
    _assert_no_debug_text(snap)


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
    _assert_no_debug_text(snap)


def test_stop_with_no_active_run_is_refused(client) -> None:
    r = client.post("/api/studio/agents/strategist/stop", json={"run_id": "stale"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# mode switching is silent: the toggle changes the mode, nothing else

def test_mode_switch_adds_nothing_to_the_conversation(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    before = [k for k in snap["conversation"]]

    _switch_mode(client, "strategist", "build")
    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["mode"] == "build"
    assert [k for k in snap["conversation"]] == before, \
        "switching modes never adds a conversation event"

    _switch_mode(client, "strategist", "plan")
    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["mode"] == "plan"
    assert [k for k in snap["conversation"]] == before


# --------------------------------------------------------------------------
# capabilities: a real ability, registered with its real parts, human-approved

def _draft_reply(name="Competitor Video Analysis"):
    draft = {
        "capability": {
            "name": name,
            "description": "Analyze competitor videos for structure, pacing, and tone.",
            "knowledge": "What to look for: hook timing, segment length, CTA placement.",
            "skills": ["competitor research", "structure mapping"],
            "tools": [],
            "resources": "examples/",
            "guidance": "Watch the video once for structure, then map each segment to our blueprint roles.",
        }
    }
    return "I can create that. Here is the capability: " + json.dumps(draft)


def test_capability_request_in_plan_mode_proposes_and_creates_nothing(
        client, _stub_brain, tmp_path) -> None:
    _stub_brain.reply = _draft_reply()
    snap = _start_turn(client, "strategist", "I want you to be able to analyze competitor videos.")

    assert snap["current_run"]["status"] == "completed"
    caps = client.get("/api/studio/agents/strategist").json()["agent"]["capabilities"]
    assert all(not c["created"] for c in caps), "nothing was created in Plan Mode"
    assert not (studio.CAPABILITIES_DIR / "strategist.json").exists(), \
        "no registration file was written in Plan Mode"


def test_yes_in_plan_mode_still_creates_nothing(client, _stub_brain) -> None:
    _stub_brain.reply = _draft_reply()
    snap = _start_turn(client, "strategist", "Yes, create it.")
    assert snap["current_run"]["status"] == "completed"
    caps = client.get("/api/studio/agents/strategist").json()["agent"]["capabilities"]
    assert all(not c["created"] for c in caps)
    assert not (studio.CAPABILITIES_DIR / "strategist.json").exists()
    assert _types(snap) <= {"user_message", "assistant_message"}


def test_capability_created_in_build_mode_is_real_and_persisted(
        client, _stub_brain) -> None:
    _switch_mode(client, "strategist", "build")
    _stub_brain.reply = _draft_reply()
    snap = _start_turn(client, "strategist", "Yes, create the competitor analysis capability.")

    assert snap["current_run"]["status"] == "completed"
    path = studio.CAPABILITIES_DIR / "strategist.json"
    assert path.exists(), "a real registration file was written"
    records = json.loads(path.read_text())
    assert len(records) == 1
    rec = records[0]
    assert rec["name"] == "Competitor Video Analysis"
    assert rec["knowledge"] and rec["guidance"], "the real parts are registered"
    assert rec["created_at"]

    # the snapshot shows it, the identity is unchanged, it survives a refresh
    snap2 = client.get("/api/studio/agents/strategist").json()
    created = [c for c in snap2["agent"]["capabilities"] if c["created"]]
    assert created and created[0]["name"] == "Competitor Video Analysis"
    assert snap2["agent"]["about"] == BY_ID["strategist"]["identity"]
    # it is loaded into the model's context on the NEXT turn
    _stub_brain.reply = "Sure."
    _start_turn(client, "strategist", "Use it.")
    system = _stub_brain.calls[-1][0]
    assert "Competitor Video Analysis" in system
    assert "What to look for" in system, "the capability's knowledge reaches the model"


def test_capability_creation_is_governed_by_the_runtime(client, _stub_brain) -> None:
    # Build Mode + model proposes (no user approval in the words) still writes
    # nothing: the model only emits the draft when the human approved — if it
    # emits one anyway, the RUNTIME is what persists, and it never persists in
    # Plan Mode (tested above). Here: Plan Mode + draft → runtime refuses.
    _stub_brain.reply = _draft_reply()
    _start_turn(client, "strategist", "be able to analyze competitor videos")
    text = _conversation_text(client.get("/api/studio/agents/strategist").json())
    assert "Not created" in text, "the runtime refusal is shown honestly"
    assert not (studio.CAPABILITIES_DIR / "strategist.json").exists()


# --------------------------------------------------------------------------
# persistence + streaming

def test_conversation_survives_refresh(client) -> None:
    snap = _start_turn(client, "strategist", "Update the strategy with the latest constraints.")
    assert len(snap["conversation"]) >= 2
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


# --------------------------------------------------------------------------
# hygiene

def test_workspace_secrets_are_not_exposed(client) -> None:
    snap = client.get("/api/studio/agents/strategist").json()
    raw = json.dumps(snap)
    assert "api_key" not in raw
    assert "password" not in raw
    assert "GLM_API_KEY" not in raw


# --------------------------------------------------------------------------
# honest no-model state: no key, no stub → a clear notice and NOTHING else

def test_no_model_shows_honest_notice_and_no_fake_reply(client, monkeypatch) -> None:
    monkeypatch.setattr(brain, "stub", None)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["model_configured"] is False

    _start_turn(client, "strategist", "Hello.")
    snap = client.get("/api/studio/agents/strategist").json()
    assert snap["current_run"]["status"] == "completed"
    assert "assistant_message" not in _types(snap), \
        "no scripted impersonation — the agent does not pretend to be intelligent"
    text = _conversation_text(snap)
    assert "conversational layer is not configured" in text
    _assert_no_debug_text(snap)


def test_model_failure_is_honest(client, _stub_brain) -> None:
    _stub_brain.fail = True
    snap = _start_turn(client, "strategist", "Hello.")
    assert snap["current_run"]["status"] == "failed"
    assert "couldn't reach the model" in _conversation_text(snap)
    _assert_no_debug_text(snap)
