# Agentic Video System

A reference-driven, script-driven, audio-as-master video editing system built for Agenticine (OpenCode fork). 15 agents across 5 departments, 12 laws, WebForge-style agent template, custom skills, human-in-the-loop sourcing.

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
   (no head)   (no head)  (Editor)   (Reviewer)  (Recruiter)
        |           |       |           |           |
   Analyzer       TTS    Graphics   Watcher/     (creates
   Planner              Animation   Blocker       agents
   Researcher           Animated   Investigator   on demand)
                        Graphics
                        Video Effects
                        Clips
                        Images
```

### Tier 1: CEO (you)
You make decisions, approve work, talk to department heads and solo agents directly. No coordinator agent — you control the pipeline.

### Tier 2: Heads (run a department)
- **Editor** — head of Production, delegates to 6 visual agents, assembles the final video
- **Reviewer** — head of Quality, final PASS/REVISE/BRANCH decision, manages Watcher/Blocker and Investigator
- **Recruiter** — solo head of Personnel, the ONLY agent that can create new agents

### Tier 3: Workers (do the specialist work)
Report to their department head. Have `task: deny` (cannot spawn other agents). Have `verify_work: deny` (cannot sign off on others' work).

## The 15 Agents

### Strategy Department (no head — sequential pipeline)
| # | Agent | What It Does |
|---|-------|-------------|
| 01 | Analyzer | Extracts template from reference video (script-first, 9 visual types, decision rules) |
| 02 | Planner | Writes tagged script on user's topic (script first, visuals second) |
| 03 | Researcher | Produces resource.md sourcing manifest (does NOT source — human does) |

### Audio Department (no head — single agent)
| # | Agent | What It Does |
|---|-------|-------------|
| 04 | TTS | Generates ONE continuous master audio track + word-level timestamps |

### Production Department (Editor is head)
| # | Agent | What It Does |
|---|-------|-------------|
| 05 | Editor | **HEAD** — delegates to 6 visual agents, assembles final video (audio is master) |
| 06 | Graphics | Creates static graphics (with user approval loop, shows examples first) |
| 07 | Animation | Creates full motion graphics (with user approval loop) |
| 08 | Animated Graphics | Creates sequential reveal graphics timed to narration |
| 09 | Video Effects | Builds video effects as reusable pieces (does NOT apply to clips) |
| 10 | Clips | Prepares sourced clips (cut, zoom, speed, apply effects TO clips) |
| 11 | Images | Prepares sourced images (overlay, side-by-side, blur, crop) |

### Quality Department (Reviewer is head)
| # | Agent | What It Does |
|---|-------|-------------|
| 12 | Reviewer | **HEAD** — quality gate, 7 fidelity checks, PASS/REVISE/BRANCH decision |
| 13 | Watcher/Blocker | Inference detector — blocks guesses in real-time (Law 1 enforcer) |
| 14 | Investigator | Root cause analyst — finds WHY something failed (does NOT fix it) |

### Personnel Department (Recruiter is solo head)
| # | Agent | What It Does |
|---|-------|-------------|
| 15 | Recruiter | **HEAD** — the ONLY agent with `create_agent` tool. Builds new agents on demand. |

## How The Approval Loop Works (For Visual Agents 06-11)

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
1. Pick an agent
2. Research the craft (YouTube, tutorials)
3. Write or update the custom skill
4. Give the agent a task + the skill
5. Evaluate the result
6. Modify the skill (or agent) based on what you saw
7. Repeat until satisfied

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

## Directory Structure

```
agentic-video-system/
├── README.md              ← this file
├── SETUP.md               ← detailed setup instructions
├── TESTING.md             ← how to test agents individually
├── .gitignore
├── opencode.json          ← main config: editor=default, disables build/plan, MCP servers
├── agent/                 ← 15 agent files (WebForge template, auto-discovered)
│   ├── 01-analyzer.md
│   ├── 02-planner.md
│   ├── 03-researcher.md
│   ├── 04-tts.md
│   ├── 05-editor.md       ← HEAD of Production (default agent)
│   ├── 06-graphics.md
│   ├── 07-animation.md
│   ├── 08-animated-graphics.md
│   ├── 09-video-effects.md
│   ├── 10-clips.md
│   ├── 11-images.md
│   ├── 12-reviewer.md     ← HEAD of Quality
│   ├── 13-watcher-blocker.md
│   ├── 14-investigator.md
│   └── 15-recruiter.md    ← HEAD of Personnel
├── skills/
│   ├── README.md          ← skill classification
│   ├── custom/            ← behavioral skills (how to think)
│   └── tools/             ← execution skills (how to operate)
│       └── skills-registry.md
├── laws/                  ← 12 law files (the constitution)
├── config/
│   ├── voice-profile.json ← TTS engine config
│   └── research-keys.json ← API keys template
├── guidelines/            ← human reference documents
│   └── footage-sourcing-guideline.md
├── system/                ← system documentation
│   ├── system-overview.md
│   └── visual-types.md
├── templates/             ← video editing style templates
│   └── README.md
└── tools/                 ← tools registry
    └── tools-registry.md
```

## What's Done vs What's Left

### Done
- 15 agent files (WebForge template — full YAML frontmatter + 13 body sections)
- 5 departments, 3 tiers
- 12 law files
- 3 custom skills (thinking layer: Analyzer, Planner, Researcher)
- Config for AgenticSign (disables built-in agents)
- Setup, Testing, and README guides
- Human sourcing guideline
- Tools registry, skills registry, system overview, visual types, templates README
- Recruiter agent (can create new agents on demand)

### To Build
- 12 custom skills (TTS, 6 visual agents, Editor, Reviewer, Watcher/Blocker, Investigator, approval-loop-protocol)
- Tool skills installation (from OpenMontage etc.)
- Actual testing of each agent with its skill
- WebForge-style tools (safe_edit, safe_bash, memory, registry, status, report_metrics, verify_work, create_agent, update_plan, revoke, activate_project)
