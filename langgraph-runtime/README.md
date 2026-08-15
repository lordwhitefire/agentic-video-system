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

# Web UI — graph view + live agent activity + CEO approval modal
uvicorn ui.web.server:app --port 8000
# open http://127.0.0.1:8000
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

## Tests

```bash
pip install pytest
python -m pytest tests -q        # 36 tests: laws, tools, graph, API
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