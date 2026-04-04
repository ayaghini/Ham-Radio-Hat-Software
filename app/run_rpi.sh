#!/usr/bin/env bash
# HAM HAT Control Center v4 — Raspberry Pi source launcher
#
# Run from the app directory:
#     ./run_rpi.sh
#
# Passes --rpi to main.py for the 1280x720 5-inch display preset.
#
# On first run: creates a local .venv and installs requirements.
# Subsequent runs reuse the existing .venv and repair it if core deps are missing.
#
# System prerequisites (install once):
#     sudo apt install python3-venv python3-tk libasound2-dev
#     sudo usermod -aG dialout $USER    # SA818 / DigiRig serial access
#     sudo usermod -aG bluetooth $USER  # BLE/PAKT access (log out to apply)
#
# If using the SA818 GPIO UART, disable the serial console first:
#     sudo raspi-config  →  Interface Options  →  Serial Port  →  disable login shell

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
    # pycaw is Windows-only; exclude it from the install on Raspberry Pi
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

# ---- Launch with RPi display preset ----
exec "$VENV_PY" main.py --rpi "$@"
