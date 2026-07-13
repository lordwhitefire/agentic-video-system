# Repo Agent Library

This directory holds the downloaded agent MD files from the OpenCode community.
HR (Voss) reads from here when recruiting new agents via the `create_agent` tool.

## Setup

```bash
# From this directory:
git clone https://github.com/ankitmundada/awesome-opencode-subagents.git ankitmundada
git clone https://github.com/jbeck018/agents-opencode.git jbeck018
```

## What's Inside

- `ankitmundada/` — 128 agents organized in 10 categories (look in `categories/`)
- `jbeck018/` — 95 agents, flat structure

## Updating

```bash
cd ankitmundada && git pull
cd ../jbeck018 && git pull
```

HR always reads from the latest version. No rebuild needed.

## How HR Uses These Files

When Hermes says "I need a frontend developer," Voss:
1. Searches this directory for `frontend-developer.md`
2. Reads the file content
3. Optionally combines it with complementary files (e.g., `react-specialist.md`, `typescript-pro.md`)
4. Calls `create_agent` with `repo_files: ["ankitmundada/categories/01-core-development/frontend-developer.md", ...]`
5. The tool concatenates the files and writes the new agent to `.opencode/agents/<name>.md`
