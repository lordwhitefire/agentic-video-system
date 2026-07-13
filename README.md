# Agentic Video System

A reference-driven, script-driven, audio-as-master video editing system built for Agenticine (OpenCode fork). 17 agents across 5 departments, 12 laws, WebForge-style agent template, custom skills, human-in-the-loop sourcing.

## Quick Start

### Option A — Isolated install (recommended)

```bash
# Clone into a dedicated config directory
git clone https://github.com/lordwhitefire/agentic-video-system.git ~/.config-agenticine/opencode

# Create an alias
echo 'alias agenticine="XDG_CONFIG_HOME=~/.config-agenticine opencode"' >> ~/.bashrc
source ~/.bashrc

# Run it
agenticine
```

### Option B — Replace stock OpenCode

```bash
git clone https://github.com/lordwhitefire/agentic-video-system.git ~/.config/opencode
opencode
```

See `SETUP.md` for troubleshooting and details.

## Architecture

```
AGENT (who you are + what you do)
    ↓ uses
CUSTOM SKILLS (how to think about the task — behavioral)
    ↓ uses
TOOL SKILLS (how to operate specific tools — execution knowledge)
    ↓ executes with
TOOLS (the actual MCP servers, ffmpeg, whisper, etc.)
```

**Agents follow the WebForge template.** Each agent file contains:
- Full YAML frontmatter (description, name, mode, temperature, steps: 35, permission block with all 24 keys)
- Full body (13 mandatory sections: Purpose, Identity, When Invoked, Expertise, Capabilities, Workflow, Communication, Escalation Rules, Boundaries, Key Distinctions, Example Interactions, Reference)

**Skills are separate.** Skills live in `skills/custom/` (behavioral) and `skills/tools/` (execution). An agent references its skills but does not contain them. This lets you swap skills without touching the agent, and test agents with different skills.

## The Org Chart — 3 Tiers, 5 Departments

```
                    YOU (CEO)
                        |
        ┌───────────┬───┴───┬───────────┬───────────┐
        |           |       |           |           |
    Strategy     Audio  Production    Quality    Personnel
  (Strategist) (Audio   (Editor)   (Reviewer)  (Recruiter)
        |       Lead)       |           |           |
   Analyzer       |     Graphics   Watcher/     (creates
   Planner       TTS   Animation   Blocker       agents
   Researcher         Animated   Investigator   on demand)
                      Graphics
                      Video Effects
                      Clips
                      Images
```

### Tier 1: CEO (you)
You make decisions, approve work, talk to the 5 department heads. The picker shows exactly 5 agents — one per department.

### Tier 2: Heads (run a department, `mode: primary`)
- **Strategist** — head of Strategy, manages Analyzer, Planner, Researcher
- **Audio Lead** — head of Audio, manages TTS
- **Editor** — head of Production, manages 6 visual agents, assembles the final video
- **Reviewer** — head of Quality, manages Watcher/Blocker and Investigator, final PASS/REVISE/BRANCH decision
- **Recruiter** — head of Personnel, the ONLY agent that can create new agents

### Tier 3: Workers (do the specialist work, `mode: subagent`)
Report to their department head. Have `task: deny` (cannot spawn other agents). Have `verify_work: deny` (cannot sign off on others' work). Invisible in the picker — spawned by their head.

## The 17 Agents

### Strategy Department (head: Strategist)
| Agent | Mode | What It Does |
|-------|------|-------------|
| strategist | primary | **HEAD** — manages Analyzer, Planner, Researcher |
| analyzer | subagent | Extracts template from reference video |
| planner | subagent | Writes tagged script on user's topic |
| researcher | subagent | Produces resource.md sourcing manifest |

### Audio Department (head: Audio Lead)
| Agent | Mode | What It Does |
|-------|------|-------------|
| audio-lead | primary | **HEAD** — manages TTS |
| tts | subagent | Generates ONE continuous master audio track + timestamps |

### Production Department (head: Editor)
| Agent | Mode | What It Does |
|-------|------|-------------|
| editor | primary | **HEAD** — delegates to 6 visual agents, assembles final video |
| graphics | subagent | Creates static graphics (with approval loop) |
| animation | subagent | Creates full motion graphics (with approval loop) |
| animated-graphics | subagent | Creates sequential reveal graphics timed to narration |
| video-effects | subagent | Builds video effects as reusable pieces |
| clips | subagent | Prepares sourced clips (cut, zoom, speed) |
| images | subagent | Prepares sourced images (overlay, side-by-side) |

### Quality Department (head: Reviewer)
| Agent | Mode | What It Does |
|-------|------|-------------|
| reviewer | primary | **HEAD** — quality gate, PASS/REVISE/BRANCH decision |
| watcher-blocker | subagent | Inference detector — blocks guesses in real-time |
| investigator | subagent | Root cause analyst — finds WHY something failed |

### Personnel Department (head: Recruiter)
| Agent | Mode | What It Does |
|-------|------|-------------|
| recruiter | primary | **HEAD** — the ONLY agent with `create_agent` tool |

## How The Approval Loop Works (For Visual Agents)

Every visual agent (Graphics, Animation, Animated Graphics, Video Effects, Clips, Images) follows this pattern:

1. **Show examples first** — before creating anything, show the user 3 reference designs or test renders
2. **Explain the plan** — in plain language, not technical jargon
3. **Go back and forth** — user gives feedback, agent adjusts, shows again
4. **Lock a standard** — once the user approves a style, use that SAME standard for all similar visuals
5. **Produce the batch** — only after the standard is locked

This is built into every visual agent's IDENTITY, not just as a workflow step. The user is not a design expert — the agent teaches what is possible by showing, not explaining theory.

## Skill Classification

Skills are split into two types:

### Custom Skills (behavioral) — `skills/custom/`
Teach an agent HOW TO THINK about its task. 3 completed:
- `script-driven-template-extraction` (Analyzer)
- `script-driven-visual-assignment` (Planner)
- `resource-md-generation` (Researcher)

12 more are marked TO BUILD in `skills/README.md`.

### Tool Skills (execution) — `skills/tools/`
Teach an agent HOW TO OPERATE a specific tool. The registry is at `skills/tools/skills-registry.md`.

See `skills/README.md` for the full classification.

## Testing Agents Individually

See `TESTING.md` for detailed instructions. The testing loop:
1. Pick a head from the picker (e.g., Editor)
2. Tell the head to test a specific worker (e.g., "Test the Graphics agent with this task")
3. The head spawns the worker, reports back
4. Evaluate the result, iterate

## The 12 Laws

| # | Law | Enforced By |
|---|-----|-------------|
| 1 | No inference | Source citation + question tool |
| 2 | No inference about inference | Source citation requirement |
| 3 | No silent substitution | safe_edit content check |
| 4 | No auto-correction | safe_edit flagging |
| 5 | No carrying over | Workflow verification steps |
| 6 | No effect substitution | verify_work checklist |
| 7 | No silent engine switching | status logging |
| 8 | Graphics must contain images | verify_work check |
| 9 | No image reusing | memory tracking |
| 10 | No watermarked images | verify_work VLM check |
| 11 | No silent runtime swap | status logging |
| 12 | No assuming context | recall before acting |

See `laws/` for the full text of each law.

## Custom Tools (Ported From WebForge)

The `tool/` directory contains actual TypeScript code — real working tools that OpenCode auto-discovers and executes. These are NOT just documentation; they are the enforcement layer for the 12 laws.

| Tool | What It Does |
|------|-------------|
| `safe_edit` | Edits files with 300-line limit, inference scanning, auto-logging |
| `safe_bash` | Runs commands with dangerous-command blocking, auto-logging |
| `memory` | Reads/writes to project memory (`.agenticine/memory/`) |
| `registry` | Looks up agent info and reporting relationships |
| `status` | Logs agent activity to shared work log |
| `report_metrics` | Workers report task metrics before sign-off |
| `verify_work` | Superiors sign off on subordinates' work |
| `create_agent` | Recruiter creates new agent files (only agent with this tool) |
| `update_plan` | Heads update the shared project plan |
| `revoke` | Strips permissions from law-violating agents |
| `activate_project` | Manages which project is active (survives compaction) |
| `edit` / `bash` / `write` | Override built-in tools with permission checks |

The `plugin/` directory contains the guardrails plugin — a pre-tool-call hook that intercepts tool calls BEFORE they execute, checks for inference patterns ("I assume", "probably", "I think"), and blocks violations.

The `project-template/` directory contains template files that `activate_project` copies into new projects (plan.md, memory folders, mailbox, status, etc.).

**All paths adapted:** `~/.config/webforge/` → `~/.config-agenticine/`, `.webforge/` → `.agenticine/`, all references renamed from WebForge to Agenticine.

## Directory Structure

```
agentic-video-system/
├── README.md
├── SETUP.md
├── TESTING.md
├── .gitignore
├── opencode.json          ← main config (default_agent, disables, MCPs)
├── agent/                 ← 17 agent files (auto-discovered)
│   ├── strategist.md      ← HEAD of Strategy (primary)
│   ├── analyzer.md
│   ├── planner.md
│   ├── researcher.md
│   ├── audio-lead.md      ← HEAD of Audio (primary)
│   ├── tts.md
│   ├── editor.md          ← HEAD of Production (primary)
│   ├── graphics.md
│   ├── animation.md
│   ├── animated-graphics.md
│   ├── video-effects.md
│   ├── clips.md
│   ├── images.md
│   ├── reviewer.md        ← HEAD of Quality (primary)
│   ├── watcher-blocker.md
│   ├── investigator.md
│   └── recruiter.md       ← HEAD of Personnel (primary)
├── tool/                  ← 15 TypeScript tool files (auto-discovered)
│   ├── safe_edit.ts       ← file editing with law enforcement
│   ├── safe_bash.ts       ← command running with blocking
│   ├── memory.ts          ← project memory read/write
│   ├── registry.ts        ← agent lookup
│   ├── status.ts          ← activity logging
│   ├── report_metrics.ts  ← worker metrics
│   ├── verify_work.ts     ← superior sign-off
│   ├── create_agent.ts    ← agent creation (Recruiter only)
│   ├── update_plan.ts     ← plan updates (heads only)
│   ├── revoke.ts          ← permission stripping
│   ├── activate_project.ts ← project switching
│   ├── edit.ts, bash.ts, write.ts ← built-in overrides
│   └── lib/               ← shared helpers (permission-check, metrics, agents-json)
├── plugin/                ← guardrails plugin (auto-discovered)
│   ├── guardrails.ts      ← pre-tool-call inference blocker
│   └── lib/patterns.ts    ← inference pattern database
├── project-template/      ← templates copied to new projects
│   ├── plan.md
│   ├── PROJECT.md
│   ├── agents.json        ← our 17 agents (org chart)
│   ├── memory/            ← STATE.md, work-log.md, etc.
│   ├── mailbox/
│   └── status/
├── skills/
│   ├── README.md
│   ├── custom/            ← behavioral skills (how to think)
│   └── tools/             ← execution skills registry
├── laws/                  ← 12 law files
├── config/                ← app-specific configs
├── guidelines/
├── system/
├── templates/
└── tools/                 ← external tools registry (documentation)
```

## What's Done vs What's Left

### Done
- 17 agent files (5 heads + 12 workers, WebForge template)
- 5 departments, each with a head
- 12 law files
- 3 custom skills (thinking layer)
- Config for Agenticine (disables built-in agents, 3 MCP servers)
- Setup, Testing, and README guides
- Human sourcing guideline
- Tools registry, skills registry, system overview, visual types

### To Build
- 12 custom skills (TTS, 6 visual agents, Editor, Reviewer, Watcher/Blocker, Investigator, approval-loop-protocol)
- Tool skills installation (from OpenMontage etc.)
- Actual testing of each agent with its skill
- WebForge-style tools (safe_edit, safe_bash, memory, registry, status, report_metrics, verify_work, create_agent, update_plan, revoke, activate_project)
