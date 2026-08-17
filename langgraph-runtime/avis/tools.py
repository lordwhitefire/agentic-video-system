"""Tool registry — the agent's hands (AUTONOMOUS_AGENTS_PLAN §5).

Every tool call flows through `call()`, which is the runtime's enforcement
point, in order:
  1. permission check  — Plan Mode asks the human before any mutating tool
  2. law check         — `guard()` runs before every mutating execution
  3. execution         — the registered function runs against shared state
  4. application       — the result is applied to the session state
  5. evidence scan     — the deterministic watcher scan runs after mutation

Deterministic, executable, observable: every call emits tool_call / tool_result
events, nothing is hidden, and nothing is faked. There is no scripted voice
anywhere — this layer only executes what the model asks for."""

from __future__ import annotations

import json
import os
import re
import threading
from pathlib import Path
from typing import Any, Callable, Optional

import avis.agents as agents_mod
import avis.events as events
import avis.knowledge as knowledge
import avis.laws as laws

ToolFn = Callable[[dict[str, Any], str, list[Any]], dict[str, Any]]

# --------------------------------------------------------------------------
# capability store — capabilities are REAL abilities; the JSON file only
# registers them. Creation supplies the real parts (knowledge, skills,
# tools, resources, guidance); nothing is claimed without them.
# --------------------------------------------------------------------------

CAPABILITIES_DIR = Path(__file__).resolve().parent.parent / "data" / "capabilities"

# handoff packages land here: data/runs/<run_id>/ (gitignored)
HANDOFF_DIR = Path(__file__).resolve().parent.parent / "data" / "runs"

ARTIFACT_KEYS = ["blueprint", "script", "manifest", "asset_bundle", "cut_spec",
                 "voice_track", "review_report"]

SUBAGENT_CLASSES = {"explore", "scout", "general"}


def _cap_file(agent_id: str) -> Path:
    return CAPABILITIES_DIR / f"{agent_id}.json"


def load_capabilities(agent_id: str) -> list[dict[str, Any]]:
    """Created capabilities for one agent, from disk. Empty list = none."""
    try:
        data = json.loads(_cap_file(agent_id).read_text())
    except (OSError, ValueError):
        return []
    if not isinstance(data, list):
        return []
    return [c for c in data if isinstance(c, dict)]


def save_capability(agent_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """Persist a REAL capability registration with its real parts. Only the
    runtime writes files; the model proposes, the human approves, the runtime
    records. Returns the saved record."""
    _cap_file(agent_id).parent.mkdir(parents=True, exist_ok=True)
    name = str(record.get("name", "")).strip() or "Unnamed capability"
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "capability"
    record = {
        "id": slug,
        "name": name,
        "description": str(record.get("description", "")).strip(),
        "knowledge": str(record.get("knowledge", "")).strip(),
        "skills": [str(s).strip() for s in (record.get("skills") or []) if str(s).strip()],
        "tools": [str(t).strip() for t in (record.get("tools") or []) if str(t).strip()],
        "resources": str(record.get("resources", "")).strip(),
        "guidance": str(record.get("guidance", "")).strip(),
        "created_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  __import__("time").gmtime()),
    }
    records = load_capabilities(agent_id)
    records.append(record)
    _cap_file(agent_id).write_text(json.dumps(records, indent=2))
    return record


def capability_context(agent_id: str) -> str:
    """Created capabilities as prompt context — the real parts (knowledge,
    guidance, tools) that make the ability actually usable."""
    blocks = []
    for c in load_capabilities(agent_id):
        parts = [f"- {c.get('name')}: {c.get('description', '')}".strip()]
        if c.get("knowledge"):
            parts.append(f"  Knowledge: {c['knowledge']}")
        if c.get("guidance"):
            parts.append(f"  Guidance: {c['guidance']}")
        if c.get("skills"):
            parts.append(f"  Skills: {', '.join(c['skills'])}")
        if c.get("tools"):
            parts.append(f"  Tools: {', '.join(c['tools'])}")
        if c.get("resources"):
            parts.append(f"  Resources: {c['resources']}")
        blocks.append("\n".join(parts))
    return "\n".join(blocks)


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

REGISTRY: dict[str, dict[str, Any]] = {}


def _register(tools: dict[str, dict[str, Any]], name: str, doc: str,
              schema: dict[str, Any], permission: str):
    def wrap(fn: Callable[[dict[str, Any], list[Any]], dict[str, Any]]):
        # adapter: old-style (state, args-list) functions -> uniform signature
        def adapted(state: dict[str, Any], agent_id: str, args: list[Any]) -> dict[str, Any]:
            return fn(state, args)
        tools[name] = {"fn": adapted, "doc": doc, "schema": schema,
                       "permission": permission}
        return adapted
    return wrap


# every primary agent carries these by default
CORE_TOOLS = ["read_artifact", "write_artifact", "read_state", "write_decision",
              "write_edit", "retrieve_memory", "retrieve_knowledge", "subagent",
              "handoff", "create_capability", "webfetch", "websearch",
              "list_run", "read_run_file"]

# subagent class toolsets (AUTONOMOUS_AGENTS_PLAN §2)
EXPLORE_TOOLS = ["read_artifact", "read_state", "retrieve_memory",
                 "retrieve_knowledge", "list_run", "read_run_file",
                 "webfetch", "websearch"]
SCOUT_TOOLS = ["read_artifact", "read_state", "retrieve_knowledge",
               "list_run", "read_run_file", "webfetch", "websearch"]
GENERAL_TOOLS = [t for t in CORE_TOOLS if t not in ("handoff", "create_capability")]

READ_ONLY_TOOLS = {"read_artifact", "read_state", "retrieve_memory",
                   "retrieve_knowledge", "score_fidelity", "pass_through",
                   "webfetch", "websearch", "list_run", "read_run_file"}

# the three engine-bound tools are registered by studio at import time;
# placeholders keep the definitions stable even before studio loads
_ENGINE_TOOLS = {"subagent", "handoff", "create_capability"}

# --------------------------------------------------------------------------
# session engine hook — the studio engine sets itself here for the current
# thread; the engine-bound tools call back into it (subagent spawn, handoff
# materialization, capability persistence)
# --------------------------------------------------------------------------

_engine = threading.local()


def set_engine(engine: Any) -> None:
    _engine.engine = engine


def current_engine() -> Any:
    return getattr(_engine, "engine", None)


def _schema(name: str, doc: str, props: dict[str, Any],
            required: list[str]) -> dict[str, Any]:
    return {"type": "function", "function": {
        "name": name, "description": doc,
        "parameters": {"type": "object", "properties": props, "required": required}}}


_SCHEMAS: dict[str, dict[str, Any]] = {}


def _s(name: str, doc: str, props: dict[str, Any],
       required: Optional[list[str]] = None) -> None:
    _SCHEMAS[name] = {"type": "object", "properties": props,
                      "required": list(required or [])}


# --- artifact chain --------------------------------------------------------
_s("read_artifact", "Read one artifact of the project state (blueprint, script, "
  "manifest, asset_bundle, cut_spec, voice_track, review_report). Fails if it "
  "does not exist yet — order is enforced; produce upstream work first.",
  {"key": {"type": "string", "enum": ARTIFACT_KEYS}}, ["key"])
_s("write_artifact", "Persist an artifact you have produced. You generate the "
  "payload yourself: it contains the work you just created from the available "
  "context. Never empty, never invented from nothing — Law 1: every fact must "
  "trace to the state you were given.",
  {"key": {"type": "string", "enum": ARTIFACT_KEYS},
   "payload": {"type": "object", "description": "the artifact YOU produced"}},
  ["key", "payload"])
_s("read_state", "Read one or more state fields by name. Fails loudly (Law 12) "
  "if a field was not produced upstream.",
  {"fields": {"type": "array", "items": {"type": "string"}}}, ["fields"])
_s("write_decision", "Persist a decision to the session memory.",
  {"agent": {"type": "string"}, "text": {"type": "string"}}, ["agent", "text"])
_s("write_edit", "Persist an edit to the session memory.",
  {"agent": {"type": "string"}, "file": {"type": "string"},
   "change": {"type": "string"}}, ["agent", "file", "change"])
_s("retrieve_memory", "Retrieve the session's own recorded decisions, edits, "
  "and revocations by keyword. All facts come from the session log — nothing "
  "invented (Law 1).",
  {"query": {"type": "string"}}, ["query"])
_s("retrieve_knowledge", "Retrieve the system's persisted knowledge base "
  "(recorded completed sessions). Deterministic ranking; facts only from "
  "recorded runs.",
  {"query": {"type": "string"}}, ["query"])
_s("subagent", "Spawn a TRANSIENT subagent to do work for you and return its "
  "final message. Class must be explore (read-only investigation), scout "
  "(read-only external research), or general (full toolset helper). NEVER "
  "spawn a primary agent — refused. Depth is capped by the runtime.",
  {"class": {"type": "string", "enum": ["explore", "scout", "general"]},
   "task": {"type": "string", "description": "the investigation task, with everything it needs"},
   "toolset": {"type": "array", "items": {"type": "string"},
               "description": "optional extra tool names"}},
  ["class", "task"])
_s("handoff", "Call when your work is finished and the next step belongs to "
  "another primary agent. The runtime packages your artifacts and your prompt "
  "into a folder; the human then decides whether to accept, reject, or "
  "redirect the handoff.",
  {"target": {"type": "string", "description": "target agent id"},
   "prompt": {"type": "string", "description": "your message to the target agent"}},
  ["target", "prompt"])
_s("create_capability", "Create a new capability for yourself: real knowledge, "
  "skills, tools, and resources that become part of your identity in future "
  "sessions. Persisted only with the human's explicit approval in this "
  "conversation.",
  {"name": {"type": "string"}, "description": {"type": "string"},
   "knowledge": {"type": "string"},
   "skills": {"type": "array", "items": {"type": "string"}},
   "tools": {"type": "array", "items": {"type": "string"},
             "description": "tool names this capability adds to your toolset"},
   "resources": {"type": "string"}, "guidance": {"type": "string"}},
  ["name", "description", "knowledge", "skills", "tools", "resources", "guidance"])
_s("webfetch", "Fetch a URL and return its visible text (read-only, truncated).",
  {"url": {"type": "string"}}, ["url"])
_s("websearch", "Web search; returns ranked results with title, url, and "
  "snippet (read-only).",
  {"query": {"type": "string"}}, ["query"])
_s("list_run", "List the files in a handoff package folder "
  "(data/runs/<run_id>). Read-only.",
  {"run_id": {"type": "string"}}, ["run_id"])
_s("read_run_file", "Read one file from a handoff package folder "
  "(data/runs/<run_id>/<file>). Read-only; strictly bounded to that folder.",
  {"run_id": {"type": "string"}, "filename": {"type": "string"}},
  ["run_id", "filename"])


# --- old deterministic domain tools (kept, node machinery is gone) ----------

@_register(REGISTRY, "read_state",
           "read_state(fields...) — read one or more state fields. Fails loudly (Law 12) if missing.",
           _SCHEMAS["read_state"], "read")
def read_state(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    missing = [f for f in args if f not in state]
    if missing:
        return {"error": f"fields not produced upstream: {missing} (Law 12)"}
    return {f: state[f] for f in args}


@_register(REGISTRY, "write_decision", "write_decision(agent, text) — persist a decision to memory.",
           _SCHEMAS["write_decision"], "mutate")
def write_decision(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    agent, text = args
    return {"decisions": [{"agent": agent, "text": text}],
            "note": f"decision recorded by {agent}"}


@_register(REGISTRY, "write_edit", "write_edit(agent, file, change) — persist an edit to memory.",
           _SCHEMAS["write_edit"], "mutate")
def write_edit(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    agent, file, change = args
    return {"edits": [{"agent": agent, "file": file, "change": change}]}


@_register(REGISTRY, "retrieve_memory",
           "retrieve_memory(query) — deterministic keyword retrieval over the session's "
           "decisions, edits, and revocations. Facts come only from the session log (Law 1).",
           _SCHEMAS["retrieve_memory"], "read")
def retrieve_memory(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    query = args[0]
    tokens = {t for t in re.split(r"\W+", query.lower()) if len(t) > 2}
    corpus: list[tuple[str, str]] = []
    for rec in state.get("decisions", []):
        corpus.append(("decision", rec.get("text", "")))
    for rec in state.get("edits", []):
        corpus.append(("edit", f"{rec.get('file', '')} {rec.get('change', '')}"))
    for rec in state.get("revocations", []):
        corpus.append(("revocation",
                       f"Law {rec.get('law', '')} {rec.get('law_name', '')} {rec.get('reason', '')}"))
    scored = []
    for kind, text in corpus:
        text_tokens = {t for t in re.split(r"\W+", text.lower()) if len(t) > 2}
        overlap = len(tokens & text_tokens)
        if overlap:
            scored.append((overlap, kind, text))
    scored.sort(key=lambda x: -x[0])
    top = [{"kind": k, "text": t} for _, k, t in scored[:5]]
    return {"retrieved": top,
            "note": f"retrieved {len(top)} memory entries for '{query}'"}


@_register(REGISTRY, "retrieve_knowledge",
           "retrieve_knowledge(query) — retrieval over the persisted knowledge "
           "repository (recorded completed sessions). Deterministic; facts only "
           "from recorded runs (Law 1).",
           _SCHEMAS["retrieve_knowledge"], "read")
def retrieve_knowledge(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    query = args[0]
    results = knowledge.retrieve(query)
    return {"retrieved_knowledge": results,
            "note": f"knowledge base: {len(results)} hit(s) for '{query}'"}


@_register(REGISTRY, "propose_source",
           "propose_source(kind, description, url, license_tbd, content_verified) — "
           "Researcher candidate source. content_verified must be False unless "
           "concretely verified (Law 1).",
           {"type": "object", "properties": {
               "kind": {"type": "string"},
               "description": {"type": "string"},
               "url": {"type": "string"},
               "license_tbd": {"type": "boolean"},
               "content_verified": {"type": "boolean"}},
               "required": ["kind", "description", "url", "license_tbd", "content_verified"]},
           "mutate")
def propose_source(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    kind, description, url, license_tbd, content_verified = args
    return {"sourcing_proposals": [{
        "kind": kind, "description": description, "url": url,
        "license": "NOT_VERIFIED" if license_tbd else "VERIFIED",
        "content_verified": bool(content_verified)}],
        "note": "proposal flagged: license/content not verified until user confirms"}


@_register(REGISTRY, "approve_source",
           "approve_source(index_in_proposals) — user-verified source becomes part of the bundle.",
           {"type": "object", "properties": {
               "index_in_proposals": {"type": "integer"}},
               "required": ["index_in_proposals"]},
           "mutate")
def approve_source(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    idx = int(args[0])
    proposals = state.get("sourcing_proposals", [])
    if not (0 <= idx < len(proposals)):
        return {"error": "no proposal at that index (Law 12)"}
    return {"asset_bundle": {"assets": [proposals[idx],
                                        *state.get("asset_bundle", {}).get("assets", [])]},
            "note": "source approved as part of the Asset Bundle"}


@_register(REGISTRY, "assign_visual",
           "assign_visual(agent, segment, asset_id, kind, image_ref?) — a production "
           "worker appends a visual assignment. Laws 8/9/10 enforced by the runtime guard.",
           {"type": "object", "properties": {
               "agent": {"type": "string"}, "segment": {"type": "string"},
               "asset_id": {"type": "string"}, "kind": {"type": "string"},
               "image_ref": {"type": "string"}},
               "required": ["agent", "segment", "asset_id", "kind"]},
           "mutate")
def assign_visual(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    agent, segment, asset_id, kind = args[:4]
    record: dict[str, Any] = {"agent": agent, "segment": segment,
                              "asset_id": asset_id, "kind": kind}
    if len(args) > 4 and args[4]:
        record["image_ref"] = args[4]
    return {"visual_assignments": [record]}


@_register(REGISTRY, "score_fidelity",
           "score_fidelity() — Reviewer: deterministic fidelity scoring of the cut "
           "spec against the blueprint, asset bundle, and voice track.",
           {"type": "object", "properties": {}}, "read")
def score_fidelity(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    blueprint = state.get("blueprint", {})
    bundle = state.get("asset_bundle", {}).get("assets", [])
    spec = state.get("cut_spec", {})
    tts = state.get("voice_track", {})

    template_count = len(blueprint.get("segments", [])) if isinstance(blueprint.get("segments"), list) else 0
    cut_count = len(spec.get("shots", []))
    owned = {a.get("id") for a in bundle}
    used = {s.get("asset_id") for s in spec.get("shots", [])}
    assigned = state.get("visual_assignments", [])

    missing_assets = sorted(used - owned)
    images_no_overlay = [a.get("segment") for a in assigned
                         if (a.get("kind") or "").startswith("graphic") and not a.get("image_ref")]
    per_kind: dict[str, list[str]] = {}
    for a in assigned:
        per_kind.setdefault(a.get("kind") or "", []).append(a.get("asset_id"))
    reuse = sum(len(v) - len(set(v)) for v in per_kind.values())
    tts_ok = len(tts.get("segments", [])) == cut_count if cut_count else False

    target = blueprint.get("target_duration_s") or 0
    pacing = spec.get("estimated_duration_s", 0) - target

    checks = {
        "structure_fidelity": cut_count == template_count,
        "pacing_within_tolerance": abs(pacing) <= max(1, 0.05 * target),
        "all_assets_exist": not missing_assets,
        "graphics_have_images": not images_no_overlay,
        "no_image_reuse": reuse == 0,
        "tts_coverage": tts_ok,
    }
    passed = all(checks.values())
    return {"review_report": {
        "checks": checks,
        "missing_assets": missing_assets,
        "decision": "pass" if passed else ("revise" if missing_assets or not tts_ok else "branch")}}


@_register(REGISTRY, "tts_plan",
           "tts_plan(engine, voice_sample) — Audio Lead picks the engine from the "
           "voice profile; switching engines demands explicit authorization (Law 7).",
           {"type": "object", "properties": {
               "engine": {"type": "string"}, "voice_sample": {"type": "string"}},
               "required": ["engine", "voice_sample"]},
           "mutate")
def tts_plan(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    engine, voice_sample = args
    profile = state.get("voice_profile", {})
    default = profile.get("default_engine")
    if engine and engine != default:
        authorized = profile.get("authorized_engines") or []
        if engine not in authorized:
            return {"error": f"engine switch to {engine} not authorized (Law 7)"}
    return {"tts_plan": {
        "engine": engine or default,
        "voice_sample": voice_sample or profile.get("voice_sample_path"),
        "loudness_target_lufs": profile.get("loudness_target_lufs", -16),
        "segments": [{"segment": i, "wav": f"segment_{i:02d}.wav"}
                     for i in range(1, 11)]}}


@_register(REGISTRY, "pass_through",
           "pass_through() — deterministic no-op.",
           {"type": "object", "properties": {}}, "read")
def pass_through(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    return {"note": "no state mutation this visit"}


# --- new read-only tools ----------------------------------------------------

@_register(REGISTRY, "read_artifact",
           "Read one artifact of the project state. Fails (Law 12) if it does not exist yet.",
           _SCHEMAS["read_artifact"], "read")
def read_artifact(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    key = args[0]
    if key not in state:
        return {"error": f"artifact '{key}' not produced yet (Law 12) — produce upstream work first"}
    return {"artifact": {key: state[key]}}


@_register(REGISTRY, "write_artifact",
           "Persist an artifact you have produced. You supply the full payload content yourself.",
           _SCHEMAS["write_artifact"], "mutate")
def write_artifact(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    key, payload = args
    if key not in ARTIFACT_KEYS:
        return {"error": f"unknown artifact key '{key}' (Law 12)"}
    if not isinstance(payload, dict) or not payload:
        return {"error": "payload must be a non-empty object — you generate the content"}
    return {key: payload, "note": f"artifact '{key}' written"}


@_register(REGISTRY, "webfetch",
           "webfetch(url) — fetch a URL and return its visible text (read-only, truncated).",
           _SCHEMAS["webfetch"], "read")
def webfetch(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    url = str(args[0])[:500]
    if not url.startswith(("http://", "https://")):
        return {"error": "url must be http(s)"}
    try:
        import httpx
        r = httpx.get(url, timeout=20, follow_redirects=True)
        r.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", r.text)
        text = re.sub(r"\s+", " ", text).strip()
        return {"url": url, "status": r.status_code,
                "text": text[:8000], "note": f"fetched {url} ({r.status_code})"}
    except Exception as e:
        return {"error": f"webfetch failed: {type(e).__name__}: {e}"}


@_register(REGISTRY, "websearch",
           "websearch(query) — web search; returns ranked results with title, "
           "url, and snippet (read-only).",
           _SCHEMAS["websearch"], "read")
def websearch(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    query = str(args[0])[:200]
    try:
        import httpx
        r = httpx.get("https://html.duckduckgo.com/html/",
                      params={"q": query}, timeout=20,
                      headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        results: list[dict[str, str]] = []
        for m in re.finditer(
                r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>'
                r'(?:.*?<a class="result__snippet"[^>]*>(.*?)</a>)?',
                r.text, re.DOTALL):
            url = re.sub(r"^//", "https://", m.group(1))
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", m.group(3) or "").strip()
            results.append({"title": title, "url": url[:300], "snippet": snippet[:400]})
            if len(results) >= 8:
                break
        if not results:
            return {"results": [], "note": f"no results for '{query}'"}
        return {"results": results, "note": f"{len(results)} result(s) for '{query}'"}
    except Exception as e:
        return {"error": f"websearch failed: {type(e).__name__}: {e}"}


def _run_folder(run_id: str) -> Optional[Path]:
    if not run_id or "/" in run_id or "\\" in run_id or run_id in (".", ".."):
        return None
    p = HANDOFF_DIR / run_id
    return p if p.is_dir() else None


@_register(REGISTRY, "list_run",
           "list_run(run_id) — list the files in a handoff package folder. Read-only.",
           _SCHEMAS["list_run"], "read")
def list_run(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    folder = _run_folder(str(args[0]))
    if folder is None:
        return {"error": f"no handoff folder '{args[0]}'"}
    files = sorted(p.name for p in folder.iterdir() if p.is_file())
    return {"run_id": str(args[0]), "files": files,
            "note": f"{len(files)} file(s) in run {args[0]}"}


@_register(REGISTRY, "read_run_file",
           "read_run_file(run_id, filename) — read one file from a handoff "
           "package folder. Read-only; strictly bounded to that folder.",
           _SCHEMAS["read_run_file"], "read")
def read_run_file(state: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    run_id, filename = str(args[0]), str(args[1])
    folder = _run_folder(run_id)
    if folder is None:
        return {"error": f"no handoff folder '{run_id}'"}
    if "/" in filename or "\\" in filename or filename in (".", "..") or not filename:
        return {"error": "filename must be a plain file name"}
    p = folder / filename
    if not p.is_file():
        return {"error": f"no file '{filename}' in run {run_id}"}
    try:
        content = p.read_text(encoding="utf-8", errors="replace")
        return {"run_id": run_id, "filename": filename, "content": content[:12000],
                "note": f"read {filename} ({len(content)} chars)"}
    except OSError as e:
        return {"error": f"read failed: {e}"}


# --------------------------------------------------------------------------
# definitions — the model's view of its tools (rebuilt per session, so
# created capabilities add their tools immediately)
# --------------------------------------------------------------------------

def tool_names(agent_id: str, role: str = "primary") -> list[str]:
    if role in SUBAGENT_CLASSES:
        table = {"explore": EXPLORE_TOOLS, "scout": SCOUT_TOOLS,
                 "general": GENERAL_TOOLS}
        return list(table[role])
    names = list(CORE_TOOLS)
    names += list(agents_mod.BY_ID.get(agent_id, {}).get("tools") or [])
    for cap in load_capabilities(agent_id):
        for t in cap.get("tools") or []:
            if t in REGISTRY and t not in names:
                names.append(t)
    return names


def definitions(agent_id: str, role: str = "primary") -> list[dict[str, Any]]:
    out = []
    for name in tool_names(agent_id, role):
        entry = REGISTRY.get(name)
        if not entry:
            continue
        out.append(_schema(name, entry["doc"], entry["schema"]["properties"],
                           entry["schema"].get("required", [])))
    return out


# --------------------------------------------------------------------------
# enforcement point
# --------------------------------------------------------------------------

def _to_positional(name: str, schema: dict[str, Any],
                   args: dict[str, Any]) -> tuple[Optional[list[Any]], Optional[str]]:
    """Convert the model's named arguments into the registered function's
    positional list, in schema property order. `fields`-style array properties
    expand into varargs."""
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    out: list[Any] = []
    for prop in props:
        if prop not in args:
            if prop in required:
                return None, f"missing required argument '{prop}' for {name}"
            continue
        value = args[prop]
        if prop == "fields" and isinstance(value, list):
            out.extend(value)
        else:
            out.append(value)
    return out, None


def _apply(state: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply a tool result to the session state: list-valued keys append,
    everything else sets. Errors and notes are never applied."""
    for k, v in result.items():
        if k in ("note", "error"):
            continue
        if isinstance(v, list):
            if isinstance(state.get(k), list):
                state[k] = state[k] + v
            else:
                state[k] = v
        else:
            state[k] = v


def evidence_scan(state: dict[str, Any], agent_id: str) -> None:
    """Deterministic watcher scan after a mutating call: concrete evidence in
    the session log → law_block event + revocation record. Law 2: blocks are
    raised only on evidence, never suspicion."""
    blocks: list[dict[str, Any]] = []
    for entry in state.get("events", []):
        text = (entry.get("text") or "").lower()
        if any(w in text for w in ("probably", "silently", "assume", "guess")):
            blocks.append({"law": 1, "law_name": "No Inference",
                           "agent": entry.get("agent", "?"),
                           "evidence": text[:240]})
    if any("use an effect off" in (e.get("text") or "").lower()
           for e in state.get("events", [])):
        blocks.append({"law": 6, "law_name": "No Effect Substitution",
                       "agent": "video-effects",
                       "evidence": "effect outside blueprint vocabulary"})
    for b in blocks:
        events.bus.emit("watcher-blocker", "law_block",
                        f"[Law {b['law']}] {b['law_name']} — {b['evidence']}",
                        law_id=b["law"], violator=b.get("agent", "?"))
        state.setdefault("revocations", []).append(
            {"law": b["law"], "law_name": b["law_name"], "agent": b["agent"],
             "reason": b["evidence"], "blocked": True,
             "scan": f"evidence scan by {agent_id}"})


def call(state: dict[str, Any], agent_id: str, name: str, args: dict[str, Any],
         mode: str, ask: Optional[Callable[[str, dict[str, Any]], bool]] = None,
         on_block: Optional[Callable[[dict[str, Any]], None]] = None) -> dict[str, Any]:
    """Execute one tool call through the runtime enforcement chain. `ask` is
    the Plan-Mode approval gate (returns True when the human approved); it may
    be None in Build Mode. Returns the tool result dict."""
    entry = REGISTRY.get(name)
    if entry is None:
        events.bus.emit(agent_id, "tool_result",
                        f"tool '{name}' not found (Law 12)", tool=name, error=True)
        return {"error": f"unknown tool '{name}' (Law 12)"}

    positional, err = _to_positional(name, entry["schema"], args)
    if err is not None:
        events.bus.emit(agent_id, "tool_result", err, tool=name, error=True)
        return {"error": err}

    mutating = entry["permission"] == "mutate"

    if mutating and mode == "plan":
        approved = ask(name, args) if ask else False
        if not approved:
            events.bus.emit(agent_id, "tool_result",
                            f"{name} blocked: Plan Mode — your approval was not granted",
                            tool=name, error=True, blocked=True)
            return {"error": f"blocked: Plan Mode requires your approval ({name})"}

    events.bus.emit(agent_id, "tool_call", f"{name}({_fmt_args(positional)})",
                    tool=name, args=list(positional))

    if mutating:
        block = laws.guard(state, agent_id, {"tool": name, "args": positional})
        if block:
            state.setdefault("revocations", []).append(block)
            if on_block:
                on_block(block)
            events.bus.emit(agent_id, "tool_result",
                            f"{name} blocked: [Law {block['law']}] {block['law_name']}",
                            tool=name, error=True, blocked=True)
            return {"error": f"blocked: [Law {block['law']}] {block['law_name']}"}

    try:
        result = entry["fn"](state, agent_id, positional)
    except Exception as e:  # noqa: BLE001 — honest surface of any failure
        result = {"error": f"{name} failed: {type(e).__name__}: {e}"}

    if "error" not in result:
        _apply(state, result)
        events.bus.emit(agent_id, "tool_result",
                        f"{name} -> {result.get('note') or 'ok'}", tool=name)
        if mutating:
            evidence_scan(state, agent_id)
    else:
        events.bus.emit(agent_id, "tool_result", f"{name} -> {result['error']}",
                        tool=name, error=True)
    return result


def _fmt_args(args: list[Any]) -> str:
    return ", ".join(json.dumps(a, ensure_ascii=False, default=str)[:60] for a in args)