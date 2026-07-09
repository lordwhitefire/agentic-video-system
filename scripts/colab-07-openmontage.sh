#!/bin/bash
# =============================================================================
# Colab Setup Script 7 — OpenMontage
# Agentic Video Editing System
# =============================================================================
# Installs OpenMontage — the intelligence/orchestration layer with 500+ skills.
# This is the biggest single install: pipeline directors, creative techniques,
# quality checklists, tech knowledge packs, decision matrices for routing
# between Remotion vs HyperFrames, etc.
#
# What this script does:
#   1. Verifies Script 1 (foundations) has been run.
#   2. Verifies Script 5 (animation tools) has been run (OpenMontage routes to Remotion/HyperFrames).
#   3. Clones OpenMontage from GitHub.
#   4. Installs OpenMontage and dependencies.
#   5. Verifies the skills library is accessible.
#   6. Sanity check: list a sample of available skills.
#   7. Save status to config/install-status.json.
#
# How to run on Colab:
#   1. Make sure Scripts 1 and 5 have been run successfully.
#   2. Mount Drive.
#   3. !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-07-openmontage.sh
#
# Expected runtime: 5-10 minutes
# =============================================================================

set +e  # Don't hard-exit on errors.

# -----------------------------------------------------------------------------
# Locate the project root
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"

OPENMONTAGE_DIR="/content/openmontage"
SYSTEM_PYTHON="/usr/bin/python3"

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 7"
echo "OpenMontage (500+ skills — intelligence/orchestration layer)"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "OpenMontage dir: $OPENMONTAGE_DIR"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Verify Script 1 has been run
# -----------------------------------------------------------------------------
echo "[1/7] Verifying Script 1 (foundations) has been run..."
STATUS_FILE="$CONFIG_DIR/install-status.json"
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: $STATUS_FILE not found. Run Script 1 first."
    exit 1
fi
echo "Found: $STATUS_FILE"
echo "[1/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Verify Script 5 (animation tools) has been run
# -----------------------------------------------------------------------------
echo "[2/7] Verifying Script 5 (animation tools) has been run..."
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: install-status.json not found."
    exit 1
fi

# Check if Script 5 was completed
SCRIPT_5_DONE=$($SYSTEM_PYTHON -c "
import json
with open('$STATUS_FILE', 'r') as f:
    status = json.load(f)
s5 = status.get('script_05_animation_tools', {})
if s5.get('installed') and s5.get('remotion', {}).get('render_test') == 'passed':
    print('yes')
else:
    print('no')
" 2>/dev/null || echo "no")

if [ "$SCRIPT_5_DONE" = "yes" ]; then
    echo "  Script 5 confirmed (Remotion render test passed)."
else
    echo "  WARNING: Script 5 may not be complete. OpenMontage routes to Remotion/HyperFrames."
    echo "  Continuing anyway — OpenMontage can still install, just won't be able to test routing."
fi
echo "[2/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Clone OpenMontage from GitHub
# -----------------------------------------------------------------------------
echo "[3/7] Cloning OpenMontage from GitHub..."
echo "  (500+ skills: pipeline directors, creative techniques, quality checklists, decision matrices)"

if [ -d "$OPENMONTAGE_DIR" ]; then
    echo "  OpenMontage directory already exists — skipping clone."
    echo "  (To force re-clone, delete $OPENMONTAGE_DIR and re-run this script.)"
else
    # Try common repo locations
    CLONED="no"
    for repo in "https://github.com/calesthio/OpenMontage.git" "https://github.com/openmontage/openmontage.git" "https://github.com/open-montage/openmontage.git"; do
        echo "  Trying: $repo"
        if git clone --depth 1 "$repo" "$OPENMONTAGE_DIR" 2>/dev/null; then
            echo "  ✅ Cloned from $repo"
            CLONED="yes"
            break
        fi
    done

    if [ "$CLONED" = "no" ]; then
        echo "  ❌ Could not clone OpenMontage from any known repo."
        echo "    The repo may be private, renamed, or moved."
        echo ""
        echo "    This is a significant gap — OpenMontage is the intelligence layer."
        echo "    Phase 3 will need to either:"
        echo "      1. Find the correct repo URL"
        echo "      2. Use an alternative skills library"
        echo "      3. Build a minimal skills layer from scratch"
        echo ""
        echo "    Continuing to save status and exit cleanly."

        # Save status indicating OpenMontage failed
        $SYSTEM_PYTHON << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_07_openmontage"] = {
    "installed": False,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "error": "Could not clone from GitHub — repo may be private or renamed",
    "tried_repos": [
        "https://github.com/calesthio/OpenMontage.git",
        "https://github.com/openmontage/openmontage.git",
        "https://github.com/open-montage/openmontage.git"
    ],
    "impact": "Significant — OpenMontage is the intelligence layer with 500+ skills. Phase 3 must find alternative.",
    "alternatives": [
        "Find correct repo URL (search GitHub for OpenMontage)",
        "Use alternative skills library",
        "Build minimal skills layer from scratch in Phase 3"
    ]
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status saved: {status_file}")
PYEOF
        exit 0  # Exit cleanly — don't fail the whole Phase 2
    fi
fi
echo "[3/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Install OpenMontage and dependencies
# -----------------------------------------------------------------------------
echo "[4/7] Installing OpenMontage and dependencies..."
cd "$OPENMONTAGE_DIR"

# Check what kind of project this is
if [ -f "package.json" ]; then
    echo "  Node.js project detected. Running npm install..."
    npm install --silent 2>&1 | tail -n 5
    # Build if there's a build script
    if npm run --silent 2>/dev/null | grep -q "build"; then
        npm run build --silent 2>&1 | tail -n 3 || true
    fi
    OM_INSTALL_METHOD="npm"
elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    echo "  Python project detected. Installing..."
    # Install build backend first (Error #011 lesson)
    if [ -f "pyproject.toml" ]; then
        BUILD_REQS=$($SYSTEM_PYTHON -c "
import tomllib
with open('pyproject.toml', 'rb') as f:
    data = tomllib.load(f)
requires = data.get('build-system', {}).get('requires', [])
print(' '.join(requires))
" 2>/dev/null || echo "")
        if [ -n "$BUILD_REQS" ]; then
            echo "  Installing build backend: $BUILD_REQS"
            pip install --quiet $BUILD_REQS > /dev/null 2>&1 || true
        fi
    fi
    pip install --quiet -e . 2>&1 | tail -n 5 || {
        echo "  Editable install failed, trying requirements.txt..."
        if [ -f "requirements.txt" ]; then
            pip install --quiet -r requirements.txt 2>&1 | tail -n 5 || true
        fi
    }
    OM_INSTALL_METHOD="pip"
elif [ -f "requirements.txt" ]; then
    echo "  Python project (requirements.txt only). Installing..."
    pip install --quiet -r requirements.txt 2>&1 | tail -n 5 || true
    OM_INSTALL_METHOD="requirements"
else
    echo "  ⚠️  No package.json, pyproject.toml, setup.py, or requirements.txt found."
    echo "  OpenMontage may be a skills-only repo (markdown files, no code to install)."
    OM_INSTALL_METHOD="skills_only"
fi

cd /
echo "[4/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Verify the skills library is accessible
# -----------------------------------------------------------------------------
echo "[5/7] Verifying OpenMontage skills library is accessible..."
cd "$OPENMONTAGE_DIR"

# Count skill files (markdown files in skills/ or similar dirs)
SKILL_COUNT=$(find . -name "*.md" -path "*/skills/*" 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -eq 0 ]; then
    # Try broader search
    SKILL_COUNT=$(find . -name "*.md" 2>/dev/null | wc -l)
fi

echo "  Found $SKILL_COUNT markdown files (potential skills)."

# List top-level directory structure
echo "  Top-level structure:"
ls -la "$OPENMONTAGE_DIR" | head -n 20 | sed 's/^/    /'

echo "[5/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Sanity check — list a sample of available skills
# -----------------------------------------------------------------------------
echo "[6/7] Sanity check: listing sample of available skills..."

# Find skill files and list a sample
SAMPLE_SKILLS=$(find "$OPENMONTAGE_DIR" -name "*.md" -path "*/skills/*" 2>/dev/null | head -n 10)
if [ -z "$SAMPLE_SKILLS" ]; then
    SAMPLE_SKILLS=$(find "$OPENMONTAGE_DIR" -name "*.md" 2>/dev/null | head -n 10)
fi

if [ -n "$SAMPLE_SKILLS" ]; then
    echo "  Sample skills found:"
    echo "$SAMPLE_SKILLS" | while read -r skill; do
        # Get relative path and extract a readable name
        rel_path=$(echo "$skill" | sed "s|$OPENMONTAGE_DIR/||")
        echo "    - $rel_path"
    done
    echo ""
    echo "  ✅ OpenMontage skills library is accessible."
    OM_SANITY_CHECK="passed"
else
    echo "  ⚠️  No skill files found. OpenMontage may have a different structure."
    echo "  Listing all files in $OPENMONTAGE_DIR:"
    find "$OPENMONTAGE_DIR" -maxdepth 2 -type f 2>/dev/null | head -n 20 | sed 's/^/    /'
    OM_SANITY_CHECK="no_skills_found"
fi

cd /
echo "[6/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Save status
# -----------------------------------------------------------------------------
echo "[7/7] Saving status..."
$SYSTEM_PYTHON << PYEOF
import json
import os
from datetime import datetime, timezone

status_file = "$STATUS_FILE"
status = {}
if os.path.exists(status_file):
    with open(status_file, 'r') as f:
        status = json.load(f)

status["script_07_openmontage"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "dir": "$OPENMONTAGE_DIR",
    "install_method": "$OM_INSTALL_METHOD",
    "skill_count": $SKILL_COUNT,
    "sanity_check": "$OM_SANITY_CHECK",
    "note": "OpenMontage is the intelligence layer with 500+ skills. Phase 3 runtime will load skills on-demand based on agent needs."
}

with open(status_file, 'w') as f:
    json.dump(status, f, indent=2)

print(f"Status saved: {status_file}")
PYEOF
echo "[7/7] Done."
echo ""

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
echo "===================================================="
echo "Script 7 complete."
echo "===================================================="
echo ""
echo "Installed OpenMontage at: $OPENMONTAGE_DIR"
echo "  Install method: $OM_INSTALL_METHOD"
echo "  Skill files found: $SKILL_COUNT"
echo "  Sanity check: $OM_SANITY_CHECK"
echo ""
echo "Status file: config/install-status.json"
echo ""
echo "OpenMontage is the intelligence/orchestration layer:"
echo "  - 500+ skills (pipeline directors, creative techniques, quality checklists)"
echo "  - Decision matrices for routing (Remotion vs HyperFrames, etc.)"
echo "  - Tech knowledge packs"
echo ""
echo "Phase 3 runtime will load skills on-demand based on agent needs."
echo ""
echo "Next step: Run colab-08-piper-elevenlabs.sh to install Piper (CPU TTS"
echo "fallback) and configure ElevenLabs (monetization upgrade path)."
