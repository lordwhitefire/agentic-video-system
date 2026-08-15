"""UI 2 — Agent Studio Dashboard + live activity (FastAPI).

Serves:
  GET  /                        the Agent Dashboard (presentation view)
  GET  /workspace/{agent_id}    agent workspace (Stage Two: full workspace UI)
  GET  /graph                   the LangGraph technical view (mermaid)
  GET  /api/graph               the LangGraph state graph as mermaid text
  GET  /api/agents              the 17 agents and departments
  GET  /api/agents/{agent_id}   one agent + live status
  GET  /api/examples            reference-analysis JSON files in examples/
  GET  /api/events              Server-Sent Events: raw runtime events
  GET  /api/studio/dashboard    Agent Dashboard snapshot (real state)
  GET  /api/studio/events       Server-Sent Events: studio-mapped events
  GET  /api/studio/agents/{id}      workspace snapshot (spec §32)
  POST /api/studio/agents/{id}/messages  send the agent a message (Plan or Build mode)
  POST /api/studio/agents/{id}/mode      switch Plan/Build interaction mode
  POST /api/studio/agents/{id}/approval  human answer to an inline approval_request
  POST /api/studio/agents/{id}/stop      real runtime cancellation (cooperative)
  POST /api/studio/agents/{id}/handoff   human-governed switch (requires explicit decision)
  GET  /api/studio/agents/{id}/events    workspace Server-Sent Events
  GET  /api/state               latest run state snapshot
  GET  /api/pending             the pending CEO approval question (script / proposals)
  POST /api/run                 start a run (JSON: topic, reference_analysis?, llm?, auto_approve?)
  POST /api/answer              answer the pending CEO approval question (JSON: resume)

The orchestrator stays deterministic; this server only observes and streams."""

from __future__ import annotations

import asyncio
import calendar
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI, Request

import avis.brain as brain
import avis.events as events
import avis.graph as g
import avis.studio as studio
import avis.tools as tools

STATIC = Path(__file__).parent / "static"
EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"

app = FastAPI(title="AVIS — Agent Studio")

_state: dict[str, Any] = {}
_graph = None
_mermaid = ""
_graph_lock = threading.Lock()
_sse_queues: list[asyncio.Queue] = []
_studio_sse_queues: list[asyncio.Queue] = []
_loop: asyncio.AbstractEventLoop | None = None
_pending_resume: list[Any] = []
_pending_question: dict[str, Any] = {}
_auto_approve = False

# --- Agent Workspace (conversation-first) state ----------------------------
# shared project context: real outputs produced across workspace runs so the
# next agent genuinely inherits the previous agent's work (spec §56/§57)
_workspace_context: dict[str, Any] = {}
# per-agent workspace store: ONE conversation stream + mode + run state. The
# human is the governance layer; nothing is routed or handoff-recommended.
_workspace_store: dict[str, dict[str, Any]] = {}
_workspace_queues: list[asyncio.Queue] = []


def _iso(ts: float | None = None) -> str:
    t = time.gmtime(ts) if ts is not None else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


def _fresh_ws_store() -> dict[str, Any]:
    """A fresh per-agent workspace: empty conversation, Plan Mode by default,
    no running process. Greeting is seeded on first snapshot."""
    return {"conversation": [], "current_run": None,
            "status": "idle", "run_id": None,
            "mode": "plan", "stop_requested": False,
            "approval_pending": None}


def _push_ws_event(agent_id: str, event: dict[str, Any]) -> None:
    """Persist ONE normalized conversation event (spec §11) and broadcast it
    to every open workspace stream. This is the only place conversation
    entries are created besides the worker's assistant messages."""
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    store["conversation"].append(event)
    if _loop is not None:
        _loop.call_soon_threadsafe(
            lambda: [q.put_nowait(event) for q in list(_workspace_queues)])


@app.on_event("startup")
def _startup() -> None:
    global _graph, _mermaid, _loop
    _loop = asyncio.get_event_loop()
    _graph, _mermaid = g.build_graph()
    events.bus.subscribe(_pump)
    events.bus.subscribe(_pump_studio)
    events.bus.subscribe(_pump_workspace)


def _pump_workspace(ev: dict[str, Any]) -> None:
    """Bus listener → normalized conversation events → workspace SSE streams.
    Live events are broadcast (not persisted — the snapshot merge rebuilds the
    timeline from the bus, spec §66), so nothing is double-recorded."""
    if _loop is None:
        return
    mapped = studio.workspace_event(ev)
    if mapped is not None:
        _loop.call_soon_threadsafe(
            lambda: [q.put_nowait(mapped) for q in list(_workspace_queues)])


def _pump(ev: dict[str, Any]) -> None:
    """Bus listener (runs on the run thread) → pushes to SSE consumers."""
    if _loop is None:
        return
    _loop.call_soon_threadsafe(lambda: [q.put_nowait(ev) for q in list(_sse_queues)])


def _pump_studio(ev: dict[str, Any]) -> None:
    """Bus listener → mapped studio events → studio SSE consumers."""
    if _loop is None:
        return
    mapped = studio.map_studio_event(ev)
    if mapped is not None:
        _loop.call_soon_threadsafe(
            lambda: [q.put_nowait(mapped) for q in list(_studio_sse_queues)])


@app.get("/")
def index() -> Any:
    return _static("dashboard.html")


@app.get("/graph")
def graph_view() -> Any:
    return _static("index.html")


@app.get("/workspace/{agent_id}")
def workspace_view(agent_id: str) -> Any:
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    return _static("workspace.html")


def _static(name: str) -> Any:
    from fastapi.responses import HTMLResponse
    return HTMLResponse((STATIC / name).read_text())


@app.get("/api/graph")
def api_graph() -> dict[str, Any]:
    from importlib.metadata import version
    try:
        v = version("langgraph")
    except Exception:
        v = "?"
    return {"mermaid": _mermaid, "engine": "langgraph " + v}


@app.get("/api/agents")
def api_agents() -> dict[str, Any]:
    from avis.agents import AGENTS
    return {"agents": AGENTS}


@app.get("/api/agents/{agent_id}")
def api_agent(agent_id: str) -> dict[str, Any]:
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    snap = studio.agent_snapshot(agent_id,
                                  bool(_state.get("running", False)),
                                  studio.waiting_agent())
    return {"agent": snap,
            "department": BY_ID[agent_id]["department"],
            "tier": BY_ID[agent_id]["tier"]}


@app.get("/api/studio/dashboard")
def api_studio_dashboard() -> dict[str, Any]:
    with _graph_lock:
        return studio.build_dashboard_snapshot(_state, _pending_question)


@app.get("/api/studio/events")
async def api_studio_events(request: Request):
    from fastapi.responses import StreamingResponse

    queue: asyncio.Queue = asyncio.Queue()
    for ev in events.bus.history():
        mapped = studio.map_studio_event(ev)
        if mapped is not None:
            queue.put_nowait(mapped)
    _studio_sse_queues.append(queue)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        finally:
            _studio_sse_queues.remove(queue)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/studio/agents/{agent_id}")
def api_workspace_snapshot(agent_id: str) -> dict[str, Any]:
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    with _graph_lock:
        store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
        if not store["conversation"]:
            _push_ws_event(agent_id, {"type": "assistant_message", "agent_id": agent_id,
                                      "timestamp": _iso(),
                                      "content": studio.greeting_reply(agent_id)})
        return studio.build_workspace_snapshot(agent_id, store, _state,
                                               _pending_question, _workspace_context)


@app.post("/api/studio/agents/{agent_id}/messages")
async def api_workspace_message(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    message = str(payload.get("message", "")).strip()
    if not message:
        return {"ok": False, "error": "message is empty"}
    llm = bool(payload.get("llm", False))
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    if store["status"] in ("working", "waiting"):
        return {"ok": False, "error": "agent is already running — wait or stop it"}
    _push_ws_event(agent_id, {"type": "user_message", "agent_id": "you",
                              "timestamp": _iso(), "content": message})
    threading.Thread(target=_run_agent_worker, args=(agent_id, message, llm),
                     daemon=True).start()
    return {"ok": True, "accepted": True}


def _run_agent_worker(agent_id: str, message: str, llm: bool = False) -> None:
    """One human message → one conversational turn, driven by real state:
      - greetings and status questions are answered conversationally, zero execution
      - Plan Mode: real reasoning + plan response only — the node never runs and
        the execution gate is ON (blocked, enforced by the runtime, spec §8)
      - Build Mode: the agent's REAL node runs with inline human approval and
        cooperative stop. Outcomes derive from real bus events, never invented.
    The human message is part of the same conversation stream (spec §18)."""
    os.environ["AVIS_LLM_ENABLED"] = "1" if llm else "0"
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    now = time.time()
    run_id = f"run-ws-{int(time.time() * 1000)}-{agent_id}"
    started = _iso(now)
    mode = store.get("mode", "plan")

    store["current_run"] = {"id": run_id, "status": "working", "started_at": started,
                            "mode": mode, "message": message}
    store["status"] = "working"
    store["run_id"] = run_id
    store["stop_requested"] = False

    _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": started,
                              "content": f"{mode.capitalize()} Mode turn started"})

    if studio.is_greeting(message):
        _finish_ws_turn(agent_id, run_id, "completed",
                        studio.greeting_reply(agent_id), started)
        return

    if studio.is_status_question(message):
        _finish_ws_turn(agent_id, run_id, "completed",
                        studio.status_summary(agent_id, store["conversation"]), started)
        return

    # Before ANY consequential execution the agent says what it will do (spec §16)
    _push_ws_event(agent_id, {"type": "intent", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": _iso(),
                              "content": studio.intent_message(agent_id, message)})

    if mode == "plan":
        # Plan Mode has zero execution authority: the gate is set defensively
        # AND the node is never invoked — only the real think stream runs, so
        # reasoning_summary events are genuine.
        tools.set_execution_blocked(True)
        try:
            brain.think_stream(agent_id, {"topic": message})
        finally:
            tools.set_execution_blocked(False)
        _finish_ws_turn(agent_id, run_id, "completed",
                        studio.plan_response(agent_id, message), started)
        return

    ctx_before = dict(_workspace_context)
    since = time.time()
    try:
        final = studio.execute_agent_run(
            agent_id, message, ctx_before,
            approver=_make_approver(agent_id, run_id, store),
            should_stop=lambda: bool(store.get("stop_requested")))
    except Exception as e:  # noqa: BLE001 — surface any failure honestly
        _finish_ws_turn(agent_id, run_id, "failed", f"Execution failed — {e}", started)
        return

    with _graph_lock:
        _workspace_context.update({k: v for k, v in final.items()
                                   if k not in ("log", "mailboxes")})

    if final.get("stopped"):
        _finish_ws_turn(agent_id, run_id, "stopped",
                        _stopped_message(agent_id, since), started)
        return

    scoped = [e for e in events.bus.history(since) if e.get("agent") == agent_id]
    error_log = [l for l in final.get("log", []) if l.get("level") == "error"]
    if error_log:
        _finish_ws_turn(agent_id, run_id, "failed",
                        f"Execution failed — {str(error_log[-1]['text'])}", started)
        return

    result_ev = [e for e in scoped if e.get("kind") == "result"]
    result_text = ""
    if result_ev:
        result_text = str(result_ev[-1]["text"]).split(" -> ", 1)[-1]
    for art in studio._artifacts_from_state(final, context=ctx_before):
        _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": _iso(),
                                  "content": f"Produced artifact: {art['name']} — {art['meta']}"})
    _finish_ws_turn(agent_id, run_id, "completed", result_text, started)


def _make_approver(agent_id: str, run_id: str,
                   store: dict[str, Any]) -> Callable[[dict[str, Any]], str]:
    """The inline human approval flow (spec §4/§5): the run PAUSES while the
    approval_request is visible in the conversation; the human answers via
    POST /approval. Stop also releases the approval as rejected."""
    import threading as _threading
    import uuid as _uuid

    def approver(question: dict[str, Any]) -> str:
        pending = {"id": f"approval-{_uuid.uuid4().hex[:8]}",
                   "run_id": run_id,
                   "question": str(question.get("question", ""))[:300],
                   "event": _threading.Event(), "answer": None}
        store["approval_pending"] = pending
        store["status"] = "waiting"
        if store.get("current_run"):
            store["current_run"]["status"] = "waiting"
        _push_ws_event(agent_id, {"type": "approval_request", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": _iso(),
                                  "approval": {"title": "Approval required",
                                               "description": pending["question"],
                                               "action": "approve",
                                               "status": "required"}})
        while not pending["event"].wait(0.2):
            if store.get("stop_requested"):
                break
        answer = pending["answer"] or "rejected"
        status = "approved" if answer == "approve" else "rejected"
        _push_ws_event(agent_id, {"type": "approval_result", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": _iso(),
                                  "approval": {"title": pending["question"][:80],
                                               "status": status}})
        store["approval_pending"] = None
        if store.get("current_run"):
            store["current_run"]["status"] = "working"
        return answer

    return approver


def _stopped_message(agent_id: str, since: float) -> str:
    """The honest post-stop report, derived from this run's real events
    (spec §6/§42). 'Stopped' is a real runtime cancellation, not a notice."""
    scoped = [e for e in events.bus.history(since) if e.get("agent") == agent_id]
    completed = [e for e in scoped if e.get("kind") == "tool_result"
                 and not e.get("error")]
    parts = ["Stopped — the run was cancelled.",
             f"Before the stop request, {len(completed)} tool call(s) had completed."]
    if not completed:
        parts.append("No tool call had completed yet.")
    parts.append("No further actions were taken after the stop request.")
    return "\n".join(parts)


def _finish_ws_turn(agent_id: str, run_id: str, status: str,
                    reply: str, started: str) -> None:
    """Close a conversational turn: persist the assistant message and the run
    status as conversation events — the ONLY assistant_message in the stream
    comes from here (bus result events are not mapped, so nothing duplicates).
    No handoff is recommended, no next agent is routed: the human governs.
    Events are pushed BEFORE the terminal status becomes visible so a client
    that observes the finished run always sees its final message."""
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    ended = _iso()

    if status == "failed":
        _push_ws_event(agent_id, {"type": "error", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "content": reply})
    else:
        _push_ws_event(agent_id, {"type": "assistant_message", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "content": reply})
        _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "content": f"Turn {status} ({time.time() - calendar.timegm(time.strptime(started, '%Y-%m-%dT%H:%M:%SZ')):.1f}s)"})

    store["status"] = status
    store["run_id"] = None
    if store.get("current_run"):
        store["current_run"]["status"] = status
        store["current_run"]["ended_at"] = ended


@app.post("/api/studio/agents/{agent_id}/handoff")
async def api_workspace_handoff(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Human-governed agent switch (spec §6/§7): there is NO auto-routing and
    NO handoff recommendation. This only carries out an EXPLICIT human
    decision — without one the runtime refuses (400, tested)."""
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    decision = str(payload.get("decision", "")).strip().lower()
    if not decision:
        raise HTTPException(status_code=400,
                            detail="unauthorized handoff: an explicit human decision is required")
    if decision not in ("approve", "redirect"):
        raise HTTPException(status_code=400, detail=f"invalid handoff decision: {decision}")
    target = payload.get("target_agent_id")
    if not target or target not in BY_ID:
        raise HTTPException(status_code=400, detail=f"invalid target agent: {target}")
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                              "timestamp": _iso(),
                              "content": f"Human decision: {decision} → "
                                         f"{studio.NAMES.get(target, target)}"})
    return {"approved": True, "decision": decision, "source_agent_id": agent_id,
            "target_agent_id": target, "workspace_url": f"/workspace/{target}"}


@app.post("/api/studio/agents/{agent_id}/mode")
async def api_workspace_mode(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Switch this agent between Plan and Build interaction modes (spec §2).
    Explicit only — never automatic; refused while a run is active."""
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    mode = str(payload.get("mode", "")).strip().lower()
    if mode not in ("plan", "build"):
        raise HTTPException(status_code=400, detail="mode must be 'plan' or 'build'")
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    if store.get("status") in ("working", "waiting"):
        return {"ok": False, "error": "agent is running — stop it first"}
    store["mode"] = mode
    _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                              "timestamp": _iso(),
                              "content": f"Switched to {mode.capitalize()} Mode"})
    return {"ok": True, "mode": mode}


@app.post("/api/studio/agents/{agent_id}/approval")
async def api_workspace_approval(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """The human answers an inline approval_request. The paused run resumes
    only from this real answer (spec §4/§5)."""
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    pending = store.get("approval_pending")
    if not pending:
        return {"ok": False, "error": "no approval is pending"}
    answer = str(payload.get("answer", "")).strip().lower()
    if answer not in ("approve", "reject", "rejected", "deny"):
        return {"ok": False, "error": "answer must be approve|rejected"}
    if answer in ("reject", "deny"):
        answer = "rejected"
    run_id = payload.get("run_id")
    if run_id and str(run_id) != str(pending["run_id"]):
        return {"ok": False, "error": "stale approval: that run has ended"}
    pending["answer"] = answer
    pending["event"].set()
    return {"ok": True, "answer": answer}


@app.post("/api/studio/agents/{agent_id}/stop")
async def api_workspace_stop(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Real runtime cancellation (spec §6/§42): cooperative — the run is asked
    to stop at its next checkpoint; a pending approval is released as rejected."""
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    run = store.get("current_run")
    run_id = payload.get("run_id")
    if not run or run.get("status") not in ("working", "waiting"):
        return {"ok": False, "error": "no active run to stop"}
    if run_id and str(run_id) != str(run["id"]):
        return {"ok": False, "error": "stale run id"}
    store["stop_requested"] = True
    store["status"] = "stopping"
    pending = store.get("approval_pending")
    if pending:
        pending["answer"] = "rejected"
        pending["event"].set()
    _push_ws_event(agent_id, {"type": "status", "agent_id": agent_id,
                              "run_id": run["id"], "timestamp": _iso(),
                              "content": "Stop requested — cancelling the run"})
    return {"ok": True, "stopping": True}


@app.get("/api/studio/agents/{agent_id}/events")
async def api_workspace_events(agent_id: str, request: Request):
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")

    queue: asyncio.Queue = asyncio.Queue()
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    if not store["conversation"]:
        _push_ws_event(agent_id, {"type": "assistant_message", "agent_id": agent_id,
                                  "timestamp": _iso(),
                                  "content": studio.greeting_reply(agent_id)})
    for ev in store["conversation"]:
        queue.put_nowait(ev)
    _workspace_queues.append(queue)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if ev.get("agent_id") not in (agent_id, "you"):
                    continue
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
        finally:
            _workspace_queues.remove(queue)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/state")
def api_state() -> dict[str, Any]:
    with _graph_lock:
        report = _state.get("review_report") or {}
        return {"running": _state.get("running", False),
                "topic": _state.get("topic"),
                "review_decision": report.get("decision"),
                "checks": report.get("checks"),
                "iterations": _state.get("iterations"),
                "revocations": len(_state.get("revocations", [])),
                "visual_assignments": len(_state.get("visual_assignments", [])),
                "llm_enabled": os.environ.get("AVIS_LLM_ENABLED", "1") == "1",
                "auto_approve": _auto_approve}


@app.get("/api/examples")
def api_examples() -> dict[str, Any]:
    files = sorted(p.name for p in EXAMPLES.glob("*.json")) if EXAMPLES.exists() else []
    return {"examples": files}


@app.get("/api/pending")
def api_pending() -> dict[str, Any]:
    with _graph_lock:
        return {"question": _pending_question, "resume": bool(_pending_resume)}


@app.get("/api/knowledge")
def api_knowledge() -> dict[str, Any]:
    import avis.knowledge as knowledge
    return {"runs": knowledge.list_runs(),
            "corpus": knowledge.load_corpus()[:300],
            "corpus_total": len(knowledge.load_corpus())}


@app.post("/api/knowledge/retrieve")
def api_knowledge_retrieve(payload: dict[str, Any]) -> dict[str, Any]:
    import avis.knowledge as knowledge
    query = str(payload.get("query", ""))[:200]
    return {"query": query, "results": knowledge.retrieve(query)}


@app.get("/api/events")
async def api_events(request: Request):
    from fastapi.responses import StreamingResponse

    queue: asyncio.Queue = asyncio.Queue()
    for ev in events.bus.history():
        queue.put_nowait(ev)
    _sse_queues.append(queue)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                yield f"data: {json.dumps(ev)}\n\n"
        finally:
            _sse_queues.remove(queue)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/run")
async def api_run(payload: dict[str, Any]) -> dict[str, Any]:
    global _state, _auto_approve
    topic = payload.get("topic", "Default topic")
    ref = payload.get("reference_analysis")
    if ref:
        p = Path(ref)
        if p.is_absolute() or ".." in p.parts or p.suffix != ".json":
            return {"ok": False, "error": "reference_analysis must be a filename inside examples/"}
        candidate = (EXAMPLES / p.name).resolve()
        if not str(candidate).startswith(str(EXAMPLES.resolve())):
            return {"ok": False, "error": "reference_analysis must live in examples/"}
        ref = str(candidate)
    os.environ["AVIS_LLM_ENABLED"] = "1" if payload.get("llm", False) else "0"
    with _graph_lock:
        _auto_approve = bool(payload.get("auto_approve", False))
        _state = g.seed_state(topic, reference_file=ref)
        _state["running"] = True

    def _worker() -> None:
        try:
            final = g.run(_graph, {k: v for k, v in _state.items() if k != "running"},
                          _remote_approver)
            with _graph_lock:
                _state.update(final)
                _state["running"] = False
        except Exception as e:
            events.bus.emit("server", "error", f"run failed: {e}")
            with _graph_lock:
                _state["running"] = False

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "topic": topic}


@app.post("/api/answer")
async def api_answer(payload: dict[str, Any]) -> dict[str, Any]:
    """Resume the pending interrupt with the CEO's answer ('approve' to pass)."""
    global _pending_question
    if not _pending_resume:
        return {"ok": False, "error": "no pending interrupt"}
    fn = _pending_resume.pop()
    _pending_question = {}
    fn(payload.get("resume", "rejected"))
    return {"ok": True}


def _remote_approver(question: dict[str, Any]) -> Any:
    global _pending_question
    if _auto_approve:
        events.bus.emit("CEO", "note", "auto-approve (demo mode)")
        return "approve"
    events.bus.emit("CEO", "interrupt", "web approval pending — answer in the browser")
    _pending_question = question
    ev = threading.Event()
    result: list[Any] = []

    def _set(v: Any) -> None:
        result.append(v)
        try:
            _pending_resume.remove(_set)
        except ValueError:
            pass
        ev.set()

    _pending_resume.append(_set)
    ev.wait(timeout=600)
    return result[0] if result else "rejected: timeout"


@app.get("/api/js/mermaid.min.js")
def mermaid_js() -> Any:
    """Offline fallback — fetch and save mermaid.min.js next to static/index.html
    to view the graph without internet."""
    return _static_jslib()


def _static_jslib() -> Any:
    from fastapi.responses import PlainTextResponse
    p = STATIC / "mermaid.min.js"
    if p.exists():
        return PlainTextResponse(p.read_text(), media_type="application/javascript")
    return PlainTextResponse("console.error('mermaid.min.js not downloaded — view needs internet');",
                             media_type="application/javascript")