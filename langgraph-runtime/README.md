# Agentic Video System — LangGraph Runtime

A runnable implementation of the [Agentic Video System](../README.md) org chart
as a **deterministic LangGraph orchestrator**: 17 agents, 5 departments, 12 laws,
human-in-the-loop CEO approvals, an optional LLM "brain", and a persistent RAG
knowledge repository — with a CLI and a live FastAPI + mermaid web dashboard.

## Resume this development session

The autonomous-agents migration is tracked in an opencode session. To relaunch
this exact session (same context, same todo list):

```bash
opencode -s ses_ffb092e08ffe0dzcemf9FbWvKf
```

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

## Agent Workspace (conversation-first)

Open `http://127.0.0.1:8000/workspace/<agent_id>` (any dashboard card) — a per-agent
workspace where you talk to one agent at a time. Everything is ONE continuous
conversation: messages, reasoning summaries, intent, tool calls/results, approvals and
errors are all entries of a single normalized timeline (spec §11) — there is no separate
activity panel.

- **Plan / Build are interaction modes, not workflow stages** — an explicit toggle in the
  top bar, per agent, defaulting to Plan. There is no prescribed workflow: the human is
  the governance layer.
- **Plan Mode has zero execution authority** — enforced by the runtime, not by prompting:
  a gate in `avis/tools.py` refuses every mutating tool while Plan Mode is active
  (read-only inspection stays allowed). Plan turns run the real think stream for genuine
  reasoning summaries, state an intent, then reply with an approach — nothing is executed
  or changed.
- **Build Mode runs the agent's REAL node** — the same tested `g.run()` loop as the full
  pipeline, single-node. The run genuinely pauses when an approval is required: the
  `approval_request` sits in the conversation until you answer Approve / Reject, and the
  run resumes from your real answer.
- **Stop is a real runtime cancellation** — cooperative; the run is halted at its next
  checkpoint (a pending approval is released as rejected) and the agent reports honestly
  what had completed before the stop request.
- **Greetings are conversational, zero execution** — "Hello" gets a friendly identity
  reply and never triggers a plan, a project, or any execution.
- **No auto-routing, no handoff chains** — runs never recommend a next agent. Switching
  agents is a human decision: the left-hand Agent Network (or a handoff call carrying an
  explicit `decision`) takes you to another agent's workspace, and its run inherits the
  real accumulated project context (`_workspace_context`).
- **Context carries forward** — artifacts and decisions produced by a run seed the next
  run's state, so a strategist → analyzer → planner conversation builds up the project
  across agents. Runs are recorded with `record=False`, keeping the RAG corpus reserved
  for full pipeline runs.
- **Right panel = agent context only** — about, capabilities, project memory (real
  context keys present) and the tools the agent has actually used, from the real event
  bus. Nothing invented.
- **Deterministic by default** — workspace runs use the scripted brain unless you send
  `{"message": ..., "llm": true}`; every outcome is still derived from real events.

**W6.7 — Projects & Sessions (OpenCode-style):**

- **One workspace per agent; projects as folders; sessions as chats** — every agent has
  one workspace, inside it multiple projects, each project holds its own session history.
  Two projects never share a chat. The project selector shows only real projects (empty
  state: "No projects yet" + Create Project). Switching projects lands on that project's
  most recent session.
- **Session naming** — first user message becomes the title (first line, markdown
  stripped, truncated to 60 chars). Placeholder titles ("New discussion") are auto-renamed
  on the first send.
- **Compaction (suggested + manual)** — when ~20 user messages pass since the last
  compaction, the agent raises `pending_compact` and emits a `compact_request` event.
  The UI shows a card: "Compact now / Not now". Declined → re-suggested after ~10 more
  messages until accepted. "Yes" summarizes everything before the last 16 events into
  `session.summary` (incremental, folds prior summary) which the prompt reads. No model
  → honest trim with placeholder note. Manual "Compact" button also available in Past
  Discussions.
- **Tool payload display** — tool lines show `→ {tool}: {arg}` from the actual args
  (priority: file, filename, key, url, query, run_id, target, class).

API:

```
GET  /api/studio/agents/<id>                agent + mode + current run + one conversation
POST /api/studio/agents/<id>/messages       {"message": "..."}            → Plan or Build turn
POST /api/studio/agents/<id>/mode           {"mode": "plan"|"build"}      → explicit mode switch
POST /api/studio/agents/<id>/approval       {"run_id": "...", "answer": "approve"|"rejected"}
POST /api/studio/agents/<id>/stop           {"run_id": "..."}             → real cancellation
POST /api/studio/agents/<id>/handoff        {"decision": "approve"|"redirect",
                                             "target_agent_id": "..."}    → refuses without decision
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
| `GET /api/studio/agents/<id>` | workspace snapshot (`?project=` scopes to project) |
| `POST /api/studio/agents/<id>/messages` | run a workspace agent's real node (project-aware session pick + naming) |
| `POST /api/studio/agents/<id>/compact` | compaction answer `{session_id, answer: "yes"|"no"}` |
| `POST /api/studio/agents/<id>/handoff` | approve / redirect / continue a handoff |
| `GET /api/studio/agents/<id>/events` | per-agent workspace SSE stream |

## Tests

```bash
pip install pytest
python -m pytest tests -q        # 88 tests: laws, tools, graph, API, studio, agents, projects
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