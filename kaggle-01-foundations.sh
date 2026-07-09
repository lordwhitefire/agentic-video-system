#!/bin/bash
# =============================================================================
# Kaggle Setup Script 1 — Foundations
# Agentic Video Editing System
# =============================================================================
# This script installs the foundational dependencies for the agentic video
# editing system on a Kaggle notebook (with GPU enabled).
#
# What this installs:
#   - System packages: ffmpeg, build-essential, git, curl, wget
#   - Node.js LTS (for Remotion, HyperFrames, MCP servers that need Node)
#   - Python utilities: pip, virtualenv, jupyter extras
#   - Verifies GPU availability (CUDA)
#   - Verifies Python and Node versions
#
# How to run on Kaggle:
#   1. Create a new notebook with GPU enabled (Settings → Accelerator → GPU T4 x2)
#   2. Enable internet (Settings → Internet → On)
#   3. In a code cell, paste:
#        !bash /kaggle/input/<dataset-name>/kaggle-01-foundations.sh
#      OR upload this file as a Kaggle Dataset, attach it to your notebook,
#      and run the command above.
#   4. Alternatively, paste the entire script content into a cell with %%bash
#
# Expected runtime: ~5-10 minutes
# =============================================================================

set -e  # exit on first error

echo "===================================================="
echo "Agentic Video Editing System — Kaggle Setup Script 1"
echo "Foundations"
echo "===================================================="
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
# Step 4: Install Node.js LTS (Kaggle may have an older version)
# -----------------------------------------------------------------------------
echo "[4/6] Installing Node.js LTS..."
# Check if Node.js is already installed and recent enough
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
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo ""
    echo "CUDA version:"
    nvcc --version 2>/dev/null | grep "release" || echo "nvcc not in PATH (PyTorch CUDA will still work)"
else
    echo "WARNING: No GPU detected. Make sure you enabled GPU in notebook settings."
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
if command -v nvidia-smi &> /dev/null; then
    echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
else
    echo "GPU: NOT DETECTED (will need GPU for Coqui XTTS-v2)"
fi
echo ""
echo "Next step: Run kaggle-02-coqui-xtts-v2.sh to install Coqui XTTS-v2"
echo "and test the voice cloning workflow."
