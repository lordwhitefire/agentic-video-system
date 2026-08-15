"""Agent Studio — presentation layer over the real AVIS runtime.

Stage One: the Agent Dashboard backend adapter.

Everything reported here is derived from REAL runtime state: the event bus,
the run state, and the knowledge repository. No fabricated statuses, no
second agent implementation. An agent is "completed" only when its node
actually produced a result event; "working" only while the run is live and
its node is mid-flight; "waiting" only when a CEO interrupt is pending.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import avis.agents as agents_mod
import avis.events as events
import avis.knowledge as knowledge

# --------------------------------------------------------------------------
# canonical agent registry (single source of truth for the studio UI)
# ids come from the runtime catalog; display metadata lives here
# --------------------------------------------------------------------------

NAMES: dict[str, str] = {
    "strategist": "Strategist",
    "analyzer": "Analyzer",
    "planner": "Planner",
    "researcher": "Researcher",
    "audio-lead": "Audio Lead",
    "tts": "TTS",
    "editor": "Editor",
    "graphics": "Graphics",
    "animation": "Animation",
    "animated-graphics": "Animated Graphics",
    "video-effects": "Video Effects",
    "clips": "Clips",
    "images": "Images",
    "reviewer": "Reviewer",
    "watcher-blocker": "Watcher / Blocker",
    "investigator": "Investigator",
    "recruiter": "Recruiter",
}

DESCRIPTIONS: dict[str, str] = {
    "strategist": "Strategy & direction",
    "analyzer": "Analysis & evaluation",
    "planner": "Planning & scripting",
    "researcher": "Sourcing & asset research",
    "audio-lead": "Audio direction & TTS planning",
    "tts": "Voiceover & audio rendering",
    "editor": "Cut & visual assembly",
    "graphics": "Static graphic overlays",
    "animation": "Motion design",
    "animated-graphics": "Animated graphic overlays",
    "video-effects": "Effect design & substitution",
    "clips": "Video clip sourcing",
    "images": "Image sourcing & overlays",
    "reviewer": "Quality review & fidelity scoring",
    "watcher-blocker": "Law watch & blocking",
    "investigator": "Law violation investigation",
    "recruiter": "Personnel & recruitment",
}

# canonical pipeline order — mirrors the deterministic graph edges in graph.py
# (watcher-blocker patrols at two watchpoints; recruiter is a registered node)
PIPELINE_ORDER: list[str] = [
    "strategist", "analyzer", "planner", "researcher", "watcher-blocker",
    "audio-lead", "tts", "editor", "graphics", "animation",
    "animated-graphics", "video-effects", "clips", "images", "reviewer",
    "investigator", "recruiter",
]

# production stages: 5 departments in org-chart order (strip, NOT a graph)
PRODUCTION_STAGES: list[dict[str, Any]] = [
    {"name": dept, "agents": [a["id"] for a in agents_mod.AGENTS
                              if a["department"] == dept]}
    for dept in ["Strategy", "Audio", "Production", "Quality", "Personnel"]
]


def registry() -> list[dict[str, Any]]:
    """Display registry: runtime id + studio display metadata."""
    out = []
    for a in agents_mod.AGENTS:
        out.append({"id": a["id"],
                    "name": NAMES.get(a["id"], a["id"]),
                    "description": DESCRIPTIONS.get(a["id"], a["department"]),
                    "department": a["department"],
                    "tier": a["tier"]})
    return out


def _agent_events(agent_id: str) -> list[dict[str, Any]]:
    return [e for e in events.bus.history() if e.get("agent") == agent_id]


def _agent_last_ts(agent_id: str) -> float:
    tss = [e["ts"] for e in _agent_events(agent_id)]
    return max(tss) if tss else 0.0


def _agent_before(ts: float) -> Optional[str]:
    """The agent whose most recent activity is closest before ts
    (used to attribute a CEO interrupt to the waiting agent)."""
    best, best_ts = None, 0.0
    for a in agents_mod.AGENTS:
        t = _agent_last_ts(a["id"])
        if 0.0 < t <= ts and t > best_ts:
            best, best_ts = a["id"], t
    return best


def waiting_agent() -> Optional[str]:
    """Agent currently blocked on a CEO interrupt, if any."""
    for e in reversed(events.bus.history()):
        if e.get("agent") == "CEO" and e.get("kind") == "interrupt":
            return _agent_before(e["ts"])
    return None


def _has_result(agent_id: str) -> bool:
    return any(e.get("kind") == "result" for e in _agent_events(agent_id))


def _last_text(agent_id: str) -> str:
    evs = _agent_events(agent_id)
    return evs[-1].get("text", "") if evs else ""


def agent_snapshot(agent_id: str, running: bool,
                   waiting: Optional[str]) -> dict[str, Any]:
    meta = {a["id"]: a for a in registry()}[agent_id]
    invoked = bool(_agent_events(agent_id))
    completed = _has_result(agent_id)
    failed = any("stopped" in (e.get("text") or "").lower()
                 or e.get("kind") == "error"
                 for e in _agent_events(agent_id))

    if waiting == agent_id:
        status = "waiting"
    elif running and invoked and not completed:
        status = "working"
    elif completed:
        status = "completed" if not failed else "failed"
    elif failed:
        status = "failed"
    else:
        status = "idle"

    if status == "idle":
        task = "Awaiting your instruction"
    elif status == "working":
        task = _last_text(agent_id) or "Working"
    else:
        task = _last_text(agent_id) or "Completed"

    # progress: real when meaningful — 100 done, 0 idle, in-flight agents
    # get their canonical pipeline position (deterministic, derived, labeled)
    if status in ("completed", "failed"):
        progress = 100
    elif status == "idle":
        progress = 0
    else:
        idx = PIPELINE_ORDER.index(agent_id) if agent_id in PIPELINE_ORDER else 0
        progress = round(100 * (idx + 1) / len(PIPELINE_ORDER))

    last_ts = _agent_last_ts(agent_id)
    return {
        "id": agent_id,
        "name": meta["name"],
        "description": meta["description"],
        "status": status,
        "current_task": task,
        "progress": progress,
        "last_activity_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(last_ts))
        if last_ts else None,
        "attention": status == "waiting",
    }


def _attention_items(waiting: Optional[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    meta = {a["id"]: a for a in registry()}
    if waiting:
        items.append({"agent_id": waiting, "name": meta[waiting]["name"],
                      "reason": "Awaiting your decision (approval required)"})
    blocked: dict[str, float] = {}
    for e in events.bus.history():
        if e.get("kind") == "law_block" and e.get("agent") in meta:
            t = e["ts"]
            if e["agent"] not in blocked or t > blocked[e["agent"]]:
                blocked[e["agent"]] = t
    for agent_id in sorted(blocked, key=blocked.get):
        if agent_id != waiting:
            items.append({"agent_id": agent_id, "name": meta[agent_id]["name"],
                          "reason": "Law violation flagged — review required"})
    return items


def _recent_activity(limit: int = 10) -> list[dict[str, Any]]:
    meta = {a["id"]: a for a in registry()}
    out = []
    for e in reversed(events.bus.history()):
        agent_id = e.get("agent", "")
        if agent_id not in meta:
            continue
        text = e.get("text") or e.get("kind", "activity")
        out.append({"agent_id": agent_id,
                    "agent_name": meta[agent_id]["name"],
                    "message": text[:160],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(e["ts"]))})
        if len(out) >= limit:
            break
    return out


def _production_stages(running: bool) -> list[dict[str, Any]]:
    stages = []
    for st in PRODUCTION_STAGES:
        ids = st["agents"]
        any_invoked = any(_agent_events(i) for i in ids)
        all_completed = all(_has_result(i) for i in ids)
        any_working = any(_agent_events(i) and not _has_result(i)
                          for i in ids) and running
        if all_completed:
            status = "Complete"
        elif any_working:
            status = "Active"
        elif any_invoked:
            status = "In Progress"
        else:
            status = "Upcoming"
        stages.append({"name": st["name"], "status": status})
    return stages


def _heatmap() -> list[int]:
    """Real activity per hour of the day (24 cells). Empty history -> empty
    grid, never invented data."""
    hours = [0] * 24
    now = time.gmtime()
    day_start = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 0, 0, 0, 0, 0, -1))
    for e in events.bus.history():
        if e["ts"] >= day_start:
            hours[int(time.gmtime(e["ts"]).tm_hour)] += 1
    if not any(hours):
        return []
    peak = max(hours)
    return [min(4, max(0, round(4 * h / peak))) for h in hours]


def build_dashboard_snapshot(run_state: dict[str, Any],
                             pending_question: Optional[dict[str, Any]]) -> dict[str, Any]:
    """The /api/studio/dashboard contract — all values derived from real state."""
    running = bool(run_state.get("running", False))
    waiting = waiting_agent() if (running and pending_question) else None

    agents = [agent_snapshot(a["id"], running, waiting) for a in registry()]
    working = [a for a in agents if a["status"] == "working"]
    idle = [a for a in agents if a["status"] == "idle"]
    waiting_list = [a for a in agents if a["status"] == "waiting"]
    attention = _attention_items(waiting)

    try:
        completed_today = len(knowledge.list_runs())
    except Exception:
        completed_today = 0

    degraded = any(e.get("agent") == "orchestrator" and e.get("kind") == "error"
                   for e in events.bus.history())

    return {
        "system": {
            "status": "degraded" if degraded else "healthy",
            "total_agents": len(agents),
            "active_agents": len(working),
            "idle_agents": len(idle),
            "waiting_agents": len(waiting_list),
            "attention_agents": len(attention),
            "completed_today": completed_today,
        },
        "agents": agents,
        "recent_activity": _recent_activity(),
        "attention": attention,
        "production": {"stages": _production_stages(running)},
        "heatmap": _heatmap(),
    }


# --------------------------------------------------------------------------
# bus event -> studio SSE event mapping
# --------------------------------------------------------------------------

def map_studio_event(ev: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Translate a raw bus event into a studio dashboard event, or None if
    the event carries no dashboard signal."""
    kind = ev.get("kind", "")
    agent = ev.get("agent", "")
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ev.get("ts", 0.0)))
    text = (ev.get("text") or "")[:160]

    if agent == "CEO" and kind == "interrupt":
        return {"type": "agent_attention_required", "agent_id": agent,
                "reason": "approval_required", "timestamp": ts}
    if agent == "CEO" and kind == "note":
        return {"type": "activity_created", "agent_id": agent,
                "message": text, "timestamp": ts}
    if kind == "result":
        return {"type": "agent_completed", "agent_id": agent, "timestamp": ts}
    if kind == "error" or "stopped" in text.lower():
        return {"type": "agent_failed", "agent_id": agent, "timestamp": ts}
    if kind == "law_block":
        return {"type": "activity_created", "agent_id": agent,
                "message": text or "law block", "timestamp": ts}
    if "invoked" in text:
        return {"type": "agent_status_changed", "agent_id": agent,
                "status": "working", "timestamp": ts}
    if kind in ("note", "tool_call", "tool_result", "decision", "thinking", "route"):
        return {"type": "activity_created", "agent_id": agent,
                "message": text or kind, "timestamp": ts}
    return None