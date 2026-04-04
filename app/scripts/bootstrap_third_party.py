#!/usr/bin/env python3
"""Install core Python requirements and optional third-party SA818 tools.

Run once after cloning / extracting the release archive:

    python scripts/bootstrap_third_party.py

Options:
    --offline    Use local resource snapshots instead of cloning from GitHub
    --dev        Also install pycaw (Windows audio volume control)
    --target     Where to store cloned repos (default: third_party/)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPOS = {
    "sa818": "https://github.com/0x9900/SA818.git",
    "srfrs":  "https://github.com/jumbo5566/SRFRS.git",
}

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# Bundled offline snapshots are expected at this path relative to the repo root.
# Layout: <repo-root>/Resources/SA818 programmer/SA818  and  <repo-root>/Resources/SRFRS/…
_RESOURCES = _ROOT.parent.parent / "Resources"

_OFFLINE_FALLBACKS: dict[str, Path] = {
    "sa818": _RESOURCES / "SA818 programmer" / "SA818",
    "srfrs":  _RESOURCES / "SRFRS" / "SRFRS-main" / "SRFRS-main",
}


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    label = " ".join(str(c) for c in cmd)
    print(f"  [run] {label}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _pip(*packages: str) -> None:
    _run([sys.executable, "-m", "pip", "install", "--upgrade", *packages])


def install_core_requirements() -> None:
    req_file = _ROOT / "requirements.txt"
    if req_file.exists():
        print("\nInstalling core requirements…")
        _pip("-r", str(req_file))
    else:
        print("\nrequirements.txt not found — installing defaults…")
        _pip("pyserial", "numpy", "sounddevice")


def install_pycaw() -> None:
    print("\nInstalling pycaw (Windows audio volume control)…")
    _pip("pycaw")


def validate_offline_sources() -> list[str]:
    """Check that bundled snapshots exist.  Prints a warning for each that is absent.
    Returns a list of the missing names so the caller can decide whether to abort."""
    missing: list[str] = []
    for name, src in _OFFLINE_FALLBACKS.items():
        if not src.exists():
            print(f"  [warn] offline fallback not found: {src}")
            missing.append(name)
    if missing:
        print(f"  [warn] expected bundles under: {_RESOURCES}")
    return missing


def clone_or_pull(name: str, url: str, target_root: Path) -> Path:
    target = target_root / name
    if target.exists() and (target / ".git").exists():
        print(f"  [git pull] {name}")
        _run(["git", "pull", "--ff-only"], cwd=target)
    elif target.exists():
        print(f"  [skip] {target} exists (not a git repo)")
    else:
        print(f"  [git clone] {name}")
        try:
            _run(["git", "clone", url, str(target)])
        except subprocess.CalledProcessError:
            # Remove partial clone so the fallback copy path can proceed cleanly.
            if target.exists() and not (target / ".git").exists():
                shutil.rmtree(target, ignore_errors=True)
            raise
    return target


def copy_local_fallback(target_root: Path) -> list[str]:
    """Copy bundled resource snapshots when offline.
    Returns list of names that were successfully copied."""
    copied: list[str] = []
    for name, src in _OFFLINE_FALLBACKS.items():
        dst = target_root / name
        if dst.exists():
            continue  # already present — don't overwrite a live clone
        if not src.exists():
            print(f"  [warn] local fallback not found: {src}")
            continue
        print(f"  [copy] {src} → {dst}")
        shutil.copytree(src, dst)
        copied.append(name)
    return copied


def install_sa818_package(target_root: Path) -> None:
    sa818_dir = target_root / "sa818"
    if not sa818_dir.exists():
        print("  [skip] sa818 directory not found — skipping package install")
        return
    has_setup     = (sa818_dir / "setup.py").exists()
    has_pyproject = (sa818_dir / "pyproject.toml").exists()
    if not (has_setup or has_pyproject):
        print(f"  [warn] {sa818_dir} has no setup.py or pyproject.toml — skipping install")
        return
    print("\nInstalling SA818 Python package from local clone…")
    _pip(str(sa818_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap HAM HAT Control Center v4 dependencies")
    parser.add_argument("--offline", action="store_true",
                        help="Use only local resource snapshots (no internet required)")
    parser.add_argument("--dev", action="store_true",
                        help="Also install pycaw (Windows-only audio volume control; skip on macOS/Linux)")
    parser.add_argument("--target", default="third_party",
                        help="Directory for cloned third-party repos (default: third_party/)")
    args = parser.parse_args()

    target_root = (_ROOT / args.target).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    # Step 1: core Python packages
    install_core_requirements()

    # Step 2: optional pycaw
    if args.dev:
        install_pycaw()

    # Step 3: third-party SA818 tools
    print("\nFetching third-party SA818 tools…")
    if args.offline:
        # Validate bundled sources exist before attempting copy so the user
        # gets an explicit message rather than a silent no-op.
        missing = validate_offline_sources()
        if missing:
            print(f"  [warn] proceeding — {len(missing)} bundle(s) unavailable offline")
        copy_local_fallback(target_root)
    else:
        for name, url in REPOS.items():
            try:
                clone_or_pull(name, url, target_root)
            except subprocess.CalledProcessError:
                print(f"  [warn] network fetch of {name} failed — trying local fallback")
                copied = copy_local_fallback(target_root)
                if not copied and not (target_root / name).exists():
                    print(f"  [warn] {name} not available via network or local fallback")
                break

    # Step 4: install SA818 Python package if the directory is valid
    install_sa818_package(target_root)

    print("\n[done] bootstrap complete")
    print(f"[info] third-party tools: {target_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
