# Agentic Video System — LangGraph Runtime Implementation Plan

> Single source of truth for the build-out. Update after every phase so work
> survives session switches (opencode / Claude / laptop).

**Started:** 2026-08-15
**Goal:** Finish & polish the LangGraph runtime into a portfolio-ready showcase for the
Capgemini Web Developer role (LangGraph agents, human-in-the-loop, RAG, FastAPI web UI,
LLM integration via Zhipu/GLM). Commit + push + make repo public.

**Repos:**
- Remote: `https://github.com/lordwhitefire/agentic-video-system` (now public)
- Runtime: `langgraph-runtime/` — committed, pushed to `main`

**LLM key:** Zhipu `GLM_API_KEY` (in the local shell profile). OpenAI-compatible
endpoint: `https://open.bigmodel.cn/api/paas/v4`, model `glm-4.5-flash`
(configurable via `AVIS_LLM_MODEL`). Never commit keys; `.gitignore` blocks `.env`.

---

## Phase 0 — Persist this plan
- [x] Write `langgraph-runtime/PLAN.md` (this file)
- [x] Keep it updated after every phase

## Phase 1 — Verify & fix the pipeline
- [x] Run full CLI pipeline end-to-end with Mbappé example (`ui.cli --yes`)
- [x] Confirm all 17 nodes fire, laws run, reviewer reaches a decision
- [x] Fix bugs found (see below)
- [x] Add hard watchdog in `graph.py:run()` (500-update budget) so a run can never spin
- [x] Acceptance: `ui.cli --yes` finishes with review decision + summary in <60s — PASS,
      exit 0, all 6 fidelity checks green, 2 CEO approvals, 344-line log

**Bugs fixed (infinite revise loop — 376 cycles in 25s before fix):**
1. `iterations` only incremented in `work_strategist`; revise loop (reviewer→editor) never hit
   the 4-iteration cap → `work_reviewer` now increments it
2. `work_researcher` read `sourcing_proposals` from stale state (staged tool output isn't in
   state mid-node) → empty bundle → `all_assets_exist` always failed; proposals now collected
   from tool return values and given ids (`src-N`)
3. `assign_visual` dropped `image_ref` (worker built it on a local dict, tool rebuilt without
   it) → Law-8 check failed; tool now accepts optional image_ref
4. `no_image_reuse` counted across workers (6 workers × same asset = "reuse") → now per-kind
5. `pacing_delta_s: 0` is falsy → perfect pacing failed `all(checks)` → now boolean
   `pacing_within_tolerance` (±5%)

## Phase 2 — Wire the Zhipu (GLM) LLM brain
- [x] `brain.py` supports OpenAI-compatible endpoints (provider priority: OPENAI_BASE_URL
      > GLM_API_KEY > api.openai.com; AVIS_LLM_MODEL override)
- [x] Zhipu wired: `https://open.bigmodel.cn/api/paas/v4`, model `glm-4.5-flash`
      (user-specified; glm-4-flash does not exist on this account)
- [x] `.env` loader in `brain.py` + `.env.example` committed (`.env` stays gitignored)
- [x] Parser now consumes `reasoning_content` (GLM-4.5 streams reasoning; with
      max_tokens=120 the plain `content` field alone produced empty lines)
- [x] `AVIS_LLM_ENABLED=0` toggle for fast deterministic runs (web UI checkbox)
- [x] Smoke tests: raw call 200; full pipeline run WITH key → PASS, 162 real GLM
      thinking lines; without key → scripted fallback, still completes

## Phase 3 — Upgrade the web UI (`ui/web/`)
- [x] Real CEO approval flow: `/api/pending` returns the interrupt question
      (script draft, asset proposals, manifest); modal with APPROVE / REJECT →
      `/api/answer` (fixed module-global shadowing bug in `_remote_approver`)
- [x] Auto-approve (demo) checkbox → `/api/run` (`auto_approve`); interactive
      mode verified end-to-end (2 approvals → pass)
- [x] Live graph highlighting: mermaid node lights up on agent events
- [x] Run controls: topic input, examples dropdown (`/api/examples`), LLM
      thinking + auto-approve checkboxes, running badge, iterations/review/
      law-blocks/visual-assign counters
- [x] Offline mermaid: `mermaid.min.js` downloaded into `static/`, served via
      `/api/js/mermaid.min.js` (no CDN dependency)
- [x] Hardcoded home path removed; `reference_analysis` validated to live in
      `examples/` (no arbitrary file reads on a public server)
- [x] Verified: `/api/graph`, `/api/agents`, `/api/examples`, `/api/events` (SSE),
      `/api/state`, `/api/pending`, `/api/answer`, `/api/run`, index page

## Phase 4 — RAG upgrade
- [x] `avis/knowledge.py`: per-run persistence to `runs/<run-id>/knowledge.json`
      (decisions, edits, review verdicts, revocations) + `state.json` audit
- [x] Deterministic BM25 retrieval (`k1=1.5, b=0.75`) over the persisted corpus;
      same query + corpus → same ranking (Law 1: facts only from recorded runs)
- [x] `retrieve_knowledge` tool added; planner now grounds its manifest with
      `prior_knowledge` from past runs (RAG in action)
- [x] `graph.run()` records every run (also on watchdog abort)
- [x] `/api/knowledge` + `/api/knowledge/retrieve`; UI panel with query box,
      run count, ranked results (verified: cross-run hit on "asset bundle approved")
- [x] `runs/` already gitignored
- [x] Fixed missing `Counter` import in knowledge.py

## Phase 5 — Tests + docs
- [x] `pytest` suite: tests/test_laws.py, test_tools.py, test_graph.py, test_api.py
      + conftest.py (forces scripted brain: AVIS_LLM_ENABLED=0 + pops keys)
- [x] 36 tests green (5.1s, offline)
- [x] `langgraph-runtime/README.md`: architecture, quick start (CLI + web),
      Zhipu config, RAG, API table, tests
- [x] Repo-root `README.md` updated with a "Runtime" section (links into runtime README)

**Bugs found & fixed during Phase 5 testing:**
1. `laws.py:66` + `agents.py:249` — `events.bus.emit(..., agent=agent_id)` in `**data`
   collided with the positional `agent` param → TypeError → ANY law violation crashed
   the runtime. Fixed: kwarg renamed to `violator=`.
2. `tools.tts_plan` — Law 7 guard was INVERTED (blocked authorized switches, allowed
   unauthorized ones). Now: switch requires engine ∈ authorized_engines.
3. Test env pollution: persistent shell exported GLM_API_KEY → tests made real 10s
   Zhipu calls per node (runs looked hung). Fixed: conftest.py.
4. `ui.web.server` monkeypatched `avis.graph.run` at IMPORT time → test_api imported
   first, so graph tests ran the web approver (auto-approving everything). Fixed:
   `/api/run` worker now passes `_remote_approver` explicitly; patch deleted.

## Phase 6 — Commit, push, make public
- [x] Secret/path scan clean (only GitHub URL references remain; .env.example empty;
      `runs/` + `.venv` + `__pycache__` + `.pytest_cache` ignored)
- [x] Fixed `knowledge.RUNS_DIR` off-by-one (was writing to repo-root `runs/`, now
      `langgraph-runtime/runs/`); removed misplaced root `runs/` (had home paths)
- [x] Committed `55736d3` (27 files, +4502) and pushed to `main`
- [x] Repo flipped public: https://github.com/lordwhitefire/agentic-video-system
- [x] Topics: langgraph, agentic-ai, llm-agents, rag, fastapi, human-in-the-loop,
      ai-agents, python, opencode, mermaid
- [x] Fresh-machine acceptance: clone → venv → `pip install -r requirements.txt` →
      `python -m ui.cli --yes` → PASS, all 6 checks green, exit 0; uvicorn boots

## Phase 7 — Agent Studio (presentation build)

> Specs (all in `~/Downloads/`):
> 1. `agent_dashboard_build_spec.md` — product concept (dashboard + workspace, human-controlled handoffs, no graph)
> 2. `agent_workspace_stage_two.md` — Stage Two = Agent Workspace (NOT this build)
> 3. `avis_agent_dashboard_complete_build.md` — **Stage One = Agent Dashboard (THIS build)**, with complete reference UI

**Stage One scope (this build):** dashboard overview only. Routes per spec §29:
`/` → Agent Dashboard · `/workspace/:agent_id` → workspace (placeholder now, full workspace is Stage Two) · `/graph` → existing technical mermaid graph (kept, NOT linked from dashboard). No navbar, no chat, no graph on the dashboard, no handoff controls on the dashboard (workspace owns those).

### Stage One — checklist
- [x] **7.1 `avis/studio.py`** (new): canonical `REGISTRY` (17 ids from `agents.AGENTS` + display name/description — single source of truth, tested against `agents.BY_ID`); `build_dashboard_snapshot(run_state, pending_question)` deriving REAL per-agent status from the event bus (result event → completed; invoked-without-result + run running → working; agent before a CEO interrupt → waiting + attention; error/stopped → failed; never invoked → idle), progress (100 completed / pipeline-position for in-flight / 0 idle), current_task = last real event text, last_activity_at from bus; system counters (total/active/idle/waiting/attention/completed_today via `knowledge.list_runs`); recent_activity (last 10 bus events); attention list (pending CEO question + law blocks); production stages (5 departments, derived from agent completions — NOT a graph); heatmap (24 real hourly buckets of bus activity — hidden when no data, never invented); `map_studio_event(ev)` → SSE event types
- [x] **7.2 `server.py` routes**: `GET /` → dashboard.html; `GET /graph` → old index.html; `GET /workspace/{agent_id}` → placeholder workspace.html (+`GET /api/agents/{agent_id}` for real identity); `GET /api/studio/dashboard` (spec §15 contract); `GET /api/studio/events` (SSE: agent_status_changed, agent_completed, agent_attention_required, agent_failed, agent_handoff_ready, activity_created). All existing endpoints untouched
- [x] **7.3 `static/dashboard.html`** — adapt the spec's complete reference UI: near-black (#07090f) premium command center, 3-column layout (System Overview / Active Work ring / Recent Activity · agent card grid + Production Overview strip · Activity heatmap + Needs Your Attention), independent cards (name/role/status/task/progress/last activity/attention glow+badge), click → /workspace/<id>, live SSE refresh, loading state, connection-loss state, keyboard access, reduced-motion support. NO fake numbers — all values from the API
- [x] **7.4 Tests** `tests/test_studio.py`: registry == agents catalog (17, no dupes); idle snapshot (0 active, all idle, empty attention); after a real auto-approve run → completed statuses real, progress 100, completed_today ≥ 1; during a blocked CEO interrupt → waiting + attention_agents ≥ 1 (polling, deterministic); SSE endpoint streams; /, /graph, /workspace pages; unknown agent 404. Update `test_index_and_graph` in test_api.py. All 36 existing tests stay green → **49/49 passed**
- [x] **7.5 Docs**: runtime README gains Agent Studio section; root README mention; this checklist updated with bugs found
- [x] **7.6 Acceptance (spec §32)**: opens directly to dashboard; no navbar; all 17 agents dynamic; independent cards, no lines, no mermaid; status/task/progress/activity/attention REAL; attention glows + badge; click opens workspace; live updates; loading + connection-loss states; keyboard + reduced motion; no conversation/tool logs/handoffs on dashboard; real runtime only, no duplicate registry/runtime
- [x] **7.7 Commit + push**: `ADD: Agent Studio Stage One — dashboard` (repo already public)

**Bugs found & fixed**
- Full-suite pollution: `test_laws` emits `law_block` events on the shared global bus, leaking into studio attention lists (and `test_api` interrupt events into waiting). Fixed with an autouse fresh-bus fixture per studio test.
- SSE streaming tests: TestClient `stream()` never completes (SSE hangs in `__enter__`), and httpx ASGITransport buffers the whole body. Tests now drive the endpoint function directly + `anext(aiter(resp.body_iterator))`.
- Shared `thread_id: run-001` across all runs: a halted run (e.g. missing `reference_analysis` → Law-1 gate halt) could leak the *previous* run's checkpoint data (stale `review_decision: pass`, assignments). Fixed: unique `uuid4` thread id per `g.run()`.
- Live-verified (uvicorn :8000): idle snapshot → full auto-approve run (15 agents completed, real progress/stages) → interactive run blocks at planner interrupt (dashboard shows Planner **waiting + attention**), answer → blocks at researcher interrupt, answer → completed, waiting/attention 0. No fabricated statuses.

**Stage Two (next build, NOT now):** Agent Workspace per `agent_workspace_stage_two.md` — conversation, work plan, tool calls, artifacts, handoff approve/redirect/continue/stop, `avis/studio.py` gains `NEXT_AGENT_MAP` + `run_agent`.

---

## Phase 8 — Agent Workspace (Stage Two, complete build)

> Spec: `~/Downloads/avis_agent_workspace_complete_build.md` (4720 lines). Two
> user-facing surfaces only: **Dashboard = overview**, **Workspace = work**.
> `Human = controller, Agent = worker, Handoff = human-approved transition`.
> No navbar, no graph, no workflow builder, no multi-agent chat, no fake events.

**Design decisions (adapting the spec to the real runtime):**
- **Per-agent runs run REAL node functions** (§3/§35/§77): each workspace message
  compiles a tiny single-node `StateGraph` around `build_node(agent_id)` and drives
  it through the existing `g.run()` loop. This keeps the tested node functions,
  tools, laws, and events — no second engine, no fake chat. `interrupt()` works
  because it runs inside a real (single-node) graph; the workspace approver
  auto-approves demo interrupts and the CEO note is recorded (honest).
- **Context transfer** (§56/§57): the run is seeded from the most recent recorded
  run's real `state.json` (reference_analysis, blueprint, script, manifest, …) so
  the next agent genuinely inherits the previous agent's outputs. If a node's
  upstream input is missing, it errors with the real Law-1 message (honest).
- **Artifacts** (§14/§71): real state keys produced by the node (blueprint, script,
  manifest, plan lock, …) render as artifact cards with the recorded run as the
  artifact store. No invented files.
- **Persistence** (§66/§67/§78): messages live in a server-side per-agent store;
  events are recoverable from `events.bus.history()`. Browser refresh restores both.

### Stage Two — checklist
- [x] **8.1 `avis/studio.py`**: canonical `HANDOFF_MAP` (full pipeline chain + reasons, single source of truth, spec §22/§54); `execute_agent_run(agent_id, message)` — single-node graph + `g.run()` + auto-approve approver + context seed from last recorded run; `build_workspace_snapshot(agent_id)` (agent §32 + messages + events + current run + handoff); `workspace_event(ev)` mapping raw bus kinds → workspace types (thinking→action, tool_call→tool_call_started, tool_result→tool_call_completed, result→agent message, interrupt→agent_waiting, …) with `sanitize()` for secrets + result truncation (§37/§70)
- [x] **8.2 `server.py`**: `GET /api/studio/agents/{id}` snapshot; `POST /api/studio/agents/{id}/messages` (real run); `POST /api/studio/agents/{id}/handoff` (approve/redirect/continue, validates target, returns `workspace_url`); `GET /api/studio/agents/{id}/events` (workspace SSE, replay + live). `/workspace/{id}` stays; dashboard endpoints untouched
- [x] **8.3 `static/workspace.html`**: replace placeholder with the spec's complete reference UI (§49): `← Overview`, agent context (identity/status/task/progress/last activity/capabilities), conversation (human/agent messages, PLAN cards, artifact cards), live activity timeline (PLAN/ACTION/TOOL CALL/TOOL RESULT/DECISION/RESULT/HANDOFF with expandable details), typing-only composer with agent-working/waiting states, handoff bar (Approve & Switch / Choose Another Agent / Continue Here), agent-selector modal, loading skeleton + empty state, SSE reconnect + snapshot reload, keyboard + reduced motion. Same visual language as the dashboard
- [x] **8.4 Tests** `tests/test_workspace.py`: snapshot = real agent identity/status/capabilities; message → run starts → working → real tool_call/tool_result events → result → handoff ready (deterministic polling); handoff approve returns next workspace URL; redirect validates target; continue records + dismisses; workspace SSE streams; `/workspace/{id}` renders; unknown agent 404; history survives "refresh" (snapshot re-fetch). All 49 existing tests stay green
- [x] **8.5 Docs**: runtime README workspace section; PLAN.md bugs found
- [x] **8.6 Acceptance (spec §78/§80 DoD)**: dashboard card opens `/workspace/<id>`; workspace shows the agent; message runs the real node; status/progress/messages/plan/tools/results/artifacts live; conversation history survives refresh; handoff recommend→approve→switch opens `/workspace/next`; redirect works; continue works; no navbar/graph/workflow-builder/multi-agent chat/fake events; secrets redacted; large outputs truncated
- [x] **8.7 Commit + push**: `ADD: Agent Workspace (Stage Two)`

## Phase 9 — Agent Workspace rebuild: conversation-first

> Spec: `~/Downloads/AVIS_Agent_Workspace_Replacement.md`. The Stage Two workspace was
> rebuilt after the user's review: ONE continuous conversation, no activity panel.
> Plan and Build are interaction modes, not workflow stages; Plan Mode has zero
> execution authority (enforced by a runtime gate, not by prompting); the human is the
> governance layer; handoffs require an explicit human decision; stop is a real runtime
> cancellation; four behaviors are locked by tests. Approved plan:
> `WORKSPACE_REBUILD_PLAN.md` (updated with the 7 corrections).

- [x] **9.1 Runtime guarantees**: `avis/tools.py` execution gate — `set_execution_blocked()`,
  `READ_ONLY_TOOLS` (read_state, retrieve_memory, retrieve_knowledge, score_fidelity,
  pass_through) stay allowed; any mutating `call()` while the gate is on emits a real
  blocked tool_call/tool_result and refuses. `avis/graph.py` `RunStopped` +
  `should_stop` — cooperative cancellation polled between stream updates,
  `final["stopped"] = True`.
- [x] **9.2 `avis/studio.py`**: one normalized timeline (`CONVERSATION_TYPES`):
  user_message, assistant_message, reasoning_summary, intent, tool_call, tool_result,
  approval_request, approval_result, error, status. `workspace_event()` remaps raw bus
  events into that single stream (result/route → None; the store owns the final
  assistant message). `is_greeting`/`greeting_reply` (conversational, zero execution),
  `is_status_question`/`status_summary` ("What have you been doing?" from real
  conversation events), `intent_message` (stated before any consequential execution),
  `plan_response` (Plan Mode: approach + "Nothing was executed"). New snapshot contract:
  `{agent(+about/capabilities/tools/memory), mode, current_run, conversation[],
  can_stop, pending_approval}` — no handoff field, no activity feed. Tool registry list
  per agent comes from the real bus; project memory labels from real `_workspace_context`.
- [x] **9.3 `server.py`**: store = conversation + mode (default `"plan"`) + run + approval;
  worker branches greeting / status question / Plan (think stream only, gate on) / Build
  (real node, inline approver, `should_stop`); `_finish_ws_turn` pushes the final
  message BEFORE the terminal status is visible (no observe-before-final-event race);
  new endpoints `POST …/mode`, `POST …/approval`, `POST …/stop`; `POST …/handoff`
  refuses (400) without an explicit human `decision`; user messages (`agent_id:"you"`)
  pass the per-agent SSE filter; greeting seeded on first snapshot.
- [x] **9.4 `static/workspace.html`**: full rebuild — top bar Plan|Build toggle + STOP;
  one conversation timeline rendering all 9 event types inline (bubbles, reasoning,
  intent card, tool cards with args/status, approval card with Approve/Reject, error,
  status lines); left Agent Network (dynamic) + project resources; right panel =
  about/capabilities/memory/tools; SSE reconnect + snapshot reload with dedup; no Live
  Activity panel.
- [x] **9.5 Tests** `tests/test_workspace.py` rewritten to the new model (18 tests,
  incl. the four critical ones: plan mode blocks tool execution — gate unit + zero tool
  events integration; build mode executes with real tool events; "Hello." = zero
  execution; unauthorized handoff → 400). Also: approval pause/resume, rejection
  surfaces as a failed run with an error event, stop = honest "Stopped" message,
  refresh survival, SSE, 404s, secrets. `tests/test_studio.py` page test asserts the new
  UI. Full suite **67/67 passed**.
- [x] **9.6 Docs + acceptance**: README workspace section rewritten to the
  conversation-first model; live acceptance — greeting zero-execution, Plan mode
  intent+reasoning+plan reply with zero tools, Build mode real tool events, approval
  pause→approve→resume→artifacts, stop releases approval and reports honestly,
  SSE streams conversation events, unauthorized handoff 400.
- [ ] **9.7 Commit + push**: `REBUILD: Agent Workspace — conversation-first (Plan/Build modes, runtime-enforced authority, inline approvals)`

**Bugs found & fixed during Phase 9:**
- The SSE per-agent filter dropped `user_message` events because the human's messages
  carry `agent_id: "you"` — the filter now accepts both.
- `threading.Event` (stored in `approval_pending`) leaked into the serialized snapshot —
  `build_workspace_snapshot` returns a plain `{id, run_id, question}` payload.
- Approval-result events were lost by the dedup key when two runs finished in the same
  second — the key now includes approval status and tool name.
- Workspace `run_id`s collided when two runs of the same agent started in one second,
  breaking turn-scoped assertions — now `int(time.time() * 1000)` based.
- `_finish_ws_turn` set the terminal status before pushing the final message; a client
  polling the store could observe the finished run without its final message — pushes
  now precede the status write.
- `time.mktime` parsed the UTC timestamp as local time, showing "Turn completed (3601s)"
  on UTC+1 machines — now `calendar.timegm`.
- `tool_result` bus events did not carry the tool name (`tool=` kwarg) — the result card
  now shows which tool completed.

---
- A `GLM_API_KEY` set in the shell made `AVIS_LLM_ENABLED` (default `"1"`) call the real
  LLM in workspace runs — 16s latency, non-deterministic tests. Workspace runs now
  default to the scripted brain (`POST …/messages` accepts `llm: true` to opt in);
  tests pin `AVIS_LLM_ENABLED=0`.
- The handoff recommendation re-appeared after approve/redirect/continue because
  `build_workspace_snapshot` re-derives it whenever the agent status is `completed` and
  the store handoff is `None`. Added a `handoff_resolved` flag set by the handoff
  endpoint and cleared on each new run, so a human decision sticks.
- Initial `tests/test_workspace.py` draft used `pytest.mark.asyncio`, which the suite
  does not use (no pytest-asyncio installed); streaming is exercised with the same
  `asyncio.run` + endpoint-function pattern as Stage One.
- `BY_ID` entries are plain dicts, not objects — test used `.name`; now reads the dict.

---

## Safety notes (PC hang question)
- Pipeline is pure in-memory CPU work: no ffmpeg, no GPU, no downloads, no disk writes.
- Bounded: 4 review-iteration cap already in `graph.py`; Phase 1 adds a hard step watchdog.
- LLM calls: 30s timeout, graceful fallback to scripted brain.
- The earlier `--yes` run aborted by the user caused no harm.