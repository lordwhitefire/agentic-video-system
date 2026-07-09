# Agentic Video Editing System — Build Checklist

A clear, ordered todo list from scaffold (done) to working system. Check items off as we complete them.

---

## Phase 0 — Scaffold ✅ DONE

- [x] Law 1 (No Inference) definition
- [x] System overview
- [x] 8 agent definition files (Analyzer, Planner/Script Writer, Researcher, Editor, Reviewer, TTS, Watcher/Blocker, Investigator)
- [x] All files in `/home/z/my-project/download/agentic-video-system/`

---

## Phase 1 — Review & Iterate Agent Definitions

Goal: catch design flaws before we wire anything. Cheaper to fix markdown than code.

- [x] **1.1** Read `01-analyzer.md` — confirmed Blueprint JSON structure, no corrections.
- [x] **1.2** Read `02-planner-script-writer.md` — confirmed Resource Manifest JSON structure and short/long-form structure expertise, no corrections.
- [x] **1.3** Read `03-researcher.md` — confirmed candidate description format and `content_verified: false` default, no corrections.
- [x] **1.4** Read `04-editor.md` — confirmed animation routing (HyperFrames / Remotion / Lottie) and video effects execution rules, no corrections.
- [x] **1.5** Read `05-reviewer.md` — confirmed 7 fidelity check categories and pass/revise/branch decision rules, no corrections.
- [x] **1.6** Read `06-tts.md` — confirmed voice style rules. TTS inventory updated to 5 engines (Coqui XTTS-v2, Fish Speech, StyleTTS2, Piper, ElevenLabs) with voice cloning as central feature.
- [x] **1.7** Read `07-watcher-blocker.md` — confirmed 8 inference detection patterns and block/ambiguous/release protocol, no corrections.
- [x] **1.8** Read `08-investigator.md` — confirmed 5 root cause categories and remediation options, no corrections.
- [x] **1.9** Apply corrections from 1.1–1.8 to the agent files. — None needed; all 8 agents approved as-is.

---

## Phase 2 — Wire Up Tools & Skills

Goal: each agent's referenced tools/skills become real connections, not just names in markdown.

- [x] **2.1a** Script 1 — Foundations.
- [x] **2.1b** Script 2 — Coqui XTTS-v2. Voice clone test PASSED.
- [x] **2.1c** Script 3 — Analysis tools. Both sanity checks PASSED.
- [x] **2.1d** Script 4 — Editing MCP servers. 3 of 4 installed. vfx-mcp permanently skipped (Python 3.13+).
- [x] **2.1e** Script 5 — Animation tools. Remotion render test PASSED. HyperFrames installed. superpowers/Lottie not on npm.
- [x] **2.1f** Script 6 — Research MCP. Firecrawl + gpt-researcher installed. RivalSearchMCP not found (non-blocking). Both sanity checks PASSED.
- [x] **2.1g** Script 7 — OpenMontage. Cloned from calesthio/OpenMontage. 1039 skill files found. Sanity check PASSED.
- [x] **2.1h** Script 8 — Piper + ElevenLabs. Piper installed + sanity check PASSED. ElevenLabs SDK installed. research-keys.json created. voice-profile.json updated.
- [x] **2.2** Install analysis tools — DONE in Script 3.
- [x] **2.3** Install OpenMontage — DONE in Script 7.
- [x] **2.4** TTS tool inventory decided — 5 engines (Coqui primary, Piper fallback, Fish Speech/StyleTTS2/ElevenLabs upgrade paths).
- [x] **2.5** Graphics/animation deps — DONE in Script 5 (Remotion, HyperFrames, Chromium via Playwright).
- [ ] **2.6** Author `tools-registry.md` — maps each agent to its concrete tool list. (Will be created in Phase 3, sub-task 3.1.)
- [ ] **2.7** Author `skills-registry.md` — maps each agent to its concrete skill list. (Will be created in Phase 3, sub-task 3.1.)
- [ ] **2.8** Test each MCP server independently — DONE partially (mcp-video confirmed installed, others cloned). Full tool-level testing happens in Phase 3 sub-task 3.4 (tool dispatcher).

**PHASE 2 COMPLETE.** All 8 install scripts done. Moving to Phase 3 (runtime). See `PHASE-3-PLAN.md`.

---

## Phase 3 — Build the Runtime / Orchestrator

Goal: Python code that loads the 8 agents, manages the loop, handles the work tree, routes messages between agents, implements the Watcher/Blocker, and persists state across Colab sessions. See `PHASE-3-PLAN.md` for full details.

- [ ] **3.1** Project structure & config files (`runtime/` dir, `config/mcp-registry.json`, `config/agent-models.json`, `config/runtime-state/`)
- [ ] **3.2** Agent loader (reads markdown, parses YAML frontmatter + system prompt)
- [ ] **3.3** LLM client abstraction (multi-model: OpenAI, Anthropic, Google, Ollama)
- [ ] **3.4** Tool dispatcher (routes tool calls to MCP servers via stdio JSON-RPC)
- [ ] **3.5** Work tree (nodes, branches, HEAD — persists to `config/runtime-state/work-tree.json`)
- [ ] **3.6** Message bus (JSON protocols between agents, append-only log)
- [ ] **3.7** Watcher/Blocker hook (8 inference detection patterns, tool revocation)
- [ ] **3.8** Investigator module (5 root cause categories, remediation proposals)
- [ ] **3.9** User interaction layer (surfaces flags/blocks/reviews in Colab cells)
- [ ] **3.10** Persistence layer (saves all state to Google Drive, resumable)
- [ ] **3.11** Main orchestrator (entry point — user runs this to edit a video)
- [ ] **3.12** End-to-end test (pick a reference video, run the full flow, document cracks)

---

## Phase 4 — Manual Walkthrough (Crack-Finding)

Goal: run one reference video through the system end-to-end and see where the scaffold breaks.

- [ ] **4.1** Pick a test reference video (something simple — a 30s commentary clip is ideal for first run).
- [ ] **4.2** Run the Analyzer. Does the Blueprint come out clean? Where does it flag for user description? Are the flags useful or annoying?
- [ ] **4.3** Pick a test topic (e.g., "Mbappé World Cup 2022"). Run the Planner. Does the Script make sense? Is the Manifest complete?
- [ ] **4.4** Run the Researcher. Do the candidate proposals give you enough to source from? Or do you find yourself wanting more info?
- [ ] **4.5** Source the assets manually. Note any friction — what info was missing, what was extra.
- [ ] **4.6** Run the Editor. Does the cut come out matching the Blueprint? Where does it diverge?
- [ ] **4.7** Run the TTS. Does the voice track fit the pacing?
- [ ] **4.8** Run the Reviewer. Are the fidelity checks catching real issues? Or are they too strict / too loose?
- [ ] **4.9** Run the Watcher/Blocker. Did it catch any real inferences? Did it false-positive on anything?
- [ ] **4.10** Document every crack found. Group by agent. Decide fix priority.

---

## Phase 5 — Iterate on Cracks

Goal: fix what broke in Phase 4.

- [ ] **5.1** Fix high-priority cracks (agents that blocked the flow, false positives that wasted time, missing fields in JSON structures).
- [ ] **5.2** Re-run Phase 4 with the fixes. See if new cracks appear or old ones persist.
- [ ] **5.3** Repeat 5.1–5.2 until the walkthrough produces a usable cut without major friction.

---

## Phase 6 — Scale Test

Goal: confirm the system works on different forms (short vs long) and different genres (commentary, essay, reaction).

- [ ] **6.1** Test with a long-form reference (8+ minute commentary).
- [ ] **6.2** Test with a short-form reference (under 60s).
- [ ] **6.3** Test with a different genre (essay, reaction, vlog).
- [ ] **6.4** Test with a reference that has heavy layered effects (exercises the user-description protocol).
- [ ] **6.5** Test with a reference that has complex audio (multiple music beds, heavy SFX).
- [ ] **6.6** Document any new cracks. Iterate.

---

## Phase 7 — Polish & Documentation

Goal: the system is usable by you without thinking hard about it.

- [ ] **7.1** Write a README for the system — how to start a run, how to respond to flags, how to interrupt, how to resume.
- [ ] **7.2** Write a "common flags and what they mean" reference — so when the Watcher/Blocker fires, you know immediately what to do.
- [ ] **7.3** Write a "known limitations" doc — what the system can't do yet, where you still need to be the brain.
- [ ] **7.4** Tune the Watcher/Blocker detection patterns based on real false positive / false negative data from Phase 4–6.
- [ ] **7.5** Final review of all agent definitions — update with everything learned.

---

## How to use this checklist

- Work top to bottom. Don't skip ahead — Phase 3 before Phase 1 means we build on broken foundations.
- Phase 1 is your job — only you can judge whether the agent definitions match your mental model.
- Phase 2 is mostly installation + decision-making. The TTS tool choice (2.4) is the biggest open question.
- Phase 3 is the heaviest build phase. We'll likely break it into sub-tasks as we go.
- Phase 4 is where the real learning happens. Expect cracks. That's the point.
- Phases 5–7 are iteration. The system won't be perfect after one walkthrough. That's normal.

## Where we are now

Phase 0 ✅ done. Ready to start Phase 1 whenever you are.

**Recommended next move:** Start reading `01-analyzer.md` and `07-watcher-blocker.md`. Those two are load-bearing. If they're right, the rest follows. If they're wrong, everything downstream inherits the error.
