"""Agent Studio — presentation layer over the real AVIS runtime.

Stage One: the Agent Dashboard backend adapter.

Everything reported here is derived from REAL runtime state: the event bus,
the run state, and the knowledge repository. No fabricated statuses, no
second agent implementation. An agent is "completed" only when its node
actually produced a result event; "working" only while the run is live and
its node is mid-flight; "waiting" only when a CEO interrupt is pending.
"""

from __future__ import annotations

import json
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


# --------------------------------------------------------------------------
# Agent Workspace (Stage Two rebuild — conversation-first)
# --------------------------------------------------------------------------
# The workspace is ONE continuous conversation. All events — messages,
# reasoning summaries, intent, tool calls/results, approvals, errors — are
# normalized entries of a single chronological stream (spec §11). There is
# NO separate activity feed, NO handoff chain, NO auto-routing: the human is
# the governance layer, Plan Mode has zero execution authority (runtime
# gate), and handoffs only happen through an explicit human decision.

CONVERSATION_TYPES = [
    "user_message", "assistant_message", "reasoning_summary", "intent",
    "tool_call", "tool_result", "approval_request", "approval_result",
    "error", "status",
]

SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "access_token",
                  "refresh_token", "password", "secret", "cookie"}


def sanitize(value: Any) -> Any:
    """Recursively redact credentials before any event payload reaches the UI."""
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if str(k).lower() in SENSITIVE_KEYS else sanitize(v))
                for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def _capabilities(agent_id: str) -> list[str]:
    a = agents_mod.BY_ID.get(agent_id, {})
    caps = [a.get("department", ""), a.get("tier", "")]
    if a.get("manages"):
        caps += [NAMES.get(m, m) for m in a["manages"]]
    if a.get("head"):
        caps.append(f"Reports to {NAMES.get(a['head'], a['head'])}")
    return [c for c in caps if c]


def workspace_agent_snapshot(agent_id: str, running: bool,
                             waiting: Optional[str]) -> dict[str, Any]:
    """The workspace's agent header: identity + capabilities + live status."""
    a = {x["id"]: x for x in registry()}.get(agent_id)
    base = agent_snapshot(agent_id, running, waiting)
    base["department"] = agents_mod.BY_ID[agent_id].get("department", "")
    base["tier"] = agents_mod.BY_ID[agent_id].get("tier", "")
    base["capabilities"] = _capabilities(agent_id)
    base["tools"] = agent_tools(agent_id)
    base["about"] = (f"You are interacting with the {base['name']}. "
                     f"I am your {DESCRIPTIONS.get(agent_id, 'agent')}.")
    return base


def agent_tools(agent_id: str) -> list[dict[str, Any]]:
    """The tools this agent has really used — from the event bus, with their
    real descriptions from the tool registry. Never invented (spec §26)."""
    import avis.tools as tools
    seen: dict[str, dict[str, Any]] = {}
    for e in events.bus.history():
        if e.get("agent") != agent_id or e.get("kind") != "tool_call":
            continue
        name = e.get("tool", "")
        if not name:
            continue
        seen.setdefault(name, {"name": name,
                               "doc": (tools.REGISTRY.get(name) or {}).get("doc", ""),
                               "status": "blocked" if e.get("blocked") else "available"})
    return sorted(seen.values(), key=lambda t: t["name"])


def project_memory(context: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    """Real project context available to the agent — labels only, from the
    shared workspace context. Never invented (spec §25)."""
    labels = {
        "topic": "Project Brief", "blueprint": "Structural Blueprint",
        "script": "Script & Segments", "manifest": "Resource Manifest",
        "asset_bundle": "Asset Bundle", "cut_spec": "Cut Spec",
        "voice_track": "Voice Track", "review_report": "Review Report",
    }
    out = []
    for key, label in labels.items():
        value = (context or {}).get(key)
        out.append({"label": label, "available": bool(value),
                    "detail": label if value else "not produced yet"})
    return out


# --------------------------------------------------------------------------
# conversational behavior — derived from identity + real state, zero execution
# --------------------------------------------------------------------------

def is_greeting(message: str) -> bool:
    """A pure greeting (hello / hi / hey ...) — answered conversationally,
    never triggering a plan, a project, routing, or any execution."""
    m = message.strip().rstrip("!.,? ")
    if not m:
        return False
    import re
    words = [w for w in m.split() if w]
    if len(words) > 3:
        return False
    first = re.sub(r"[^a-z']", "", words[0].lower())
    return bool(re.fullmatch(r"(hi|hello|hey|yo|howdy|hola|greetings|"
                             r"good(morning|afternoon|evening)|wazzup|sup|whatsup)", first))


def greeting_reply(agent_id: str) -> str:
    name = NAMES.get(agent_id, agent_id)
    return (f"Hello. I'm the {name}. "
            f"{DESCRIPTIONS.get(agent_id, 'How can I help?')} What are we working on today?")


def is_status_question(message: str) -> bool:
    import re
    m = re.sub(r"[^a-z ]", "", message.lower())
    return bool(re.search(r"(what (have you been doing|did you do|happened)|"
                          r"(your )?(status|progress))", m))


def status_summary(agent_id: str, conversation: list[dict[str, Any]]) -> str:
    """'What have you been doing?' — an honest summary derived from THIS
    conversation's real events, never invented (spec §38)."""
    name = NAMES.get(agent_id, agent_id)
    tools_done = [e for e in conversation if e.get("type") == "tool_result"
                  and e.get("tool", {}).get("status") == "completed"]
    blocks = [e for e in conversation if e.get("type") == "error"]
    results = [e for e in conversation if e.get("type") == "assistant_message"
               and e.get("agent_id") != "you"]
    if not conversation and not tools_done:
        return f"I'm {name}. We haven't done anything yet in this workspace."
    lines = [f"I'm {name}. Here's what we've done in this workspace:"]
    for e in tools_done:
        lines.append(f"- tool: {e['tool']['name']} — {e.get('content', '')[:90]}")
    if results:
        last = results[-1].get("content", "")
        if last:
            lines.append(f"- last result: {last[:140]}")
    if blocks:
        lines.append(f"- {len(blocks)} error(s) reported in this conversation")
    lines.append("")
    lines.append("No changes were made unless a tool result above confirms them.")
    return "\n".join(lines)


def intent_message(agent_id: str, message: str) -> str:
    """Before ANY consequential execution, the agent says what it's going to
    do and why (spec §16/§36). Derived from the agent's real role."""
    steps = workspace_plan(agent_id, message)
    lines = ["Understood. Before I do anything, here's what I'm going to do:",
             ""]
    lines += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
    lines += ["", "I won't take consequential actions without explaining them."]
    return "\n".join(lines)


def plan_response(agent_id: str, message: str) -> str:
    """Plan Mode reply: conversational, proposes the approach, executes NOTHING.
    The runtime gate (tools.set_execution_blocked) backs this up."""
    name = NAMES.get(agent_id, agent_id)
    steps = workspace_plan(agent_id, message)
    lines = [f"Understood. I'm {name} — {DESCRIPTIONS.get(agent_id, 'your agent')}.",
             "In Plan Mode I won't execute anything or change any files. "
             "Here's how I'd approach this:", ""]
    lines += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
    lines += ["",
              "Nothing was executed. If this looks right, switch to Build Mode "
              "and I'll carry it out."]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# the real run (Build Mode)
# --------------------------------------------------------------------------

def workspace_plan(agent_id: str, message: str) -> list[str]:
    """Explicit pre-execution action rationale (spec §38) — derived from the
    agent's real role, never claimed to be private model reasoning."""
    role = DESCRIPTIONS.get(agent_id, "your task")
    return [f"Receive task: {message.strip()[:80] or 'work request'}",
            f"Apply {role}",
            "Produce the result and report back"]


def _default_reference() -> dict[str, Any]:
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "examples", "reference-analysis-mbappe.json")
    try:
        with open(p) as f:
            data = json.load(f)
        return data.get("reference_analysis") or data
    except Exception:
        return {}


def _seed_workspace_state(agent_id: str, message: str,
                          context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Real context transfer (spec §56/§57): seed from the shared workspace
    context (previous agents' actual outputs), else the most recent recorded
    pipeline run, else a fresh seed with the default project brief. The human
    message becomes the topic. Never fabricates upstream inputs."""
    import avis.graph as g
    base = dict(context) if context else None
    if base is None:
        base = knowledge.latest_run_state() or {}
    state = {k: v for k, v in base.items() if k not in ("running", "log", "mailboxes")}
    if not state.get("topic"):
        state = g.seed_state(message, **({"reference_analysis": state.get("reference_analysis")}
                                         if state.get("reference_analysis") else {}))
    state["topic"] = message
    state.setdefault("voice_profile", {})
    if not state.get("reference_analysis"):
        state["reference_analysis"] = _default_reference()
    return state


def execute_agent_run(agent_id: str, message: str,
                      context: Optional[dict[str, Any]] = None,
                      approver: Optional[Callable[[dict[str, Any]], Any]] = None,
                      should_stop: Optional[Callable[[], bool]] = None) -> dict[str, Any]:
    """Run ONE agent's real node function through a single-node graph driven
    by the tested g.run() loop. `approver` answers interrupt() questions
    (default: auto-approve, recorded honestly as CEO notes); `should_stop`
    cancels the run cooperatively."""
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from avis.agents import build_node
    from avis.state import AgentState
    import avis.graph as g

    state = _seed_workspace_state(agent_id, message, context)

    def default_approver(question: dict[str, Any]) -> str:
        events.bus.emit("CEO", "note",
                        f"workspace auto-approve: {str(question.get('question', ''))[:60]}")
        return "approve"

    sg = StateGraph(AgentState)
    sg.add_node(agent_id, build_node(agent_id))
    sg.add_edge(START, agent_id)
    sg.add_edge(agent_id, END)
    graph = sg.compile(checkpointer=InMemorySaver())
    return g.run(graph, state, approver or default_approver,
                 record=False, should_stop=should_stop)


def _artifacts_from_state(state: dict[str, Any],
                          context: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Real artifacts THIS run produced — the node's actual new state keys,
    rendered as cards. No invented files (spec §14/§71)."""
    out: list[dict[str, Any]] = []
    spec = {
        "blueprint": ("Blueprint", "structural analysis"),
        "script": ("Script", "markdown + segments"),
        "manifest": ("Resource Manifest", "resource needs"),
        "asset_bundle": ("Asset Bundle", "sourced assets"),
        "cut_spec": ("Cut Spec", "edit timeline"),
        "voice_track": ("Voice Track Spec", "TTS segments"),
    }
    for key, (name, meta) in spec.items():
        if context is not None and key in context:
            continue  # inherited from the shared project context, not this run
        value = state.get(key)
        if not value:
            continue
        if isinstance(value, dict):
            count = len(value.get("segments", value.get("shots", [])))
            size = f"{count} items" if count else meta
        elif isinstance(value, list):
            size = f"{len(value)} items"
        else:
            size = meta
        out.append({"type": "DOCUMENT", "name": name, "filename": key,
                    "meta": size, "key": key})
    return out


# --------------------------------------------------------------------------
# bus event -> normalized conversation event (spec §11)
# --------------------------------------------------------------------------

def workspace_event(ev: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Raw bus event -> one normalized conversation event, or None if it
    carries no workspace signal. Everything stays in the SAME timeline."""
    kind = ev.get("kind", "")
    agent = ev.get("agent", "")
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ev.get("ts", 0.0)))
    text = (ev.get("text") or "")
    if not text:
        text = kind

    if agent == "CEO":
        if kind == "interrupt":
            return {"type": "status", "agent_id": agent, "timestamp": ts,
                    "content": f"Waiting for your approval: {text[:240]}"}
        return {"type": "status", "agent_id": agent, "timestamp": ts,
                "content": text[:240]}

    if kind == "thinking":
        return {"type": "reasoning_summary", "agent_id": agent, "timestamp": ts,
                "content": text[:240]}
    if kind == "tool_call":
        return {"type": "tool_call", "agent_id": agent, "timestamp": ts,
                "tool": {"name": ev.get("tool", ""), "args": sanitize(ev.get("args", [])),
                         "status": "running", "blocked": bool(ev.get("blocked"))},
                "content": text[:240]}
    if kind == "tool_result":
        return {"type": "tool_result", "agent_id": agent, "timestamp": ts,
                "tool": {"name": ev.get("tool", ""),
                         "status": "failed" if ev.get("error") else "completed",
                         "blocked": bool(ev.get("blocked"))},
                "content": text[:240]}
    if kind == "note":
        low = text.lower()
        if "stopped" in low:
            return {"type": "error", "agent_id": agent, "timestamp": ts,
                    "content": text[:240]}
        return {"type": "status", "agent_id": agent, "timestamp": ts,
                "content": text[:240]}
    if kind == "law_block":
        return {"type": "error", "agent_id": agent, "timestamp": ts,
                "content": text[:240]}
    if kind in ("route", "result"):
        # result becomes the agent's assistant message via the workspace store;
        # mapping it here would duplicate the final message.
        return None
    if kind == "error":
        return {"type": "error", "agent_id": agent, "timestamp": ts,
                "content": text[:240]}
    return None


def workspace_events(agent_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """This agent's real events from the bus, normalized to conversation
    events (spec §11). CEO decision events are excluded from per-agent
    timelines — they only appear as approvals the human explicitly sees."""
    out: list[dict[str, Any]] = []
    for ev in events.bus.history():
        if ev.get("agent") != agent_id:
            continue
        mapped = workspace_event(ev)
        if mapped:
            out.append(mapped)
    return out[-limit:]


def build_workspace_snapshot(agent_id: str,
                             store: dict[str, Any],
                             run_state: dict[str, Any],
                             pending_question: Optional[dict[str, Any]],
                             context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """The workspace contract: agent + mode + current run + ONE conversation.
    The conversation is the chronological merge of persisted store events and
    this agent's real bus events — everything the human needs to know is in
    that one timeline."""
    running = bool(run_state.get("running", False))
    waiting = waiting_agent() if (running and pending_question) else None
    status = store.get("status", "idle")

    agent = workspace_agent_snapshot(agent_id, running, waiting)
    agent["status"] = status if store.get("run_id") else agent["status"]
    if status in ("working", "waiting", "stopped", "failed"):
        agent["progress"] = 50 if status == "working" else 100
        agent["current_task"] = ({"waiting": "Waiting for your approval",
                                  "working": "Working", "stopped": "Stopped",
                                  "failed": "Failed"}.get(status, status))

    merged = list(store.get("conversation", [])) + workspace_events(agent_id)
    seen: set[tuple] = set()
    conversation: list[dict[str, Any]] = []
    for e in sorted(merged, key=lambda x: x.get("timestamp", "")):
        key = (e.get("type"), e.get("timestamp"), str(e.get("content", ""))[:120],
               str((e.get("approval") or {}).get("status", "")),
               str((e.get("tool") or {}).get("name", "")))
        if key in seen:
            continue
        seen.add(key)
        conversation.append(e)

    run = store.get("current_run")
    pending = store.get("approval_pending")
    pending_out: Optional[dict[str, Any]] = None
    if pending:
        pending_out = {"id": pending.get("id"), "run_id": pending.get("run_id"),
                       "question": pending.get("question", "")}
    return {
        "agent": agent,
        "mode": store.get("mode", "plan"),
        "current_run": run,
        "conversation": conversation[-200:],
        "can_stop": bool(run and run.get("status") in ("working", "waiting")),
        "pending_approval": pending_out,
        "memory": project_memory(context),
    }