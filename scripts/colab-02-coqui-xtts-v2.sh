#!/bin/bash
# =============================================================================
# Colab Setup Script 2 — Coqui XTTS-v2 (Python 3.11 venv approach)
# Agentic Video Editing System
# =============================================================================
# Coqui TTS requires Python <3.12. Colab's default Python is 3.12.
# Solution: use `uv` to install Python 3.11 in isolation, create a venv,
# install Coqui into the venv. Colab's system Python stays at 3.12.
#
# See ERRORS-AND-FIXES.md Error #006 for the full explanation.
#
# What this script does:
#   1. Verifies Script 1 (foundations) has been run.
#   2. Verifies GPU is available.
#   3. Installs `uv` (fast Python package manager).
#   4. Uses `uv` to install Python 3.11.
#   5. Creates a venv at /content/coqui-venv with Python 3.11.
#   6. Installs PyTorch (CUDA 12.1) + Coqui TTS v0.22.0 + audio libs into venv.
#   7. Sanity check — generate audio with default voice (using venv's python).
#   8. Voice sample demand (Law 1 — no inference):
#      - If sample exists: clone voice, store clone ID, generate test audio.
#      - If no sample: emit voice_sample_demand flag, exit cleanly.
#   9. Save status to config/install-status.json.
#
# How to run on Colab:
#   1. Make sure Script 1 has been run successfully.
#   2. Mount Drive.
#   3. !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-02-coqui-xtts-v2.sh
#
# Expected runtime: 8-15 minutes (uv is fast; model download ~1.8GB is the slow part)
# =============================================================================

set -e  # exit on first error

# -----------------------------------------------------------------------------
# Locate the project root
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/output"
VOICE_SAMPLES_DIR="$PROJECT_ROOT/voice-samples"

# Venv location — in Colab ephemeral storage (NOT Drive — Drive is too slow for venvs)
VENV_DIR="/content/coqui-venv"
VENV_PYTHON="$VENV_DIR/bin/python"

# Colab sets MPLBACKEND to matplotlib_inline which the venv's matplotlib doesn't recognize.
# Set to Agg (non-interactive) so matplotlib imports cleanly inside the venv.
# See ERRORS-AND-FIXES.md Error #007.
export MPLBACKEND=Agg

# Coqui TTS requires interactive CPML license confirmation on first model download.
# Set COQUI_TOS_AGREED=1 to pre-accept non-interactively (script can't read stdin).
# This does NOT bypass the license — it acknowledges it programmatically.
# User has agreed to CPML by choosing Coqui as the testing-phase TTS engine.
# voice-profile.json records commercial_use: false; TTS agent will refuse Coqui
# when commercial_use becomes true (see agents/06-tts.md Law 1 compliance).
# See ERRORS-AND-FIXES.md Error #008.
export COQUI_TOS_AGREED=1

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 2"
echo "Coqui XTTS-v2 (Python 3.11 venv) + Voice Clone Test"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Venv location: $VENV_DIR"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Verify Script 1 has been run
# -----------------------------------------------------------------------------
echo "[1/9] Verifying Script 1 (foundations) has been run..."
STATUS_FILE="$CONFIG_DIR/install-status.json"
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: $STATUS_FILE not found."
    echo "Script 1 (colab-01-foundations.sh) must be run first."
    exit 1
fi
echo "Found: $STATUS_FILE"
echo "[1/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Verify GPU
# -----------------------------------------------------------------------------
echo "[2/9] Verifying GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: No GPU detected. Enable: Runtime → Change runtime type → T4 GPU."
    exit 1
fi
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
echo "GPU detected: $GPU_NAME"
echo "[2/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Install uv (fast Python package manager)
# -----------------------------------------------------------------------------
echo "[3/9] Installing uv..."
pip install --quiet uv
echo "uv installed: $(uv --version)"
echo "[3/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Install Python 3.11 via uv
# -----------------------------------------------------------------------------
echo "[4/9] Installing Python 3.11 via uv..."
uv python install 3.11
echo "Python 3.11 installed."
echo "[4/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Create venv with Python 3.11 (skip if already exists with Coqui)
# -----------------------------------------------------------------------------
echo "[5/9] Creating venv at $VENV_DIR..."

# Check if venv already exists AND has Coqui installed AND has compatible transformers
# Note: BeamSearchScorer was deprecated in transformers v4.41 and removed in v4.50.
# Coqui imports it, so any transformers >= 4.41 will fail. Must be < 4.41.
# See ERRORS-AND-FIXES.md Error #009.
VENV_HAS_COQUI="no"
if [ -f "$VENV_PYTHON" ]; then
    VENV_HAS_COQUI=$($VENV_PYTHON -c "
try:
    import TTS
    # Check transformers version — Coqui needs <4.41 (BeamSearchScorer removed in 4.50)
    import transformers
    version_parts = transformers.__version__.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1])
    if major > 4 or (major == 4 and minor >= 41):
        print('transformers_too_new')
    else:
        print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")
fi

if [ "$VENV_HAS_COQUI" = "yes" ]; then
    echo "  Existing venv found with Coqui + compatible transformers — skipping venv creation."
    echo "  (To force re-install, delete $VENV_DIR and re-run this script.)"
    echo "  Python version: $($VENV_PYTHON --version)"
elif [ "$VENV_HAS_COQUI" = "transformers_too_new" ]; then
    echo "  Existing venv found but transformers is too new (>=4.41). Pinning to <4.41..."
    uv pip install --python "$VENV_PYTHON" "transformers>=4.33,<4.41"
    echo "  transformers pinned. Python version: $($VENV_PYTHON --version)"
else
    # Either no venv, or venv exists but Coqui not installed — fresh start
    if [ -d "$VENV_DIR" ]; then
        echo "  Existing venv found but Coqui not installed — removing for fresh install."
        rm -rf "$VENV_DIR"
    fi
    uv venv "$VENV_DIR" --python 3.11
    echo "  Venv created."
    echo "  Python version: $($VENV_PYTHON --version)"
fi
echo "[5/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Install PyTorch + Coqui TTS + audio libs into venv (skip if already installed)
# -----------------------------------------------------------------------------
echo "[6/9] Installing PyTorch (CUDA 12.1) + Coqui TTS v0.22.0 + audio libs..."

if [ "$VENV_HAS_COQUI" = "yes" ]; then
    echo "  Coqui + compatible transformers already installed in venv — skipping install."
elif [ "$VENV_HAS_COQUI" = "transformers_too_new" ]; then
    echo "  transformers was just pinned in Step 5 — skipping full install."
else
    echo "  (This takes a few minutes — uv is fast but the packages are large.)"

    # Install PyTorch with CUDA 12.1
    uv pip install --python "$VENV_PYTHON" \
        torch torchvision torchaudio \
        --index-url https://download.pytorch.org/whl/cu121

    # Install Coqui TTS
    uv pip install --python "$VENV_PYTHON" TTS==0.22.0

    # Install audio support libraries
    uv pip install --python "$VENV_PYTHON" librosa soundfile scipy numpy

    # Pin transformers to <4.41 — Coqui imports BeamSearchScorer which was
    # deprecated in transformers v4.41 and removed in v4.50. uv's resolver
    # pulls latest transformers which breaks Coqui's import chain.
    # Range 4.33-4.40 is known to work with Coqui XTTS-v2.
    # See ERRORS-AND-FIXES.md Error #009.
    echo "  Pinning transformers to <4.41 (Coqui compatibility)..."
    uv pip install --python "$VENV_PYTHON" "transformers>=4.33,<4.41"
fi

echo "All packages installed into venv."
echo "  PyTorch: $($VENV_PYTHON -c 'import torch; print(torch.__version__)')"
echo "  CUDA available: $($VENV_PYTHON -c 'import torch; print(torch.cuda.is_available())')"
echo "  GPU: $($VENV_PYTHON -c 'import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")')"
echo "  Coqui TTS: $($VENV_PYTHON -c 'import TTS; print(getattr(TTS, "__version__", "installed"))')"
echo "  transformers: $($VENV_PYTHON -c 'import transformers; print(transformers.__version__)')"
echo "[6/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Sanity check — generate audio with default Coqui voice
# -----------------------------------------------------------------------------
echo "[7/9] Sanity check: generating test audio with Coqui's default voice..."
mkdir -p "$OUTPUT_DIR/coqui-test"

# Write the sanity check script to a temp file, run with venv python
cat > /tmp/coqui_sanity_check.py << PYEOF
import torch
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"  Using device: {device}")
if device == "cpu":
    print("  WARNING: Running on CPU. Generation will be slow.")

print("  Loading XTTS-v2 model (first run downloads ~1.8GB, be patient)...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

test_text = "Hello, this is a test of the Coqui XTTS version 2 voice generation system."
output_path = "$OUTPUT_DIR/coqui-test/sanity-check.wav"
print(f"  Generating: '{test_text}'")
tts.tts_to_file(
    text=test_text,
    file_path=output_path,
    language="en",
    speaker="Ana Florence"
)
print(f"  Saved: {output_path}")
print("  Sanity check PASSED.")
PYEOF

$VENV_PYTHON /tmp/coqui_sanity_check.py
echo "[7/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 8: Voice sample demand (Law 1 — no inference)
# -----------------------------------------------------------------------------
echo "[8/9] Voice sample demand (Law 1: No Inference)..."
echo ""

# Look for any voice sample in voice-samples/ folder
VOICE_SAMPLE=$(find "$VOICE_SAMPLES_DIR" -type f \( -name "*.wav" -o -name "*.mp3" \) 2>/dev/null | head -n 1)

if [ -z "$VOICE_SAMPLE" ]; then
    echo "============================================================"
    echo "VOICE SAMPLE DEMAND — Law 1 (No Inference)"
    echo "============================================================"
    echo ""
    echo "STATUS: voice_sample_demand"
    echo ""
    echo "No voice sample found in:"
    echo "  $VOICE_SAMPLES_DIR"
    echo ""
    echo "REQUIREMENTS:"
    echo "  - Duration: 6+ seconds (10-30 seconds ideal)"
    echo "  - Format: WAV or MP3"
    echo "  - Content: clean speech, no background music,"
    echo "    no other speakers, single speaker (you only)"
    echo "  - Recommended: natural conversational pace, varying intonation"
    echo ""
    echo "ACTION REQUIRED:"
    echo "  Upload your voice sample to:"
    echo "    $VOICE_SAMPLES_DIR/my-voice-v1.wav"
    echo ""
    echo "  Then re-run this script. The script will:"
    echo "    1. Detect your voice sample."
    echo "    2. Perform cloning with Coqui XTTS-v2."
    echo "    3. Store the clone ID in config/voice-profile.json."
    echo "    4. Generate a test audio in YOUR voice."
    echo ""
    echo "NOTE: This script does NOT proceed with a stock voice pretending"
    echo "to be your clone. That would be a Law 1 violation (silent substitution)."
    echo "============================================================"

    # Save status to install-status.json with the demand flag
    cat > /tmp/coqui_save_demand_status.py << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_02_coqui_xtts_v2"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "approach": "uv_python_311_venv",
    "venv_path": "$VENV_DIR",
    "tts_library": "TTS==0.22.0",
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "gpu": "$GPU_NAME",
    "sanity_check_passed": True,
    "voice_clone_test": "awaiting_sample",
    "voice_sample_demand": True,
    "voice_sample_path_required": "$VOICE_SAMPLES_DIR/my-voice-v1.wav"
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status updated: {status_file}")
print(f"voice_sample_demand flag set to: True")
PYEOF
    /usr/bin/python3 /tmp/coqui_save_demand_status.py  # use system python for json (faster)
    exit 0
fi

echo "Voice sample found: $VOICE_SAMPLE"
echo ""

# -----------------------------------------------------------------------------
# Step 8b: Perform voice cloning and generate test audio in user's voice
# -----------------------------------------------------------------------------
echo "Performing voice cloning with Coqui XTTS-v2..."
echo ""

cat > /tmp/coqui_voice_clone.py << PYEOF
import torch
import json
import os
import shutil
from datetime import datetime, timezone
from TTS.api import TTS

voice_sample = "$VOICE_SAMPLE"
config_dir = "$CONFIG_DIR"
output_dir = "$OUTPUT_DIR/coqui-test"
voice_profile_path = os.path.join(config_dir, "voice-profile.json")

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"  Device: {device}")

print("  Loading XTTS-v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

test_text = "This is a test of my cloned voice. The Coqui XTTS version 2 system has analyzed my voice sample and is now generating speech that sounds like me."
cloned_output = os.path.join(output_dir, "my-voice-cloned-test.wav")
print(f"  Generating test audio in YOUR voice...")
print(f"  Text: '{test_text}'")
tts.tts_to_file(
    text=test_text,
    file_path=cloned_output,
    language="en",
    speaker_wav=voice_sample
)
print(f"  Saved: {cloned_output}")

# Update voice-profile.json with clone info
print("  Updating voice-profile.json...")
with open(voice_profile_path, 'r') as f:
    profile = json.load(f)

# Coqui doesn't return a "clone ID" — the voice sample path IS the clone reference.
profile["clone_ids"]["coqui_xtts_v2"] = voice_sample
profile["voice_sample_path"] = voice_sample

# Backup the original voice sample to config/ for persistence
config_voice_backup = os.path.join(config_dir, "coqui-voice-reference.wav")
shutil.copy2(voice_sample, config_voice_backup)
print(f"  Voice sample backed up to: {config_voice_backup}")

with open(voice_profile_path, 'w') as f:
    json.dump(profile, f, indent=2)
print(f"  voice-profile.json updated.")
print(f"  clone_ids.coqui_xtts_v2 = {voice_sample}")

print("")
print("  VOICE CLONE TEST PASSED.")
print(f"  Test audio: {cloned_output}")
PYEOF

$VENV_PYTHON /tmp/coqui_voice_clone.py

echo "[8/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 9: Save status
# -----------------------------------------------------------------------------
echo "[9/9] Saving status..."
cat > /tmp/coqui_save_final_status.py << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_02_coqui_xtts_v2"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "approach": "uv_python_311_venv",
    "venv_path": "$VENV_DIR",
    "tts_library": "TTS==0.22.0",
    "model": "tts_models/multilingual/multi-dataset/xtts_v2",
    "gpu": "$GPU_NAME",
    "sanity_check_passed": True,
    "voice_clone_test": "passed",
    "voice_sample_demand": False,
    "voice_sample_path": "$VOICE_SAMPLE",
    "test_audio_path": "$OUTPUT_DIR/coqui-test/my-voice-cloned-test.wav",
    "voice_profile_updated": True
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status saved: {status_file}")
PYEOF
/usr/bin/python3 /tmp/coqui_save_final_status.py
echo "[9/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Script 2 complete."
echo "===================================================="
echo ""
echo "Installed (in Python 3.11 venv at $VENV_DIR):"
echo "  - PyTorch: $($VENV_PYTHON -c 'import torch; print(torch.__version__)')"
echo "  - CUDA available: $($VENV_PYTHON -c 'import torch; print(torch.cuda.is_available())')"
echo "  - GPU: $GPU_NAME"
echo "  - Coqui TTS: $($VENV_PYTHON -c 'import TTS; print(getattr(TTS, "__version__", "installed"))')"
echo ""
echo "Tests:"
echo "  - Sanity check (default voice): PASSED"
if [ -n "$VOICE_SAMPLE" ]; then
    echo "  - Voice clone test (YOUR voice): PASSED"
    echo ""
    echo "Voice profile:"
    echo "  - Sample used: $VOICE_SAMPLE"
    echo "  - Clone ID stored in: config/voice-profile.json"
    echo "  - Test audio (in your voice): $OUTPUT_DIR/coqui-test/my-voice-cloned-test.wav"
    echo "  - Backup of voice sample: config/coqui-voice-reference.wav"
else
    echo "  - Voice clone test: AWAITING SAMPLE (see voice_sample_demand above)"
fi
echo ""
echo "Status file: config/install-status.json"
echo ""
echo "IMPORTANT: The venv at $VENV_DIR is in Colab ephemeral storage."
echo "It will be lost when the Colab session dies. Re-running this script"
echo "in a new session will re-create the venv (~3-5 minutes with uv)."
echo ""
echo "Next step: Run colab-03-analysis-tools.sh to install Whisper, PySceneDetect,"
echo "OpenCV, and Deep SORT for the Analyzer agent."
