#!/usr/bin/env bash
# HAM HAT Control Center v4 — macOS PyInstaller build script
#
# Run from the app/ directory:
#     ./packaging/build_mac.sh
#
# Prerequisites:
#   - macOS 11.0+
#   - .venv already set up (run ./run_mac.command first if needed)
#   - Optional: export CODESIGN_IDENTITY="Developer ID Application: …" before running
#
# Output: dist/HamHatCC.app

set -euo pipefail
cd "$(dirname "$0")/.."   # ensure we're in the app/ directory

VENV_PY=".venv/bin/python3"
# Use 'python3 -m pip' rather than the .venv/bin/pip script; the script's
# shebang may be stale if the venv was created in a different directory.

# ---- Preflight ----
if [ ! -f "$VENV_PY" ]; then
    echo "ERROR: .venv not found."
    echo "Run ./run_mac.command first to set up the environment, then retry."
    exit 1
fi

if ! python3 -c "import platform; assert platform.system() == 'Darwin'" 2>/dev/null; then
    echo "ERROR: This script must be run on macOS."
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
echo "Building HamHatCC.app..."
"$VENV_PY" -m PyInstaller packaging/app_mac.spec --noconfirm

echo ""
echo "============================================================"
echo "  Build complete: dist/HamHatCC.app"
echo "============================================================"
echo ""
echo "Exit checks — verify each before shipping:"
echo "  1. App launches cleanly:"
echo "       open dist/HamHatCC.app"
echo "  2. Profile path resolves:"
echo "       ~/Library/Application Support/HamHatCC  (created on first run)"
echo "  3. Profile save/load: save a profile, quit, reopen, confirm it loads"
echo "  4. Audio enumeration: Setup tab shows system audio devices"
echo "  5. Serial scan: Setup tab serial section responds (no hardware needed)"
echo "  6. BLE scan: PAKT mode triggers macOS Bluetooth permission dialog on first use"
echo "  7. Optional dependency fallback:"
echo "       - sv_ttk absent → app uses fallback theme"
echo "       - PIL absent → map shows grid rather than tiles"
echo ""
if [ -n "${CODESIGN_IDENTITY:-}" ]; then
    echo "Signing identity: $CODESIGN_IDENTITY"
    echo "Next: codesign --deep --force --sign \"$CODESIGN_IDENTITY\" dist/HamHatCC.app"
    echo "Then: xcrun notarytool submit <zip> --apple-id … --team-id … --wait"
else
    echo "No CODESIGN_IDENTITY set — skipping code signing note."
    echo "Set the env var and re-run to get signing instructions."
fi
