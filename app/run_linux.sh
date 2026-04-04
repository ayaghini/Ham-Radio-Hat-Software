#!/usr/bin/env bash
# HAM HAT Control Center v4 — Linux desktop source launcher
#
# Run from the app directory:
#     ./run_linux.sh
#
# On first run: creates a local .venv and installs requirements.
# Subsequent runs reuse the existing .venv and repair it if core deps are missing.
#
# System prerequisites (install once):
#     sudo apt install python3-venv python3-tk libasound2-dev
#     sudo usermod -aG dialout $USER    # serial port access
#     sudo usermod -aG bluetooth $USER  # BLE/PAKT access (log out to apply)

cd "$(dirname "$0")"

# ---- Python check ----
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo "Install it with:  sudo apt install python3 python3-venv"
    exit 1
fi

# ---- tkinter check (system package; cannot be installed via pip) ----
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "ERROR: python3-tk is not installed."
    echo "Install it with:  sudo apt install python3-tk"
    exit 1
fi

# ---- requirements.txt presence check ----
if [ ! -f requirements.txt ]; then
    echo "ERROR: requirements.txt not found in $(pwd)"
    echo "Make sure you are running this script from the app directory."
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
        echo "Ensure python3-venv is installed:  sudo apt install python3-venv"
        exit 1
    fi
    echo "Installing dependencies..."
    "$VENV_PIP" install --upgrade pip -q
    # pycaw is Windows-only; exclude it from the install on Linux
    grep -v pycaw requirements.txt | "$VENV_PIP" install -r /dev/stdin -q
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies."
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
