# AVIS React Workspace Frontend

Vite + React + TypeScript frontend for the agent workspace, served by the
FastAPI backend (`ui/web/server.py`) under `/workspace`.

## Build (serve from FastAPI)

```bash
npm install
npm run build        # outputs to ../static/react/
cd .. && uvicorn ui.web.server:app --port 8000
# open http://localhost:8000/workspace/strategist
```

## Dev (hot reload)

```bash
npm run dev          # http://localhost:5173/workspace/
```

`vite.config.ts` proxies `/api` to `http://localhost:8000`, so during
development run uvicorn on port 8000 alongside the Vite dev server.

## Layout (W6.6 + W6.7)

- `src/AvisWorkspace.tsx` — the workspace: **left project selector + agent
  network**, **center full-width chat** (messages, inline working row with Stop,
  approval/handoff cards, suggestions strip above composer), **right panel as
  overlay drawer** (About / Capabilities / Memory & Context / Tools & Resources
  + Past Discussions) — toggled by the panel icon, Escape closes.
- `src/components/Chat.tsx` — conversation (smart autoscroll: snap only when
  <80px from bottom), composer (enter=send, shift+enter=newline), `Markdown.tsx`
  mini renderer (no raw HTML, no new deps).
- `src/components/RightRail.tsx` — Past Discussions modal (project-scoped real
  sessions only, "No history yet.", Compact button).
- `src/avis-workspace.css` — grid: 1fr conversation, fixed overlay rail,
  `--topbar-h` var, suggestions static strip, breakpoint cleanup (no two-column
  re-declarations).
- Per-agent variation: `agents` array in `AvisWorkspace.tsx` (name, color, icon,
  role, about). Network list, resources, capabilities, memory, tools — identical
  across agents by design.
- **W6.7**: `fetchSnapshot(agentId, projectId)`, `compactSession()` in `live.ts`;
  project selector via `liveProjects` (empty state + Create); seed greetings
  removed; tool arg display `→ {tool}: {arg}`; compaction card in Conversation.
