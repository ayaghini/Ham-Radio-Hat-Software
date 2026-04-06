#!/usr/bin/env bash
# run_android.sh — Build, deploy, and optionally run the HAM HAT Control Center APK.
#
# Usage:
#   ./run_android.sh                  # debug build
#   ./run_android.sh release          # release build (needs signing key)
#   ./run_android.sh deploy           # debug build + install on connected device
#   ./run_android.sh run              # debug build + install + launch on device
#   ./run_android.sh clean            # remove build artefacts
#   ./run_android.sh dev              # run directly with Python on desktop (no APK)
#
# Prerequisites (Linux / macOS build host):
#   pip install buildozer
#   sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool \
#       pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev cmake \
#       libffi-dev libssl-dev  # Debian/Ubuntu
#   # On macOS: brew install autoconf libtool pkg-config cmake
#
# The first build downloads Android SDK/NDK automatically (~4 GB) into .buildozer/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE="${1:-debug}"

# ── Sanity checks ─────────────────────────────────────────────────────────────
check_buildozer() {
    if ! command -v buildozer &>/dev/null; then
        echo "ERROR: buildozer not found. Install with: pip install buildozer"
        exit 1
    fi
}

check_python() {
    if ! python3 -c "import kivy" &>/dev/null; then
        echo "ERROR: kivy not installed. Install with: pip install kivy kivymd"
        exit 1
    fi
}

check_adb() {
    if ! command -v adb &>/dev/null; then
        echo "WARNING: adb not found — cannot deploy to device."
        echo "Install Android SDK platform-tools and add to PATH."
        return 1
    fi
    return 0
}

# ── Modes ────────────────────────────────────────────────────────────────────

case "$MODE" in

    dev)
        echo "=== Running HAM HAT CC on desktop (development mode) ==="
        check_python
        # Add repo root and app/ to sys.path via engine_bridge, then run
        PYTHONPATH="${SCRIPT_DIR}/..":"${SCRIPT_DIR}/../.." python3 main.py
        ;;

    clean)
        echo "=== Cleaning build artefacts ==="
        check_buildozer
        buildozer android clean
        rm -rf .buildozer/android/platform/build/dists
        echo "Clean done."
        ;;

    debug)
        echo "=== Debug build ==="
        check_buildozer
        buildozer android debug
        APK=$(ls bin/*debug*.apk 2>/dev/null | tail -1)
        if [ -n "$APK" ]; then
            echo ""
            echo "✓ APK built: $APK"
            echo "  Install with: adb install -r $APK"
        else
            echo "ERROR: APK not found after build."
            exit 1
        fi
        ;;

    release)
        echo "=== Release build ==="
        check_buildozer
        if [ -z "${ANDROID_KEYSTORE:-}" ]; then
            echo "ERROR: Set ANDROID_KEYSTORE, ANDROID_KEY_ALIAS, ANDROID_KEY_PASS"
            echo "  export ANDROID_KEYSTORE=/path/to/hamhat.keystore"
            echo "  export ANDROID_KEY_ALIAS=hamhat"
            echo "  export ANDROID_KEY_PASS=yourpassword"
            exit 1
        fi
        buildozer android release
        APK=$(ls bin/*release*.apk 2>/dev/null | tail -1)
        echo "✓ Unsigned release APK: $APK"
        echo "  Sign with: zipalign + apksigner or jarsigner"
        ;;

    deploy)
        echo "=== Debug build + deploy to device ==="
        check_buildozer
        if ! check_adb; then exit 1; fi
        buildozer android debug deploy
        echo "✓ Installed on connected device."
        echo "  Launch manually or run: ./run_android.sh run"
        ;;

    run)
        echo "=== Debug build + deploy + launch ==="
        check_buildozer
        if ! check_adb; then exit 1; fi
        buildozer android debug deploy run
        echo "✓ App launched on device."
        echo "  View logs with: adb logcat -s python"
        ;;

    logcat)
        echo "=== Device logcat (python process only) ==="
        if ! check_adb; then exit 1; fi
        adb logcat -s python
        ;;

    *)
        echo "Unknown mode: $MODE"
        echo "Usage: $0 [dev|debug|release|deploy|run|logcat|clean]"
        exit 1
        ;;
esac
