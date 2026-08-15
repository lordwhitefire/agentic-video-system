# Workspace Rebuild Plan (simple terms)

We are rebuilding the agent workspace so it feels like talking to an
assistant, not running a pipeline dashboard.

## The one idea everything hangs on

**Plan and Build are interaction modes, not workflow stages.**
Agents are NOT assigned a predefined sequence of actions.

It is not:

```
Plan → Strategy → Route → Build → Test
```

It is:

```
Human
  ↕
Agent
  ↕
Tools / files / execution
```

And when another agent is useful:

```
Human
  ↕
Agent A
  ↓  "I recommend Agent B"
  ↓
Human approval
  ↓
Agent B
```

**The human is the governance layer.**

## What we're keeping (don't touch)

- The agent registry (all 17 AVIS agents, their identities, capabilities).
- The real execution engine — agents really do work, we don't fake it.
- The dashboard overview page (`/`), the API, and all existing tests that
  still make sense.

## What we're changing (the workspace screen at /workspace/<agent>)

### 1. One conversation, everything inline

- Today the right side is a separate "Live Activity" panel.
- New: ALL events appear inside the single chat — agent messages,
  **reasoning/progress summaries** (NOT hidden chain-of-thought), tool calls,
  tool results, approvals, errors.
- **No activity tab, no separate execution panel, no second feed. Ever.**

Important: "thinking" means **agent-visible reasoning/progress summaries** —
what the agent intends to inspect, why it's taking an action, what it
discovered, and what it plans to do next. We never expose a private
chain-of-thought transcript.

Example:

```
VIDEO STRATEGY AGENT

I'm going to inspect the existing video configuration first.
I want to understand how the current pipeline handles
reference assets before I make any changes.

[Read file]
avis/config/video.yaml
```

### 2. One normalized chronological event stream

Everything in the chat comes from ONE array, in chronological order:

```
conversation[]
  ├── user_message
  ├── assistant_message
  ├── reasoning_summary
  ├── tool_call
  ├── tool_result
  ├── approval_request
  ├── approval_result
  ├── error
  └── status
```

We must NOT secretly keep separate `messages`, `activity`, and `toolLogs`
state and merge them visually. One stream. The renderer just styles each
event type differently.

### 3. Plan / Build mode

- A clear switch in the top bar: **Plan** | **Build**.
- Both modes are conversational (agent talks, asks questions, plans).
- **Plan Mode has NO execution authority.** The runtime must REJECT/block
  tool calls, file writes, file modifications, and command execution from a
  Plan-mode run. Not "instructed not to" — physically blocked.
- **Build Mode:** The agent MAY execute tools, files, and commands within its
  granted permissions. It stays conversational and explains consequential
  intended actions before executing them. The human can interrupt at any time.
- The user decides whether they want to plan first — there is NO mandatory
  planning phase before Build. Plan and Build are modes of interaction, not
  stages in a hard-coded workflow.
- Sending a message never auto-enters Build Mode. Switching is explicit.

### 4. Conversational greeting

- Saying "Hello" (or opening an empty workspace) gets a friendly reply like:
  "Hello. I'm the Video Strategy Agent. What are we working on today?"
- NO automatic plan, routing, project creation, or tool use on greeting.
- **Zero execution** — a greeting produces a conversational response only.

### 5. No hard-coded workflow

- Remove automatic "next agent" handoff chains and department routing from
  the workspace behavior.
- If the agent thinks another agent should help, it proposes it inline and
  asks your permission. You decide.
- **Handoff approval is enforced by the runtime, not just displayed by the
  UI.** If the human has not approved, the runtime physically blocks the
  handoff from invoking the other agent. No "I recommend Visual Agent →
  [Approve]" that secretly switches anyway.
- The agent never assumes a project or invents next steps.

### 6. Right panel = about the agent

- The right side becomes context: About, Capabilities, Memory & Context,
  Tools & Resources — all from the real registry/state.
- Never an activity feed.

### 7. Interrupt / stop

Two separate concepts:

- **While working, the user can keep typing / interacting where supported.**
- **Stop** is an explicit operation that actually cancels/interrupts the
  runtime execution — not just a UI button that hides the stream.

After cancellation, the UI shows the REAL execution state. The stop message
comes from actual execution state (never claims no changes occurred unless
the runtime confirms that).

## What I will do first (Step 1)

1. Read the current `avis/studio.py`, `ui/web/server.py`, and
   `ui/web/static/workspace.html` carefully.
2. Write the rebuild so the registry + engine stay; only the workspace
   interaction model changes.

## Test plan

- Existing 59 tests must stay green (or be updated only where the old
  auto-routing behavior is intentionally removed).
- The four critical runtime tests:

  1. **Plan-mode run → tool execution is rejected** (runtime blocks it).
  2. **Build-mode run → permitted tool executes.**
  3. **"Hello" → only a conversational response; zero execution.**
  4. **Unauthorized handoff → runtime blocks it until human approval.**

These test the runtime, not the UI.

## Out of scope (don't do)

- No new workflow engine, orchestration graph, or automatic routing rules.
- No multi-agent chat room.
- No fake events, fake tool calls, or invented projects.
- No React/Tailwind build toolchain (the project has none — we keep the
  single-file static HTML approach, which the spec allows).
