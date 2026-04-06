# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for HAM HAT Control Center v4 — Linux desktop
#
# Build from the app/ directory:
#     ./packaging/build_linux.sh
# Or manually:
#     pyinstaller packaging/app_linux.spec --noconfirm
#
# Output: dist/hamhatcc/  (one-folder bundle)
# Launch: ./dist/hamhatcc/hamhatcc
#
# Requirements:
#   - System packages: python3-tk libasound2-dev (or libasound2)
#   - .venv set up by ./run_linux.sh (or manually)
#   - PyInstaller: pip install pyinstaller
#
# Permissions note:
#   Serial access: sudo usermod -aG dialout $USER  (then log out/in)
#   BLE access:    sudo usermod -aG bluetooth $USER (then log out/in)

block_cipher = None

# SPECPATH is the directory containing this spec file (app/packaging/).
# The app root (app/) is one level up.
import os as _os
_APP_DIR = _os.path.dirname(SPECPATH)

a = Analysis(
    [_os.path.join(_APP_DIR, 'main.py')],
    pathex=[_APP_DIR],
    binaries=[],
    datas=[
        (_os.path.join(_APP_DIR, 'tiles'),   'tiles'),
        (_os.path.join(_APP_DIR, 'VERSION'), '.'),
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
        'pycaw',      # Windows-only audio volume control; not available on Linux
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
    name='hamhatcc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
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
    name='hamhatcc',
)
