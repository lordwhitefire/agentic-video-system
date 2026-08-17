"""Agent Workspace acceptance tests — the runtime governs, the LLM speaks.

The contract (WORKSPACE_REBUILD_PLAN v2 + WORKSPACE_CONVERSATION_REBUILD_PLAN):

- EVERY user message takes the SAME path: context → model → runtime
  enforcement. There is no classifier, no canned reply, no intent state.
- The conversation contains no runtime-log events (no turn started/completed,
  no mode-switch messages, no "invoked", no "produced artifact", no CEO
  notes, no "task received" brain lines).
- Plan Mode has zero execution authority without the human's approval
  (runtime-enforced ask gate); Build Mode runs the agent's real tools with
  inline human approval and cooperative stop.
- A capability is a REAL ability: creation persists its real parts (name,
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
    monkeypatch.setattr(studio, "WORKSPACES", {})
    yield


@pytest.fixture(autouse=True)
def _isolate_capabilities(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "CAPABILITIES_DIR", Path(tmp_path) / "capabilities")
    yield


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "RUNS_DIR", str(tmp_path))
    with TestClient(server.app) as c:
        yield c


def _conv(snap) -> list[dict]:
    active = snap.get("active_session")
    return (active or {}).get("conversation", [])


def _poll(client, agent_id, predicate, timeout: float = 30.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        snap = client.get(f"/api/studio/agents/{agent_id}").json()
        if predicate(snap):
            return snap
        time.sleep(0.1)
    pytest.fail(f"timed out waiting for {agent_id} workspace state")


def _run_done(snap) -> bool:
    active = snap.get("active_session")
    return active is None or active["status"] not in ("working", "waiting", "stopping")


def _types(snap) -> set[str]:
    return {e["type"] for e in _conv(snap)}


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
    return "\n".join(e.get("content", "") for e in _conv(snap))


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
    snap = client.get("/api/studio/agents/video-strategy").json()
    agent = snap["agent"]
    assert agent["id"] == "video-strategy"
    assert agent["name"] == "Video Strategy Agent"
    assert agent["identity"] == BY_ID["video-strategy"]["identity"]
    assert agent["capabilities"]
    assert all("name" in c and "created" in c for c in agent["capabilities"])
    assert all(not c["created"] for c in agent["capabilities"]), \
        "a fresh workspace has no created capabilities"
    assert snap["active_session"] is None, "a fresh workspace has no sessions"
    assert snap["model_configured"] is True, "the stub brain is the configured model"
    # the timeline only ever uses the normalized event types
    assert _types(snap) <= set(studio.CONVERSATION_TYPES)


def test_snapshot_capabilities_are_real_labels_not_org_chart(client) -> None:
    snap = client.get("/api/studio/agents/video-strategy").json()
    labels = {c["name"] for c in snap["agent"]["capabilities"]}
    assert not (labels & {"Strategy", "head", "Analyzer", "Planner", "Researcher"})
    assert "Market & Audience Insight" in labels
    assert snap["agent"]["skills"]


def test_subagent_workspace_resolves(client) -> None:
    snap = client.get("/api/studio/agents/audience-analyzer").json()
    assert snap["agent"]["id"] == "audience-analyzer"
    assert snap["agent"]["name"] == "Audience Analyzer"
    assert snap["active_session"] is None


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
        client.post("/api/studio/agents/nobody/approval", json={"answer": "approve"}).status_code
        == 404
    )
    assert (
        client.post("/api/studio/agents/nobody/stop", json={}).status_code
        == 404
    )


def test_empty_message_rejected(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages", json={"message": "  "})
    assert r.status_code == 200
    assert r.json()["ok"] is False


def test_invalid_mode_rejected(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/mode", json={"mode": "deploy"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


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
    snap = _start_turn(client, "video-strategy", message)

    assert snap["active_session"]["status"] == "idle"
    # exactly one model call, with the FULL context: identity, mode, history, capabilities
    assert len(_stub_brain.calls) == 1, "every message is exactly one model call"
    record = _stub_brain.calls[0]
    system, user = record["system"], record["user"]
    assert "You are Video Strategy Agent" in system
    assert "PLAN MODE" in system
    assert "Market & Audience Insight" in system
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
    # the ask gate: in Plan Mode a mutating tool runs only with the human's
    # explicit approval — otherwise it is refused and nothing is applied.
    state: dict = {}
    res = tools.call(state, "video-strategy", "write_edit",
                     {"agent": "video-strategy", "file": "topic",
                      "change": "Plan mode must not write"},
                     mode="plan", ask=lambda name, args: False)
    assert "error" in res and "blocked" in res["error"]
    read = tools.call(state, "video-strategy", "read_state",
                      {"fields": ["topic"]}, mode="plan")
    assert "blocked" not in str(read), "read-only inspection stays allowed"

    approved: dict = {}
    ok = tools.call(state, "video-strategy", "write_edit",
                    {"agent": "video-strategy", "file": "topic",
                     "change": "the human approved this"},
                    mode="plan", ask=lambda name, args: True)
    assert "error" not in ok, "an approved mutating call is applied"


def test_plan_mode_turn_executes_nothing(client, _stub_brain) -> None:
    snap = _start_turn(client, "video-strategy",
                       "Create a strategy for a new product video.")

    assert snap["active_session"]["status"] == "idle"
    assert _types(snap) & {"tool_call", "tool_result"} == set()
    assert _types(snap) <= {"user_message", "assistant_message"}
    _assert_no_debug_text(snap)


# --------------------------------------------------------------------------
# CRITICAL 2: Build Mode executes for real

def test_build_mode_runs_the_real_engine_with_tool_events(
        client, _stub_brain) -> None:
    _start_turn(client, "video-strategy", "Hello.")
    _switch_mode(client, "video-strategy", "build")
    _stub_brain.add_tools([{"name": "write_decision", "arguments": {
        "agent": "video-strategy", "text": "long-form locked in"}}])
    snap = _start_turn(client, "video-strategy",
                       "Produce the strategic direction.")

    assert snap["active_session"]["status"] == "idle"
    assert "tool_call" in _types(snap)
    assert "tool_result" in _types(snap)
    after_last_tool = [e for e in _conv(snap)
                       if e.get("tool", {}).get("name") is not None]
    results = [e for e in _conv(snap)
               if e["type"] == "tool_result"
               and e.get("tool", {}).get("status") == "completed"]
    assert results, "the build-mode tool really ran"
    tail = _conv(snap)[_conv(snap).index(results[-1]) + 1:]
    final_msgs = [e for e in tail if e["type"] == "assistant_message"]
    assert final_msgs, "the agent's final message follows the real result"
    assert final_msgs[-1]["content"], "the final message is the model's own words"
    _assert_no_debug_text(snap)


# --------------------------------------------------------------------------
# inline human approval: the run genuinely pauses and resumes on the answer

def test_plan_mode_approval_flow_pauses_and_resumes(client, _stub_brain) -> None:
    _stub_brain.add_tools([{"name": "write_decision", "arguments": {
        "agent": "video-strategy", "text": "position on accessibility"}}])
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "Lock in the positioning decision."})
    assert r.json()["ok"] is True

    snap = _poll(client, "video-strategy",
                 lambda s: s["active_session"]["pending_approval"] is not None)
    assert snap["active_session"]["can_stop"] is True
    assert "approval_request" in _types(snap)

    r = client.post("/api/studio/agents/video-strategy/approval",
                    json={"answer": "approve"})
    assert r.status_code == 200 and r.json()["ok"] is True

    snap = _poll(client, "video-strategy",
                 lambda s: (s["active_session"]["pending_approval"] is None
                            and _run_done(s)))
    assert snap["active_session"]["status"] == "idle"
    assert "approval_result" in _types(snap)
    tool_results = [e for e in _conv(snap)
                    if e["type"] == "tool_result"
                    and e.get("tool", {}).get("status") == "completed"]
    assert tool_results, "the approved tool really ran"
    _assert_no_debug_text(snap)


def test_approval_rejected_then_run_finishes(client, _stub_brain) -> None:
    _stub_brain.add_tools([{"name": "write_decision", "arguments": {
        "agent": "video-strategy", "text": "position on accessibility"}}])
    client.post("/api/studio/agents/video-strategy/messages",
                json={"message": "Lock in the positioning decision."})
    snap = _poll(client, "video-strategy",
                 lambda s: s["active_session"]["pending_approval"] is not None)

    r = client.post("/api/studio/agents/video-strategy/approval",
                    json={"answer": "rejected"})
    assert r.json()["ok"] is True

    snap = _poll(client, "video-strategy",
                 lambda s: (s["active_session"]["pending_approval"] is None
                            and _run_done(s)))
    results = [e for e in _conv(snap)
               if e["type"] == "approval_result"
               and e.get("approval", {}).get("status") == "rejected"]
    assert results, "the rejection surfaces as an approval_result event"
    blocked = [e for e in _conv(snap)
               if e["type"] == "tool_result" and e.get("tool", {}).get("blocked")]
    assert blocked, "the blocked tool is reported honestly"
    _assert_no_debug_text(snap)


def test_approval_without_pending_returns_ok_false(client) -> None:
    _start_turn(client, "video-strategy", "Hello.")
    r = client.post("/api/studio/agents/video-strategy/approval",
                    json={"answer": "approve"})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# stop is a REAL runtime cancellation, with an honest post-stop event

def test_stop_cancels_a_pending_run_with_honest_message(client, _stub_brain) -> None:
    _stub_brain.add_tools([{"name": "write_decision", "arguments": {
        "agent": "video-strategy", "text": "position on accessibility"}}])
    client.post("/api/studio/agents/video-strategy/messages",
                json={"message": "Lock in the positioning decision."})
    snap = _poll(client, "video-strategy",
                 lambda s: s["active_session"]["pending_approval"] is not None)

    r = client.post("/api/studio/agents/video-strategy/stop", json={})
    assert r.status_code == 200
    assert r.json()["stopping"] is True

    snap = _poll(client, "video-strategy",
                 lambda s: (s["active_session"]["pending_approval"] is None
                            and _run_done(s)))
    assert snap["active_session"]["status"] == "idle"
    status_events = [e for e in _conv(snap)
                     if e["type"] == "status" and "stopped" in (e.get("content") or "")]
    assert status_events, "the runtime reports the stop honestly"
    _assert_no_debug_text(snap)


def test_stop_with_no_active_run_is_refused(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/stop", json={})
    assert r.status_code == 200
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------
# mode switching is silent: the toggle changes the mode, nothing else

def test_mode_switch_adds_nothing_to_the_conversation(client) -> None:
    snap = _start_turn(client, "video-strategy", "Hello.")
    before = [k for k in _conv(snap)]

    _switch_mode(client, "video-strategy", "build")
    snap = client.get("/api/studio/agents/video-strategy").json()
    assert snap["active_session"]["mode"] == "build"
    assert [k for k in _conv(snap)] == before, \
        "switching modes never adds a conversation event"

    _switch_mode(client, "video-strategy", "plan")
    snap = client.get("/api/studio/agents/video-strategy").json()
    assert snap["active_session"]["mode"] == "plan"
    assert [k for k in _conv(snap)] == before


# --------------------------------------------------------------------------
# capabilities: a real ability, registered with its real parts, human-approved

def _capability_call():
    return [{"name": "create_capability", "arguments": {
        "name": "Competitor Video Analysis",
        "description": "Analyze competitor videos for structure, pacing, and tone.",
        "knowledge": "What to look for: hook timing, segment length, CTA placement.",
        "skills": ["competitor research", "structure mapping"],
        "tools": [],
        "resources": "examples/",
        "guidance": "Watch the video once for structure, then map each segment to our roles."}}]


def test_capability_request_in_plan_mode_proposes_and_creates_nothing(
        client, _stub_brain) -> None:
    _stub_brain.add_tools(_capability_call())
    client.post("/api/studio/agents/video-strategy/messages",
                json={"message": "I want you to be able to analyze competitor videos."})
    snap = _poll(client, "video-strategy",
                 lambda s: s["active_session"]["pending_approval"] is not None)

    r = client.post("/api/studio/agents/video-strategy/approval",
                    json={"answer": "approve"})
    assert r.json()["ok"] is True
    snap = _poll(client, "video-strategy",
                 lambda s: s["active_session"]["pending_approval"] is None and _run_done(s))

    caps = client.get("/api/studio/agents/video-strategy").json()["agent"]["capabilities"]
    assert all(not c["created"] for c in caps), "nothing was created in Plan Mode"
    assert not (tools.CAPABILITIES_DIR / "video-strategy.json").exists(), \
        "no registration file was written in Plan Mode — the runtime only persists in Build Mode"


def test_capability_created_in_build_mode_is_real_and_persisted(
        client, _stub_brain) -> None:
    _start_turn(client, "video-strategy", "Hello.")
    _switch_mode(client, "video-strategy", "build")
    _stub_brain.add_tools(_capability_call())
    snap = _start_turn(client, "video-strategy",
                       "Yes, create the capability.")

    assert snap["active_session"]["status"] == "idle"
    path = tools.CAPABILITIES_DIR / "video-strategy.json"
    assert path.exists(), "a real registration file was written"
    records = json.loads(path.read_text())
    assert len(records) == 1
    rec = records[0]
    assert rec["name"] == "Competitor Video Analysis"
    assert rec["knowledge"] and rec["guidance"], "the real parts are registered"
    assert rec["created_at"]

    # the snapshot shows it and it survives a refresh
    snap2 = client.get("/api/studio/agents/video-strategy").json()
    created = [c for c in snap2["agent"]["capabilities"] if c["created"]]
    assert created and created[0]["name"] == "Competitor Video Analysis"
    # it is loaded into the model's context on the NEXT turn
    _stub_brain.add_text("Sure.")
    _start_turn(client, "video-strategy", "Use it.")
    system = _stub_brain.calls[-1]["system"]
    assert "Competitor Video Analysis" in system
    assert "What to look for" in system, "the capability's knowledge reaches the model"


def test_capability_creation_is_governed_by_the_runtime(client, _stub_brain) -> None:
    # Build Mode alone is not enough: the model emits the call but the human
    # never approved it in the conversation — the RUNTIME persists nothing.
    _start_turn(client, "video-strategy", "Hello.")
    _switch_mode(client, "video-strategy", "build")
    _stub_brain.add_tools(_capability_call())
    snap = _start_turn(client, "video-strategy", "Talk to me.")

    assert snap["active_session"]["status"] == "idle"
    results = [e for e in _conv(snap)
               if e["type"] == "tool_result"
               and e.get("tool", {}).get("status") == "failed"]
    assert results, "the unapproved creation is refused at the runtime"
    assert not (tools.CAPABILITIES_DIR / "video-strategy.json").exists(), \
        "nothing was persisted without the human's explicit approval"


# --------------------------------------------------------------------------
# persistence + streaming

def test_conversation_survives_refresh(client) -> None:
    snap = _start_turn(client, "video-strategy", "Update the strategy with the latest constraints.")
    assert len(_conv(snap)) >= 2
    session_id = snap["active_session"]["id"]

    reloaded = client.get(f"/api/studio/agents/video-strategy?session_id={session_id}").json()
    assert reloaded["active_session"]["id"] == session_id
    assert [k for k in _conv(reloaded)] == [k for k in _conv(snap)], \
        "the same persisted timeline comes back after a page refresh"


def test_workspace_sse_streams_real_conversation_events(client) -> None:
    _start_turn(client, "video-strategy", "Hello.")
    _start_turn(client, "video-strategy", "Map the market.")

    class _FakeRequest:
        query_params = {}

        async def is_disconnected(self) -> bool:
            return False

    async def _probe() -> list[str]:
        resp = await server.api_workspace_events("video-strategy", _FakeRequest())  # type: ignore[arg-type]
        types = []
        async for chunk in resp.body_iterator:
            text = chunk.decode() if isinstance(chunk, bytes) else chunk
            if "event: " not in text:
                continue
            if "event: keepalive" in text:
                continue
            types.append(text.split("event: ")[1].splitlines()[0])
            if "user_message" in types and "assistant_message" in types:
                break
        return types

    types = asyncio.run(_probe())
    assert "assistant_message" in types
    assert "user_message" in types


# --------------------------------------------------------------------------
# hygiene

def test_workspace_secrets_are_not_exposed(client) -> None:
    snap = client.get("/api/studio/agents/video-strategy").json()
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

    snap = client.get("/api/studio/agents/video-strategy").json()
    assert snap["model_configured"] is False

    _start_turn(client, "video-strategy", "Hello.")
    snap = client.get("/api/studio/agents/video-strategy").json()
    assert snap["active_session"]["status"] == "idle"
    assert "assistant_message" not in _types(snap), \
        "no scripted impersonation — the agent does not pretend to be intelligent"
    text = _conversation_text(snap)
    assert "conversational layer is not configured" in text
    _assert_no_debug_text(snap)


def test_model_failure_is_honest(client, _stub_brain) -> None:
    _stub_brain.fail = True
    snap = _start_turn(client, "video-strategy", "Hello.")
    assert snap["active_session"]["status"] == "failed"
    assert "couldn't reach the model" in _conversation_text(snap)
    _assert_no_debug_text(snap)


# --------------------------------------------------------------------------
# W6 — workspace memory block (right-rail slots + agent context)

def test_memory_block_roundtrip(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "help me plan the film"})
    sid = r.json()["session_id"]
    put = client.put(
        f"/api/studio/agents/video-strategy/sessions/{sid}/memory",
        json={"memory": {"brief": "A 60-90s brand film.",
                         "audience": "Young professionals."}})
    assert put.status_code == 200 and put.json()["ok"] is True
    got = client.get(
        f"/api/studio/agents/video-strategy/sessions/{sid}/memory").json()
    assert got["memory"]["brief"] == "A 60-90s brand film."
    assert got["memory"]["audience"] == "Young professionals."
    assert got["memory"]["brand"] == ""

    snap = client.get("/api/studio/agents/video-strategy").json()["active_session"]
    slots = {s["key"]: s for s in snap["memory_slots"]}
    assert slots["brief"]["label"] == "Project Brief"
    assert slots["brief"]["available"] is True
    assert slots["audience"]["available"] is True
    assert slots["brand"]["available"] is False
    assert snap["memory"]["brief"] == "A 60-90s brand film."


def test_memory_validation(client) -> None:
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "plan the launch"})
    sid = r.json()["session_id"]
    url = f"/api/studio/agents/video-strategy/sessions/{sid}/memory"
    bad = client.put(url, json={"memory": {"nope": "x"}})
    assert bad.json()["ok"] is False
    assert "unknown memory keys" in bad.json()["error"]
    nonstr = client.put(url, json={"memory": {"brief": 42}})
    assert nonstr.json()["ok"] is False
    assert "strings" in nonstr.json()["error"]


def test_memory_unknown_session_404(client) -> None:
    assert client.get(
        "/api/studio/agents/video-strategy/sessions/nope/memory").status_code == 404
    assert client.get(
        "/api/studio/agents/nobody/sessions/x/memory").status_code == 404


def test_memory_included_in_prompt_context(client, _stub_brain, monkeypatch) -> None:
    orig = studio._Engine._build_user_prompt
    captured: dict[str, str] = {}

    def spy(self):
        text = orig(self)
        captured["prompt"] = text
        return text

    monkeypatch.setattr(studio._Engine, "_build_user_prompt", spy)
    r = client.post("/api/studio/agents/video-strategy/messages",
                    json={"message": "plan the film"})
    sid = r.json()["session_id"]
    client.put(f"/api/studio/agents/video-strategy/sessions/{sid}/memory",
               json={"memory": {"brief": "launch teaser, 30s"}})
    _stub_brain.add_text("I have the brief.")
    client.post("/api/studio/agents/video-strategy/messages",
                json={"message": "go", "session_id": sid})
    _poll(client, "video-strategy",
          lambda s: (s.get("active_session") or {}).get("status") == "idle")
    assert "workspace memory:" in captured["prompt"]
    assert "Project Brief" in captured["prompt"]
    assert "launch teaser, 30s" in captured["prompt"]
