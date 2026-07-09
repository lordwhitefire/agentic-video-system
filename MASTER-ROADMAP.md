# Agentic Video Editing System — Master Roadmap

This file is your single source of truth for the whole project. If we lose touch, open this file — it tells you exactly where we are and what's next.

**Last updated:** 2026-07-09
**Current phase:** Phase 3 — Build the Runtime / Orchestrator
**Current step:** Phase 3 planning — I'm writing the runtime plan. Read it, then we start building.

**Environment:** Google Colab. T4 GPU enabled, 15GB VRAM, CUDA 12.8. Python 3.11 venv at `/content/coqui-venv` for Coqui + Whisper. System Python 3.12 for everything else. MCP servers at `/content/mcp-servers/`. Animation tools at `/content/animation-tools/`. Research tools at `/content/research-tools/`. OpenMontage at `/content/openmontage` (1039 skills). Piper model at `/content/tts-engines/piper-models/`. Persistent storage via Google Drive mount.

**Status:**
- Phase 0 (Scaffold) ✅ DONE
- Phase 1 (Review agents) ✅ DONE
- Phase 2 (Wire up tools & skills) ✅ DONE — All 8 install scripts complete.
- Phase 3 (Build runtime) 🚧 STARTING NOW

---

## The Big Picture — 7 Phases

```
Phase 0 — Scaffold                  ✅ DONE
Phase 1 — Review agent definitions  ✅ DONE
Phase 2 — Wire up tools & skills    🚧 IN PROGRESS (you are here)
Phase 3 — Build runtime/orchestrator ⬜ pending
Phase 4 — Manual walkthrough        ⬜ pending
Phase 5 — Iterate on cracks         ⬜ pending
Phase 6 — Scale test                ⬜ pending
Phase 7 — Polish & documentation    ⬜ pending
```

---

## Phase 0 — Scaffold ✅ DONE

What was built:
- `laws/law-1-no-inference.md` — the constitution of the system
- `system/system-overview.md` — the flow, the 8 agents, the work tree
- 8 agent definition files (in `agents/`)
- `worklog.md` — running log of all work done

---

## Phase 1 — Review Agent Definitions ✅ DONE

You reviewed all 8 agents and approved them with no corrections:
- `01-analyzer.md`
- `02-planner-script-writer.md`
- `03-researcher.md`
- `04-editor.md`
- `05-reviewer.md`
- `06-tts.md` (updated with 5-engine TTS inventory + runtime voice sample demand)
- `07-watcher-blocker.md`
- `08-investigator.md`

---

## Phase 2 — Wire Up Tools & Skills 🚧 IN PROGRESS

**Goal:** get every tool and skill installed on Kaggle so the agents can actually use them.

**Architecture:** All execution on Kaggle cloud GPU. No local pipeline. Kaggle notebook is ephemeral — persistence handled in Phase 3.

### The 8 install scripts (one at a time, not all at once)

```
✅ = done   ⬜ = pending   🚧 = current

Script 1  — Foundations              ✅ DONE
Script 2  — Coqui XTTS-v2            ✅ DONE
Script 3  — Analysis tools           ✅ DONE
Script 4  — Editing MCP servers      ✅ DONE
Script 5  — Animation tools          ✅ DONE
Script 6  — Research MCP             ✅ DONE
Script 7  — OpenMontage              ✅ DONE
Script 8  — Piper + ElevenLabs       ✅ DONE
```

**PHASE 2 COMPLETE.** All tools and skills installed. Moving to Phase 3 (runtime).

**Rule:** Only ever ONE script in front of you at a time. Run it, report back, I write the next one.

### What each script installs

| # | Script | What it installs | Why |
|---|---|---|---|
| 1 | Foundations | FFmpeg, Node.js, Python utils, system libs, GPU check | Everything else depends on these |
| 2 | Coqui XTTS-v2 | Coqui XTTS-v2, voice cloning deps, first clone test | Primary TTS — riskiest piece, test early |
| 3 | Analysis tools | Whisper, PySceneDetect, OpenCV, Deep SORT | Analyzer agent's eyes |
| 4 | Editing MCP servers | mcp-video, kdenlive-mcp, VFX MCP, video-audio-mcp, dubnium0/ffmpeg-mcp | Editor agent's hands |
| 5 | Animation tools | HyperFrames, Remotion, Lottie Creator MCP, remotion-superpowers | Animation layer |
| 6 | Research MCP | RivalSearchMCP, gpt-researcher, Firecrawl | Researcher agent's tools |
| 7 | OpenMontage | The 500+ skill library | Intelligence/orchestration layer |
| 8 | Piper + ElevenLabs | CPU fallback TTS + ElevenLabs API config | Fallbacks and monetization path |

### Other Phase 2 tasks (after all 8 scripts run)

- `2.6` Write `tools-registry.md` — maps each agent to its concrete tool list
- `2.7` Write `skills-registry.md` — maps each agent to its concrete skill list
- `2.8` Test each MCP server independently

---

## Phase 3 — Build the Runtime / Orchestrator ⬜ PENDING

**Goal:** a Python script that loads the agents, manages the loop, handles the work tree, routes messages between agents, and persists state across Kaggle sessions.

Sub-tasks:
- 3.1 Pick runtime language (Python recommended)
- 3.2 Build agent loader (reads markdown files, instantiates LLM clients)
- 3.3 Build tool dispatcher (routes tool calls to MCP servers)
- 3.4 Build work tree (nodes = project states, branches = forks, HEAD = current preview)
- 3.5 Build agent message bus (JSON protocols from agent files)
- 3.6 Build Watcher/Blocker hook (intercepts tool calls, runs detection patterns)
- 3.7 Build user interaction layer (surfaces flags/blocks/reviews to you)
- 3.8 Build persistence layer (Kaggle Datasets for state, config, asset storage)

---

## Phase 4 — Manual Walkthrough (Crack-Finding) ⬜ PENDING

**Goal:** run one reference video through the system end-to-end and see where it breaks.

Sub-tasks:
- 4.1 Pick a test reference video (30s commentary clip ideal)
- 4.2 Run Analyzer — does Blueprint come out clean?
- 4.3 Pick test topic, run Planner — does Script + Manifest make sense?
- 4.4 Run Researcher — do candidate proposals give you enough to source from?
- 4.5 Source assets manually, note friction
- 4.6 Run Editor — does cut match Blueprint?
- 4.7 Run TTS — does voice fit pacing?
- 4.8 Run Reviewer — are fidelity checks catching real issues?
- 4.9 Run Watcher/Blocker — any real inferences caught? Any false positives?
- 4.10 Document every crack, group by agent, prioritize fixes

---

## Phase 5 — Iterate on Cracks ⬜ PENDING

- 5.1 Fix high-priority cracks
- 5.2 Re-run Phase 4, see if new cracks appear
- 5.3 Repeat until walkthrough produces a usable cut without major friction

---

## Phase 6 — Scale Test ⬜ PENDING

- 6.1 Test long-form reference (8+ min commentary)
- 6.2 Test short-form reference (under 60s)
- 6.3 Test different genre (essay, reaction, vlog)
- 6.4 Test heavy layered effects (exercises user-description protocol)
- 6.5 Test complex audio (multiple music beds, heavy SFX)
- 6.6 Document new cracks, iterate

---

## Phase 7 — Polish & Documentation ⬜ PENDING

- 7.1 Write README for the system
- 7.2 Write "common flags and what they mean" reference
- 7.3 Write "known limitations" doc
- 7.4 Tune Watcher/Blocker detection patterns based on real data
- 7.5 Final review of all agent definitions

---

## Where You Are Right Now

### PHASE 2 IS COMPLETE. Welcome to Phase 3.

All 8 install scripts are done. Every tool and skill is installed on your Colab environment:

| Layer | What's installed |
|---|---|
| Foundations | FFmpeg, Node.js, Python utils, Tesla T4 GPU (15GB VRAM, CUDA 12.8) |
| TTS (primary) | Coqui XTTS-v2 in Python 3.11 venv, your voice cloned |
| TTS (fallback) | Piper (CPU, no cloning), ElevenLabs SDK (API, monetization upgrade) |
| Analysis | faster-whisper, openai-whisper, PySceneDetect, OpenCV, Deep SORT |
| Editing MCP | mcp-video (119 tools), ffmpeg-mcp-dubnium (40+ tools), video-audio-mcp |
| Animation | Remotion (render test PASSED), HyperFrames |
| Research | Firecrawl MCP, gpt-researcher, supporting libs (httpx, bs4, lxml, trafilatura) |
| Intelligence | OpenMontage — 1039 skills (video-edit, video-translate, elevenlabs, tailwind-design-system, threejs-fundamentals, playwright-recording, and 1033 more) |

**Known gaps (non-blocking):**
- vfx-mcp — requires Python 3.13+ (Colab has 3.12), permanently skipped. mcp-video covers effects.
- remotion-superpowers — not on npm/GitHub. Remotion alone is sufficient.
- Lottie Creator MCP — not on npm/GitHub. Remotion covers most animation.
- RivalSearchMCP — private/not found. gpt-researcher + Firecrawl cover research.

### Next: Phase 3 — Build the Runtime / Orchestrator

Open **`PHASE-3-PLAN.md`** for the full plan. Summary:

The runtime is the Python code that loads the 8 agents, manages the loop, handles the work tree, routes messages between agents, implements the Watcher/Blocker, and persists state across Colab sessions.

**12 sub-tasks**, built one at a time:
- 3.1 Project structure & config files
- 3.2 Agent loader (reads markdown, parses frontmatter + system prompt)
- 3.3 LLM client abstraction (multi-model: OpenAI, Anthropic, Google, Ollama)
- 3.4 Tool dispatcher (routes tool calls to MCP servers)
- 3.5 Work tree (nodes, branches, HEAD)
- 3.6 Message bus (JSON protocols between agents)
- 3.7 Watcher/Blocker hook (8 inference detection patterns)
- 3.8 Investigator module (5 root cause categories)
- 3.9 User interaction layer (surfaces flags/blocks/reviews)
- 3.10 Persistence layer (saves state to Google Drive)
- 3.11 Main orchestrator (entry point — user runs this to edit a video)
- 3.12 End-to-end test (pick a reference video, run the full flow)

### What I need from you before we start building

Three decisions (detailed in `PHASE-3-PLAN.md`):

1. **Which LLM providers?** OpenAI only / OpenAI+Anthropic / +Google / +Ollama
2. **Which model per agent?** All same model / each agent specific / user picks per run
3. **Do you have API keys ready?** (You'll add them to `config/research-keys.json`)

Answer these, then I start writing the runtime at sub-task 3.1.

### Full context — how we got here

1. ✅ Script 1 — Foundations (FFmpeg, Node.js, Python, Tesla T4 GPU).
2. ✅ Script 2 — Coqui XTTS-v2 in Python 3.11 venv. Voice clone test PASSED.
3. ✅ Script 3 — Analysis tools (Whisper, PySceneDetect, OpenCV, Deep SORT). Both sanity checks PASSED.
4. ✅ Script 4 — Editing MCP servers. 3 of 4 installed. vfx-mcp permanently skipped (Python 3.13+).
5. ✅ Script 5 — Animation tools. Remotion render test PASSED. HyperFrames installed. superpowers/Lottie not on npm.
6. ✅ Script 6 — Research MCP. Firecrawl + gpt-researcher installed. RivalSearchMCP private/not found (non-blocking). Both sanity checks PASSED.
7. ✅ Script 7 — OpenMontage. Cloned from calesthio/OpenMontage. 1039 skill files found. Sanity check PASSED.
8. ✅ Script 8 — Piper + ElevenLabs. Piper installed + sanity check PASSED. ElevenLabs SDK installed. research-keys.json template created. voice-profile.json updated.
9. 🚧 Now: Phase 3 — Build the Runtime. Open `PHASE-3-PLAN.md` for the plan.

### For future updates (the standard workflow)

When I send you an updated `agentic-video-system.zip`:

1. Delete the old `agentic-video-system/` folder in Drive (or rename to `agentic-video-system-old/` as backup).
2. Upload the new zip (overwrites the old one if same name).
3. In Colab: mount Drive, run the unzip cell (overwrites old files with new ones), run the new script.
4. The unzip overwrites old files with new ones. Paths stay the same. Scripts keep working.

---

## If We Lose Touch

Open this file. Check the "Current step" line at the top. That tells you exactly what to do next.

If you're mid-script and something breaks, tell me:
1. Which script number (1–8)
2. Which step inside the script (the `[1/6]`, `[2/6]` markers)
3. The error output

I'll know exactly where we are and what to fix.

---

## File Locations (this folder, when uploaded to Google Drive)

```
MyDrive/agentic-video-system/
├── README.md                      ← start here — how to use this folder
├── MASTER-ROADMAP.md              ← THIS FILE — single source of truth for project state
├── PHASE-3-PLAN.md                ← Phase 3 runtime build plan (READ THIS NEXT)
├── BUILD-CHECKLIST.md             ← detailed checklist with checkboxes
├── ERRORS-AND-FIXES.md            ← every error we hit, with cause + fix
├── worklog.md                     ← running log of all work done
├── laws/
│   └── law-1-no-inference.md      ← the constitution
├── system/
│   └── system-overview.md         ← the flow, the agents, the work tree
├── agents/
│   ├── 01-analyzer.md
│   ├── 02-planner-script-writer.md
│   ├── 03-researcher.md
│   ├── 04-editor.md
│   ├── 05-reviewer.md
│   ├── 06-tts.md                  ← updated with 5-engine TTS inventory
│   ├── 07-watcher-blocker.md
│   └── 08-investigator.md
├── scripts/
│   ├── colab-01-foundations.sh      ← Script 1 (DONE)
│   ├── colab-02-coqui-xtts-v2.sh    ← Script 2 (DONE)
│   ├── colab-03-analysis-tools.sh   ← Script 3 (DONE)
│   ├── colab-04-editing-mcp.sh      ← Script 4 (DONE)
│   ├── colab-05-animation-tools.sh  ← Script 5 (DONE)
│   ├── colab-06-research-mcp.sh     ← Script 6 (DONE)
│   ├── colab-07-openmontage.sh      ← Script 7 (DONE)
│   └── colab-08-piper-elevenlabs.sh ← Script 8 (READY TO RUN — FINAL)
├── voice-samples/
│   └── README.md                  ← empty until TTS agent demands a sample
├── output/
│   └── README.md                  ← empty until system produces output
└── config/
    ├── README.md
    ├── voice-profile.json         ← initial template — TTS agent reads/writes this
    └── install-status.json        ← created by Script 1 after successful run
```

When uploaded to Drive, the path prefix is `/content/drive/MyDrive/` (after Drive mount in Colab).

The zip `agentic-video-system.zip` contains all of the above. Re-download and re-upload whenever I update files.

---

## One-Line Summary

**Script 1 done + GPU confirmed (Tesla T4). Now: download the updated zip (with Script 2), re-upload to Drive, put a voice sample (6+ sec WAV/MP3) in voice-samples/, run `!bash /content/drive/MyDrive/agentic-video-system/scripts/colab-02-coqui-xtts-v2.sh`, report back. Coqui will clone your voice and generate a test audio.**
