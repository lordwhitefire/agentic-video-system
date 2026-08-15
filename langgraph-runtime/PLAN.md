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

## Safety notes (PC hang question)
- Pipeline is pure in-memory CPU work: no ffmpeg, no GPU, no downloads, no disk writes.
- Bounded: 4 review-iteration cap already in `graph.py`; Phase 1 adds a hard step watchdog.
- LLM calls: 30s timeout, graceful fallback to scripted brain.
- The earlier `--yes` run aborted by the user caused no harm.