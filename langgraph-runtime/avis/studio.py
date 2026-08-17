"""Agent Studio — the session engine and multi-session workspace store
(AUTONOMOUS_AGENTS_PLAN §3, §6, §7, §8).

One engine runs every session — primary and subagent alike:

    studio.run_session(agent_id, session_id, task, state, mode, role,
                       should_stop, steps_cap=25)

The LLM is the agent: we give it identity, capabilities (incl. created ones,
dynamic), skills, the 12 laws, its tools, a state summary, and the task. It
decides HOW. The runtime governs only permissions (Plan = read + ask,
Build = fully autonomous), the laws, the steps cap, the stop signal, and
honesty. There is no workflow engine, no division-of-labor graph, no
predetermined handoff chain — work moves between primary agents only through
a human-approved handoff, and the human walks to the next workspace."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

import avis.agents as agents_mod
import avis.brain as brain_mod
import avis.events as events
import avis.knowledge as knowledge
import avis.laws as laws_mod
import avis.tools as tools

# --------------------------------------------------------------------------
# display metadata (single source of truth for the UI)
# --------------------------------------------------------------------------

NAMES: dict[str, str] = {
    "strategist": "Strategist", "analyzer": "Analyzer", "planner": "Planner",
    "researcher": "Researcher", "audio-lead": "Audio Lead", "tts": "TTS",
    "editor": "Editor", "graphics": "Graphics", "animation": "Animation",
    "animated-graphics": "Animated Graphics", "video-effects": "Video Effects",
    "clips": "Clips", "images": "Images", "reviewer": "Reviewer",
    "watcher-blocker": "Watcher / Blocker", "investigator": "Investigator",
    "recruiter": "Recruiter",
}

DESCRIPTIONS: dict[str, str] = {
    "strategist": "Strategy & direction", "analyzer": "Analysis & evaluation",
    "planner": "Planning & scripting", "researcher": "Sourcing & asset research",
    "audio-lead": "Audio direction & TTS planning", "tts": "Voiceover & audio rendering",
    "editor": "Cut & visual assembly", "graphics": "Static graphic overlays",
    "animation": "Motion design", "animated-graphics": "Animated graphic overlays",
    "video-effects": "Effect design & substitution", "clips": "Video clip sourcing",
    "images": "Image sourcing & overlays", "reviewer": "Quality review & fidelity scoring",
    "watcher-blocker": "Law watch & blocking", "investigator": "Law violation investigation",
    "recruiter": "Personnel & recruitment",
}

CONVERSATION_TYPES = [
    "user_message", "assistant_message", "reasoning_summary",
    "tool_call", "tool_result", "approval_request", "approval_result",
    "handoff_request", "handoff_result", "error", "status",
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


def registry() -> list[dict[str, Any]]:
    """Display registry: runtime id + studio display metadata."""
    out = []
    for a in agents_mod.AGENTS:
        out.append({"id": a["id"], "name": NAMES.get(a["id"], a["id"]),
                    "description": DESCRIPTIONS.get(a["id"], a["department"]),
                    "department": a["department"], "tier": a["tier"]})
    return out


# --------------------------------------------------------------------------
# multi-session workspace store (§7)
# --------------------------------------------------------------------------

WORKSPACES: dict[str, dict[str, Any]] = {}
_store_lock = threading.Lock()


def _iso(ts: Optional[float] = None) -> str:
    t = time.gmtime(ts) if ts is not None else time.gmtime()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


def _workspace(agent_id: str) -> dict[str, Any]:
    with _store_lock:
        ws = WORKSPACES.setdefault(agent_id, {"sessions": {}, "active_session_id": None})
        return ws


def _session_seed(task: str, run_id: Optional[str] = None) -> dict[str, Any]:
    """Fresh session state: no artifacts (Law 12 read failures are honest),
    default voice profile for tts_plan, and an empty evidence log."""
    return {"topic": task, "events": [], "decisions": [], "edits": [],
            "revocations": [], "substitutions": [], "sourcing_proposals": [],
            "visual_assignments": [], "voice_profile": {
                "default_engine": os.environ.get("AVIS_TTS_DEFAULT_ENGINE", "local"),
                "authorized_engines": ["local"],
                "loudness_target_lufs": -16},
            "run_id": run_id}


def new_session(agent_id: str, task: str, mode: str = "plan",
                title: Optional[str] = None,
                run_id: Optional[str] = None,
                sender: Optional[str] = None) -> dict[str, Any]:
    """Create a NEW independent session in the agent's workspace. The old
    session is never replaced or touched — it stays in the workspace history."""
    ws = _workspace(agent_id)
    now = time.time()
    sid = f"{agent_id}-{int(now * 1000)}"
    if title is None:
        title = (task.strip()[:60] or "new session")
        if sender:
            title = f"handoff: {sender} -> {agent_id}"
    session: dict[str, Any] = {
        "id": sid, "title": title, "created_at": _iso(now),
        "last_activity_at": _iso(now), "mode": mode, "status": "idle",
        "task": task, "run_id": run_id,
        "conversation": [], "state": _session_seed(task, run_id),
        "handoff": None, "approval": None,
        "_approval_event": None, "stop_requested": False,
    }
    with _store_lock:
        ws["sessions"][sid] = session
        ws["active_session_id"] = sid
    return session


def list_sessions(agent_id: str) -> list[dict[str, Any]]:
    ws = _workspace(agent_id)
    with _store_lock:
        out = []
        for s in ws["sessions"].values():
            out.append({"id": s["id"], "title": s["title"], "status": s["status"],
                        "mode": s["mode"], "last_activity_at": s["last_activity_at"],
                        "handoff_pending": bool(s.get("handoff")),
                        "run_id": s.get("run_id")})
        out.sort(key=lambda s: s["last_activity_at"], reverse=True)
        return out


def get_session(agent_id: str, session_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    ws = _workspace(agent_id)
    with _store_lock:
        sid = session_id or ws.get("active_session_id")
        return ws["sessions"].get(sid) if sid else None


def activate_session(agent_id: str, session_id: str) -> bool:
    ws = _workspace(agent_id)
    with _store_lock:
        if session_id not in ws["sessions"]:
            return False
        ws["active_session_id"] = session_id
        return True


def delete_session(agent_id: str, session_id: str) -> Optional[str]:
    """Delete a session and its timeline. The ACTIVE session cannot be deleted
    while it is active; a running/waiting session cannot be deleted."""
    ws = _workspace(agent_id)
    with _store_lock:
        session = ws["sessions"].get(session_id)
        if session is None:
            return "no such session"
        if session["status"] in ("working", "waiting", "stopping"):
            return "session is active — stop it first"
        if ws.get("active_session_id") == session_id:
            return "the active session cannot be deleted"
        del ws["sessions"][session_id]
        return None


def touch(session: dict[str, Any]) -> None:
    session["last_activity_at"] = _iso()


# --------------------------------------------------------------------------
# the session engine (§3)
# --------------------------------------------------------------------------

class _Engine:
    """One session's runtime: prompt building, the tool loop, permission
    enforcement, law checks, evidence scans, approvals, handoffs, subagents.
    One human message = one session turn (the same-path principle)."""

    def __init__(self, agent_id: str, session: Optional[dict[str, Any]],
                 task: str, state: dict[str, Any], mode: str, role: str = "primary",
                 should_stop: Optional[Callable[[], bool]] = None,
                 steps_cap: int = 25, parent_depth: int = 0) -> None:
        self.agent_id = agent_id
        self.session = session
        self.task = task
        self.state = state
        self.mode = mode
        self.role = role
        self.should_stop = should_stop
        self.steps_cap = steps_cap
        self.parent_depth = parent_depth

    # --- events ----------------------------------------------------------
    def emit(self, type_: str, **data: Any) -> None:
        ev = {"type": type_, "timestamp": _iso(), "agent_id": self.agent_id, **data}
        if self.session is not None:
            self.session["conversation"].append(ev)
        kind = {"user_message": "user_message", "assistant_message": "note",
                "reasoning_summary": "thinking", "tool_call": "tool_call",
                "tool_result": "tool_result", "approval_request": "approval_request",
                "approval_result": "approval_result", "handoff_request": "handoff_request",
                "handoff_result": "handoff_result", "error": "error",
                "status": "status"}.get(type_, "note")
        events.bus.emit(self.agent_id, kind, str(data.get("content", "")), **{
            k: sanitize(v) for k, v in data.items() if k not in ("content",)})

    # --- the loop ----------------------------------------------------------
    def run(self) -> dict[str, Any]:
        prev = tools.current_engine()
        tools.set_engine(self)
        try:
            return self._run()
        finally:
            tools.set_engine(prev)

    def _run(self) -> dict[str, Any]:
        system = self._build_system_prompt()
        user = self._build_user_prompt()
        defs = tools.definitions(self.agent_id, self.role)
        steps = 0

        while True:
            if self.should_stop and self.should_stop():
                self.emit("status", content="stopped")
                return {"status": "stopped"}
            if steps >= self.steps_cap:
                self.emit("status",
                          content=f"stopped at the step cap ({self.steps_cap})")
                return {"status": "stopped_cap"}
            steps += 1

            try:
                text, calls = brain_mod.get_brain().converse_with_tools(
                    system, user, defs)
            except brain_mod.ModelUnreachable:
                self.emit("error", content="I couldn't reach the model right "
                          "now. Please try again in a moment.")
                return {"status": "failed"}

            if text:
                self.emit("reasoning_summary" if calls else "assistant_message",
                          content=text)
            if not calls:
                return {"status": "completed", "final_text": text}

            for tc in calls:
                name = str(tc.get("name", ""))
                args = tc.get("arguments") or {}
                self.state.setdefault("events", []).append(
                    {"agent": self.agent_id, "kind": "tool_call", "tool": name,
                     "args": args, "ts": time.time()})
                self.emit("tool_call", content=f"{name} called",
                          tool={"name": name, "args": sanitize(args),
                                "status": "running"})

                result = tools.call(
                    self.state, self.agent_id, name, args, self.mode,
                    ask=self._ask if self.mode == "plan" else None,
                    on_block=lambda b: self.emit(
                        "error",
                        content=f"[Law {b['law']}] {b['law_name']} — {b.get('reason', '')}"))

                ok = "error" not in result
                self.emit("tool_result",
                          content=str(result.get("note") or result.get("error") or "ok")[:240],
                          tool={"name": name,
                                "status": "completed" if ok else "failed",
                                "blocked": not ok})
                self.state.setdefault("events", []).append(
                    {"agent": self.agent_id, "kind": "tool_result", "tool": name,
                     "error": not ok, "text": str(result.get("note") or result.get("error") or ""),
                     "ts": time.time()})

                if result.get("_handoff"):
                    return {"status": "handed_off", "handoff": result["handoff"]}
                if self.should_stop and self.should_stop():
                    self.emit("status", content="stopped")
                    return {"status": "stopped"}

            if self.should_stop and self.should_stop():
                self.emit("status", content="stopped")
                return {"status": "stopped"}

    # --- Plan-Mode ask gate -----------------------------------------------
    def _ask(self, name: str, args: dict[str, Any]) -> bool:
        """A mutating tool call in Plan Mode pauses here with an
        approval_request; the human answers via the API. Rejected or stopped
        → False: the tool is blocked, nothing is applied."""
        session = self.session
        if session is None:
            return False
        pending = {"id": f"approval-{uuid.uuid4().hex[:8]}",
                   "question": f"Approve calling {name} with {json.dumps(args, default=str)[:200]}?",
                   "event": threading.Event(), "answer": None}
        session["approval"] = pending
        session["status"] = "waiting"
        self.emit("approval_request", content=pending["question"],
                  approval={"title": "Approval required",
                            "description": pending["question"],
                            "action": "approve", "status": "required"})
        while not pending["event"].wait(0.2):
            if (self.should_stop and self.should_stop()) or session.get("stop_requested"):
                pending["answer"] = "rejected"
                break
        answer = pending["answer"] or "rejected"
        status = "approved" if answer == "approve" else "rejected"
        session["approval"] = None
        self.emit("approval_result", content=status,
                  approval={"title": name, "status": status})
        if session.get("stop_requested"):
            session["stop_requested"] = False
        return answer == "approve"

    # --- prompt building ----------------------------------------------------
    def _build_system_prompt(self) -> str:
        a = agents_mod.BY_ID.get(self.agent_id, {})
        if self.role in ("explore", "scout", "general"):
            name = {"explore": "Explore", "scout": "Scout",
                    "general": "General"}[self.role]
            role_line = (f"You are {name}, a transient {self.role} subagent "
                         f"working for {NAMES.get(self.agent_id, self.agent_id)}. "
                         "You exist for one task, return your findings, and vanish.")
            caps = ""
        else:
            name = NAMES.get(self.agent_id, self.agent_id)
            role = DESCRIPTIONS.get(self.agent_id, "an agent")
            identity = a.get("identity", f"I'm the {name} — {role}.")
            role_line = f"You are {name} — {role}. {identity}"
            caps = (f"Your capabilities: "
                    + ", ".join(c["name"] for c in self._capabilities()) + ".")

        mode_line = {
            "plan": ("You are in PLAN MODE. You may read and analyze freely, but "
                     "every action that changes anything is paused for the human's "
                     "approval. Propose, investigate, and prepare — then the human "
                     "decides."),
            "build": ("You are in BUILD MODE. You may carry out work with your "
                      "tools autonomously. The human can stop you at any time; "
                      "you can also stop and ask."),
        }.get(self.mode, "You are in PLAN MODE.")

        created = tools.capability_context(self.agent_id) if self.role == "primary" else ""
        return "\n".join([
            role_line,
            "",
            mode_line,
            "",
            caps if caps else "",
            "Your skills: " + (", ".join(a.get("skills") or []) or "none yet") + ".",
            created,
            "",
            "The 12 laws of this system are runtime-enforced guards, not "
            "suggestions. Violating them blocks the action and is recorded:",
            laws_text(),
            "",
            "How to work: you decide how. Produce artifacts with "
            "write_artifact (YOU generate the payload content yourself — it is "
            "the work you just did, never left empty). When your current work is "
            "finished and the next step belongs to another primary agent, call "
            "handoff — the runtime packages your work and the human decides. "
            "Create capabilities with create_capability only when the human has "
            "explicitly approved doing so in this conversation. Never spawn a "
            "primary agent as a subagent. If you lack an ability, say so "
            "honestly and offer to create it.",
            "",
            "Before a consequential action, say in your own words what you are "
            "about to do and why. Be conversational, natural, honest, and never "
            "invent facts (Law 1).",
        ])

    def _build_user_prompt(self) -> str:
        mem_lines = "\n".join(
            f"- {label}: {'available' if value else 'not produced yet'}"
            for label, value in _memory_labels(self.state))
        history = "\n".join(self._history_lines())
        extra = ""
        if self.role == "primary" and self.session and self.session.get("run_id"):
            extra = (f"\n\nYou have received a handoff package in the folder "
                     f"data/runs/{self.session['run_id']}/ — examine it with "
                     "list_run / read_run_file and decide.")
        return "\n".join([
            f"task: {self.task}",
            "",
            "current project state:",
            mem_lines,
            extra,
            "",
            "conversation so far:",
            history or "(this is the start of the session)",
        ])

    def _history_lines(self) -> list[str]:
        out = []
        for e in (self.session or {}).get("conversation", [])[-16:]:
            t = e.get("type")
            if t == "user_message":
                out.append(f"human: {e.get('content', '')}")
            elif t == "assistant_message":
                out.append(f"you: {e.get('content', '')}")
            elif t == "reasoning_summary":
                out.append(f"(you are working: {e.get('content', '')[:120]})")
            elif t == "tool_result":
                out.append(f"tool {e.get('tool', {}).get('name', '')} -> "
                           f"{e.get('content', '')[:120]}")
            elif t in ("approval_result",):
                out.append(f"approval: {e.get('content', '')}")
        return out

    def _capabilities(self) -> list[dict[str, Any]]:
        a = agents_mod.BY_ID.get(self.agent_id, {})
        out = [{"name": c, "created": False} for c in (a.get("capabilities") or [])]
        out += [{"name": c.get("name", "Unnamed capability"), "created": True}
                for c in tools.load_capabilities(self.agent_id)]
        return out


def laws_text() -> str:
    return "\n".join(f"  L{law['id']:>2} — {law['name']}: {law['rule']}"
                     for law in laws_mod.LAWS)


def _memory_labels(state: dict[str, Any]) -> list[tuple[str, bool]]:
    labels = [("blueprint", "Structural Blueprint"), ("script", "Script & Segments"),
              ("manifest", "Resource Manifest"), ("asset_bundle", "Asset Bundle"),
              ("cut_spec", "Cut Spec"), ("voice_track", "Voice Track"),
              ("review_report", "Review Report")]
    return [(label, bool(state.get(key))) for key, label in labels]


def run_session(agent_id: str, session_id: str, task: str, state: dict[str, Any],
                mode: str, role: str = "primary",
                should_stop: Optional[Callable[[], bool]] = None,
                steps_cap: int = 25, parent_depth: int = 0,
                session: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """One engine for everything (§3): one human message = one session turn.
    Termination is always one of: the model stops, the steps cap, the stop
    signal, a handoff, or a real error."""
    engine = _Engine(agent_id, session, task, state, mode, role=role,
                     should_stop=should_stop, steps_cap=steps_cap,
                     parent_depth=parent_depth)
    outcome = engine.run()

    if session is not None:
        touch(session)
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

    if role == "primary" and mode == "build" and session is not None:
        produced = [k for k in tools.ARTIFACT_KEYS if state.get(k)]
        if produced:
            knowledge.record_run(state,
                                 run_id=f"session-{session_id.replace(':', '-')}")
    return outcome


# --------------------------------------------------------------------------
# engine-bound tools — registered at import (the runtime writes files; the
# model proposes, the human approves; never the reverse)
# --------------------------------------------------------------------------

def _engine_subagent(state: dict[str, Any], agent_id: str,
                     args: list[Any]) -> dict[str, Any]:
    eng = tools.current_engine()
    cls = str(args[0]) if args else ""
    task = str(args[1]) if len(args) > 1 else ""
    toolset = args[2] if len(args) > 2 and isinstance(args[2], list) else None
    if cls not in tools.SUBAGENT_CLASSES:
        return {"error": f"subagent class must be one of "
                         f"{sorted(tools.SUBAGENT_CLASSES)}"}
    if cls in agents_mod.BY_ID:
        return {"error": f"'{cls}' is a primary agent — never a subagent"}
    if eng.parent_depth >= 3:
        return {"error": "subagent depth cap reached (3)"}
    child = _Engine(cls, None, task, state, eng.mode, role=cls,
                    should_stop=eng.should_stop, steps_cap=eng.steps_cap,
                    parent_depth=eng.parent_depth + 1)
    outcome = child.run()
    if outcome.get("status") != "completed":
        return {"error": f"subagent {cls} failed: {outcome.get('status')}"}
    text = outcome.get("final_text") or "done"
    return {"subagent_result": text,
            "note": f"subagent {cls} finished — {text[:120]}"}


def _engine_handoff(state: dict[str, Any], agent_id: str,
                    args: list[Any]) -> dict[str, Any]:
    target = str(args[0]) if args else ""
    prompt = str(args[1]) if len(args) > 1 else ""
    if target not in agents_mod.BY_ID:
        return {"error": f"unknown target agent '{target}'"}
    if not prompt.strip():
        return {"error": "handoff prompt must not be empty"}
    run_id = f"{agent_id}-{target}-{int(time.time() * 1000)}"
    folder = tools.HANDOFF_DIR / run_id
    folder.mkdir(parents=True, exist_ok=True)

    wrote: list[str] = []
    for key in tools.ARTIFACT_KEYS:
        if state.get(key) is not None:
            (folder / f"{key}.json").write_text(
                json.dumps(state[key], indent=2, ensure_ascii=False, default=str))
            wrote.append(f"{key}.json")
    decisions = "\n".join(f"- {d.get('agent', '?')}: {d.get('text', '')}"
                          for d in state.get("decisions", []))
    (folder / "decisions.md").write_text(
        f"# Decisions\n\n{decisions or '(none recorded)'}\n")
    (folder / "context.json").write_text(json.dumps({
        "run_id": run_id, "sender": agent_id, "target": target,
        "topic": state.get("topic"), "mode": eng.mode,
        "exists": {k: state.get(k) is not None for k in tools.ARTIFACT_KEYS},
        "missing": [k for k in tools.ARTIFACT_KEYS if state.get(k) is None],
    }, indent=2))
    (folder / "HANDOFF.md").write_text(
        f"# Handoff — {NAMES.get(agent_id, agent_id)} to "
        f"{NAMES.get(target, target)}\n\n{prompt}\n")
    return {"_handoff": True,
            "handoff": {"run_id": run_id, "target": target, "prompt": prompt,
                        "folder": str(folder), "files": wrote}}


def _engine_create_capability(state: dict[str, Any], agent_id: str,
                              args: list[Any]) -> dict[str, Any]:
    eng = tools.current_engine()
    (name, description, knowledge_txt, skills, tools_list,
     resources, guidance) = args[:7]
    name = str(name or "").strip()
    if not name:
        return {"error": "capability needs a name"}
    if eng.mode != "build":
        return {"error": "capability creation requires BUILD MODE — the runtime "
                         "only persists in Build Mode with explicit human approval"}
    if not _human_approved(eng.session, name):
        return {"error": "not persisted — the human must explicitly approve "
                         "creating this capability in the conversation first"}
    record = tools.save_capability(agent_id, {
        "name": name, "description": str(description or ""),
        "knowledge": str(knowledge_txt or ""),
        "skills": [str(s) for s in (skills or [])],
        "tools": [str(t) for t in (tools_list or [])],
        "resources": str(resources or ""), "guidance": str(guidance or "")})
    return {"capability": record,
            "note": f"capability '{record['name']}' created — it is now part of "
                    "my identity in future sessions"}


def _human_approved(session: Optional[dict[str, Any]], name: str) -> bool:
    """Deterministic check: the most recent user messages explicitly approve
    creating THIS capability. The model judges the words; the runtime persists."""
    if session is None:
        return False
    seen = 0
    name_low = name.lower()
    for ev in reversed(session.get("conversation", [])):
        if ev.get("type") != "user_message":
            continue
        seen += 1
        text = (ev.get("content") or "").lower()
        approved = any(w in text for w in ("approve", "yes", "create it",
                                           "go ahead", "go ahead and", "okay", "ok "))
        if approved and (name_low in text or "capability" in text):
            return True
        if seen >= 4:
            break
    return False


def _register_engine_tools() -> None:
    specs = {
        "subagent": (tools._SCHEMAS["subagent"], _engine_subagent,
                     "Spawn a TRANSIENT subagent (explore/scout/general) and return "
                     "its final message. Never a primary agent."),
        "handoff": (tools._SCHEMAS["handoff"], _engine_handoff,
                    "Finish your current work and hand off to another primary "
                    "agent. The runtime packages your artifacts and prompt; the "
                    "human decides."),
        "create_capability": (tools._SCHEMAS["create_capability"], _engine_create_capability,
                              "Create a new capability for yourself (real knowledge, "
                              "skills, tools). Persisted only with explicit human approval."),
    }
    for name, (schema, fn, doc) in specs.items():
        tools.REGISTRY[name] = {"fn": fn, "doc": doc, "schema": schema,
                                "permission": "mutate"}


_register_engine_tools()

# --------------------------------------------------------------------------
# handoff resolution — the human decides (§6)
# --------------------------------------------------------------------------

def resolve_handoff(agent_id: str, session_id: str, decision: str,
                    target_agent_id: Optional[str] = None,
                    note: Optional[str] = None) -> dict[str, Any]:
    """The three human outcomes for a pending handoff. Accept: seed a NEW
    session in the target workspace (existing sessions untouched) with the
    package. Reject: nothing moves; the sender's session keeps its history.
    Redirect: append the human's note to HANDOFF.md, then seed (possibly to a
    different target)."""
    sender = get_session(agent_id, session_id)
    if sender is None:
        return {"ok": False, "error": "no such session"}
    ho = sender.get("handoff")
    if not ho:
        return {"ok": False, "error": "no pending handoff on that session"}
    decision = str(decision or "").lower()
    if decision not in ("accept", "reject", "redirect"):
        return {"ok": False, "error": "decision must be accept|reject|redirect"}

    if decision == "reject":
        sender["conversation"].append({"type": "handoff_result",
                                       "agent_id": agent_id, "timestamp": _iso(),
                                       "content": "rejected",
                                       "handoff": {"status": "rejected",
                                                   "target": ho["target"],
                                                   "run_id": ho["run_id"]}})
        sender["handoff"] = None
        sender["status"] = "idle"
        touch(sender)
        return {"ok": True, "decision": "reject", "target": ho["target"],
                "run_id": ho["run_id"]}

    target = target_agent_id or ho["target"]
    if target not in agents_mod.BY_ID:
        return {"ok": False, "error": f"invalid target agent: {target}"}

    if decision == "redirect" and note and note.strip():
        folder = tools.HANDOFF_DIR / ho["run_id"]
        handoff_md = folder / "HANDOFF.md"
        if handoff_md.is_file():
            with open(handoff_md, "a") as f:
                f.write(f"\n\n## Human note (redirect)\n{note.strip()}\n")

    task = (f"You received a handoff from {NAMES.get(agent_id, agent_id)} "
            f"({ho['run_id']}). Examine the folder and decide: what do you "
            "need, and what is your plan?")
    seeded = new_session(target, task, mode="plan",
                         sender=NAMES.get(agent_id, agent_id),
                         run_id=ho["run_id"])

    sender["conversation"].append({"type": "handoff_result",
                                   "agent_id": agent_id, "timestamp": _iso(),
                                   "content": "accepted",
                                   "handoff": {"status": "accepted",
                                               "target": target,
                                               "run_id": ho["run_id"],
                                               "session_id": seeded["id"]}})
    sender["handoff"] = None
    sender["status"] = "idle"
    touch(sender)
    return {"ok": True, "decision": "accept" if decision == "accept" else "redirect",
            "target": target, "run_id": ho["run_id"],
            "session_id": seeded["id"], "title": seeded["title"]}


# --------------------------------------------------------------------------
# snapshots
# --------------------------------------------------------------------------

def _agent_header(agent_id: str) -> dict[str, Any]:
    a = agents_mod.BY_ID.get(agent_id, {})
    return {
        "id": agent_id,
        "name": NAMES.get(agent_id, agent_id),
        "description": DESCRIPTIONS.get(agent_id, a.get("department", "")),
        "department": a.get("department", ""),
        "tier": a.get("tier", ""),
        "identity": a.get("identity", f"I'm the {NAMES.get(agent_id, agent_id)}."),
        "capabilities": _capabilities(agent_id),
        "skills": a.get("skills", []),
        "tools": _agent_tools(agent_id),
        "manages": a.get("manages", []),
        "head": a.get("head"),
    }


def _capabilities(agent_id: str) -> list[dict[str, Any]]:
    a = agents_mod.BY_ID.get(agent_id, {})
    out = [{"name": c, "created": False} for c in (a.get("capabilities") or [])]
    out += [{"name": c.get("name", "Unnamed capability"), "created": True}
            for c in tools.load_capabilities(agent_id)]
    return out


def _agent_tools(agent_id: str) -> list[dict[str, Any]]:
    out = []
    for name in tools.tool_names(agent_id, "primary"):
        entry = tools.REGISTRY.get(name)
        if entry:
            out.append({"name": name, "doc": entry["doc"],
                        "permission": entry["permission"]})
    return sorted(out, key=lambda t: t["name"])


def build_workspace_snapshot(agent_id: str,
                             session_id: Optional[str] = None) -> dict[str, Any]:
    """The workspace contract: agent + session list + the active session's
    conversation (one timeline)."""
    session = get_session(agent_id, session_id)
    sessions = list_sessions(agent_id)

    active = None
    if session is not None:
        active = {
            "id": session["id"], "title": session["title"],
            "status": session["status"], "mode": session["mode"],
            "task": session["task"], "run_id": session.get("run_id"),
            "conversation": session["conversation"][-200:],
            "pending_approval": None if not session.get("approval") else {
                "id": session["approval"]["id"],
                "question": session["approval"]["question"]},
            "pending_handoff": None if not session.get("handoff") else {
                "run_id": session["handoff"]["run_id"],
                "target": session["handoff"]["target"],
                "prompt": session["handoff"]["prompt"][:300],
                "decision": session["handoff"]["decision"]},
            "can_stop": session["status"] in ("working", "waiting"),
            "memory": [{"label": label, "available": bool(session["state"].get(key))}
                       for key, label in _memory_labels(session["state"])],
        }
    return {"agent": _agent_header(agent_id),
            "sessions": sessions,
            "active_session_id": session["id"] if session else None,
            "active_session": active,
            "model_configured": brain_mod.model_configured()}


def _session_status(agent_id: str) -> str:
    ws = _workspace(agent_id)
    with _store_lock:
        sid = ws.get("active_session_id")
        s = ws["sessions"].get(sid) if sid else None
        return s["status"] if s else "idle"


def build_dashboard_snapshot() -> dict[str, Any]:
    """Org overview (§8): every agent's workspace, sessions, and live
    activity. There is no Run flow and no graph — only the human drives work."""
    agents = []
    for a in agents_mod.AGENTS:
        agent_id = a["id"]
        sessions = list_sessions(agent_id)
        active = get_session(agent_id)
        handoffs = [s for s in sessions if s["handoff_pending"]]
        last_ts = max((s["last_activity_at"] for s in sessions), default=None)
        agents.append({
            "id": agent_id, "name": NAMES.get(agent_id, agent_id),
            "description": DESCRIPTIONS.get(agent_id, a.get("department", "")),
            "department": a["department"], "tier": a["tier"],
            "status": active["status"] if active else "idle",
            "session_count": len(sessions),
            "handoff_pending": len(handoffs),
            "last_activity_at": last_ts,
            "active_session_id": active["id"] if active else None,
        })
    return {
        "system": {
            "total_agents": len(agents),
            "total_sessions": sum(a["session_count"] for a in agents),
            "attention_agents": sum(1 for a in agents
                                    if a["handoff_pending"] or a["status"] == "waiting"),
            "model_configured": brain_mod.model_configured(),
        },
        "agents": agents,
        "recent_activity": _recent_activity(),
    }


def _recent_activity(limit: int = 12) -> list[dict[str, Any]]:
    out = []
    meta = {a["id"]: a for a in registry()}
    for e in reversed(events.bus.history()):
        agent_id = e.get("agent", "")
        if agent_id not in meta and not str(agent_id).startswith(("explore", "scout", "general")):
            continue
        name = (NAMES.get(agent_id, agent_id) if agent_id in meta
                else f"subagent:{agent_id}")
        kind = e.get("kind", "note")
        text = e.get("text") or kind
        if kind in ("tool_call", "tool_result"):
            text = f"{kind}: {text[:120]}"
        out.append({"agent_id": agent_id, "agent_name": name, "message": text[:160],
                    "timestamp": _iso(e.get("ts", 0.0))})
        if len(out) >= limit:
            break
    return out


def no_model_notice() -> str:
    return ("The conversational layer is not configured. Add an API key "
            "(GLM_API_KEY or OPENAI_API_KEY) to talk to me.")


def model_failed_line() -> str:
    return ("I couldn't reach the model right now. Please try again in a "
            "moment.")


def map_studio_event(ev: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Map a raw bus event to a studio dashboard event (SSE)."""
    kind = ev.get("kind", "")
    agent = ev.get("agent", "")
    ts = _iso(ev.get("ts", 0.0))
    text = (ev.get("text") or "")[:160]

    if kind == "approval_request":
        return {"type": "agent_attention_required", "agent_id": agent,
                "reason": "approval_required", "timestamp": ts}
    if kind == "note":
        return {"type": "activity_created", "agent_id": agent,
                "message": text, "timestamp": ts}
    if kind == "result":
        return {"type": "agent_completed", "agent_id": agent, "timestamp": ts}
    if kind == "error" or "stopped" in text.lower():
        return {"type": "agent_failed", "agent_id": agent, "timestamp": ts}
    if kind == "law_block":
        return {"type": "activity_created", "agent_id": agent,
                "message": text or "law block", "timestamp": ts}
    if kind in ("tool_call", "tool_result", "handoff_request", "handoff_result",
                "approval_result"):
        return {"type": "activity_created", "agent_id": agent,
                "message": text or kind, "timestamp": ts}
    return None


# keep the strict conversation whitelist visible for source sweeps
_CONVERSATION_WHITELIST = set(CONVERSATION_TYPES)