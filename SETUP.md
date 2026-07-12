# Setup Guide

## Prerequisites

- AgenticSign binary installed (your OpenCode fork)
- Git
- Python 3.11+ (for TTS and some tools)
- FFmpeg installed

## Your Config Path

Your AgenticSign global config lives at:
```
/home/lordwhitefire/.config-agenticine
```

This is for global installs. The recommended approach (below) uses project-level config — no need to touch the global path.

## Step 1: Clone The Repo

```bash
cd ~
git clone https://github.com/lordwhitefire/agentic-video-system.git
cd agentic-video-system
```

## Step 2: Launch AgenticSign

Run AgenticSign from inside the repo directory:

```bash
cd ~/agentic-video-system
agentic-sign
```

AgenticSign will:
- Read `opencode.json` from the repo root (standard OpenCode config filename)
- Set `editor` as the default agent
- Disable OpenCode's built-in `build` and `plan` agents
- Auto-discover all 15 agents from the `agent/` folder
- Load the 3 MCP servers configured (Context7, GitHub, Playwright)

No extra setup needed. The `opencode.json` at the repo root is all OpenCode needs.

### Option B: Global install (alternative)

If you want the agents available everywhere, not just in this repo:

```bash
mkdir -p /home/lordwhitefire/.config-agenticine/agent
mkdir -p /home/lordwhitefire/.config-agenticine/skills/custom
mkdir -p /home/lordwhitefire/.config-agenticine/skills/tools

cp agent/*.md /home/lordwhitefire/.config-agenticine/agent/
cp opencode.json /home/lordwhitefire/.config-agenticine/opencode.json
cp skills/custom/*.md /home/lordwhitefire/.config-agenticine/skills/custom/
cp skills/tools/*.md /home/lordwhitefire/.config-agenticine/skills/tools/
```

Then launch AgenticSign from anywhere:
```bash
agentic-sign
```

## Step 3: Verify The Setup

Launch AgenticSign:
```bash
agentic-sign
```

You should see ONLY these 15 agents:
1. Analyzer
2. Planner
3. Researcher
4. TTS
5. Editor (default — this is what loads first)
6. Graphics
7. Animation
8. Animated Graphics
9. Video Effects
10. Clips
11. Images
12. Reviewer
13. Watcher/Blocker
14. Investigator
15. Recruiter

If you see OpenCode's built-in `build` or `plan` agents, the config did not disable them. See Troubleshooting below.

## Step 4: Install Skills

### Custom Skills (behavioral)
Already in `skills/custom/`. 3 are complete:
- `script-driven-template-extraction.md` (Analyzer)
- `script-driven-visual-assignment.md` (Planner)
- `resource-md-generation.md` (Researcher)

12 more are marked TO BUILD in `skills/README.md`. Build them one at a time through the research → test → refine loop described in `TESTING.md`.

### Tool Skills (execution)
The tool skills registry is at `skills/tools/skills-registry.md`. It catalogs skill repositories (OpenMontage 1039 skills + others). To install actual tool skills:

```bash
# Example: OpenMontage
git clone <openmontage-repo-url> /tmp/openmontage
cp /tmp/openmontage/skills/*.md skills/tools/
```

## Step 5: Test An Agent

See `TESTING.md` for detailed instructions on testing individual agents with the research → test → refine loop.

## Troubleshooting

### Built-in agents still appear

The `opencode.json` disables `build` and `plan`:
```json
"agent": {
  "build": { "disable": true },
  "plan": { "disable": true }
}
```

If they still appear, your AgenticSign build may use a different config key. Try adding to `opencode.json`:
```json
"agents": {
  "build": { "disable": true },
  "plan": { "disable": true }
}
```

Or set an environment variable before launching:
```bash
OPENCODE_DISABLE_BUILT_IN=1 agentic-sign
```

### Agents don't appear at all

Check that:
- You're running `agentic-sign` from inside the repo directory (so OpenCode finds `opencode.json`)
- The `agent/` folder exists at the repo root (singular, not `agents/`)
- Each agent file starts with `---` on line 1 (YAML frontmatter)
- Each agent file has valid YAML frontmatter with at minimum `name` and `description`

### Skills not loading

Skills are loaded by the agent at runtime via the `skill` tool. Make sure:
- The skill file exists at the path referenced in the agent's "Skills You Use" section
- The skill file is valid Markdown
- The agent has `skill: allow` in its permission block (all our agents do)

### Config not found

OpenCode looks for `opencode.json` in:
1. The current working directory (project-level — recommended)
2. `~/.config/opencode/opencode.json` (global)
3. `~/.config-agenticine/opencode.json` (your custom global path)

Make sure `opencode.json` is at the repo root, not in a subfolder. It must be named exactly `opencode.json` — not `agentic-sign.json` or `config.json`.

## Repo Structure (After Setup)

```
agentic-video-system/
├── README.md              ← overview + architecture
├── SETUP.md               ← this file
├── TESTING.md             ← how to test agents individually
├── .gitignore             ← excludes video/audio/credentials
├── opencode.json          ← main config (default_agent, disables, MCPs)
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
│   ├── README.md          ← skill classification (custom vs tools)
│   ├── custom/            ← behavioral skills (how to think)
│   │   ├── script-driven-template-extraction.md
│   │   ├── script-driven-visual-assignment.md
│   │   └── resource-md-generation.md
│   └── tools/             ← execution skills (how to operate)
│       └── skills-registry.md
├── laws/                  ← 12 law files (the constitution)
├── config/                ← app-specific configs (NOT OpenCode config)
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
