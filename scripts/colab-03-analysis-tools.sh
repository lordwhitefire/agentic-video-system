#!/bin/bash
# =============================================================================
# Colab Setup Script 3 — Analysis Tools
# Agentic Video Editing System
# =============================================================================
# Installs the Analyzer agent's tools:
#   - Whisper / faster-whisper (transcription) — into Coqui venv (shares PyTorch)
#   - PySceneDetect (scene boundary detection) — into system Python
#   - OpenCV (computer vision primitives) — into system Python
#   - Deep SORT (object tracking) — into system Python (via pip from GitHub)
#
# What this script does:
#   1. Verifies Script 2 (Coqui) has been run.
#   2. Verifies GPU.
#   3. Installs faster-whisper into the Coqui venv (Python 3.11).
#   4. Installs openai-whisper into the Coqui venv (full Whisper, optional).
#   5. Installs PySceneDetect into system Python (3.12).
#   6. Installs OpenCV into system Python.
#   7. Installs Deep SORT into system Python (from GitHub).
#   8. Sanity check: transcribe a test audio with Whisper (GPU), detect scenes
#      in a test video with PySceneDetect.
#   9. Save status to config/install-status.json.
#
# How to run on Colab:
#   1. Make sure Script 2 has been run successfully.
#   2. Mount Drive.
#   3. !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-03-analysis-tools.sh
#
# Expected runtime: 8-15 minutes (Whisper model download is the slow part)
# =============================================================================

set -e  # exit on first error

# -----------------------------------------------------------------------------
# Locate the project root
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/output"

VENV_DIR="/content/coqui-venv"
VENV_PYTHON="$VENV_DIR/bin/python"
SYSTEM_PYTHON="/usr/bin/python3"

# Environment variables needed for venv (see Errors #007, #008)
export MPLBACKEND=Agg
export COQUI_TOS_AGREED=1

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 3"
echo "Analysis Tools (Whisper, PySceneDetect, OpenCV, Deep SORT)"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Coqui venv:   $VENV_DIR"
echo "System Python: $($SYSTEM_PYTHON --version)"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Verify Script 2 has been run
# -----------------------------------------------------------------------------
echo "[1/9] Verifying Script 2 (Coqui) has been run..."
STATUS_FILE="$CONFIG_DIR/install-status.json"
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: $STATUS_FILE not found. Run Script 1 and Script 2 first."
    exit 1
fi

# Check if Coqui venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERROR: Coqui venv not found at $VENV_DIR."
    echo "Run Script 2 (colab-02-coqui-xtts-v2.sh) first."
    exit 1
fi
echo "Coqui venv found."
echo "[1/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Verify GPU
# -----------------------------------------------------------------------------
echo "[2/9] Verifying GPU..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: No GPU detected. Whisper GPU mode requires GPU."
    exit 1
fi
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
echo "GPU detected: $GPU_NAME"
echo "[2/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Install faster-whisper into Coqui venv (Python 3.11)
# -----------------------------------------------------------------------------
echo "[3/9] Installing faster-whisper into Coqui venv (Python 3.11)..."
echo "  (faster-whisper is 4x faster than openai-whisper with same accuracy)"

# Check if already installed
FWHISPER_INSTALLED=$($VENV_PYTHON -c "
try:
    import faster_whisper
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$FWHISPER_INSTALLED" = "yes" ]; then
    echo "  faster-whisper already installed — skipping."
else
    uv pip install --python "$VENV_PYTHON" faster-whisper
    echo "  faster-whisper installed."
fi

# Print version
$VENV_PYTHON -c "import faster_whisper; print(f'  faster-whisper version: {faster_whisper.__version__}')"
echo "[3/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Install openai-whisper into Coqui venv (full Whisper, fallback)
# -----------------------------------------------------------------------------
echo "[4/9] Installing openai-whisper into Coqui venv (full Whisper, fallback)..."
echo "  (openai-whisper is slower but supports more languages and outputs word-level timestamps)"

OWHISPER_INSTALLED=$($VENV_PYTHON -c "
try:
    import whisper
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$OWHISPER_INSTALLED" = "yes" ]; then
    echo "  openai-whisper already installed — skipping."
else
    uv pip install --python "$VENV_PYTHON" openai-whisper
    echo "  openai-whisper installed."
fi

$VENV_PYTHON -c "import whisper; print(f'  openai-whisper version: {whisper.__version__ if hasattr(whisper, \"__version__\") else \"installed\"}')"
echo "[4/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Install PySceneDetect into system Python (3.12)
# -----------------------------------------------------------------------------
echo "[5/9] Installing PySceneDetect into system Python (3.12)..."

PYSDET_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import scenedetect
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$PYSDET_INSTALLED" = "yes" ]; then
    echo "  PySceneDetect already installed — skipping."
else
    pip install --quiet scenedetect[opencv]
    echo "  PySceneDetect installed."
fi

$SYSTEM_PYTHON -c "import scenedetect; print(f'  scenedetect version: {scenedetect.__version__}')"
echo "[5/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Install OpenCV into system Python
# -----------------------------------------------------------------------------
echo "[6/9] Installing OpenCV into system Python..."

CV2_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import cv2
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$CV2_INSTALLED" = "yes" ]; then
    echo "  OpenCV already installed — skipping."
else
    pip install --quiet opencv-python-headless
    echo "  OpenCV installed."
fi

$SYSTEM_PYTHON -c "import cv2; print(f'  opencv version: {cv2.__version__}')"
echo "[6/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Install Deep SORT into system Python
# -----------------------------------------------------------------------------
echo "[7/9] Installing Deep SORT into system Python..."
echo "  (Deep SORT is not on PyPI — cloning from GitHub)"

DEEPSORT_DIR="/content/deep_sort_realtime"
if [ -d "$DEEPSORT_DIR" ]; then
    echo "  Deep SORT directory already exists — skipping clone."
else
    git clone --depth 1 https://github.com/levan92/deep_sort_realtime.git "$DEEPSORT_DIR"
fi

# Install deep_sort_realtime package
DSORT_INSTALLED=$($SYSTEM_PYTHON -c "
try:
    import deep_sort_realtime
    print('yes')
except ImportError:
    print('no')
" 2>/dev/null || echo "no")

if [ "$DSORT_INSTALLED" = "yes" ]; then
    echo "  deep_sort_realtime already installed — skipping."
else
    cd "$DEEPSORT_DIR"
    pip install --quiet -e .
    cd /
    echo "  deep_sort_realtime installed."
fi

$SYSTEM_PYTHON -c "import deep_sort_realtime; print('  deep_sort_realtime: imported successfully')"
echo "[7/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 8: Sanity checks
# -----------------------------------------------------------------------------
echo "[8/9] Running sanity checks..."
mkdir -p "$OUTPUT_DIR/analysis-test"

# -----------------------------------------------------------------------------
# Sanity Check A: Transcribe the Coqui sanity-check audio with faster-whisper
# -----------------------------------------------------------------------------
echo ""
echo "  Sanity Check A: Transcribe Coqui test audio with faster-whisper..."
SANITY_AUDIO="$OUTPUT_DIR/coqui-test/sanity-check.wav"

if [ ! -f "$SANITY_AUDIO" ]; then
    echo "    WARNING: $SANITY_AUDIO not found."
    echo "    Skipping Whisper sanity check. (Re-run Script 2 to regenerate it.)"
    WHISPER_TEST="skipped"
else
    cat > /tmp/whisper_sanity.py << PYEOF
from faster_whisper import WhisperModel

print("    Loading whisper-small model (first run downloads ~500MB)...")
model = WhisperModel("small", device="cuda", compute_type="float16")

audio_path = "$SANITY_AUDIO"
print(f"    Transcribing: {audio_path}")
segments, info = model.transcribe(audio_path)

print(f"    Detected language: {info.language} (prob: {info.language_probability:.2f})")
print(f"    Transcription:")
full_text = ""
for segment in segments:
    print(f"      [{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
    full_text += segment.text + " "
print(f"    Full text: {full_text.strip()}")
print("    Whisper sanity check PASSED.")
PYEOF
    $VENV_PYTHON /tmp/whisper_sanity.py
    WHISPER_TEST="passed"
fi

# -----------------------------------------------------------------------------
# Sanity Check B: Detect scenes in a test video with PySceneDetect
# -----------------------------------------------------------------------------
echo ""
echo "  Sanity Check B: Detect scenes with PySceneDetect..."

# Create a synthetic test video (2 seconds of solid colors, 2 cuts)
TEST_VIDEO="$OUTPUT_DIR/analysis-test/test-video.mp4"
echo "    Creating synthetic test video with 2 cuts..."
ffmpeg -y -loglevel error \
    -f lavfi -i "color=c=red:s=640x480:d=2" \
    -f lavfi -i "color=c=green:s=640x480:d=2" \
    -f lavfi -i "color=c=blue:s=640x480:d=2" \
    -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1[outv]" \
    -map "[outv]" -c:v libx264 -pix_fmt yuv420p "$TEST_VIDEO"

cat > /tmp/scenedetect_sanity.py << PYEOF
from scenedetect import detect, ContentDetector

video_path = "$TEST_VIDEO"
print(f"    Detecting scenes in: {video_path}")
scenes = detect(video_path, ContentDetector())

print(f"    Detected {len(scenes)} scenes:")
for i, (start, end) in enumerate(scenes):
    print(f"      Scene {i+1}: {start.get_seconds():.2f}s -> {end.get_seconds():.2f}s")

if len(scenes) >= 2:
    print("    PySceneDetect sanity check PASSED. (2+ scenes detected)")
else:
    print("    PySceneDetect sanity check FAILED. (expected 2+ scenes)")
    raise RuntimeError("Scene detection did not find expected cuts")
PYEOF

$SYSTEM_PYTHON /tmp/scenedetect_sanity.py
SCENE_TEST="passed"
echo ""
echo "[8/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 9: Save status
# -----------------------------------------------------------------------------
echo "[9/9] Saving status..."
$SYSTEM_PYTHON << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_03_analysis_tools"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "gpu": "$GPU_NAME",
    "faster_whisper": {
        "installed_in": "coqui_venv",
        "venv_path": "$VENV_DIR",
        "model_default": "small",
        "device": "cuda",
        "compute_type": "float16"
    },
    "openai_whisper": {
        "installed_in": "coqui_venv",
        "venv_path": "$VENV_DIR"
    },
    "pyscenedetect": {
        "installed_in": "system_python",
        "python_version": "$($SYSTEM_PYTHON --version 2>&1)"
    },
    "opencv": {
        "installed_in": "system_python",
        "version": "$($SYSTEM_PYTHON -c 'import cv2; print(cv2.__version__)')"
    },
    "deep_sort": {
        "installed_in": "system_python",
        "source_dir": "$DEEPSORT_DIR"
    },
    "sanity_checks": {
        "whisper_transcription": "$WHISPER_TEST",
        "scene_detection": "$SCENE_TEST"
    }
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status saved: {status_file}")
PYEOF
echo "[9/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Script 3 complete."
echo "===================================================="
echo ""
echo "Installed:"
echo "  In Coqui venv (Python 3.11):"
echo "    - faster-whisper: $($VENV_PYTHON -c 'import faster_whisper; print(faster_whisper.__version__)')"
echo "    - openai-whisper: $($VENV_PYTHON -c 'import whisper; print(getattr(whisper, "__version__", "installed"))')"
echo "  In system Python (3.12):"
echo "    - PySceneDetect: $($SYSTEM_PYTHON -c 'import scenedetect; print(scenedetect.__version__)')"
echo "    - OpenCV: $($SYSTEM_PYTHON -c 'import cv2; print(cv2.__version__)')"
echo "    - deep_sort_realtime: imported successfully"
echo ""
echo "Sanity checks:"
echo "  - Whisper transcription: $WHISPER_TEST"
echo "  - PySceneDetect scene detection: $SCENE_TEST"
echo ""
echo "Status file: config/install-status.json"
echo ""
echo "Next step: Run colab-04-editing-mcp.sh to install MCP servers for the Editor agent"
echo "(mcp-video, kdenlive-mcp-server, VFX MCP, video-audio-mcp, dubnium0/ffmpeg-mcp)."
