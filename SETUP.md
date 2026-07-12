# Setup Guide

## Prerequisites

- OpenCode installed — `curl -fsSL https://opencode.ai/install | bash`
- Git
- Python 3.11+ (for TTS and some tools)
- FFmpeg installed

## Setup

### Option A — Isolated install (recommended)

Use this if you want Agenticine separate from your stock OpenCode:

```bash
# Clone this repo into a dedicated config directory
git clone https://github.com/lordwhitefire/agentic-video-system.git ~/.config-agenticine/opencode

# Create an alias that points OpenCode at the isolated config
echo 'alias agenticine="XDG_CONFIG_HOME=~/.config-agenticine opencode"' >> ~/.bashrc
source ~/.bashrc

# Run it
agenticine
```

### Option B — Replace stock OpenCode

Use this if you want Agenticine as your only OpenCode:

```bash
git clone https://github.com/lordwhitefire/agentic-video-system.git ~/.config/opencode
opencode
```

## Verify The Setup

After running `agenticine` (or `opencode` for Option B), you should see ONLY these 15 agents:

1. Analyzer
2. Planner
3. Researcher
4. TTS
5. Editor (default — loads first)
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

If you see OpenCode's built-in `build` or `plan` agents, the config did not disable them. Check `opencode.json` at the repo root — it should have:

```json
"agent": {
  "build": { "disable": true },
  "plan": { "disable": true }
}
```

## Install Skills

### Custom Skills (behavioral)
Already in `skills/custom/`. 3 are complete:
- `script-driven-template-extraction.md` (Analyzer)
- `script-driven-visual-assignment.md` (Planner)
- `resource-md-generation.md` (Researcher)

12 more are marked TO BUILD in `skills/README.md`. Build them one at a time through the research → test → refine loop described in `TESTING.md`.

### Tool Skills (execution)
The tool skills registry is at `skills/tools/skills-registry.md`. To install actual tool skills:

```bash
# Example: OpenMontage
git clone <openmontage-repo-url> /tmp/openmontage
cp /tmp/openmontage/skills/*.md skills/tools/
```

## Test An Agent

See `TESTING.md` for detailed instructions on testing individual agents.

## Troubleshooting

### Built-in agents still appear

The `opencode.json` disables `build` and `plan`. If they still appear, try adding to `opencode.json`:

```json
"agents": {
  "build": { "disable": true },
  "plan": { "disable": true }
}
```

### Agents don't appear at all

Check that:
- You cloned the repo into the right place (`~/.config-agenticine/opencode/` for Option A, `~/.config/opencode/` for Option B)
- The `agent/` folder exists at the repo root (singular, not `agents/`)
- Each agent file starts with `---` on line 1 (YAML frontmatter)
- Each agent file has valid YAML frontmatter with at minimum `name` and `description`

### Skills not loading

Skills are loaded by the agent at runtime via the `skill` tool. Make sure:
- The skill file exists at the path referenced in the agent's "Skills You Use" section
- The skill file is valid Markdown
- The agent has `skill: allow` in its permission block (all our agents do)

### Config not found

OpenCode looks for `opencode.json` at `$XDG_CONFIG_HOME/opencode/opencode.json`. Make sure:
- The repo is cloned into the right directory (not a subfolder of it)
- The file is named exactly `opencode.json` (not `agenticine.json`, `config.json`, etc.)
- The file is at the repo root, not nested inside a `config/` folder

## Repo Structure

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
