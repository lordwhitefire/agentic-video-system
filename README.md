# Agentic Video Editing System

A reference-driven, agent-based video editing system. You give a reference video and a topic. The system analyzes the reference, tells you what to source, you source the assets, the system assembles the final cut, reviews it against the reference, and delivers it for your corrections.

**Law 1 (No Inference)** is the constitution of the system. Every agent stops and asks rather than guessing. See `laws/law-1-no-inference.md`.

---

## How to use this folder

This folder is self-contained. Upload it once to your Google Drive, run scripts from Colab against it, re-upload when files change.

### One-time setup

1. Download `agentic-video-system.zip` to your computer.
2. In Google Drive (drive.google.com): **New** → **File upload** → select `agentic-video-system.zip`. (Drive only lets you upload files, not folders — that's why we upload the zip and unzip it from Colab.)
3. Open Colab → new notebook → Runtime → **T4 GPU**.
4. Cell 1 (mount Drive):
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
5. Cell 2 (unzip in place on Drive):
   ```python
   import zipfile
   import os

   zip_path = '/content/drive/MyDrive/agentic-video-system.zip'
   extract_to = '/content/drive/MyDrive/'

   with zipfile.ZipFile(zip_path, 'r') as zip_ref:
       zip_ref.extractall(extract_to)

   print("Extracted. Contents of agentic-video-system/:")
   for item in os.listdir('/content/drive/MyDrive/agentic-video-system'):
       print(f"  {item}")
   ```
6. Verify you see: `README.md`, `MASTER-ROADMAP.md`, `BUILD-CHECKLIST.md`, `ERRORS-AND-FIXES.md`, `worklog.md`, `agents`, `config`, `laws`, `output`, `scripts`, `system`, `voice-samples`.

### Running a script on Colab

After the one-time setup (Drive mounted, folder unzipped), running a script is just one cell:

```python
!bash /content/drive/MyDrive/agentic-video-system/scripts/colab-01-foundations.sh
```

Replace `colab-01-foundations.sh` with whichever script you're running.

### When I update files

When I send you an updated `agentic-video-system.zip`:

1. (Optional) In Drive, rename the old `agentic-video-system/` folder to `agentic-video-system-old/` as backup, or just delete it.
2. Upload the new zip (overwrites the old one if same name).
3. In Colab: mount Drive, run the unzip cell (overwrites old files with new ones), run the new script.
4. Paths stay the same. Scripts keep working.

---

## Folder structure

| Folder / File | Purpose |
|---|---|
| `README.md` | This file. Start here. |
| `MASTER-ROADMAP.md` | Single source of truth for project state. Open this if you're lost. |
| `BUILD-CHECKLIST.md` | Detailed checklist of every task. |
| `ERRORS-AND-FIXES.md` | Every error we hit, with cause + fix. Check here first when something breaks. |
| `worklog.md` | Running log of all work done. |
| `laws/` | The system's laws. Currently just `law-1-no-inference.md`. |
| `system/` | System overview, flow, agent roster. |
| `agents/` | The 8 agent definition files (markdown, in awesome-opencode-subagents format). |
| `scripts/` | All Colab install scripts. Run these one at a time. |
| `voice-samples/` | Your voice sample for Coqui cloning goes here. Agent will demand it at runtime when needed. |
| `output/` | Generated videos, audio, and intermediate artifacts save here. |
| `config/` | Voice profile config, install status, agent state. The system reads and writes here. |

---

## Where we are right now

Check `MASTER-ROADMAP.md` for current status. The "Current step" line at the top tells you exactly what to do next.

As of last update: **Phase 2 — Script 1 of 8 ready to run on Colab.**

---

## The 8 scripts (one at a time)

```
Script 1  — Foundations              ← READY (colab-01-foundations.sh)
Script 2  — Coqui XTTS-v2            ← written after Script 1 works
Script 3  — Analysis tools           ← written after Script 2 works
Script 4  — Editing MCP servers      ← written after Script 3 works
Script 5  — Animation tools          ← written after Script 4 works
Script 6  — Research MCP             ← written after Script 5 works
Script 7  — OpenMontage              ← written after Script 6 works
Script 8  — Piper + ElevenLabs       ← written after Script 7 works
```

Rule: only ever one script in front of you. Run it, report back, I write the next.

---

## Law 1 — No Inference (the constitution)

Every agent in this system obeys Law 1: no gap-filling, no fabrication, no silent guessing. When an agent hits a gap, it stops and asks. Enforced by the Watcher/Blocker agent (which revokes tools when it detects inference) and the Investigator agent (which diagnoses blocked agents and reports to you).

Full text: `laws/law-1-no-inference.md`

---

## Contact / getting unstuck

If something breaks:
1. Check `ERRORS-AND-FIXES.md` — your error may already be there.
2. Check `MASTER-ROADMAP.md` "If We Lose Touch" section.
3. Tell me: which script, which step (`[1/6]`, `[2/6]`, etc.), and the error output.
