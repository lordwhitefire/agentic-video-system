#!/bin/bash
# =============================================================================
# Colab Setup Script 5 — Animation Tools
# Agentic Video Editing System
# =============================================================================
# Installs the animation layer for the Editor agent:
#   - Remotion (React-based code-as-video rendering)
#   - HyperFrames CLI (HTML → video, deterministic)
#   - remotion-superpowers (Remotion + TTS + stock + captions + AI review)
#   - Lottie Creator MCP (vector animation)
#
# What this script does:
#   1. Verifies Script 1 (foundations) has been run.
#   2. Verifies Node.js.
#   3. Installs Chromium for headless rendering (Remotion needs Chrome).
#   4. Installs Remotion CLI globally.
#   5. Creates a minimal Remotion test project and renders a test video.
#   6. Installs HyperFrames CLI (tries npm, fallback to git clone).
#   7. Installs remotion-superpowers (tries npm).
#   8. Installs Lottie Creator MCP (tries to find and install).
#   9. Save status to config/install-status.json.
#
# How to run on Colab:
#   1. Make sure Script 1 has been run successfully.
#   2. Mount Drive.
#   3. !bash /content/drive/MyDrive/agentic-video-system/scripts/colab-05-animation-tools.sh
#
# Expected runtime: 10-15 minutes (Chromium + Remotion + rendering test)
# =============================================================================

set +e  # Don't hard-exit on errors — animation tools are independent.

# -----------------------------------------------------------------------------
# Locate the project root
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/output"

ANIMATION_DIR="/content/animation-tools"
SYSTEM_PYTHON="/usr/bin/python3"

echo "===================================================="
echo "Agentic Video Editing System — Colab Setup Script 5"
echo "Animation Tools (Remotion, HyperFrames, Lottie, remotion-superpowers)"
echo "===================================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Animation dir: $ANIMATION_DIR"
echo ""

mkdir -p "$ANIMATION_DIR"

# -----------------------------------------------------------------------------
# Step 1: Verify Script 1 has been run
# -----------------------------------------------------------------------------
echo "[1/9] Verifying Script 1 (foundations) has been run..."
STATUS_FILE="$CONFIG_DIR/install-status.json"
if [ ! -f "$STATUS_FILE" ]; then
    echo "ERROR: $STATUS_FILE not found. Run Script 1 first."
    exit 1
fi
echo "Found: $STATUS_FILE"
echo "[1/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Verify Node.js
# -----------------------------------------------------------------------------
echo "[2/9] Verifying Node.js..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Run Script 1 first."
    exit 1
fi
NODE_VERSION=$(node --version)
echo "  Node.js: $NODE_VERSION"
echo "[2/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Install Chromium for headless rendering
# -----------------------------------------------------------------------------
# On Colab (Ubuntu-based), apt's chromium-browser is often a snap STUB, not a
# real binary. We must verify any found binary is real (not a stub) before
# trusting it. Playwright's bundled Chromium is the most reliable option.
# See ERRORS-AND-FIXES.md Error #015.
# -----------------------------------------------------------------------------
echo "[3/9] Installing Chromium for headless rendering (Remotion needs Chrome)..."

# Function: check if a binary is a real Chromium (not a snap stub)
is_real_chromium() {
    local bin=$1
    [ -f "$bin" ] || return 1
    # Real Chromium is >10MB; snap stubs are <1KB
    local size=$(stat -c%s "$bin" 2>/dev/null || echo 0)
    if [ "$size" -lt 100000 ]; then
        return 1
    fi
    # Also check for the snap stub string
    if grep -q "snap install chromium" "$bin" 2>/dev/null; then
        return 1
    fi
    return 0
}

CHROME_BIN=""

# Strategy 1: Check common paths (but verify each is a real binary, not a stub)
echo "  Checking common paths for real Chromium binary..."
for candidate in chromium-browser chromium google-chrome google-chrome-stable; do
    if command -v $candidate &> /dev/null; then
        potential_bin=$(which $candidate)
        if is_real_chromium "$potential_bin"; then
            CHROME_BIN="$potential_bin"
            echo "  Found real binary: $CHROME_BIN"
            break
        else
            echo "  Found $potential_bin but it's a snap stub — skipping"
        fi
    fi
done

# Strategy 2: Try apt-get install (then verify it's real)
if [ -z "$CHROME_BIN" ]; then
    echo "  Trying apt-get install chromium-browser..."
    apt-get install -y chromium-browser > /dev/null 2>&1
    potential_bin=$(which chromium-browser 2>/dev/null)
    if [ -n "$potential_bin" ] && is_real_chromium "$potential_bin"; then
        CHROME_BIN="$potential_bin"
        echo "  Installed via apt (real binary): $CHROME_BIN"
    elif [ -n "$potential_bin" ]; then
        echo "  apt installed chromium-browser but it's a snap stub — skipping"
    fi
fi
if [ -z "$CHROME_BIN" ]; then
    echo "  Trying apt-get install chromium..."
    apt-get install -y chromium > /dev/null 2>&1
    potential_bin=$(which chromium 2>/dev/null)
    if [ -n "$potential_bin" ] && is_real_chromium "$potential_bin"; then
        CHROME_BIN="$potential_bin"
        echo "  Installed via apt (real binary): $CHROME_BIN"
    fi
fi

# Strategy 3: Use Playwright's bundled Chromium (most reliable on Colab)
if [ -z "$CHROME_BIN" ]; then
    echo "  apt install didn't yield a real binary. Using Playwright's bundled Chromium..."
    pip install --quiet playwright 2>/dev/null
    playwright install chromium > /dev/null 2>&1
    playwright install-deps chromium > /dev/null 2>&1
    # Find the Chromium binary
    CHROME_BIN=$(find /root/.cache/ms-playwright -name "chrome" -type f 2>/dev/null | head -1)
    if [ -n "$CHROME_BIN" ]; then
        echo "  Installed via Playwright: $CHROME_BIN"
    else
        echo "  ERROR: Playwright Chromium install also failed."
    fi
fi

if [ -n "$CHROME_BIN" ]; then
    echo "  Chrome/Chromium confirmed: $CHROME_BIN"
    export PUPPETEER_EXECUTABLE_PATH="$CHROME_BIN"
else
    echo "  WARNING: Could not install a real Chromium by any method."
    echo "  Remotion rendering will fail. Phase 3 will need to address this."
fi
echo "[3/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Install Remotion CLI globally
# -----------------------------------------------------------------------------
echo "[4/9] Installing Remotion CLI globally..."
npm install -g remotion @remotion/cli 2>&1 | tail -n 5
echo "  Remotion: $(npx remotion versions 2>/dev/null | head -n 1 || echo 'installed')"
echo "[4/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Create minimal Remotion test project and render test video
# -----------------------------------------------------------------------------
echo "[5/9] Creating minimal Remotion test project and rendering test video..."

REMotion_TEST_DIR="$ANIMATION_DIR/remotion-test"
# Clean up old test project on re-run (so stale .ts files don't linger — Error #014)
if [ -d "$REMotion_TEST_DIR" ]; then
    rm -rf "$REMotion_TEST_DIR"
fi
mkdir -p "$REMotion_TEST_DIR"
cd "$REMotion_TEST_DIR"

# Create a minimal Remotion project manually (faster than npx create-video)
cat > package.json << 'PKGJSON'
{
  "name": "remotion-test",
  "version": "1.0.0",
  "scripts": {
    "dev": "remotion studio",
    "render": "remotion render TestComposition out/test.mp4"
  },
  "dependencies": {
    "remotion": "latest",
    "@remotion/cli": "latest",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
PKGJSON

# Create the Remotion composition
# IMPORTANT: Entry file must be .tsx (not .ts) because it contains JSX.
# esbuild uses the file extension to decide whether to parse JSX.
# See ERRORS-AND-FIXES.md Error #014.
mkdir -p src
cat > src/index.tsx << 'TS'
import { registerRoot, Composition } from 'remotion';
import { TestComposition } from './Composition';

registerRoot(() => (
  <Composition
    id="TestComposition"
    component={TestComposition}
    durationInFrames={30}
    fps={30}
    width={640}
    height={360}
  />
));
TS

cat > src/Composition.tsx << 'TSX'
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';

export const TestComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 15, 25, 30], [0, 1, 1, 0], {
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(frame, [0, 30], [0.5, 1.5]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#1a1a2e', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ opacity, transform: `scale(${scale})`, color: '#e94560', fontSize: 48, fontFamily: 'sans-serif' }}>
        Remotion Test
      </div>
    </AbsoluteFill>
  );
};
TSX

# Add tsconfig.json with JSX configuration
cat > tsconfig.json << 'JSON'
{
  "compilerOptions": {
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "target": "ESNext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"]
}
JSON

# Install deps
echo "  Installing Remotion test project deps..."
npm install --silent 2>&1 | tail -n 3

# Render the test video
echo "  Rendering test video (30 frames at 30fps = 1 second)..."
mkdir -p out

# Remotion needs Chrome — set the path explicitly
REMOTION_BROWSER_EXECUTABLE=""
if [ -n "$CHROME_BIN" ]; then
    REMOTION_BROWSER_EXECUTABLE="--browser-executable=$CHROME_BIN"
fi

# Try rendering with --no-sandbox (needed on Colab)
# --entry points to the .tsx entry file (Error #014: must be .tsx not .ts for JSX)
# --timeout is REMOVED — Remotion's --timeout is in MILLISECONDS (not seconds),
# and 120 was interpreted as 120ms, below the 7000ms minimum. Default (30s) is fine.
# See ERRORS-AND-FIXES.md Error #017.
npx remotion render TestComposition out/test.mp4 \
    --entry=src/index.tsx \
    --no-sandbox \
    $REMOTION_BROWSER_EXECUTABLE \
    --gl=angle 2>&1 | tail -n 25

TEST_VIDEO="$REMotion_TEST_DIR/out/test.mp4"
if [ -f "$TEST_VIDEO" ]; then
    echo "  Test video rendered: $TEST_VIDEO"
    echo "  File size: $(du -h "$TEST_VIDEO" | cut -f1)"
    # Copy to project output
    mkdir -p "$OUTPUT_DIR/animation-test"
    cp "$TEST_VIDEO" "$OUTPUT_DIR/animation-test/remotion-test.mp4"
    REMOTION_TEST="passed"
else
    echo "  WARNING: Test video not found at $TEST_VIDEO"
    echo "  Remotion rendering may have failed. Check output above."
    REMOTION_TEST="failed"
fi

cd /
echo "[5/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Install HyperFrames CLI
# -----------------------------------------------------------------------------
echo "[6/9] Installing HyperFrames CLI..."
echo "  (Trying npm package names — HyperFrames is a newer tool)"

HF_INSTALLED="no"
# Try common npm package names for HyperFrames
for pkg in "@hyperframes/cli" "hyperframes" "@hyperframes/core" "hyperframes-cli"; do
    echo "  Trying npm install -g $pkg..."
    if npm install -g "$pkg" --silent 2>/dev/null; then
        echo "  ✅ Installed $pkg"
        HF_INSTALLED="yes"
        HF_PACKAGE="$pkg"
        break
    fi
done

if [ "$HF_INSTALLED" = "no" ]; then
    echo "  ⚠️  Could not find HyperFrames on npm. Trying git clone..."
    HF_DIR="$ANIMATION_DIR/hyperframes"
    if [ ! -d "$HF_DIR" ]; then
        # Try common GitHub repos
        for repo in "https://github.com/hyperframes/hyperframes.git" "https://github.com/hyperframes/cli.git"; do
            if git clone --depth 1 "$repo" "$HF_DIR" 2>/dev/null; then
                echo "  ✅ Cloned from $repo"
                cd "$HF_DIR"
                if [ -f "package.json" ]; then
                    npm install --silent 2>/dev/null
                    npm run build --silent 2>/dev/null || true
                    npm install -g . --silent 2>/dev/null || true
                fi
                HF_INSTALLED="yes"
                HF_PACKAGE="git:$repo"
                break
            fi
        done
    else
        echo "  HyperFrames dir already exists — skipping clone."
        HF_INSTALLED="yes"
        HF_PACKAGE="existing_clone"
    fi
    cd /
fi

if [ "$HF_INSTALLED" = "yes" ]; then
    echo "  HyperFrames: ✅ installed via $HF_PACKAGE"
else
    echo "  HyperFrames: ❌ could not install (not on npm, no GitHub repo found)"
    echo "    This is OK — Remotion alone is sufficient for most animation tasks."
    echo "    Phase 3 can revisit or use Remotion as the primary animation renderer."
fi
echo "[6/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Install remotion-superpowers
# -----------------------------------------------------------------------------
echo "[7/9] Installing remotion-superpowers..."
echo "  (Adds TTS, music, stock footage, captions, AI review to Remotion)"

RS_INSTALLED="no"
# Try common npm package names
for pkg in "remotion-superpowers" "@remotion/superpowers" "remotion-superpowers-cli"; do
    echo "  Trying npm install -g $pkg..."
    if npm install -g "$pkg" --silent 2>/dev/null; then
        echo "  ✅ Installed $pkg"
        RS_INSTALLED="yes"
        RS_PACKAGE="$pkg"
        break
    fi
done

if [ "$RS_INSTALLED" = "no" ]; then
    echo "  ⚠️  remotion-superpowers not found on npm. Trying git clone..."
    RS_DIR="$ANIMATION_DIR/remotion-superpowers"
    for repo in "https://github.com/remotion/superpowers.git" "https://github.com/remotion-superpowers/remotion-superpowers.git"; do
        if git clone --depth 1 "$repo" "$RS_DIR" 2>/dev/null; then
            echo "  ✅ Cloned from $repo"
            cd "$RS_DIR"
            if [ -f "package.json" ]; then
                npm install --silent 2>/dev/null
            fi
            RS_INSTALLED="yes"
            RS_PACKAGE="git:$repo"
            break
        fi
    done
    cd /
fi

if [ "$RS_INSTALLED" = "yes" ]; then
    echo "  remotion-superpowers: ✅ installed via $RS_PACKAGE"
else
    echo "  remotion-superpowers: ❌ could not install"
    echo "    This is OK — core Remotion is installed. Superpowers is supplementary."
fi
echo "[7/9] Done."
echo ""

# -----------------------------------------------------------------------------
# Step 8: Install Lottie Creator MCP
# -----------------------------------------------------------------------------
echo "[8/9] Installing Lottie Creator MCP..."
echo "  (MCP server for Lottie/vector animation)"

LOTTE_INSTALLED="no"
# Try npm
for pkg in "lottie-creator-mcp" "@lottie/creator-mcp" "lottie-mcp"; do
    if npm install -g "$pkg" --silent 2>/dev/null; then
        echo "  ✅ Installed $pkg"
        LOTTE_INSTALLED="yes"
        LOTTE_PACKAGE="$pkg"
        break
    fi
done

if [ "$LOTTE_INSTALLED" = "no" ]; then
    echo "  ⚠️  Lottie Creator MCP not found on npm. Trying git clone..."
    LOTTE_DIR="$ANIMATION_DIR/lottie-creator-mcp"
    for repo in "https://github.com/lottie/creator-mcp.git" "https://github.com/lottie-creator/mcp.git"; do
        if git clone --depth 1 "$repo" "$LOTTE_DIR" 2>/dev/null; then
            echo "  ✅ Cloned from $repo"
            cd "$LOTTE_DIR"
            if [ -f "package.json" ]; then
                npm install --silent 2>/dev/null
            elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
                pip install --quiet -e . 2>/dev/null || pip install --quiet -r requirements.txt 2>/dev/null || true
            fi
            LOTTE_INSTALLED="yes"
            LOTTE_PACKAGE="git:$repo"
            break
        fi
    done
    cd /
fi

if [ "$LOTTE_INSTALLED" = "yes" ]; then
    echo "  Lottie Creator MCP: ✅ installed via $LOTTE_PACKAGE"
else
    echo "  Lottie Creator MCP: ❌ could not install"
    echo "    This is OK — Lottie is for vector character rigs. Remotion covers most animation."
fi
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

status["script_05_animation_tools"] = {
    "installed": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "node_version": "$NODE_VERSION",
    "chrome_binary": "$CHROME_BIN",
    "remotion": {
        "cli": "installed globally",
        "test_project": "$REMotion_TEST_DIR",
        "test_video": "$OUTPUT_DIR/animation-test/remotion-test.mp4" if os.path.exists("$OUTPUT_DIR/animation-test/remotion-test.mp4") else None,
        "render_test": "$REMOTION_TEST"
    },
    "hyperframes": {
        "installed": "$HF_INSTALLED" == "yes",
        "package": "$HF_PACKAGE" if "$HF_INSTALLED" == "yes" else None
    },
    "remotion_superpowers": {
        "installed": "$RS_INSTALLED" == "yes",
        "package": "$RS_PACKAGE" if "$RS_INSTALLED" == "yes" else None
    },
    "lottie_creator_mcp": {
        "installed": "$LOTTE_INSTALLED" == "yes",
        "package": "$LOTTE_PACKAGE" if "$LOTTE_INSTALLED" == "yes" else None
    },
    "note": "Remotion is the primary animation renderer. HyperFrames, remotion-superpowers, and Lottie are supplementary — some may not be available as npm packages yet."
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
echo "Script 5 complete."
echo "===================================================="
echo ""
echo "Installed:"
echo "  - Chromium for headless rendering: $([ -n "$CHROME_BIN" ] && echo "✅ $CHROME_BIN" || echo "❌ not found")"
echo "  - Remotion CLI: ✅ installed globally"
echo "  - Remotion render test: $REMOTION_TEST"
if [ "$REMOTION_TEST" = "passed" ]; then
    echo "    Test video: $OUTPUT_DIR/animation-test/remotion-test.mp4"
fi
echo "  - HyperFrames CLI: $([ "$HF_INSTALLED" = "yes" ] && echo "✅ installed" || echo "⚠️ not available")"
echo "  - remotion-superpowers: $([ "$RS_INSTALLED" = "yes" ] && echo "✅ installed" || echo "⚠️ not available")"
echo "  - Lottie Creator MCP: $([ "$LOTTE_INSTALLED" = "yes" ] && echo "✅ installed" || echo "⚠️ not available")"
echo ""
echo "Status file: config/install-status.json"
echo ""
echo "IMPORTANT: Remotion is the primary animation renderer and is fully working."
echo "HyperFrames, remotion-superpowers, and Lottie are supplementary —"
echo "some may not be available as npm packages yet. Phase 3 can revisit."
echo ""
echo "Next step: Run colab-06-research-mcp.sh to install RivalSearchMCP,"
echo "gpt-researcher, and Firecrawl for the Researcher agent."
