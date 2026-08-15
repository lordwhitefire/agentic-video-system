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
  POST /api/studio/agents/{id}/messages  send the agent a task (runs its real node)
  POST /api/studio/agents/{id}/handoff   approve / redirect / continue a handoff
  GET  /api/studio/agents/{id}/events    workspace Server-Sent Events
  GET  /api/state               latest run state snapshot
  GET  /api/pending             the pending CEO approval question (script / proposals)
  POST /api/run                 start a run (JSON: topic, reference_analysis?, llm?, auto_approve?)
  POST /api/answer              answer the pending CEO approval question (JSON: resume)

The orchestrator stays deterministic; this server only observes and streams."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request

import avis.events as events
import avis.graph as g
import avis.studio as studio

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

# --- Agent Workspace (Stage Two) state -------------------------------------
# shared project context: real outputs produced across workspace handoffs so
# the next agent genuinely inherits the previous agent's work (spec §56/§57)
_workspace_context: dict[str, Any] = {}
# per-agent workspace store: messages, synthetic run/handoff events, status
_workspace_store: dict[str, dict[str, Any]] = {}
_workspace_queues: list[asyncio.Queue] = []


def _iso(ts: float | None = None) -> str:
    t = time.gmtime(ts) if ts is not None else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


def _fresh_ws_store() -> dict[str, Any]:
    return {"messages": [], "events": [], "current_run": None,
            "status": "idle", "run_id": None, "handoff": None}


def _ws_events(agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Merged, deduped, time-ordered events for one agent: synthetic store
    events + real bus events (recoverable, survives refresh — spec §66)."""
    merged = list(_workspace_store.get(agent_id, {}).get("events", [])) \
        + studio.workspace_events(agent_id)
    seen: set[tuple] = set()
    out: list[dict[str, Any]] = []
    for e in sorted(merged, key=lambda x: x.get("timestamp", "")):
        key = (e.get("type"), e.get("timestamp"), str(e.get("data", ""))[:120])
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out[-limit:]


def _push_ws_event(agent_id: str, event: dict[str, Any]) -> None:
    """Record a synthetic workspace event and broadcast it to open workspaces."""
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    store["events"].append(event)
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
    """Bus listener → mapped workspace events → workspace SSE consumers."""
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
        return studio.build_workspace_snapshot(agent_id, store, _state, _pending_question)


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
    store["messages"].append({"role": "human", "content": message,
                              "timestamp": _iso()})
    threading.Thread(target=_run_agent_worker, args=(agent_id, message, llm),
                     daemon=True).start()
    return {"ok": True, "accepted": True}


def _run_agent_worker(agent_id: str, message: str, llm: bool = False) -> None:
    """Runs the agent's REAL node function (single-node graph, tested g.run
    loop). Outcome and result text are derived from real bus events — never
    invented. Context from the shared workspace project is carried forward.
    LLM is off by default so workspace runs are deterministic and fast."""
    os.environ["AVIS_LLM_ENABLED"] = "1" if llm else "0"
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    now = time.time()
    run_id = f"run-ws-{time.strftime('%H%M%S', time.gmtime(now))}-{agent_id}"
    started = _iso(now)
    store["current_run"] = {"id": run_id, "status": "working", "started_at": started}
    store["status"] = "working"
    store["handoff"] = None
    store["handoff_resolved"] = False
    store["run_id"] = run_id

    _push_ws_event(agent_id, {"type": "run_started", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": started})
    _push_ws_event(agent_id, {"type": "agent_status_changed", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": started,
                              "data": {"status": "working"}})
    _push_ws_event(agent_id, {"type": "agent_progress_changed", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": started,
                              "data": {"progress": 0}})
    _push_ws_event(agent_id, {"type": "plan_created", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": started,
                              "data": {"steps": studio.workspace_plan(agent_id, message)}})

    ctx_before = dict(_workspace_context)
    since = time.time()
    try:
        final = studio.execute_agent_run(agent_id, message, ctx_before)
    except Exception as e:  # noqa: BLE001 — surface any failure honestly
        _finish_ws_run(agent_id, run_id, "failed", None, f"run failed: {e}")
        return

    with _graph_lock:
        _workspace_context.update({k: v for k, v in final.items()
                                   if k not in ("log", "mailboxes")})

    scoped = [e for e in events.bus.history(since) if e.get("agent") == agent_id]
    stopped = [e for e in scoped
               if e.get("kind") == "note" and "stopped" in str(e.get("text", "")).lower()]
    error_log = [l for l in final.get("log", []) if l.get("level") == "error"]
    if stopped or error_log:
        detail = (stopped[-1]["text"] if stopped else str(error_log[-1]["text"]))
        _finish_ws_run(agent_id, run_id, "failed", None, detail)
        return

    result_ev = [e for e in scoped if e.get("kind") == "result"]
    result_text = ""
    if result_ev:
        result_text = str(result_ev[-1]["text"])
        result_text = result_text.split(" -> ", 1)[-1]
    artifacts = studio._artifacts_from_state(final, context=ctx_before)
    _finish_ws_run(agent_id, run_id, "completed", result_text, None, artifacts)


def _finish_ws_run(agent_id: str, run_id: str, status: str,
                   result_text: Optional[str], error: Optional[str],
                   artifacts: Optional[list[dict[str, Any]]] = None) -> None:
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())
    ended = _iso()
    store["status"] = status
    if store.get("current_run"):
        store["current_run"]["status"] = status

    if status == "failed":
        store["messages"].append({"role": "agent", "content": f"Execution failed — {error}",
                                  "timestamp": ended})
        store["events"].append({"type": "run_failed", "agent_id": agent_id,
                                "run_id": run_id, "timestamp": ended,
                                "data": {"error": error}})
        _push_ws_event(agent_id, {"type": "run_failed", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "data": {"error": error}})
        _push_ws_event(agent_id, {"type": "agent_status_changed", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "data": {"status": "failed"}})
        return

    store["events"].append({"type": "run_completed", "agent_id": agent_id,
                            "run_id": run_id, "timestamp": ended,
                            "data": {"result": result_text or ""}})
    _push_ws_event(agent_id, {"type": "run_completed", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": ended,
                              "data": {"result": result_text or ""}})
    _push_ws_event(agent_id, {"type": "agent_status_changed", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": ended,
                              "data": {"status": "completed"}})
    _push_ws_event(agent_id, {"type": "agent_progress_changed", "agent_id": agent_id,
                              "run_id": run_id, "timestamp": ended,
                              "data": {"progress": 100}})

    if result_text:
        store["messages"].append({"role": "agent", "content": result_text,
                                  "timestamp": ended})
        _push_ws_event(agent_id, {"type": "message_created", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "data": {"role": "agent", "content": result_text,
                                           "timestamp": ended}})

    for art in artifacts or []:
        art_msg = dict(art)
        art_msg["type"] = "artifact"
        art_msg["timestamp"] = ended
        store["messages"].append(art_msg)
        _push_ws_event(agent_id, {"type": "artifact_created", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "data": {"name": art["name"], "filename": art["filename"],
                                           "meta": art["meta"]}})

    handoff = studio.handoff_recommendation(agent_id)
    if handoff:
        store["handoff"] = handoff
        _push_ws_event(agent_id, {"type": "handoff_ready", "agent_id": agent_id,
                                  "run_id": run_id, "timestamp": ended,
                                  "data": handoff})


@app.post("/api/studio/agents/{agent_id}/handoff")
async def api_workspace_handoff(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    from fastapi import HTTPException
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    decision = str(payload.get("decision", ""))
    if decision not in ("approve", "redirect", "continue"):
        return {"ok": False, "error": f"invalid handoff decision: {decision}"}
    target = payload.get("target_agent_id")
    store = _workspace_store.setdefault(agent_id, _fresh_ws_store())

    if decision == "continue":
        store["handoff"] = None
        store["handoff_resolved"] = True
        _push_ws_event(agent_id, {"type": "handoff_redirected", "agent_id": agent_id,
                                  "timestamp": _iso(), "data": {"decision": "continue"}})
        store["messages"].append({"role": "system",
                                  "content": "Handoff declined — continuing with this agent.",
                                  "timestamp": _iso()})
        return {"approved": True, "decision": "continue"}

    if not target or target not in BY_ID:
        raise HTTPException(status_code=400, detail=f"invalid target agent: {target}")
    store["handoff"] = None
    store["handoff_resolved"] = True
    wtype = "handoff_approved" if decision == "approve" else "handoff_redirected"
    _push_ws_event(agent_id, {"type": wtype, "agent_id": agent_id,
                              "timestamp": _iso(), "data": {"target_agent_id": target}})
    store["messages"].append({"role": "system",
                              "content": f"Handoff {'approved' if decision == 'approve' else 'redirected'} → "
                                         f"{studio.NAMES.get(target, target)}.",
                              "timestamp": _iso()})
    return {"approved": True, "decision": decision, "source_agent_id": agent_id,
            "target_agent_id": target, "workspace_url": f"/workspace/{target}"}


@app.get("/api/studio/agents/{agent_id}/events")
async def api_workspace_events(agent_id: str, request: Request):
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    from avis.agents import BY_ID
    if agent_id not in BY_ID:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")

    queue: asyncio.Queue = asyncio.Queue()
    for ev in _ws_events(agent_id):
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
                if ev.get("agent_id") != agent_id:
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