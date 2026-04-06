# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for HAM HAT Control Center v4 — macOS
#
# Build from the app/ directory:
#     ./packaging/build_mac.sh
# Or manually:
#     pyinstaller packaging/app_mac.spec --noconfirm
#
# Output: dist/HamHatCC.app
#
# Requirements:
#   - .venv set up by ./run_mac.command (or manually)
#   - PyInstaller: pip install pyinstaller
#   - Optional code signing: export CODESIGN_IDENTITY="Developer ID Application: …"
#
# macOS permission notes (required for full functionality):
#   NSBluetoothAlwaysUsageDescription — PAKT BLE scan / connect
#   NSMicrophoneUsageDescription      — sounddevice audio input (APRS decode)
#   USB serial adapters (SA818 / DigiRig) require no special entitlement
#
# Notarization: after signing, run:
#   xcrun notarytool submit dist/HamHatCC.zip --apple-id … --team-id … --wait
#   xcrun stapler staple dist/HamHatCC.app

import os

block_cipher = None

# SPECPATH is the directory containing this spec file (app/packaging/).
# The app root (app/) is one level up.
_APP_DIR = os.path.dirname(SPECPATH)

a = Analysis(
    [os.path.join(_APP_DIR, 'main.py')],
    pathex=[_APP_DIR],
    binaries=[],
    datas=[
        (os.path.join(_APP_DIR, 'tiles'),   'tiles'),
        (os.path.join(_APP_DIR, 'VERSION'), '.'),
    ],
    hiddenimports=[
        # App packages — listed to supplement PyInstaller's own analysis.
        # Not guaranteed complete; update if the build logs show missing imports.
        'app',
        'app.app',
        'app.app_state',
        'app.engine',
        'app.engine.aprs_engine',
        'app.engine.aprs_modem',
        'app.engine.audio_router',
        'app.engine.audio_tools',
        'app.engine.comms_mgr',
        'app.engine.display_config',
        'app.engine.mesh_mgr',
        'app.engine.models',
        'app.engine.platform_paths',
        'app.engine.profile',
        'app.engine.radio_ctrl',
        'app.engine.sa818_client',
        'app.engine.tile_provider',
        'app.engine.pakt',
        'app.engine.pakt.capability',
        'app.engine.pakt.chunker',
        'app.engine.pakt.constants',
        'app.engine.pakt.service',
        'app.engine.pakt.telemetry',
        'app.engine.pakt.transport',
        'app.ui',
        'app.ui.aprs_tab',
        'app.ui.comms_tab',
        'app.ui.events',
        'app.ui.main_tab',
        'app.ui.mesh_tab',
        'app.ui.setup_tab',
        'app.ui.widgets',
        # Core runtime dependencies
        'sounddevice',
        'numpy',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        # Optional dependencies — bundled if present in .venv;
        # app degrades gracefully when any of these are absent.
        'bleak',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'scipy',
        'sv_ttk',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pycaw',      # Windows-only audio volume control; not available on macOS
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HamHatCC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,                             # None = native arch (arm64 or x86_64)
    codesign_identity=os.environ.get('CODESIGN_IDENTITY'),
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='HamHatCC',
)

app = BUNDLE(
    coll,
    name='HamHatCC.app',
    icon=None,                          # Add path to .icns file when available
    bundle_identifier='com.hamhat.controlcenter',
    info_plist={
        # Bluetooth permission — PAKT BLE scan / connect
        'NSBluetoothAlwaysUsageDescription':
            'HAM HAT Control Center requires Bluetooth for PAKT radio access.',
        # Microphone — APRS audio decoding via sounddevice
        'NSMicrophoneUsageDescription':
            'HAM HAT Control Center requires microphone access for APRS audio decoding.',
        'CFBundleShortVersionString': '4.0',
        'CFBundleVersion': '4.0',
        'LSMinimumSystemVersion': '11.0',
        # High-resolution display support
        'NSHighResolutionCapable': True,
    },
)
