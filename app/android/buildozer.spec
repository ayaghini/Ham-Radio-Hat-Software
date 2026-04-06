[app]

# App identity
title        = HAM HAT Control Center
package.name = hamhatcc
package.domain = com.hamhat
version      = 4.0

# Source
source.dir  = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,xml,txt
# Include the engine from the parent app/ directory so engine_bridge can find it.
# Buildozer resolves these relative to the project root (source.dir = .).
# We add ../engine and ../app/engine via source.include_patterns.
source.include_patterns = assets/*,kv/*.kv

# Requirements
# ── Core framework ──────────────────────────────────────────────────────────
requirements =
    python3,
    kivy==2.3.0,
    kivymd==1.2.0,
    pillow,
    plyer,
    bleak>=0.22.0,
    pyserial,
    numpy,
    scipy

# ── Phase 2 notes ────────────────────────────────────────────────────────────
# bleak 0.22+:  BLE with Android backend (requires BLUETOOTH_SCAN/CONNECT perms)
# pyserial:     SA818 USB OTG fallback (primary path is usbserial4a via jnius)
# numpy/scipy:  APRS AFSK DSP (aprs_modem_bridge.py + app.engine.aprs_modem)
# usbserial4a:  android.gradle_dependencies = com.github.felHR85:UsbSerial:6.1.0
#               imported via jnius at runtime (not a Python package)

# Entry point
entrypoint = main.py

# Icon / splash (place 512x512 PNG at assets/icon.png and assets/splash.png)
icon.filename    = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/splash.png

# Orientation
orientation = portrait,landscape

# ── Android ─────────────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1

[app:android]

# API levels
android.api    = 33
android.minapi = 26     # Android 8.0 — minimum for BLE + USB host + modern audio
android.ndk    = 25b
android.sdk    = 33
android.build_tools_version = 33.0.2

# CPU architecture — arm64-v8a covers all modern Android phones/tablets.
# Add armeabi-v7a for older 32-bit devices.
android.arch = arm64-v8a

# Gradle dependencies
# usbserial4a provides Python USB serial for Android via pyjnius
android.gradle_dependencies =
    com.github.felHR85:UsbSerial:6.1.0

# Java extras for USB device filter
# android.add_assets = assets/device_filter.xml

# Manifest permissions
android.permissions =
    BLUETOOTH,
    BLUETOOTH_ADMIN,
    BLUETOOTH_SCAN,
    BLUETOOTH_CONNECT,
    ACCESS_FINE_LOCATION,
    RECORD_AUDIO,
    READ_EXTERNAL_STORAGE,
    WRITE_EXTERNAL_STORAGE,
    INTERNET,
    FOREGROUND_SERVICE

# USB host feature (for SA818 USB OTG)
android.features =
    android.hardware.usb.host

# Meta-data for USB device attached intent filter (SA818 / DigiRig)
# android.meta_data =
#     android.hardware.usb.action.USB_DEVICE_ATTACHED:@xml/device_filter

# Enable Android back-button (important for usability)
android.allow_backup = True

# Target SDK and compile SDK
android.target_api = 33

# Services (foreground service keeps BLE alive in background)
# Phase 2: notification-based foreground service implemented in hal/foreground_service.py
# Uses startForeground() via jnius rather than p4a service template.
# If a true background service is needed (Phase 3), uncomment:
# android.services = BleService:service/ble_service.py:foreground

# Whitelist python imports (helps Buildozer include all needed modules)
android.whitelist_requirements = requests,urllib3,certifi

# ── iOS (placeholder — not yet targeted) ────────────────────────────────────
[app:ios]
# ios.codesign.allowed = false

# ── Buildozer internal ───────────────────────────────────────────────────────
[buildozer:internal]
build_dir = .buildozer
bin_dir = bin
