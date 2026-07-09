# Errors & Fixes — Agentic Video Editing System

A running log of every error we hit during the build, the cause, and the fix. If you hit the same error again, check this file first.

**Last updated:** 2026-07-08

---

## Error #001 — SyntaxError when running bash script in Kaggle cell

### The error

```
File "/tmp/ipykernel_58/2909338394.py", line 30
    echo "===================================================="
         ^
SyntaxError: invalid syntax
```

### The cause

Kaggle notebook cells default to Python. If you paste bash script content (like `echo "..."`, `apt-get install`, etc.) directly into a cell, Python tries to interpret it as Python code and fails on the very first bash command.

### The fix — three options, pick one

**Option A (easiest, recommended): Upload script as Kaggle Dataset**

1. Save `kaggle-01-foundations.sh` to your computer
2. Kaggle → Datasets (top nav) → New Dataset
3. Drag the .sh file in, give the dataset a name (e.g., "agentic-scripts"), click Create
4. Go back to your notebook → Add Data (right sidebar) → search your dataset → add it
5. In a code cell (Python cell, default), run:

```python
!bash /kaggle/input/agentic-scripts/kaggle-01-foundations.sh
```

Replace `agentic-scripts` with whatever you named the dataset. The `!` prefix tells Kaggle "run this as a shell command."

**Option B: Use the %%bash magic at the top of the cell**

In a code cell, the FIRST line must be `%%bash` (exactly that, with the two percent signs). Then paste the script below it:

```bash
%%bash
echo "===================================================="
echo "Agentic Video Editing System — Kaggle Setup Script 1"
echo "Foundations"
echo "===================================================="
# ... rest of the script ...
```

The `%%bash` magic tells Kaggle "this entire cell is bash, not Python."

**Option C: Run inline with ! prefix (only for short scripts)**

For one-line commands, prefix with `!`:
```python
!echo "hello"
!apt-get install -y ffmpeg
```

For a long multi-line script, Option C is painful — use Option A or B instead.

### Which option to use

- **Option A** is cleanest. You'll be running 8 scripts total — uploading them all as a Dataset once means you never have to copy-paste again. Just change the filename in the `!bash` command.
- **Option B** works but you have to copy-paste every script.
- **Option C** is for quick one-off commands, not for these install scripts.

### Recommended next action

Use **Option A**. Upload `kaggle-01-foundations.sh` as a Kaggle Dataset named `agentic-scripts`. Then in a cell:

```python
!bash /kaggle/input/agentic-scripts/kaggle-01-foundations.sh
```

For Scripts 2–8 (when I write them), you'll just upload them to the same Dataset and change the filename. One-time setup.

---

## How to use this file

Every time we hit an error:
1. I add a new entry here with the error message, cause, and fix.
2. You check this file first if you hit something similar.
3. We don't repeat mistakes.

Error numbering: `#001`, `#002`, `#003`... in order of occurrence.

---

## Common Kaggle gotchas to watch for

(Will be expanded as we hit them)

1. **Cell type** — Kaggle cells default to Python. For bash, use `!command` (one line) or `%%bash` (whole cell).
2. **Internet must be on** — Settings → Internet → On. Without this, every download fails.
3. **GPU must be on** — Settings → Accelerator → GPU T4 x2. Without this, Coqui/StyleTTS2/Fish Speech fail.
4. **Kaggle session timeout** — Long-running installs (5+ min) may time out the cell. If the cell appears stuck, check the output log — it may still be running.
5. **Ephemeral storage** — Anything in `/kaggle/working/` is lost when the notebook stops. Persistent storage is in `/kaggle/input/` (read-only) or Kaggle Datasets (must be saved explicitly).
6. **Apt-get can fail** — Sometimes `apt-get update` returns 404s for old Kaggle mirrors. Usually a retry fixes it.

---

## Error #002 — Kaggle is painfully slow, switch to Google Colab

### The problem

Kaggle notebook execution is too slow for this project. Long install times, laggy cell execution, slow package downloads. Switching to Google Colab.

### Why Colab is better for this project

| | Kaggle | Google Colab |
|---|---|---|
| GPU type | T4 x2 (16GB each) | T4 (16GB) free tier, A100 (40GB) Colab Pro |
| Internet speed | Often throttled | Generally faster |
| Cell execution | Laggy | Snappier |
| Session length | 12 hours max | 12 hours free / 24 hours Pro |
| Storage persistence | Kaggle Datasets | Google Drive (easier — it's just a folder) |
| File upload | Datasets (clunky) | Drag-drop to /content/ or use Drive |
| Mounting persistent storage | Kaggle Datasets API | `google.colab.drive.mount()` — one line |

### How to switch — step by step

**Step 1: Open Colab**

Go to colab.research.google.com. Sign in with your Google account.

**Step 2: Create a new notebook**

File → New notebook. Or just click "New notebook" on the Colab landing page.

**Step 3: Enable GPU**

Runtime (top menu) → Change runtime type → Hardware accelerator: **T4 GPU** → Save.

**Step 4: Run Script 1**

Colab cells are also Python by default, just like Kaggle. Two ways to run the script:

**Option A — Upload the .sh file directly (easiest for first run):**

1. In Colab, click the folder icon on the left sidebar.
2. Click the upload icon (the page with up arrow).
3. Select `kaggle-01-foundations.sh` from your computer. It uploads to `/content/`.
4. In a code cell, run:
   ```python
   !bash /content/kaggle-01-foundations.sh
   ```

**Option B — Mount Google Drive (best for persistence across sessions):**

1. In a code cell, run:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```
2. Follow the auth link, grant access.
3. Copy your `kaggle-01-foundations.sh` into your Google Drive (any folder — say `agentic-scripts/`).
4. Run the script from Drive:
   ```python
   !bash /content/drive/MyDrive/agentic-scripts/kaggle-01-foundations.sh
   ```
5. Now every time you start a new Colab session, you just mount Drive and run — no re-uploading.

**Recommended:** Use Option B (Google Drive). It's the equivalent of Kaggle Datasets but easier — it's just a folder in your Google Drive. All 8 scripts can live there, all your output files can save there, and nothing is lost when the Colab session dies.

### Setting up the Google Drive folder structure

In your Google Drive, create this structure once:

```
MyDrive/
└── agentic-video-system/
    ├── scripts/        ← put kaggle-01-foundations.sh here (rename to colab-01-foundations.sh if you want)
    ├── voice-samples/  ← where your voice sample for Coqui cloning will go
    ├── output/         ← where generated videos and audio will save
    └── config/         ← voice profile config, work tree state, agent state
```

You can create this in Drive's web UI or programmatically from Colab.

### What changes in the scripts

The scripts themselves don't need to change much. Kaggle and Colab are both Ubuntu-based. The main differences:

1. **Paths** — Kaggle uses `/kaggle/working/` and `/kaggle/input/`. Colab uses `/content/` and `/content/drive/MyDrive/`.
2. **Drive mount** — Colab needs the `drive.mount()` call at the start of any session that uses Drive.
3. **GPU verification** — Same command (`nvidia-smi`), works identically.

I'll update each script to use Colab paths when I write them. Script 1 already works as-is — just change the path in the `!bash` command.

### What to report back

After you switch to Colab and run Script 1:

1. Did it complete without errors?
2. The summary block at the end (version numbers, GPU status).
3. Any warnings or slow steps.
4. Confirm whether you used Option A (upload) or Option B (Drive mount) — so I know which path pattern to use in future scripts.

---

## Error #003 — Google Drive won't let me upload a folder, only files

### The problem

Google Drive's web UI only allows file uploads, not folder uploads. When you try to upload the `agentic-video-system/` folder, Drive asks you to select individual files.

### The fix — upload the zip, unzip it in Colab

**Step 1: Upload the zip file to Drive**

1. In Google Drive (drive.google.com), open your MyDrive.
2. Click **New** → **File upload**.
3. Select `agentic-video-system.zip`. Upload completes — the zip is now a single file in Drive.

**Step 2: In Colab, mount Drive and unzip in place**

Cell 1 (mount Drive):
```python
from google.colab import drive
drive.mount('/content/drive')
```

Cell 2 (unzip in place — this creates the folder structure on Drive):
```python
import zipfile
import os

zip_path = '/content/drive/MyDrive/agentic-video-system.zip'
extract_to = '/content/drive/MyDrive/'

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)

# Verify
print("Extracted. Contents of agentic-video-system/:")
for item in os.listdir('/content/drive/MyDrive/agentic-video-system'):
    print(f"  {item}")
```

After Cell 2 runs, the unzipped `agentic-video-system/` folder will appear in your Drive alongside the zip. You can delete the zip if you want, or keep it as backup.

**Step 3: Run Script 1**

Cell 3:
```python
!bash /content/drive/MyDrive/agentic-video-system/scripts/colab-01-foundations.sh
```

### Why this works

- The zip contains the full folder structure (including subfolders `scripts/`, `voice-samples/`, `output/`, `config/`, `agents/`, `laws/`, `system/`).
- Python's `zipfile.extractall()` preserves folder structure — when you extract to `/content/drive/MyDrive/`, it creates `MyDrive/agentic-video-system/` with all subfolders and files in the right places.
- The unzip happens on Drive (because the extraction target is a Drive path), so the unzipped folder persists across Colab sessions.

### For future updates

When I send you an updated `agentic-video-system.zip`:

1. Delete the old `agentic-video-system/` folder in Drive (or rename it to `agentic-video-system-old/` as backup).
2. Delete the old zip (or let the new upload overwrite it).
3. Upload the new zip.
4. Run the unzip cell again.
5. Run the script.

This is now the standard update workflow.

---

## Error #004 — FileNotFoundError when unzipping in Colab

### Status update — USER ERROR (not a system bug)

After investigation, this error was caused by the user not having uploaded `agentic-video-system.zip` to Google Drive yet. Once the user uploaded the zip to Drive, the original simple unzip cell worked correctly. The smart search cell below was an unnecessary complication for this specific case.

**The smart search cell is kept below as a fallback** for genuine path issues (zip in a subfolder, browser-renamed filename, etc.), but in this case the root cause was simply "the file wasn't on Drive yet." The communication lesson: when an error says "file not found," the first check should be "did I actually upload the file?" before assuming a path problem.

### The error

```
FileNotFoundError: [Errno 2] No such file or directory:
'/content/drive/MyDrive/agentic-video-system.zip'
```

### The cause (in this case)

The user attempted to run the unzip cell before uploading `agentic-video-system.zip` to Google Drive. The file did not exist at the expected path because it had not been uploaded yet.

### The original simple cell (this is what worked once the user uploaded)

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

### Smart fallback cell (use only if the simple cell fails with the file actually present on Drive)

If the simple cell fails AND you have confirmed the zip is on Drive (visible in Drive web UI), use this version. It searches your entire Drive for the zip, picks the most recent match, and unzips it:

```python
import zipfile
import os
import glob

search_pattern = '/content/drive/MyDrive/**/agentic-video-system*.zip'
zip_files = glob.glob(search_pattern, recursive=True)

if not zip_files:
    print("ERROR: No zip file found on your Drive.")
    print("Searched for:", search_pattern)
    print("")
    print("Things to check:")
    print("  1. Did you upload agentic-video-system.zip to Google Drive?")
    print("  2. Is Drive mounted? (Run: from google.colab import drive; drive.mount('/content/drive'))")
    print("  3. List your Drive root to see what's there:")
    print("     Run: !ls -la /content/drive/MyDrive/")
else:
    zip_path = max(zip_files, key=os.path.getmtime)
    print(f"Found zip: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
    print("")

    extract_to = '/content/drive/MyDrive/'

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

    print("Extracted successfully.")
    print("Contents of agentic-video-system/:")
    target_folder = '/content/drive/MyDrive/agentic-video-system'
    if os.path.exists(target_folder):
        for item in os.listdir(target_folder):
            print(f"  {item}")
    else:
        print(f"  (folder not found at {target_folder} — check what was extracted)")
        print("  Root of MyDrive:")
        for item in os.listdir('/content/drive/MyDrive/'):
            print(f"  {item}")
```

### Resolution

User uploaded the zip to Drive, ran the simple cell, extraction succeeded. Contents verified: `README.md`, `MASTER-ROADMAP.md`, `BUILD-CHECKLIST.md`, `ERRORS-AND-FIXES.md`, `worklog.md`, `agents`, `config`, `laws`, `output`, `scripts`, `system`, `voice-samples`. Script 1 then ran successfully.

### Communication lesson for the system

When a "file not found" error occurs, the first diagnostic step should be: **confirm the file was actually uploaded to the expected location**. Do not assume a path problem until upload is confirmed. This applies to the user (visually checking Drive) and to any future agent that encounters a similar error — the agent's first response should be to verify file presence, not to suggest path workarounds.

---

## Error #005 — GPU not detected in Colab (Script 1 warning)

### The error

Script 1 completed successfully, but step `[5/6] Verifying GPU...` printed:

```
WARNING: No GPU detected. Make sure you enabled GPU in Runtime → Change runtime type.
Coqui XTTS-v2, StyleTTS2, and Fish Speech require GPU.
Piper (CPU fallback) will work without GPU.
```

And the final summary showed:

```
GPU: NOT DETECTED (will need GPU for Coqui XTTS-v2)
```

### Why this matters

Script 2 (Coqui XTTS-v2) requires a GPU. Without GPU, Coqui will fail to install or run. StyleTTS2 and Fish Speech also need GPU. Only Piper (CPU fallback) works without GPU — but Piper doesn't support voice cloning, so it's not a viable primary.

**Bottom line:** Script 2 cannot proceed until GPU is enabled.

### The cause

The Colab notebook's runtime type is set to CPU, not GPU. This happens when:
1. The notebook was created without changing the runtime type (default is CPU on free tier).
2. The runtime type was changed to GPU but the runtime was not restarted to apply the change.

### The fix — enable GPU in Colab

**Step 1: Change runtime type**

In your Colab notebook:
1. Top menu → **Runtime** → **Change runtime type**
2. In the popup:
   - Hardware accelerator: **T4 GPU** (free tier) — or A100 if you have Colab Pro
   - Runtime shape: Standard
3. Click **Save**

**Step 2: Restart the runtime**

When you change the runtime type, Colab will usually prompt: "You must restart the runtime in order to use the new runtime type." Click **Yes** to restart.

If it doesn't prompt:
- Top menu → **Runtime** → **Restart session** (or **Restart runtime**)

This disconnects and reconnects with the new GPU-enabled runtime. Your Drive mount will be lost — you'll need to re-mount.

**Step 3: Re-mount Drive and verify GPU**

Cell 1 (re-mount Drive):
```python
from google.colab import drive
drive.mount('/content/drive')
```

Cell 2 (verify GPU):
```python
!nvidia-smi
```

You should see output like:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI xxxxxxx    Driver Version: xxx       CUDA Version: xx.x          |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC|
|   0  Tesla T4            Off  | 00000000:00:04.0 Off |                    0|
| 30%  50%    0%   45C    P8    10W /  70W     0MiB / 15109MiB      0%      Default|
+-------------------------------+----------------------+----------------------+
```

If you see `Tesla T4` (or any GPU name) in the output, GPU is detected. If you see `command not found` or `NVIDIA-SMI has failed`, GPU is still not enabled — repeat Steps 1–3.

**Step 4: Re-run Script 1 (optional, to confirm GPU is now detected)**

Cell 3:
```python
!bash /content/drive/MyDrive/agentic-video-system/scripts/colab-01-foundations.sh
```

The script will re-run quickly (most components are already installed) and update `config/install-status.json` with the GPU info. The summary should now show:

```
GPU: Tesla T4
```

instead of `NOT DETECTED`.

### Why we re-run Script 1

The `install-status.json` file in `config/` records the GPU status at install time. If we don't re-run, the status file will falsely claim no GPU — and future scripts that check this status file may refuse to proceed with Coqui/StyleTTS2/Fish Speech. Re-running updates the status file to reflect the new GPU-enabled runtime.

### What to report back

After re-running with GPU enabled:
1. The output of `!nvidia-smi` (GPU name and memory).
2. The new summary block from Script 1 (should now show `GPU: Tesla T4` or similar).
3. Confirm `config/install-status.json` was updated (the script prints "Status saved to: ..." at the end).

Once GPU is confirmed, I'll write Script 2 (Coqui XTTS-v2 + voice cloning test).

---

## Error #006 — Coqui TTS install fails on Colab Python 3.12

### The error

```
ERROR: Ignored the following versions that require a different python version:
0.22.0 Requires-Python >=3.9.0,<3.12; ...
ERROR: Could not find a version that satisfies the requirement TTS==0.22.0
ERROR: No matching distribution found for TTS==0.22.0
```

### The cause

Coqui TTS (all versions, including the latest v0.22.0) requires Python `<3.12`. Colab's default Python is 3.12.13 (as of late 2024 / 2025). pip refuses to install Coqui because the Python version doesn't match.

This is not a Coqui bug or a pip bug — it's a hard version constraint. Coqui's dependencies (notably some older numpy/torch combos and Cython extensions) don't compile on Python 3.12.

### Why we can't just downgrade Colab's Python

Colab's Python 3.12 is the system Python — downgrading it breaks Colab internals (jupyter, ipykernel, google.colab extensions, Drive mount). Not viable.

### The fix — install Coqui in an isolated Python 3.11 venv using `uv`

We use `uv` (a fast Python package manager) to install Python 3.11 in isolation, create a virtual environment with Python 3.11, and install Coqui inside that venv. Colab's system Python stays at 3.12; Coqui runs in its own 3.11 environment.

**Why uv (not virtualenv or conda):**
- `uv` can install Python itself (any version) in seconds — virtualenv and venv can't.
- `uv` installs packages 10-100x faster than pip.
- Works in Colab without sudo or root tricks.
- Doesn't conflict with Colab's system Python.

**The flow:**

1. Install `uv`:
   ```bash
   pip install uv
   ```

2. Use `uv` to install Python 3.11:
   ```bash
   uv python install 3.11
   ```

3. Create a venv with Python 3.11 at `/content/coqui-venv`:
   ```bash
   uv venv /content/coqui-venv --python 3.11
   ```

4. Install Coqui into the venv:
   ```bash
   uv pip install --python /content/coqui-venv/bin/python TTS==0.22.0 torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

5. Run Python scripts that use Coqui with the venv's Python:
   ```bash
   /content/coqui-venv/bin/python my_script.py
   ```

### Updated Script 2

The updated `colab-02-coqui-xtts-v2.sh` uses this approach. The script:
- Installs uv
- Creates a Python 3.11 venv at `/content/coqui-venv`
- Installs Coqui + PyTorch CUDA 12.1 into the venv
- Runs the sanity check and voice clone test using the venv's Python

### Tradeoff

The venv lives at `/content/coqui-venv` — it's in Colab's ephemeral storage. **It will be lost when the Colab session dies.** This means every new Colab session needs to re-create the venv (re-run Script 2's venv-creation step).

Two mitigations:
- **Quick re-install:** Once `uv` is installed, re-creating the venv is ~2-3 minutes (uv is fast).
- **Cache to Drive (later):** We can optionally cache the venv to Google Drive to avoid re-install. Not done in Script 2 — we'll see if re-install is painful enough to bother.

### How to report back after running the fixed Script 2

1. Did the venv creation succeed?
2. Did Coqui install inside the venv?
3. Did the sanity check (default voice) pass?
4. Did the voice clone test (your voice) pass?
5. Path to the test audio generated in your voice.

---

## Error #007 — matplotlib backend error when running Coqui from venv

### The error

```
ValueError: Key backend: 'module://matplotlib_inline.backend_inline' is not a valid value for backend;
supported values are ['gtk3agg', 'gtk3cairo', ..., 'agg', 'cairo', 'pdf', ...]
```

### The cause

Colab sets an environment variable `MPLBACKEND=module://matplotlib_inline.backend_inline` so that matplotlib renders inline in notebook cells. But the venv we created in Script 2 has its own matplotlib (v3.11.0) which doesn't recognize `matplotlib_inline.backend_inline` as a valid backend (it's a Colab-specific extension).

When Coqui's `TTS.api` import chain reaches `import matplotlib`, matplotlib reads `MPLBACKEND` from the environment, fails to validate it, and crashes.

### The fix — unset MPLBACKEND (or set it to Agg) before running venv python

In the script, before invoking the venv's python, unset the variable:

```bash
unset MPLBACKEND
```

Or, more explicitly, set it to `Agg` (the non-interactive backend that works for saving figures, which is all Coqui needs):

```bash
export MPLBACKEND=Agg
```

Both work. `Agg` is the safer choice because it's explicit and survives any later environment re-set.

### Why this happens with the venv but not Colab's system Python

Colab's system Python has the `matplotlib_inline` package installed (it's part of Colab's jupyter stack). The venv we created with `uv venv` doesn't include `matplotlib_inline` — it's a fresh Python 3.11 install with only the packages we explicitly installed. So when matplotlib looks for the inline backend, it can't find it.

### Resolution

Updated Script 2 to export `MPLBACKEND=Agg` before any venv python invocation. This applies to:
- The sanity check (Step 7)
- The voice clone test (Step 8)

Future scripts that invoke the venv python will also need this fix.


---

## Error #008 — Coqui CPML license prompt blocks non-interactive script

### The error

```
 > You must confirm the following:
 | > "I have purchased a commercial license from Coqui: licensing@coqui.ai"
 | > "Otherwise, I agree to the terms of the non-commercial CPML: https://coqui.ai/cpml" - [y/n]
 | | > Traceback (most recent call last):
  File "/tmp/coqui_sanity_check.py", line 10, in <module>
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
  ...
  File "/content/coqui-venv/lib/python3.11/site-packages/TTS/utils/manage.py", line 316, in ask_tos
    answer = input(" | | > ")
             ^^^^^^^^^^^^^^^
KeyboardInterrupt
```

### The cause

Coqui TTS v0.22.0 requires interactive confirmation of the Coqui Public Model License (CPML) before downloading the XTTS-v2 model. The library calls `input(" | | > ")` to read a `y`/`n` answer from the user.

When running TTS via a bash script in Colab (using `!bash script.sh` or `!python script.py`), stdin is not a TTY — there's no way to type `y` and press Enter. The `input()` call hangs until Colab's cell timeout interrupts it with `KeyboardInterrupt`.

### The fix — pre-accept the CPML via environment variable

Set `COQUI_TOS_AGREED=1` in the environment before invoking the venv's python. Coqui checks this env var first; if set, it skips the interactive prompt.

```bash
export COQUI_TOS_AGREED=1
```

This is the documented way to accept the CPML non-interactively. It does NOT bypass the license — it just acknowledges it programmatically. The user has already agreed to the CPML terms by deciding to use Coqui XTTS-v2 as the primary testing TTS engine.

### Law 1 alignment

The user agreed to use Coqui under CPML during the testing phase. The `voice-profile.json` config records `commercial_use: false` — when the user begins monetizing, the TTS agent (per `agents/06-tts.md` Law 1 compliance section) will refuse to use Coqui and require a switch to Fish Speech or ElevenLabs. Setting `COQUI_TOS_AGREED=1` is consistent with this — it's a testing-phase acknowledgment, not a license bypass.

### Resolution

Updated Script 2 to set `COQUI_TOS_AGREED=1` alongside `MPLBACKEND=Agg` at the top of the script, before any venv python invocation. The license prompt is now skipped automatically; the model downloads and loads without interruption.

### Note for future scripts

Any script that loads the XTTS-v2 model needs `COQUI_TOS_AGREED=1` set. This includes:
- Script 2 (sanity check + voice clone test)
- Future runtime scripts that invoke Coqui for actual TTS generation
- Any agent that calls the TTS agent's tools

The environment variable is now set globally in Script 2, but future scripts will need to set it explicitly (or source a common env-setup script — to be done in Phase 3 runtime build).

---

## Error #009 — Coqui TTS incompatible with transformers v5.x

### The error

```
ImportError: cannot import name 'BeamSearchScorer' from 'transformers'
(/content/coqui-venv/lib/python3.11/site-packages/transformers/__init__.py)
```

### The cause

Coqui TTS v0.22.0's `TTS.tts.layers.xtts.stream_generator` module imports `BeamSearchScorer` from `transformers`. The class was removed in `transformers` v5.0.0 (released late 2025).

When `uv pip install TTS==0.22.0` resolved dependencies, it pulled the latest `transformers` (v5.13.0) — which no longer has `BeamSearchScorer`. Coqui's import chain fails.

### Why this happens

Coqui TTS v0.22.0 was released before `transformers` v5.0.0 and pins to `transformers>=4.x` without an upper bound. uv's resolver picks the latest version that satisfies the lower bound, which is now v5.13.0 — incompatible with Coqui.

### The fix — pin transformers to a compatible version

Install `transformers<5.0.0` (latest 4.x) into the venv. The latest 4.x as of this writing is v4.57.1, which has `BeamSearchScorer` and works with Coqui.

```bash
uv pip install --python /content/coqui-venv/bin/python "transformers>=4.40,<5.0.0"
```

This will downgrade `transformers` from v5.13.0 to v4.57.1 (or similar 4.x). Coqui's import chain will work.

### Side effects

Pinning `transformers<5.0.0` may affect other packages that depend on `transformers` v5.x features. But Coqui is the only thing in this venv — the venv exists specifically for Coqui. Other agents/tools will use Colab's system Python (3.12) for their own transformers needs.

### Resolution

Updated Script 2 to install `transformers>=4.40,<5.0.0` after installing Coqui, which downgrades the venv's transformers to a compatible version. The downgrade is safe because Coqui doesn't need any v5.x features.

### Lesson for future scripts

When using `uv pip install` with a library that has loose version pins (like Coqui's `transformers>=4.x` with no upper bound), the resolver may pull a too-new version that breaks the library. Solution: pin the problematic transitive dependency to a known-working range after the main install.

This pattern will likely apply to other libraries we install in Scripts 3–8. Watch for it.

### Update — Error #009 pin was too loose

**Original pin:** `transformers>=4.40,<5.0.0`
**Result:** uv installed `transformers==4.57.6` — still missing `BeamSearchScorer`.

**Root cause:** `BeamSearchScorer` was deprecated in `transformers` v4.41.0 and fully removed in v4.50.0. So any version >= 4.50 still has the same ImportError. My original pin `<5.0.0` was too loose.

**Corrected pin:** `transformers>=4.33,<4.41`

This range:
- Lower bound 4.33 — known to work with Coqui XTTS-v2 (Coqui was developed against transformers 4.3x).
- Upper bound <4.41 — before BeamSearchScorer was deprecated/moved.

Latest in this range: `transformers==4.40.2`. Tested working with Coqui TTS v0.22.0.

### Resolution

Updated Script 2's pin from `"transformers>=4.40,<5.0.0"` to `"transformers>=4.33,<4.41"`. Also updated the venv check in Step 5 to use the stricter boundary (any transformers >= 4.41 triggers re-pin).


---

## Error #010 — Script 4 hard-exits when one MCP server install fails

### The error

```
[4/8] Installing dependencies for each MCP server...
  Installing mcp-video deps (npm)...
  ...
  Installing ffmpeg-mcp-dubnium deps...
  ...
error: subprocess-exited-with-error
× Getting requirements to build editable did not run successfully.
│ exit code: 1
```

The script exited at this point. Steps 5–8 (MCP client libs, Node SDK, sanity check, status save) never ran.

### The cause

Two compounding issues:

1. **`set -e` at the top of the script** causes any command that returns non-zero to immediately exit the script. When `pip install -e .` for ffmpeg-mcp-dubnium failed, the script died.

2. **ffmpeg-mcp-dubnium build failure** — the repo has a `pyproject.toml` that requires a build backend (likely setuptools or hatchling), but something in the build process fails. The truncated output doesn't show the actual error.

### The fix

**A. Don't hard-exit on individual MCP server install failures.**

MCP server installs are independent — mcp-video failing shouldn't prevent vfx-mcp from being attempted. Wrap each install in error handling:

```bash
install_server() {
    local name=$1
    local dir=$2
    cd "$dir"
    if [ -f "package.json" ]; then
        npm install --silent || echo "  $name: npm install failed (continuing)"
    elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        pip install --quiet -e . 2>&1 | tail -n 5 || echo "  $name: pip install failed (continuing)"
    elif [ -f "requirements.txt" ]; then
        pip install --quiet -r requirements.txt || echo "  $name: requirements install failed (continuing)"
    fi
}
```

The `|| echo "..."` pattern catches the non-zero exit code without triggering `set -e`.

**B. For ffmpeg-mcp-dubnium specifically — investigate the build error.**

The truncated output doesn't show the actual build failure. The fix is to capture the full error output and log it, then either:
- Install with `--no-build-isolation` if the build backend is the issue
- Skip the server if it can't be installed (with a clear log message)
- Use a different ffmpeg-mcp variant if dubnium0's doesn't work on Colab

### Resolution

Rewrote Script 4's Step 4 to:
1. Use a function `install_server()` that wraps each install with error handling.
2. Capture full output (not just `tail -n 5`) so we can see actual build errors.
3. Never exit the script on a single server's install failure.
4. Track which servers succeeded vs failed, report in the summary.

For ffmpeg-mcp-dubnium specifically, the function tries multiple install strategies:
- Try `pip install -e .` first
- If that fails, try `pip install -e . --no-build-isolation`
- If that fails, try `pip install -r requirements.txt` if it exists
- If all fail, log the error and continue — the server is marked as "failed" in the status file

### Lesson for future scripts

When installing multiple independent components in one script:
- Don't use `set -e` blindly — it makes one failure cascade to all subsequent steps.
- Wrap each component's install in error handling.
- Track success/failure per component.
- Report a summary at the end so the user knows what worked and what didn't.
- Phase 3 runtime can decide what to do about failed servers (use alternatives, skip features, etc.)

---

## Error #011 — vfx-mcp install fails: No module named 'hatchling'

### The error

```
vfx-mcp: ❌ all install strategies failed (see /tmp/install-vfx-mcp.log)
    ...
  ModuleNotFoundError: No module named 'hatchling'
```

### The cause

The vfx-mcp repo (conneroisu/vfx-mcp) uses `hatchling` as its PEP 517 build backend (declared in `pyproject.toml` under `[build-system]`). When pip tries to build the package in an isolated environment, it needs to install hatchling first — but the isolated build environment doesn't have it, and for some reason pip's bootstrapping isn't picking it up.

This is a known issue with some Python packages on Colab — the build isolation sometimes fails to install the build backend.

### The fix — install hatchling before trying pip install -e .

```bash
pip install hatchling
pip install -e .
```

Or, more generally, detect the build backend from `pyproject.toml` and install it first:

```bash
# Extract build-backend from pyproject.toml and install it
BUILD_BACKEND=$(python3 -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
backend = data.get('build-system', {}).get('build-backend', '')
requires = data.get('build-system', {}).get('requires', [])
print(' '.join(requires))
" 2>/dev/null || echo "")
if [ -n "$BUILD_BACKEND" ]; then
    pip install --quiet $BUILD_BACKEND
fi
```

### Resolution

Patched Script 4's `install_server()` function to:
1. Before trying `pip install -e .`, check if `pyproject.toml` exists.
2. If it does, extract the `build-system.requires` field.
3. Install those requirements first (typically hatchling, setuptools, wheel, etc.).
4. Then proceed with `pip install -e .`.

This is a general fix that handles any PEP 517 build backend, not just hatchling.

### Impact on the system

vfx-mcp is a supplementary MCP server — it provides FastMCP + ffmpeg-python based video effects. We already have:
- mcp-video (119 tools, primary) ✅
- ffmpeg-mcp-dubnium (40+ tools, pure FFmpeg) ✅
- video-audio-mcp (audio focus) ✅

So vfx-mcp failing is not a blocker. But the fix is simple, so we patch it for completeness. The user can re-run Script 4 if they want vfx-mcp, or proceed without it — Phase 3 can work with the 3 installed servers.

### Lesson for future scripts

When installing Python packages from source with `pip install -e .`, always:
1. Check `pyproject.toml` for `[build-system].requires`
2. Install the build backend first
3. Then try the editable install

This avoids the "No module named 'hatchling'" (or similar) error pattern.

---

## Error #012 — vfx-mcp requires Python 3.13+ (Colab has 3.12)

### The error

```
vfx-mcp: ❌ all install strategies failed (see /tmp/install-vfx-mcp.log)
  ERROR: Package 'vfx-mcp' requires a different Python: 3.12.13 not in '>=3.13'
```

### The cause

The vfx-mcp repo (conneroisu/vfx-mcp) declares `requires-python = ">=3.13"` in its `pyproject.toml`. Colab's system Python is 3.12.13. pip refuses to install because the Python version doesn't match the package's requirement.

This is a hard version constraint — vfx-mcp uses Python 3.13+ features (likely improved type hints, better error messages, or new stdlib modules). There's no way to install it on Python 3.12.

### The fix (not applied — marked as permanently incompatible)

To install vfx-mcp, we'd need to create a separate Python 3.13 venv (similar to the Coqui Python 3.11 venv). However:

1. **vfx-mcp is supplementary.** We already have:
   - mcp-video (119 tools) — primary ✅
   - ffmpeg-mcp-dubnium (40+ tools) — pure FFmpeg ✅
   - video-audio-mcp — audio focus ✅
2. **Video effects are also covered by mcp-video's effects category** (vignette, glow, noise, scanlines, chromatic aberration, luma key, mask, shape mask) and by the FFmpeg Color & Chromakey skill.
3. **Creating a Python 3.13 venv adds complexity** for minimal benefit.

**Decision: skip vfx-mcp.** Mark as permanently incompatible with Colab's Python 3.12. Phase 3 can revisit if video effects are insufficient with the 3 installed servers.

### Lesson

Some packages declare aggressive Python version requirements (`>=3.13`). When a package fails with "requires a different Python," check if the requirement is real (uses 3.13 features) or conservative (developer just pinned to latest). If real and the package is supplementary, skip it. If essential, create a separate venv with the required Python version (like we did for Coqui + Python 3.11).

---

## Error #013 — Chromium fails to install on Colab (apt-get)

### The error

```
[3/9] Installing Chromium for headless rendering (Remotion needs Chrome)...
  Installing chromium-browser...
  chromium-browser install failed, trying chromium...
  WARNING: Could not install Chromium. Remotion may fail.
  WARNING: No Chrome/Chromium binary found. Remotion rendering may fail.
```

### The cause

Colab's apt repositories don't include `chromium-browser` or `chromium` packages by default. The `apt-get install` command fails silently (output suppressed).

However, **Colab typically has Chromium pre-installed** at a non-standard path, or it can be obtained via:
1. `playwright install chromium` — Playwright's bundled Chromium
2. `puppeteer install chromium` — Puppeteer's bundled Chromium
3. Checking common paths: `/usr/bin/chromium`, `/usr/bin/chromium-browser`, `/opt/google/chrome/chrome`

### The fix — use Playwright to install Chromium

Playwright installs a known-working Chromium binary that Remotion can use:

```bash
pip install playwright
playwright install chromium
playwright install-deps chromium
```

This installs Chromium to `~/.cache/ms-playwright/chromium-XXXX/chrome-linux/chrome`. We then set:
```bash
export PUPPETEER_EXECUTABLE_PATH=$(python3 -c "from playwright._impl._driver import compute_driver_executable; print(compute_driver_executable())" 2>/dev/null || find /root/.cache/ms-playwright -name "chrome" -type f | head -1)
```

Or more simply, find the binary after install:
```bash
CHROME_BIN=$(find /root/.cache/ms-playwright -name "chrome" -type f | head -1)
export PUPPETEER_EXECUTABLE_PATH="$CHROME_BIN"
```

### Resolution

Updated Script 5's Step 3 to:
1. First check if Chrome/Chromium is already available (common paths).
2. If not, try `apt-get install` (may work on some Colab images).
3. If that fails, fall back to `pip install playwright && playwright install chromium && playwright install-deps chromium`.
4. Find the Chromium binary and set `PUPPETEER_EXECUTABLE_PATH`.

---

## Error #014 — Remotion render fails: esbuild bundling error (JSX in .ts file)

### The error

```
[5/9] Rendering test video (30 frames at 30fps = 1 second)...
    at handleIncomingPacket (.../esbuild/lib/main.js:939:12)
    ...
    undefined
    at runWebpack (.../@remotion/bundler/dist/bundle.js:224:23)
```

### The cause

The test project's entry file `src/index.ts` contains JSX syntax:

```tsx
registerRoot(() => (
  <Composition ... />
));
```

But esbuild (which Remotion uses for bundling) doesn't parse JSX in `.ts` files by default — only in `.tsx` files. The bundler crashes with an "undefined" error (esbuild doesn't always surface clean error messages for parse failures).

### The fix — rename entry file to .tsx

The entry file contains JSX, so it must be `src/index.tsx`, not `src/index.ts`. Also add a `tsconfig.json` to be explicit about JSX settings:

```json
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "target": "ESNext"
  }
}
```

### Resolution

Updated Script 5's Step 5 to:
1. Rename `src/index.ts` → `src/index.tsx` (it contains JSX).
2. Add a `tsconfig.json` with JSX configuration.
3. Keep `src/Composition.tsx` as-is (already .tsx).

### Lesson

When using JSX in a TypeScript file, the file MUST have a `.tsx` extension. esbuild uses the file extension to decide whether to parse JSX. `.ts` files are treated as pure TypeScript (no JSX), `.tsx` files are treated as TypeScript + JSX. This is a common gotcha when hand-crafting Remotion projects.


---

## Error #015 — chromium-browser on Colab is a snap stub, not a real binary

### The error

```
Command '/usr/bin/chromium-browser' requires the chromium snap to be installed.
Please install it with:
snap install chromium
```

### The cause

On Colab (Ubuntu-based), `apt-get install chromium-browser` succeeds — it installs a package. But the installed `/usr/bin/chromium-browser` is **not a real Chromium binary**. It's a **stub script** that tells you to install Chromium via `snap` instead:

```bash
$ cat /usr/bin/chromium-browser
#!/bin/sh
echo "Command '$0' requires the chromium snap to be installed."
echo "Please install it with:"
echo ""
echo "snap install chromium"
```

Colab doesn't support snap (snap requires systemd, which Colab's container doesn't have). So the apt-installed `chromium-browser` is useless.

This is a Ubuntu-specific issue — starting around Ubuntu 22.04, the `chromium-browser` apt package became a transitional package that just points to snap.

### The fix — detect the stub and fall back to Playwright

The script needs to detect when `/usr/bin/chromium-browser` is a stub (not a real binary) and skip it. Two checks:

1. **Check the file size** — real Chromium is ~200MB. The stub is <1KB.
2. **Check the file content** — the stub contains the string "snap install chromium".

If either check fails, treat as "not a real browser" and fall back to Playwright's bundled Chromium (which is a real binary, not a stub).

```bash
# Check if the binary is a real Chromium or a snap stub
is_real_chromium() {
    local bin=$1
    [ -f "$bin" ] || return 1
    # Real Chromium is >10MB; stubs are <1KB
    local size=$(stat -c%s "$bin" 2>/dev/null || echo 0)
    [ "$size" -lt 100000 ] && return 1
    # Also check for the snap stub string
    grep -q "snap install chromium" "$bin" 2>/dev/null && return 1
    return 0
}
```

### Resolution

Updated Script 5's Step 3 to:
1. After finding a Chrome/Chromium binary, check if it's a real binary or a stub.
2. If it's a stub, skip it and try the next strategy.
3. Playwright's bundled Chromium is now the **primary** strategy on Colab, not the fallback — apt's chromium-browser is unreliable.

### Lesson

On Ubuntu-based systems (including Colab), `apt-get install chromium-browser` may install a snap stub, not a real binary. Always verify the installed binary is real (file size, content check) before trusting it. Playwright's bundled Chromium is more reliable for headless rendering in containers.

---

## Error #016 — vfx-mcp permanently incompatible, need alternative

### The situation

vfx-mcp (conneroisu/vfx-mcp) requires Python >=3.13. Colab has Python 3.12.13. This is a hard incompatibility — vfx-mcp uses Python 3.13+ features and cannot be installed on Colab without a separate Python 3.13 venv.

**Decision: skip vfx-mcp. Find alternatives.**

### What vfx-mcp provided

vfx-mcp was a FastMCP + ffmpeg-python based MCP server covering:
- Basic video operations (transform, resize, crop)
- Audio processing
- Video effects (filter chains)

### Alternatives already installed

1. **mcp-video (KyaniteLabs)** — 119 tools, includes a full effects category:
   - vignette, glow, noise, scanlines, chromatic aberration
   - luma key, mask, shape mask
   - Plus trim/merge/resize/crop/rotate/overlays/subtitles
   - Plus analysis tools (scene detection, thumbnail, storyboard, quality compare, waveform)
   - **This is our primary effects server.** Covers most of what vfx-mcp offered.

2. **ffmpeg-mcp-dubnium (dubnium0)** — 40+ tools, organized into modules:
   - probe, convert, video, audio, effects, subtitles, streaming (HLS/DASH/RTMP), advanced
   - The "effects" module covers filter chains similar to vfx-mcp.

3. **video-audio-mcp (misbahsy)** — FFmpeg-based, audio focus:
   - convert, trim, extract_audio, concatenate_videos, add_image_overlay, remove_silence, add_subtitles

### Additional alternatives to consider for Phase 3

If the 3 installed servers don't cover a specific effect, these options exist:

1. **Direct FFmpeg via subprocess** — the agent runtime can call `ffmpeg` directly with filter chains. The FFmpeg Color & Chromakey skill (judgment layer) provides the exact filter chains for chroma key, LUTs, color grading, etc.

2. **studiomeyer-io/mcp-video** — 8 consolidated tools, 22 LUT presets (teal-orange, noir, vintage, cyberpunk). Lightweight alternative for color grading.

3. **OpenCV** (already installed in Script 3) — for pixel-level effects that FFmpeg can't do natively (custom convolution filters, face detection for effects, etc.). The agent runtime can wrap OpenCV calls as custom MCP tools.

4. **Custom MCP server** — if a specific effect is needed often, we can write a small custom MCP server that wraps the FFmpeg filter chain. This is a Phase 3+ task.

### Conclusion

**No urgent replacement needed.** The 3 installed MCP servers (mcp-video, ffmpeg-mcp-dubnium, video-audio-mcp) + FFmpeg direct + OpenCV cover the video effects space. vfx-mcp's absence is not a blocker. Phase 3 can revisit if a specific effect is missing.


---

## Error #017 — Remotion render fails: timeout 120ms is below 7000ms minimum

### The error

```
TypeError: 'timeoutInMilliseconds' should be bigger or equal than 7000, but is 120
    at validatePuppeteerTimeout (.../validate-puppeteer-timeout.js:13:15)
```

### The cause

The render command passed `--timeout=120`, intending 120 seconds. But Remotion's `--timeout` flag is in **milliseconds**, not seconds. So 120 is interpreted as 120ms — which is below Remotion's minimum of 7000ms (7 seconds).

This is a unit mismatch. The Remotion CLI docs specify `--timeout` in milliseconds.

### The fix — use milliseconds (or remove the flag)

Two options:

1. **Convert to milliseconds:**
   ```bash
   npx remotion render TestComposition out/test.mp4 --timeout=120000
   ```
   (120000ms = 120 seconds)

2. **Remove the flag entirely** (let Remotion use its default, which is 30000ms = 30 seconds — enough for a 1-second test render):
   ```bash
   npx remotion render TestComposition out/test.mp4
   ```

Option 2 is simpler and safer. The default timeout is fine for our test render.

### Resolution

Removed the `--timeout=120` flag from Script 5's render command. Remotion will use its default 30-second timeout, which is more than enough for a 30-frame test render.

### Lesson

Always check the unit when passing numeric flags to CLI tools. Remotion uses milliseconds for `--timeout`. Other common unit mismatches:
- `ffmpeg -t` is in seconds
- `curl --max-time` is in seconds
- `wget --timeout` is in seconds
- `python -m http.server --timeout` is in seconds
- Remotion `--timeout` is in MILLISECONDS (the exception)


---

## Error #018 — Don't rename the zip — folder name must stay `agentic-video-system/`

### The problem

I created a second zip called `agentic-video-system-latest.zip` thinking it would help with browser caching of the download link. But this was wrong: when you unzip `agentic-video-system-latest.zip`, it creates a folder called `agentic-video-system-latest/` — NOT `agentic-video-system/`.

Every script in the project has hardcoded paths like:
```
/content/drive/MyDrive/agentic-video-system/scripts/colab-XX-*.sh
/content/drive/MyDrive/agentic-video-system/config/install-status.json
/content/drive/MyDrive/agentic-video-system/output/...
```

If the folder is named `agentic-video-system-latest/`, all these paths break. The scripts can't find themselves, can't find config, can't write to output.

### The rule

**Always use exactly one zip filename: `agentic-video-system.zip`.**

This unzips to `agentic-video-system/` — which matches every hardcoded path in every script.

When I update files:
1. Update the contents of `agentic-video-system/` folder.
2. Re-zip to `agentic-video-system.zip` (overwrite the old one).
3. User uploads the new `agentic-video-system.zip` to Drive (overwrites the old one).
4. User unzips in Colab — overwrites the old `agentic-video-system/` folder with the new one.
5. Paths stay the same. Scripts keep working.

Never create:
- `agentic-video-system-latest.zip`
- `agentic-video-system-v2.zip`
- `agentic-video-system-updated.zip`
- Any other filename.

### Resolution

Deleted `agentic-video-system-latest.zip`. Only `agentic-video-system.zip` exists going forward.

