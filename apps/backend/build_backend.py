#!/usr/bin/env python3
"""Build script for PyInstaller backend executable."""

import os
import sys
import shutil
import subprocess
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent
DIST_DIR = BACKEND_ROOT / "dist"
BUILD_DIR = BACKEND_ROOT / "build"
SPEC_FILE = BACKEND_ROOT / "twitch_clipper.spec"
RESOURCES_DIR = BACKEND_ROOT / "resources"

def clean_build():
    """Clean previous build artifacts."""
    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"Cleaned {dir_path}")

def ensure_resources():
    """Ensure resources directory exists with required files."""
    RESOURCES_DIR.mkdir(parents=True, exist_ok=True)

    models_dir = RESOURCES_DIR / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    fonts_dir = RESOURCES_DIR / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder for Montserrat font
    font_file = fonts_dir / "Montserrat-Bold.ttf"
    if not font_file.exists():
        font_file.write_text("")  # Placeholder - replace with actual font

    print("Resources directory ready")

def run_pyinstaller():
    """Run PyInstaller with the spec file."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=BACKEND_ROOT, capture_output=True, text=True)

    if result.returncode != 0:
        print("PyInstaller failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

    print("PyInstaller completed successfully")

def copy_to_frontend():
    """Copy built backend to frontend extraResources."""
    frontend_resources = Path(__file__).parent.parent / "frontend" / "backend"
    frontend_resources.mkdir(parents=True, exist_ok=True)

    # Copy dist contents
    if DIST_DIR.exists():
        for item in DIST_DIR.iterdir():
            dest = frontend_resources / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.copytree(item, dest) if item.is_dir() else shutil.copy2(item, dest)
            print(f"Copied {item.name} to frontend resources")

def main():
    print("=== Building Twitch Clipper Backend ===")
    clean_build()
    ensure_resources()
    run_pyinstaller()
    copy_to_frontend()
    print("=== Backend build complete ===")

if __name__ == "__main__":
    main()