# Repo Agent Library

This directory holds downloaded agent MD files from the OpenCode community.
The Recruiter reads from here when creating new agents via the `create_agent` tool.

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

The Recruiter always reads from the latest version. No rebuild needed.

## How The Recruiter Uses These Files

When you tell the Recruiter "I need a new agent for X," the Recruiter:
1. Searches this directory for relevant agent templates
2. Reads the file content
3. Optionally combines it with complementary files
4. Calls `create_agent` with `repo_files: ["ankitmundada/categories/.../agent.md", ...]`
5. The tool concatenates the files and writes the new agent to `agent/<name>.md`
