# Agentic Video System — LangGraph Runtime

A runnable implementation of the [Agentic Video System](../README.md) org chart
as a **deterministic LangGraph orchestrator**: 17 agents, 5 departments, 12 laws,
human-in-the-loop CEO approvals, an optional LLM "brain", and a persistent RAG
knowledge repository — with a CLI and a live FastAPI + mermaid web dashboard.

```
CEO (you) ──► 5 department heads ──► 12 workers
  │            Strategy · Audio · Production · Quality · Personnel
  │
  ├─ deterministic pipeline (hard-wired edges, watchpoints, iteration cap)
  ├─ 12 laws enforced by guard() at every step + Watcher/Blocker patrols
  ├─ human approvals via LangGraph interrupt() (script, asset bundle)
  ├─ optional LLM thinking (OpenAI-compatible, Zhipu GLM supported)
  └─ RAG: every run persisted to runs/<run-id>/knowledge.json, retrievable via BM25
```

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# CLI — streaming console (auto-approve all CEO prompts for a demo run)
python -m ui.cli --yes \
  --topic "Why Mbappé shines on the biggest stage" \
  --reference-analysis examples/reference-analysis-mbappe.json

# Web UI — dashboard + workspace landing
uvicorn ui.web.server:app --port 8000
# open http://127.0.0.1:8000  →  Agent Dashboard (default), /graph = technical mermaid view
```

## Architecture

| Layer | Files | Role |
|-------|-------|------|
| State | `avis/state.py` | Single `AgentState` TypedDict, reducers for logs/decisions |
| Agents | `avis/agents.py` | 17 deterministic nodes (strategist → … → recruiter) |
| Graph | `avis/graph.py` | Hard-wired edges, watchpoints, review pass/revise/branch, watchdog (500-update budget) |
| Laws | `avis/laws.py` | 12 guards; violations emit a law_block + revocation record |
| Tools | `avis/tools.py` | Executable tool registry (read/write state, assign visuals, score fidelity, RAG) |
| Brain | `avis/brain.py` | Optional LLM thinking; deterministic scripted fallback |
| Knowledge | `avis/knowledge.py` | Per-run persistence + deterministic BM25 retrieval (RAG) |
| Events | `avis/events.py` | Thread-safe event bus → both UIs observe the run live |
| UI 1 | `ui/cli.py` | Streaming console, ANSI colors, stdin approvals |
| UI 2 | `ui/web/` | FastAPI + SSE + mermaid graph view, CEO modal, knowledge panel |
| UI 3 | `avis/studio.py` + `static/dashboard.html` | Agent Dashboard — live overview of all 17 agents, statuses/attention from the real event bus (see below) |

## Agent Studio — Dashboard (Stage One)

Open `http://127.0.0.1:8000/` — the Agent Dashboard is the default landing page (the
technical mermaid graph stays at `/graph`; `/workspace/<agent_id>` is the Stage Two
workspace landing page).

- **17 agent cards** — name/role, real status (`working` / `waiting` / `completed` /
  `failed` / `idle`), real `current_task` and `last_activity_at` taken from the event bus,
  progress (100 on completion, pipeline position while in flight, 0 idle). Never invented.
- **Needs Your Attention** — an agent before a CEO approval (the run is blocked on its
  interrupt) glows and shows a badge; answered from the run's own progress.
- **Production Overview** — 5 department stages (Strategy / Audio / Production / Quality /
  Personnel), derived from real agent completions. Not a graph.
- **Activity heatmap** — real hourly buckets of event-bus activity; hidden when empty.
- **Live updates** — SSE at `/api/studio/events` (`agent_status_changed`,
  `agent_completed`, `agent_attention_required`, `agent_failed`, `agent_handoff_ready`,
  `activity_created`), with loading and connection-loss states.
- **API** — `GET /api/studio/dashboard` returns the full snapshot; `GET /api/agents/<id>`
  returns an agent's real identity/description.

Run it the same way as the web UI above. `AVIS_LLM_ENABLED` is honored — everything
works fully offline with the deterministic scripted brain.

## Agent Workspace (Stage Two)

Open `http://127.0.0.1:8000/workspace/<agent_id>` (any dashboard card) — a per-agent
workspace where you can talk to one agent at a time. Each workspace is backed by a real
run of that agent's node function through the same tested graph loop — no simulated
chat, no invented output.

- **Conversation** — send a message; the agent runs its REAL node, and the result comes
  from its own event-bus outcome. The conversation is stored server-side per agent, so
  it survives page reloads.
- **Live Activity** — a per-agent timeline of real events (`plan_created`,
  `action_started`, `tool_call_started/completed/failed`, `artifact_created`,
  `run_completed`, …) streamed over SSE. CEO decision events are excluded — each
  workspace only shows its own agent's work.
- **Context carries forward** — artifacts and decisions produced by a run seed the next
  run's state (`_workspace_context`), so a chained strategist → analyzer → planner
  conversation builds up the project across agents. Runs are recorded with
  `record=False`, keeping the RAG corpus reserved for full pipeline runs.
- **Handoffs** — when a run finishes, a recommended next agent appears
  (HANDOFF_MAP). Approve &amp; Switch takes you to that agent's workspace (its run will
  see the accumulated context); Choose Another Agent redirects to any of the other 16;
  Continue Here declines the handoff.
- **Deterministic by default** — workspace runs use the scripted brain unless you send
  `{"message": ..., "llm": true}`; every outcome is still derived from real events.

API:

```
GET  /api/studio/agents/<id>                agent + current run + messages + events + handoff
POST /api/studio/agents/<id>/messages       {"message": "..."}            → real node run
POST /api/studio/agents/<id>/handoff        {"decision": "approve"|"redirect"|"continue",
                                             "target_agent_id": "...", "run_id": "..."}
GET  /api/studio/agents/<id>/events         per-agent SSE stream (keepalive 15s)
```

## The LLM brain (optional)

No key = fully deterministic scripted brain. With a key, every agent streams real
reasoning lines before acting — the orchestrator never depends on the LLM.

```bash
# Zhipu (BigModel) — OpenAI-compatible
export GLM_API_KEY=...            # default model glm-4.5-flash
# or any OpenAI-compatible endpoint
export OPENAI_BASE_URL=https://.../v1 OPENAI_API_KEY=...
# model override
export AVIS_LLM_MODEL=...
# disable LLM thinking for fast deterministic runs
export AVIS_LLM_ENABLED=0
```

Copy `.env.example` → `.env` for a project-local config (gitignored).

## RAG knowledge repository

Every run is recorded to `runs/<run-id>/` (`knowledge.json` corpus + `state.json`
audit). The planner grounds its script with `retrieve_knowledge(topic)` — prior
decisions from past runs. The web UI has a knowledge panel; API:

```
GET  /api/knowledge               runs + corpus
POST /api/knowledge/retrieve      {"query": "asset bundle"} → BM25-ranked hits
```

## Web API

| Endpoint | Purpose |
|----------|---------|
| `GET /api/graph` | mermaid graph + engine version |
| `GET /api/agents` | the 17 agents / departments / tiers |
| `GET /api/examples` | reference-analysis JSON files in `examples/` |
| `GET /api/events` | Server-Sent Events: thinking, tools, laws, routes live |
| `GET /api/state` | run snapshot (decision, checks, iterations, blocks) |
| `GET /api/pending` | the pending CEO question (script / proposals) |
| `POST /api/run` | `{topic, reference_analysis, llm, auto_approve}` |
| `POST /api/answer` | `{resume: "approve" | "rejected"}` |
| `GET /api/studio/agents/<id>` | workspace snapshot (see Agent Workspace) |
| `POST /api/studio/agents/<id>/messages` | run a workspace agent's real node |
| `POST /api/studio/agents/<id>/handoff` | approve / redirect / continue a handoff |
| `GET /api/studio/agents/<id>/events` | per-agent workspace SSE stream |

## Tests

```bash
pip install pytest
python -m pytest tests -q        # 59 tests: laws, tools, graph, API, studio
```

Tests force the scripted brain (offline, deterministic, fast).

## Key design points

- **Determinism first**: the graph structure never changes at runtime; the only
  branches are review pass/revise/branch and human approvals. LLM thinking is
  pure observability.
- **Human-in-the-loop**: CEO approvals are LangGraph `interrupt()` — the run
  genuinely stops and waits for an answer (CLI stdin or web modal).
- **Laws are code**: `guard()` runs all 12 checks on every action; Watcher/Blocker
  re-scans the run log at watchpoints; violations escalate to Investigator.
- **Never hangs**: 4-iteration review cap + 500-update watchdog + 30s LLM timeout
  with scripted fallback.