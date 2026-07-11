# Agentic Video Editing System

A template-driven, agent-based video editing system. You provide a reference video and a topic. The system analyzes the reference to extract its structural template (HOW it was made — not WHAT it said), then creates a NEW video on your topic following that template.

## Law 1 (No Inference) is the constitution. Every agent obeys all 12 laws. See `laws/`.

## Quick Start

1. **Read** `system/system-overview.md` — understand the flow
2. **Read** `system/visual-types.md` — understand the 5 visual types
3. **Install** tools from `tools/tools-registry.md`
4. **Install** skills from `skills/skills-registry.md`
5. **Provide** a reference video + topic
6. **Run** the flow: Analyze → Plan → Research → Execute → Review → Deliver

## Repo Structure

```
agentic-video-system/
├── README.md                    ← You are here
├── laws/                        ← 12 laws (the constitution)
├── agents/                      ← 8 agent definitions
├── system/                      ← System documentation
│   ├── system-overview.md       ← The flow, agents, work tree
│   └── visual-types.md          ← 5 visual types
├── tools/                       ← Tools registry (every tool, repo link)
├── skills/                      ← Skills registry (every skill repo)
├── config/                      ← Config templates
│   ├── voice-profile.json       ← TTS voice profile
│   └── research-keys.json       ← API keys template
├── templates/                   ← Video editing style templates
└── scripts/                     ← Assembly + utility scripts
```

## The 8 Agents

| # | Agent | Lane |
|---|-------|------|
| 01 | Analyzer | Perceive reference → produce Blueprint (template) |
| 02 | Planner / Script Writer | Blueprint + topic → Script + Manifest |
| 03 | Researcher | Source clips, images, audio directly |
| 04 | Editor | Assemble cut from assets + blueprint + script |
| 05 | Reviewer | Cut vs Blueprint → pass / revise / branch |
| 06 | TTS | Script + pacing → voice audio (user's cloned voice) |
| 07 | Watcher / Blocker | Monitor all agents for inference → revoke + log |
| 08 | Investigator | Diagnose blocked agents → report to user |

## The 12 Laws

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

## Key Principle

**The reference video is a STYLE TEMPLATE, not content to reproduce.** The new video has completely different content — only the structural shell (segment count, pacing, visual style, cutting rhythm) is carried over.

**The script drives everything.** Every sentence is marked with what visual appears on screen. The Editor reads these markers and executes them exactly. No guessing.

**Audio is the MASTER.** Visuals are placed to match the audio. The audio determines when visuals change. Visual duration must always be ≥ audio duration.
