#!/usr/bin/env bash
# HAM HAT Control Center v4 — macOS source launcher
#
# Double-click this file in Finder, or run from Terminal:
#     ./run_mac.command
#
# On first run: creates a local .venv and installs requirements.
# Subsequent runs reuse the existing .venv and repair it if core deps are missing.
#
# Note: macOS may ask for Bluetooth permission on first launch if the PAKT
# hardware mode is used.  Grant it when prompted.

# Run from this script's own directory regardless of how it was launched
# (Finder sets the working directory to $HOME, not the script location)
cd "$(dirname "$0")"

# ---- Python check ----
if ! command -v python3 &>/dev/null; then
    echo ""
    echo "ERROR: python3 not found."
    echo "Install Python 3.10+ from https://python.org"
    echo "  or via Homebrew:  brew install python"
    echo ""
    read -r -p "Press Return to close..." _
    exit 1
fi

# ---- requirements.txt presence check ----
if [ ! -f requirements.txt ]; then
    echo "ERROR: requirements.txt not found in $(pwd)"
    echo "Make sure you are running this script from the app directory."
    read -r -p "Press Return to close..." _
    exit 1
fi

VENV_PY=".venv/bin/python3"
VENV_PIP=".venv/bin/pip"

# ---- Create .venv on first run ----
if [ ! -f "$VENV_PY" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        read -r -p "Press Return to close..." _
        exit 1
    fi
    echo "Installing dependencies..."
    "$VENV_PIP" install --upgrade pip -q
    # pycaw is Windows-only; exclude it from the install on macOS
    grep -v pycaw requirements.txt | "$VENV_PIP" install -r /dev/stdin -q
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
        read -r -p "Press Return to close..." _
        exit 1
    fi
    echo "Setup complete."
fi

# ---- Repair stale .venv if core deps are missing ----
if ! "$VENV_PY" -c "import sounddevice" 2>/dev/null; then
    echo "Missing dependencies detected. Repairing..."
    "$VENV_PIP" install --upgrade pip -q
    grep -v pycaw requirements.txt | "$VENV_PIP" install -r /dev/stdin -q
fi

# ---- Launch ----
exec "$VENV_PY" main.py "$@"
