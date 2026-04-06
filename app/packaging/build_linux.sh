#!/usr/bin/env bash
# HAM HAT Control Center v4 — Linux PyInstaller build script
#
# Run from the app/ directory:
#     ./packaging/build_linux.sh
#
# Prerequisites:
#   - System packages: python3-tk libasound2-dev python3-venv
#   - .venv already set up (run ./run_linux.sh first if needed)
#
# Output: dist/hamhatcc/  (one-folder bundle)
# Launch: ./dist/hamhatcc/hamhatcc

set -euo pipefail
cd "$(dirname "$0")/.."   # ensure we're in the app/ directory

VENV_PY=".venv/bin/python3"
# Use 'python3 -m pip' rather than the .venv/bin/pip script; the script's
# shebang may be stale if the venv was created in a different directory.

# ---- Preflight ----
if [ ! -f "$VENV_PY" ]; then
    echo "ERROR: .venv not found."
    echo "Run ./run_linux.sh first to set up the environment, then retry."
    exit 1
fi

if ! python3 -c "import platform; assert platform.system() == 'Linux'" 2>/dev/null; then
    echo "ERROR: This script must be run on Linux."
    exit 1
fi

# ---- Install PyInstaller if absent ----
if ! "$VENV_PY" -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller into .venv..."
    "$VENV_PY" -m pip install pyinstaller -q
    echo "PyInstaller installed."
fi

PYINSTALLER_VER=$("$VENV_PY" -c "import PyInstaller; print(PyInstaller.__version__)")
echo "PyInstaller: $PYINSTALLER_VER"

# ---- Build ----
echo ""
echo "Building dist/hamhatcc/..."
"$VENV_PY" -m PyInstaller packaging/app_linux.spec --noconfirm

echo ""
echo "============================================================"
echo "  Build complete: dist/hamhatcc/"
echo "============================================================"
echo ""
echo "Exit checks — verify each before shipping:"
echo "  1. Binary launches cleanly:"
echo "       ./dist/hamhatcc/hamhatcc"
echo "  2. Profile path resolves:"
echo "       ~/.local/share/hamhatcc  (created on first run)"
echo "  3. Profile save/load: save a profile, quit, reopen, confirm it loads"
echo "  4. Audio enumeration: Setup tab shows system audio devices"
echo "  5. Serial scan: Setup tab serial section responds (no hardware needed)"
echo "  6. BLE prerequisites (PAKT mode):"
echo "       - BlueZ installed:       which bluetoothd"
echo "       - bluetooth group:       groups | grep bluetooth"
echo "       - dbus available:        systemctl status bluetooth"
echo "  7. Optional dependency fallback:"
echo "       - sv_ttk absent → app uses fallback theme"
echo "       - PIL absent → map shows grid rather than tiles"
echo ""
echo "Permissions (if not already set):"
echo "  sudo usermod -aG dialout \$USER    # serial access"
echo "  sudo usermod -aG bluetooth \$USER  # BLE access"
echo "  (log out and back in after adding groups)"
