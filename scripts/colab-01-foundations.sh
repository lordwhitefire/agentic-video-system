#!/bin/bash
# =============================================================================
# Colab Setup Script 1 — Foundations
# Agentic Video Editing System
# =============================================================================
# This script installs foundational dependencies on a Google Colab GPU notebook.
# It is designed to live inside the agentic-video-system/ folder on your Google
# Drive, so it can find its own location and save outputs to the right places.
#
# What this installs:
#   - System packages: ffmpeg, build-essential, git, curl, wget
#   - Node.js LTS (for Remotion, HyperFrames, MCP servers that need Node)
#   - Python utilities: pip, virtualenv, requests, pyyaml, tqdm, rich, python-dotenv
#   - Verifies GPU availability (CUDA)
#   - Saves a status file to config/ so future scripts know foundations are installed
#
# How to run on Colab:
#   1. Upload the entire agentic-video-system/ folder to your Google Drive
#      (so it lives at MyDrive/agentic-video-system/)
#   2. Open colab.research.google.com → New notebook
#   3. Runtime → Change runtime type → T4 GPU → Save
#   4. In a code cell:
#        from google.colab import drive
#        drive.mount('/content/drive')
#   5. In the next code cell:
#        !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-01-foundations.sh
#
# Expected runtime: ~5-10 minutes
# =============================================================================

set -e  # exit on first error

# -----------------------------------------------------------------------------
# Locate the project root (parent of this script's directory)
# This lets the script find config/, output/, etc. no matter where it's run from.
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/output"
VOICE_SAMPLES_DIR="$PROJECT_ROOT/voice-samples"

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 1"
echo "Foundations"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Config dir:   $CONFIG_DIR"
echo "Output dir:   $OUTPUT_DIR"
echo ""

# -----------------------------------------------------------------------------
# Step 1: System packages
# -----------------------------------------------------------------------------
echo "[1/6] Installing system packages..."
apt-get update -y
apt-get install -y \
    ffmpeg \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    software-properties-common \
    libsndfile1 \
    libgl1 \
    libglib2.0-0
echo "[1/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Verify FFmpeg
# -----------------------------------------------------------------------------
echo "[2/6] Verifying FFmpeg..."
ffmpeg -version | head -n 1
echo "[2/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Verify Python and pip
# -----------------------------------------------------------------------------
echo "[3/6] Verifying Python..."
python3 --version
python3 -m pip --version
echo "[3/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Install Node.js LTS (Colab may have an older version)
# -----------------------------------------------------------------------------
echo "[4/6] Installing Node.js LTS..."
NODE_VERSION=$(node --version 2>/dev/null | sed 's/v//' | cut -d. -f1 || echo "0")
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "Node.js version $NODE_VERSION found — installing LTS 20.x..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
else
    echo "Node.js version $NODE_VERSION already installed — skipping."
fi
node --version
npm --version
echo "[4/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Verify GPU availability
# -----------------------------------------------------------------------------
echo "[5/6] Verifying GPU..."
GPU_INFO="NOT_DETECTED"
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader)
    echo ""
    echo "CUDA version:"
    nvcc --version 2>/dev/null | grep "release" || echo "nvcc not in PATH (PyTorch CUDA will still work)"
else
    echo "WARNING: No GPU detected. Make sure you enabled GPU in Runtime → Change runtime type."
    echo "Coqui XTTS-v2, StyleTTS2, and Fish Speech require GPU."
    echo "Piper (CPU fallback) will work without GPU."
fi
echo "[5/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Install Python utility packages
# -----------------------------------------------------------------------------
echo "[6/6] Installing Python utility packages..."
pip install --quiet --upgrade pip
pip install --quiet \
    virtualenv \
    requests \
    pyyaml \
    tqdm \
    rich \
    python-dotenv
echo "[6/6] Done."
echo ""

# -----------------------------------------------------------------------------
# Save status to config/ so future scripts know foundations are installed
# -----------------------------------------------------------------------------
mkdir -p "$CONFIG_DIR"
STATUS_FILE="$CONFIG_DIR/install-status.json"
cat > "$STATUS_FILE" << EOF
{
  "script_01_foundations": {
    "installed": true,
    "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "ffmpeg": "$(ffmpeg -version | head -n 1 | sed 's/ffmpeg version //; s/ Copyright.*//')",
    "node": "$(node --version)",
    "npm": "$(npm --version)",
    "python": "$(python3 --version)",
    "gpu": "$GPU_INFO",
    "colab_runtime": true
  }
}
EOF
echo "Status saved to: $STATUS_FILE"
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Script 1 complete."
echo "===================================================="
echo ""
echo "Installed:"
echo "  - FFmpeg: $(ffmpeg -version | head -n 1)"
echo "  - Node.js: $(node --version)"
echo "  - npm: $(npm --version)"
echo "  - Python: $(python3 --version)"
echo ""
if [ "$GPU_INFO" != "NOT_DETECTED" ]; then
    echo "GPU: $GPU_INFO"
else
    echo "GPU: NOT DETECTED (will need GPU for Coqui XTTS-v2)"
fi
echo ""
echo "Status file written to: config/install-status.json"
echo ""
echo "Next step: Run colab-02-coqui-xtts-v2.sh to install Coqui XTTS-v2"
echo "and test the voice cloning workflow."
