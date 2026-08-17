"""UI 2 — Agent Studio Dashboard + Workspaces (FastAPI).

Serves (AUTONOMOUS_AGENTS_PLAN §8, §12):
  GET  /                         the Agent Dashboard (org overview)
  GET  /workspace/{agent_id}     agent workspace page (conversation-first)
  GET  /api/agents               the 17 agents + departments
  GET  /api/agents/{agent_id}    one agent display metadata
  GET  /api/examples             reference-analysis JSON files in examples/
  GET  /api/events               Server-Sent Events: raw runtime events
  GET  /api/studio/dashboard     Agent Dashboard snapshot (org overview)
  GET  /api/studio/events        Server-Sent Events: studio-mapped events
  GET  /api/studio/agents/{id}   workspace snapshot (one agent + session list)
  GET  /api/studio/agents/{id}/sessions/{sid}  single session details
  POST /api/studio/agents/{id}/sessions        new session
  POST /api/studio/agents/{id}/sessions/{sid}/activate
  DELETE /api/studio/agents/{id}/sessions/{sid}
  POST /api/studio/agents/{id}/messages   send a message (one turn)
  POST /api/studio/agents/{id}/mode       switch Plan/Build mode
  POST /api/studio/agents/{id}/approval   answer inline approval_request
  POST /api/studio/agents/{id}/stop       cooperative stop
  POST /api/studio/agents/{id}/handoff    resolve handoff (accept/reject/redirect)
  GET  /api/studio/agents/{id}/events   workspace SSE (conversation)
  GET  /api/knowledge             knowledge base (recorded sessions)

No workflow engine, no /api/run, no /api/answer, no graph — the human drives
work via conversations and handoffs."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse

import avis.brain as brain_mod
import avis.events as events
import avis.knowledge as knowledge
import avis.studio as studio

STATIC = Path(__file__).parent / "static"
EXAMPLES = Path(__file__).resolve().parent.parent.parent / "examples"

app = FastAPI(title="AVIS — Agent Studio")

# --- SSE queues -----------------------------------------------------------

_sse_queues: list[asyncio.Queue] = []
_studio_sse_queues: list[asyncio.Queue] = []
_workspace_queues: list[asyncio.Queue] = []
_loop: asyncio.AbstractEventLoop | None = None


def _iso(ts: Optional[float] = None) -> str:
    t = time.gmtime(ts) if ts is not None else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


# --- bus pumps ------------------------------------------------------------

def _pump(ev: dict[str, Any]) -> None:
    if _loop is None:
        return
    _loop.call_soon_threadsafe(
        lambda: [q.put_nowait(ev) for q in list(_sse_queues)])


def _pump_studio(ev: dict[str, Any]) -> None:
    if _loop is None:
        return
    mapped = studio.map_studio_event(ev)
    if mapped is not None:
        _loop.call_soon_threadsafe(
            lambda: [q.put_nowait(mapped) for q in list(_studio_sse_queues)])


def _pump_workspace(ev: dict[str, Any]) -> None:
    if _loop is None:
        return
    # Workspace SSE only shows events for the current agent + "you"
    # The filtering happens in the endpoint.
    _loop.call_soon_threadsafe(
        lambda: [q.put_nowait(ev) for q in list(_workspace_queues)])


@app.on_event("startup")
def _startup() -> None:
    global _loop
    _loop = asyncio.get_event_loop()
    events.bus.subscribe(_pump)
    events.bus.subscribe(_pump_studio)
    events.bus.subscribe(_pump_workspace)


# --- static pages ---------------------------------------------------------

def _static(name: str) -> HTMLResponse:
    return HTMLResponse((STATIC / name).read_text())


@app.get("/")
def index() -> HTMLResponse:
    return _static("dashboard.html")


@app.get("/workspace/{agent_id}")
def workspace_view(agent_id: str) -> HTMLResponse:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    return _static("workspace.html")


# --- registry & agents ----------------------------------------------------

@app.get("/api/agents")
def api_agents() -> dict[str, Any]:
    return {"agents": studio.registry()}


@app.get("/api/agents/{agent_id}")
def api_agent(agent_id: str) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    meta = {a["id"]: a for a in studio.registry()}[agent_id]
    return {"agent": meta, "department": meta["department"], "tier": meta["tier"]}


# --- dashboard ------------------------------------------------------------

@app.get("/api/studio/dashboard")
def api_studio_dashboard() -> dict[str, Any]:
    return studio.build_dashboard_snapshot()


@app.get("/api/studio/events")
async def api_studio_events(request: Request):
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
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


# --- workspace API --------------------------------------------------------

@app.get("/api/studio/agents/{agent_id}")
def api_workspace_snapshot(agent_id: str,
                           session_id: Optional[str] = None) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    return studio.build_workspace_snapshot(agent_id, session_id)


@app.get("/api/studio/agents/{agent_id}/sessions/{session_id}")
def api_session_detail(agent_id: str, session_id: str) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    sess = studio.get_session(agent_id, session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail=f"no such session: {session_id}")
    return {"id": sess["id"], "title": sess["title"],
            "status": sess["status"], "mode": sess["mode"],
            "task": sess["task"], "run_id": sess.get("run_id"),
            "created_at": sess["created_at"],
            "last_activity_at": sess["last_activity_at"],
            "conversation": sess["conversation"][-200:],
            "state_artifacts": {k: sess["state"].get(k) is not None
                                for k in studio._memory_labels({})}}


@app.post("/api/studio/agents/{agent_id}/sessions")
async def api_new_session(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    task = str(payload.get("task", "")).strip()
    if not task:
        return {"ok": False, "error": "task is empty"}
    mode = str(payload.get("mode", "plan")).lower()
    if mode not in ("plan", "build"):
        return {"ok": False, "error": "mode must be 'plan' or 'build'"}
    sess = studio.new_session(agent_id, task, mode=mode)
    return {"ok": True, "session_id": sess["id"], "title": sess["title"]}


@app.post("/api/studio/agents/{agent_id}/sessions/{session_id}/activate")
async def api_activate_session(agent_id: str, session_id: str) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    if not studio.activate_session(agent_id, session_id):
        raise HTTPException(status_code=404, detail=f"no such session: {session_id}")
    return {"ok": True, "active_session_id": session_id}


@app.delete("/api/studio/agents/{agent_id}/sessions/{session_id}")
async def api_delete_session(agent_id: str, session_id: str) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    err = studio.delete_session(agent_id, session_id)
    if err:
        return {"ok": False, "error": err}
    return {"ok": True}


@app.post("/api/studio/agents/{agent_id}/messages")
async def api_workspace_message(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    message = str(payload.get("message", "")).strip()
    if not message:
        return {"ok": False, "error": "message is empty"}
    session_id = payload.get("session_id")
    session = studio.get_session(agent_id, session_id) if session_id else None
    if session is None:
        # no session specified → active or new
        session = studio.get_session(agent_id) or studio.new_session(
            agent_id, message, mode="plan")
    if session["status"] in ("working", "waiting", "stopping"):
        return {"ok": False, "error": "agent is already running — wait or stop it"}

    # append user message
    session["conversation"].append({"type": "user_message", "agent_id": "you",
                                     "timestamp": _iso(), "content": message})

    threading.Thread(target=_run_session_worker,
                     args=(agent_id, session["id"], message),
                     daemon=True).start()
    return {"ok": True, "session_id": session["id"]}


def _run_session_worker(agent_id: str, session_id: str, message: str) -> None:
    session = studio.get_session(agent_id, session_id)
    if session is None:
        return
    session["status"] = "working"
    session["stop_requested"] = False

    if not brain_mod.model_configured():
        session["conversation"].append({
            "type": "status", "agent_id": agent_id,
            "timestamp": _iso(),
            "content": studio.no_model_notice()})
        session["status"] = "idle"
        return

    def should_stop() -> bool:
        return session.get("stop_requested", False)

    outcome = studio.run_session(
        agent_id, session_id, message, session["state"],
        session["mode"], session=session,
        should_stop=should_stop)

    # knowledge recording happens inside run_session for Build Mode

    if outcome.get("status") == "handed_off":
        ho = outcome["handoff"]
        session["handoff"] = {"run_id": ho["run_id"], "target": ho["target"],
                              "prompt": ho["prompt"], "decision": None}
        session["status"] = "handed_off"
    elif outcome.get("status") in ("stopped", "stopped_cap"):
        session["status"] = "idle"
    elif outcome.get("status") == "failed":
        session["status"] = "failed"
    else:
        session["status"] = "idle"


@app.post("/api/studio/agents/{agent_id}/mode")
async def api_workspace_mode(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    mode = str(payload.get("mode", "")).strip().lower()
    if mode not in ("plan", "build"):
        return {"ok": False, "error": "mode must be 'plan' or 'build'"}
    session_id = payload.get("session_id")
    session = studio.get_session(agent_id, session_id)
    if session is None:
        return {"ok": False, "error": "no active session"}
    if session["status"] in ("working", "waiting", "stopping"):
        return {"ok": False, "error": "agent is running — stop it first"}
    session["mode"] = mode
    return {"ok": True, "mode": mode}


@app.post("/api/studio/agents/{agent_id}/approval")
async def api_workspace_approval(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    session_id = payload.get("session_id")
    session = studio.get_session(agent_id, session_id)
    if session is None:
        return {"ok": False, "error": "no such session"}
    pending = session.get("approval")
    if not pending:
        return {"ok": False, "error": "no approval is pending"}
    answer = str(payload.get("answer", "")).strip().lower()
    if answer not in ("approve", "reject", "rejected", "deny"):
        return {"ok": False, "error": "answer must be approve|rejected"}
    if answer in ("reject", "deny"):
        answer = "rejected"
    run_id = payload.get("run_id")
    if run_id and str(run_id) != str(pending.get("run_id", "")):
        return {"ok": False, "error": "stale approval: that run has ended"}
    pending["answer"] = answer
    pending["event"].set()
    return {"ok": True, "answer": answer}


@app.post("/api/studio/agents/{agent_id}/stop")
async def api_workspace_stop(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    session_id = payload.get("session_id")
    session = studio.get_session(agent_id, session_id)
    if session is None:
        return {"ok": False, "error": "no such session"}
    if session["status"] not in ("working", "waiting"):
        return {"ok": False, "error": "no active run to stop"}
    session["stop_requested"] = True
    session["status"] = "stopping"
    pending = session.get("approval")
    if pending:
        pending["answer"] = "rejected"
        pending["event"].set()
    return {"ok": True, "stopping": True}


@app.post("/api/studio/agents/{agent_id}/handoff")
async def api_workspace_handoff(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    decision = str(payload.get("decision", "")).strip().lower()
    if decision not in ("accept", "reject", "redirect"):
        return {"ok": False, "error": "decision must be accept|reject|redirect"}
    session_id = payload.get("session_id")
    session = studio.get_session(agent_id, session_id)
    if session is None:
        return {"ok": False, "error": "no such session"}
    ho = session.get("handoff")
    if not ho:
        return {"ok": False, "error": "no pending handoff on that session"}
    target = payload.get("target_agent_id") or ho["target"]
    note = payload.get("note")

    result = studio.resolve_handoff(agent_id, session_id, decision,
                                    target_agent_id=target, note=note)
    if not result.get("ok"):
        return result

    # On accept/redirect: auto-run the seeded session in the target workspace
    if result.get("decision") in ("accept", "redirect"):
        target = result["target"]
        seeded_id = result["session_id"]
        seeded = studio.get_session(target, seeded_id)
        if seeded:
            threading.Thread(target=_run_session_worker,
                             args=(target, seeded_id, seeded["task"]),
                             daemon=True).start()

    return result


# --- workspace SSE --------------------------------------------------------

@app.get("/api/studio/agents/{agent_id}/events")
async def api_workspace_events(agent_id: str, request: Request):
    if agent_id not in studio.NAMES:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    session_id = request.query_params.get("session_id")
    session = studio.get_session(agent_id, session_id)
    if session is None:
        session = studio.get_session(agent_id)
    if session is None:
        raise HTTPException(status_code=404, detail="no session for this agent")

    queue: asyncio.Queue = asyncio.Queue()
    for ev in session["conversation"]:
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
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


# --- knowledge / raw events ----------------------------------------------

@app.get("/api/knowledge")
def api_knowledge() -> dict[str, Any]:
    return {"runs": knowledge.list_runs(),
            "corpus": knowledge.load_corpus()[:300],
            "corpus_total": len(knowledge.load_corpus())}


@app.post("/api/knowledge/retrieve")
def api_knowledge_retrieve(payload: dict[str, Any]) -> dict[str, Any]:
    query = str(payload.get("query", ""))[:200]
    return {"query": query, "results": knowledge.retrieve(query)}


@app.get("/api/events")
async def api_events(request: Request):
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
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.get("/api/examples")
def api_examples() -> dict[str, Any]:
    files = sorted(p.name for p in EXAMPLES.glob("*.json")) if EXAMPLES.exists() else []
    return {"examples": files}


# keep for backward-compat (returns empty - no run flow)
@app.get("/api/state")
def api_state() -> dict[str, Any]:
    return {"running": False, "topic": None, "review_decision": None,
            "iterations": 0, "revocations": 0, "visual_assignments": 0,
            "llm_enabled": brain_mod.model_configured(), "auto_approve": False}


@app.get("/api/pending")
def api_pending() -> dict[str, Any]:
    return {"question": None, "resume": False}