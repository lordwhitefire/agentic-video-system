# Agentic Video System

A reference-driven, script-driven, audio-as-master video editing system built for AgenticSign (OpenCode fork). 14 agents, 12 laws, custom skills, human-in-the-loop sourcing.

## Quick Start

```bash
# 1. Clone this repo
cd ~
git clone https://github.com/lordwhitefire/agentic-video-system.git
cd agentic-video-system

# 2. Launch AgenticSign from this directory
agentic-sign
```

When AgenticSign launches, you will see ONLY the 14 agents from this repo. OpenCode's built-in agents are disabled in `config/agentic-sign.json`.

For detailed setup (including global config at `/home/lordwhitefire/.config-agenticine`), see `SETUP.md`.

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

**Agents are lean.** Each agent file contains only:
- Who the agent is (identity)
- What the agent does (responsibility)
- What the agent does NOT do (boundaries)
- Which skills it uses (referenced, not embedded)

**Skills are separate.** Skills live in `skills/custom/` (behavioral) and `skills/tools/` (execution). An agent references its skills but does not contain them. This lets you swap skills without touching the agent, and test agents with different skills.

## The 14 Agents

### Thinking Layer (plan the video)
| # | Agent | What It Does |
|---|-------|-------------|
| 01 | Analyzer | Extracts template from reference video |
| 02 | Planner | Writes tagged script on user's topic |
| 03 | Researcher | Produces resource.md sourcing manifest |

### Audio Layer (the master track)
| # | Agent | What It Does |
|---|-------|-------------|
| 04 | TTS | Generates continuous audio + word-level timestamps |

### Visual Preparation Layer (create/prepare every visual)
| # | Agent | What It Does |
|---|-------|-------------|
| 05 | Graphics | Creates static graphics |
| 06 | Animation | Creates full motion graphics |
| 07 | Animated Graphics | Creates sequential reveal graphics |
| 08 | Video Effects | Builds video effects as reusable pieces |
| 09 | Clips | Prepares sourced clips (cut, zoom, speed) |
| 10 | Images | Prepares sourced images (overlay, side-by-side) |

### Assembly Layer (put it together)
| # | Agent | What It Does |
|---|-------|-------------|
| 11 | Editor | Head of editing department, delegates + assembles |

### Enforcement Layer (keep it honest)
| # | Agent | What It Does |
|---|-------|-------------|
| 12 | Reviewer | Quality gate, 7 fidelity checks |
| 13 | Watcher/Blocker | Inference detector, blocks guesses |
| 14 | Investigator | Root cause analyst when things fail |

## Skill Classification

Skills are split into two types. This separation is critical.

### Custom Skills (behavioral)
These teach an agent HOW TO THINK about its task. They are workflow-specific, written by us, and live in `skills/custom/`. Examples:
- `script-driven-template-extraction` — how the Analyzer breaks down a reference
- `script-driven-visual-assignment` — how the Planner tags a script
- `resource-md-generation` — how the Researcher writes the manifest
- `approval-loop-protocol` — how visual agents collaborate with the user (TO BE BUILT)

### Tool Skills (execution)
These teach an agent HOW TO OPERATE a specific tool. They come from skill repos like OpenMontage (1039 skills) and others. They live in `skills/tools/`. The registry is at `skills/tools/skills-registry.md`.

An agent needs BOTH: custom skills tell it what workflow to follow, tool skills tell it how to execute each step.

See `skills/README.md` for the full classification.

## Testing Agents Individually

This repo is structured so you can test one agent at a time without running the whole pipeline. See `TESTING.md` for detailed instructions.

The testing loop:
1. Pick an agent
2. Research the craft (YouTube, tutorials)
3. Write or update the custom skill
4. Give the agent a task + the skill
5. Evaluate the result
6. Modify the skill (or agent) based on what you saw
7. Repeat until satisfied

## The 12 Laws

The laws are the constitution. Every agent obeys them. See `laws/` for the full text.

1. No Inference
2. No Inference About Inference
3. No Silent Substitution
4. No Auto-Correction
5. No Carrying Over
6. No Effect Substitution
7. No Silent Engine Switching
8. Graphics Must Contain Images
9. No Image Reusing
10. No Watermarked Images
11. No Silent Runtime Swap
12. No Assuming Context

## Directory Structure

```
agentic-video-system/
├── README.md              ← this file
├── SETUP.md               ← detailed setup instructions
├── TESTING.md             ← how to test agents individually
├── .gitignore
├── agents/                ← 14 agent files (WHO + WHAT only)
├── skills/
│   ├── README.md          ← skill classification
│   ├── custom/            ← behavioral skills (how to think)
│   └── tools/             ← execution skills (how to operate)
│       └── skills-registry.md
├── laws/                  ← 12 law files (the constitution)
├── config/
│   ├── agentic-sign.json  ← config that disables built-in agents
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

## Disabling OpenCode's Built-In Agents

The config at `config/agentic-sign.json` sets `disable_built_in_agents: true`. When you use AgenticSign with this config, you will ONLY see the 14 agents from this repo. OpenCode's built-in agents (engineer, planner, etc.) will not appear.

If your AgenticSign build uses a different config key, see `SETUP.md` → Troubleshooting for alternatives.

## What's Done vs What's Left

### Done
- 14 agent files (WHO + WHAT for each)
- 12 law files
- 3 custom skills (thinking layer: Analyzer, Planner, Researcher)
- Config for AgenticSign (disables built-in agents)
- Setup, Testing, and README guides
- Human sourcing guideline
- Tools registry, skills registry, system overview, visual types, templates README

### To Build
- 12 custom skills (TTS, 6 visual agents, Editor, Reviewer, Watcher/Blocker, Investigator, approval-loop-protocol)
- Tool skills installation (from OpenMontage etc.)
- Actual testing of each agent with its skill
