#!/usr/bin/env bash
# setup.sh — one-command bootstrap for a fresh machine
# Installs system tools from scripts/system-tools.json, then pip-installs requirements.txt
# and builds the React app.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$SCRIPT_DIR/system-tools.json"
REQUIREMENTS="$ROOT_DIR/requirements.txt"
REACT_DIR="$ROOT_DIR/ui/web/react"

# Detect package manager
detect_pkg_mgr() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v brew >/dev/null 2>&1; then
        echo "brew"
    elif command -v winget >/dev/null 2>&1; then
        echo "winget"
    else
        echo "unknown"
    fi
}

PKG_MGR=$(detect_pkg_mgr)
echo "Detected package manager: $PKG_MGR"

if [[ "$PKG_MGR" == "unknown" ]]; then
    echo "WARNING: No supported package manager found. Skipping system tool installation."
    echo "Please install tools manually: ffmpeg, git, python3"
else
    # Parse manifest and install tools
    echo "Installing system tools from $MANIFEST..."
    if ! command -v jq >/dev/null 2>&1; then
        echo "Installing jq for JSON parsing..."
        case "$PKG_MGR" in
            apt) sudo apt-get update && sudo apt-get install -y jq ;;
            dnf) sudo dnf install -y jq ;;
            brew) brew install jq ;;
            winget) winget install --id=stedolan.jq -e ;;
        esac
    fi

    # Read tools from manifest
    TOOLS=$(jq -r '.tools[] | @base64' "$MANIFEST")
    for tool_b64 in $TOOLS; do
        tool=$(echo "$tool_b64" | base64 -d)
        name=$(echo "$tool" | jq -r '.name')
        pkg=$(echo "$tool" | jq -r ".${PKG_MGR}")
        required=$(echo "$tool" | jq -r '.required')

        if [[ -z "$pkg" || "$pkg" == "null" ]]; then
            echo "  No package mapping for $name on $PKG_MGR, skipping"
            continue
        fi

        if command -v "$name" >/dev/null 2>&1; then
            echo "  $name already installed, skipping"
            continue
        fi

        echo "  Installing $name ($pkg)..."
        case "$PKG_MGR" in
            apt)
                sudo apt-get update && sudo apt-get install -y "$pkg"
                ;;
            dnf)
                sudo dnf install -y "$pkg"
                ;;
            brew)
                brew install "$pkg"
                ;;
            winget)
                winget install --id="$pkg" -e
                ;;
        esac

        if [[ $? -eq 0 ]]; then
            echo "  $name installed successfully"
        else
            if [[ "$required" == "true" ]]; then
                echo "ERROR: Required tool $name failed to install"
                exit 1
            else
                echo "  WARNING: Optional tool $name failed to install"
            fi
        fi
    done
fi

# Python dependencies
echo "Installing Python dependencies from $REQUIREMENTS..."
cd "$ROOT_DIR"
if [[ -f "$REQUIREMENTS" ]]; then
    pip install -r "$REQUIREMENTS"
else
    echo "WARNING: $REQUIREMENTS not found"
fi

# Build React app
echo "Building React app in $REACT_DIR..."
if [[ -d "$REACT_DIR" ]]; then
    cd "$REACT_DIR"
    if [[ -f "package.json" ]]; then
        npm ci
        npm run build
    else
        echo "WARNING: package.json not found in $REACT_DIR"
    fi
else
    echo "WARNING: React directory not found at $REACT_DIR"
fi

echo "Setup complete!"