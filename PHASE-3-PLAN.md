# Phase 3 — Build the Runtime / Orchestrator

**Goal:** Write the Python code that loads the 8 agents, manages the agent loop, handles the work tree, routes messages between agents, implements the Watcher/Blocker, and persists state across Colab sessions.

This is where the system becomes alive. Phases 0–2 gave us the blueprints (agent definitions) and the parts (tools + skills). Phase 3 builds the engine that makes them work together.

**Last updated:** 2026-07-09
**Status:** Planning — read this, then we start building.

---

## The Runtime's Job

The runtime is the conductor. It:

1. **Loads agents** — reads each agent's markdown file, parses the YAML frontmatter (description, mode, tools, temperature, steps) and the system prompt body, instantiates an LLM client with that prompt.
2. **Manages the loop** — each agent runs perceive → reason → act → observe → reflect → decide, repeatedly, until it stops or is blocked.
3. **Routes messages** — agents communicate via the JSON protocols defined in their markdown files (e.g., `blueprint_ready`, `inference_risk`, `agent_blocked`). The runtime is the message bus.
4. **Handles the work tree** — nodes (project states), branches (forks), HEAD (current preview). Persists to Google Drive.
5. **Enforces Law 1** — the Watcher/Blocker hook intercepts every tool call, runs the 8 inference detection patterns, can revoke tool access mid-run.
6. **Surfaces to the user** — flags, blocks, review requests, voice sample demands all route to you. You respond, the runtime routes your response back.
7. **Persists state** — Colab sessions die. The runtime saves all state to Google Drive so a new session can resume where the old one left off.

---

## Architecture Decisions (Locked In)

### Language: Python

Python for the runtime. Reasons:
- All analysis tools (Whisper, PySceneDetect, OpenCV, Deep SORT) are Python-native.
- Coqui TTS is Python.
- MCP Python client library is installed.
- Colab's system Python is 3.12 — the runtime runs on system Python.
- The Coqui venv (Python 3.11) is invoked via subprocess when Coqui is needed.

### LLM Client: Multi-model (user's choice per agent)

The runtime supports multiple LLM providers because the user explicitly said "I use different models." Each agent's frontmatter can specify which model to use. Initial supported providers:
- OpenAI (GPT-4, GPT-4o, etc.) — via `openai` Python package
- Anthropic (Claude) — via `anthropic` Python package
- Google (Gemini) — via `google-generativeai` package
- Local models (Ollama) — via `ollama` package or HTTP

The runtime reads API keys from `config/research-keys.json` (already created in Script 8). User can add keys there as needed.

### State Persistence: Google Drive

All state persists to Google Drive under `config/runtime-state/`:
- `work-tree.json` — the work tree (nodes, branches, HEAD)
- `agent-state/{agent-id}.json` — per-agent working memory, current inputs/outputs
- `message-log.jsonl` — append-only log of all inter-agent messages
- `block-log.jsonl` — append-only log of all Watcher/Blocker actions
- `current-run.json` — the active run's metadata (reference video path, topic, current phase)

### MCP Integration: Spawn-on-demand

MCP servers are NOT daemons. The runtime spawns them on-demand via stdio JSON-RPC when an agent needs a tool. Each server has a known invocation command (recorded in `config/mcp-registry.json` — to be created in Phase 3). The runtime:
1. Receives a tool call request from an agent.
2. Looks up which MCP server provides that tool.
3. Spawns the server (if not already running).
4. Sends the tool call via JSON-RPC.
5. Returns the result to the agent.
6. Keeps the server alive for the session (reuses for subsequent calls).

### Watcher/Blocker: Hook Layer

The Watcher/Blocker is implemented as a wrapper around every tool call. Before a tool call executes:
1. The runtime sends the call details (agent ID, tool name, arguments, agent's reasoning) to the Watcher/Blocker module.
2. The Watcher/Blocker runs the 8 inference detection patterns.
3. If a positive match: revoke the agent's tools, freeze state, trigger the Investigator, notify the user.
4. If an ambiguous signal: route to the Investigator for review.
5. If clean: let the tool call proceed.

---

## Phase 3 Sub-tasks

### 3.1 — Project structure and config files
- Create `runtime/` directory in the project folder.
- Create `config/mcp-registry.json` — maps each MCP server to its invocation command.
- Create `config/agent-models.json` — maps each agent to its LLM model + provider.
- Create `config/runtime-state/` directory for persistence.

### 3.2 — Agent loader
- Python module that reads each agent's markdown file.
- Parses YAML frontmatter (description, mode, tools, temperature, steps).
- Extracts the system prompt body (everything after the frontmatter).
- Returns an `Agent` object with: id, system_prompt, tools_config, temperature, max_steps, model_config.

### 3.3 — LLM client abstraction
- Python class that wraps multiple LLM providers (OpenAI, Anthropic, Google, Ollama).
- Single interface: `client.complete(system_prompt, messages, temperature, max_tokens)`.
- Reads API keys from `config/research-keys.json`.
- Routes to the correct provider based on agent's model_config.

### 3.4 — Tool dispatcher
- Python module that routes tool calls to the correct MCP server.
- Spawns MCP servers on-demand via stdio JSON-RPC.
- Caches running servers for the session.
- Returns tool results to the agent.

### 3.5 — Work tree
- Python class that manages nodes, branches, HEAD.
- Each node = a project state (blueprint + script + manifest + asset bundle + cut).
- Edges = operations (analyzed, planned, edited, reviewed).
- Branches = alternative execution paths.
- Persists to `config/runtime-state/work-tree.json`.

### 3.6 — Message bus
- Python module that routes JSON messages between agents.
- Each agent has an inbox (queue of messages).
- The runtime processes messages in order, routes to the correct agent.
- Logs every message to `config/runtime-state/message-log.jsonl`.

### 3.7 — Watcher/Blocker hook
- Python module that wraps every tool call.
- Implements the 8 inference detection patterns from `agents/07-watcher-blocker.md`.
- On positive detection: revoke tools, freeze state, trigger Investigator, notify user.
- On ambiguous signal: route to Investigator.
- Logs every action to `config/runtime-state/block-log.jsonl`.

### 3.8 — Investigator module
- Python module that takes over when an agent is blocked.
- Reads the blocked agent's frozen state, the Watcher/Blocker's log, upstream artifacts.
- Classifies root cause (5 categories from `agents/08-investigator.md`).
- Proposes remediation options.
- Reports to user via the user interaction layer.

### 3.9 — User interaction layer
- Python module that surfaces flags, blocks, review requests, voice sample demands to the user.
- In Colab: displays as cell output (formatted text + prompts).
- Accepts user input (text responses, file uploads for voice samples).
- Routes user responses back to the correct agent or the Investigator.

### 3.10 — Persistence layer
- Python module that saves/loads all state to Google Drive.
- On run start: load `current-run.json`, `work-tree.json`, `agent-state/`.
- On state change: save immediately (Colab can die anytime).
- On run resume: detect incomplete run, offer to resume or start fresh.

### 3.11 — Main orchestrator
- Python script that ties everything together.
- Reads the user's request (reference video + topic).
- Runs the flow: analyze → plan → research → execute → review → corrections → deliver.
- Coordinates agents, handles pauses (e.g., waiting for user to source assets).
- This is the entry point — the user runs this script to start a video edit.

### 3.12 — End-to-end test
- Pick a simple test reference video (30s commentary clip).
- Run the full flow end-to-end.
- Document every crack found.
- Iterate.

---

## Build Order

We'll build in this order, one module at a time, testing each before moving on:

```
3.1  Project structure & config files          ← START HERE
3.2  Agent loader
3.3  LLM client abstraction
3.4  Tool dispatcher
3.5  Work tree
3.6  Message bus
3.7  Watcher/Blocker hook
3.8  Investigator module
3.9  User interaction layer
3.10 Persistence layer
3.11 Main orchestrator
3.12 End-to-end test
```

Each module gets its own Python file in `runtime/`. We'll write them one at a time, test in Colab, fix issues, then move to the next.

---

## What I need from you before we start building

Three decisions:

### 1. Which LLM providers do you want to support initially?

The runtime is multi-model, but we need to start somewhere. Options:
- **OpenAI only** (simplest — you probably already have an API key)
- **OpenAI + Anthropic** (covers GPT-4 and Claude)
- **OpenAI + Anthropic + Google** (covers GPT-4, Claude, Gemini)
- **All of the above + Ollama** (for local models)

### 2. Which model does each agent use by default?

Different agents have different needs. The Analyzer needs strong vision (GPT-4o or Claude 3.5 Sonnet). The Editor needs good code generation. The Watcher/Blocker needs fast inference. Options:
- **All agents use the same model** (simplest — pick one, e.g., GPT-4o)
- **Each agent has a specific model** (I'll propose defaults based on each agent's needs)
- **User picks per run** (flexible but more setup each time)

### 3. Do you have API keys ready?

For the providers you chose in question 1, do you have API keys? You'll add them to `config/research-keys.json` (already created). We can start building the runtime before keys are added — the LLM client will just fail when we test it until keys are in place.

---

## What's next

Answer those three questions. Then I start writing the runtime, beginning with sub-task 3.1 (project structure and config files). We'll go one module at a time, just like the install scripts — write, test in Colab, fix, move on.

This is the build phase. It'll take longer than Phase 2 (each module is real Python code, not just install scripts). But by the end, you'll have a working agent runtime that can actually edit videos.

---

## Estimated timeline

Rough estimate, assuming we go one module per session:
- 3.1–3.4 (loader, LLM client, tool dispatcher): 2–3 sessions
- 3.5–3.6 (work tree, message bus): 2 sessions
- 3.7–3.8 (Watcher/Blocker, Investigator): 2 sessions
- 3.9–3.10 (user interaction, persistence): 1–2 sessions
- 3.11 (main orchestrator): 1–2 sessions
- 3.12 (end-to-end test + fixes): 2–3 sessions

Total: ~12–15 sessions for Phase 3. Could be faster if modules click, slower if we hit integration issues.

After Phase 3: Phase 4 (manual walkthrough with a real reference video), Phase 5 (iterate on cracks), Phase 6 (scale test), Phase 7 (polish).

We're getting close to a working system.
