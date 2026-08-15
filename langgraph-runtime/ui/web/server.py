"""UI 2 — Agent Studio Dashboard + live activity (FastAPI).

Serves:
  GET  /                        the Agent Dashboard (presentation view)
  GET  /workspace/{agent_id}    agent workspace (placeholder — Stage Two build)
  GET  /graph                   the LangGraph technical view (mermaid)
  GET  /api/graph               the LangGraph state graph as mermaid text
  GET  /api/agents              the 17 agents and departments
  GET  /api/agents/{agent_id}   one agent + live status
  GET  /api/examples            reference-analysis JSON files in examples/
  GET  /api/events              Server-Sent Events: raw runtime events
  GET  /api/studio/dashboard    Agent Dashboard snapshot (real state)
  GET  /api/studio/events       Server-Sent Events: studio-mapped events
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
from pathlib import Path
from typing import Any

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


@app.on_event("startup")
def _startup() -> None:
    global _graph, _mermaid, _loop
    _loop = asyncio.get_event_loop()
    _graph, _mermaid = g.build_graph()
    events.bus.subscribe(_pump)
    events.bus.subscribe(_pump_studio)


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