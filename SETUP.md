# Setup Guide

## Prerequisites

- AgenticSign binary installed (your OpenCode fork)
- Git
- Python 3.11+ (for TTS and some tools)
- FFmpeg installed

## Your Config Path

Your AgenticSign config lives at:
```
/home/lordwhitefire/.config-agenticine
```

All setup instructions below use this path. Adjust if your installation differs.

## Step 1: Clone The Repo

```bash
cd ~
git clone https://github.com/lordwhitefire/agentic-video-system.git
cd agentic-video-system
```

## Step 2: Point AgenticSign At This Repo

You have two options.

### Option A: Project-level config (recommended)

When you run AgenticSign from the repo directory, it picks up the config automatically:

```bash
cd ~/agentic-video-system
agentic-sign
```

AgenticSign will:
- Load the config from `config/agentic-sign.json`
- Disable all built-in agents (`disable_built_in_agents: true`)
- Load only the 14 agents from `./agents/`

### Option B: Global config

Copy the agents and config to your global AgenticSign config directory:

```bash
mkdir -p /home/lordwhitefire/.config-agenticine/agents
mkdir -p /home/lordwhitefire/.config-agenticine/skills/custom
mkdir -p /home/lordwhitefire/.config-agenticine/skills/tools

cp agents/*.md /home/lordwhitefire/.config-agenticine/agents/
cp config/agentic-sign.json /home/lordwhitefire/.config-agenticine/config.json
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

You should see ONLY these 14 agents:
1. Analyzer
2. Planner
3. Researcher
4. TTS
5. Graphics Creator
6. Animation Creator
7. Animated Graphics Creator
8. Video Effects Creator
9. Clips Preparer
10. Images Preparer
11. Editor
12. Reviewer
13. Watcher/Blocker
14. Investigator

If you see OpenCode's built-in agents (engineer, planner, etc.), the config did not disable them. See Troubleshooting below.

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

Your AgenticSign build may use a different config key. Check the build's documentation. Common alternatives to try in `config/agentic-sign.json`:

```json
// Option 1
{ "disable_built_in_agents": true }

// Option 2
{ "agents": { "built_in": false, "directory": "./agents" } }

// Option 3
{ "agent": { "disable_built_in": true, "directory": "./agents" } }
```

Or set an environment variable before launching:
```bash
AGENTIC_SIGN_DISABLE_BUILT_IN=1 agentic-sign
```

Try each until the built-in agents disappear.

### Agents don't appear at all

Check that the agent files are in the right directory and have valid YAML frontmatter. Each agent file must start with:

```yaml
---
name: <agent-name>
display_name: <Display Name>
layer: <thinking|audio|visual-prep|assembly|enforcement>
role: <one-line role description>
---
```

### Skills not loading

Skills are loaded by the agent at runtime. Make sure:
- The skill file exists at the path referenced in the agent's "Skills You Use" section
- The skill file is valid Markdown
- The agent's system prompt includes the skill (this depends on how AgenticSign injects skills — check your build's docs)

### Config path issues

If AgenticSign doesn't find the config at `/home/lordwhitefire/.config-agenticine`, check:
- Does the directory exist? (`mkdir -p /home/lordwhitefire/.config-agenticine`)
- Does the config file exist there? (`config.json`)
- Is the agent directory path in the config correct? (Should point to your cloned repo's `agents/` folder, or to the copied agents in the config directory)

## Repo Structure (After Setup)

```
agentic-video-system/
├── README.md              ← overview + architecture
├── SETUP.md               ← this file
├── TESTING.md             ← how to test agents individually
├── .gitignore             ← excludes video/audio/credentials
├── agents/                ← 14 agent files (WHO + WHAT only)
│   ├── 01-analyzer.md
│   ├── 02-planner.md
│   ├── 03-researcher.md
│   ├── 04-tts.md
│   ├── 05-graphics.md
│   ├── 06-animation.md
│   ├── 07-animated-graphics.md
│   ├── 08-video-effects.md
│   ├── 09-clips.md
│   ├── 10-images.md
│   ├── 11-editor.md
│   ├── 12-reviewer.md
│   ├── 13-watcher-blocker.md
│   └── 14-investigator.md
├── skills/
│   ├── README.md          ← skill classification (custom vs tools)
│   ├── custom/            ← behavioral skills (how to think)
│   │   ├── script-driven-template-extraction.md
│   │   ├── script-driven-visual-assignment.md
│   │   └── resource-md-generation.md
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
