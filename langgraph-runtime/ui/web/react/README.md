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

## Layout

- `src/AvisWorkspace.tsx` — the workspace: left agent network, chat panel,
  right rail (About / Capabilities / Memory & Context / Tools & Resources).
- `src/avis-workspace.css` — pixel-accurate styling (from the AVIS spec).
- Per-agent variation is driven by the `agents` array in
  `AvisWorkspace.tsx` (name, color, icon, role, about, greeting). Everything
  else — network list, resources, capabilities, memory, tools — is identical
  across agents by design.
