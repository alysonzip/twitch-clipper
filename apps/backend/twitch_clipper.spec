# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(SPECPATH).parent.parent.parent.parent
BACKEND_ROOT = Path(SPECPATH)
SRC_ROOT = BACKEND_ROOT / "src"
RESOURCES_ROOT = BACKEND_ROOT / "resources"

# Collect data files
def collect_data_files():
    data_files = []

    # Models
    models_dir = RESOURCES_ROOT / "models"
    if models_dir.exists():
        for model_file in models_dir.rglob("*"):
            if model_file.is_file():
                rel_path = model_file.relative_to(BACKEND_ROOT)
                data_files.append((str(model_file), str(rel_path.parent)))

    # Fonts
    fonts_dir = RESOURCES_ROOT / "fonts"
    if fonts_dir.exists():
        for font_file in fonts_dir.rglob("*"):
            if font_file.is_file():
                rel_path = font_file.relative_to(BACKEND_ROOT)
                data_files.append((str(font_file), str(rel_path.parent)))

    return data_files

# Collect binaries (ffmpeg, etc.)
def collect_binaries():
    binaries = []

    # FFmpeg - try to find system ffmpeg or use bundled
    ffmpeg_paths = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("/usr/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
    ]

    for ffmpeg_path in ffmpeg_paths:
        if ffmpeg_path.exists():
            binaries.append((str(ffmpeg_path), "."))
            break

    return binaries

# Hidden imports
hiddenimports = [
    # Core
    'uvicorn',
    'uvicorn.lifespan.on',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websocket.auto',
    'fastapi',
    'fastapi.openapi',
    'starlette',
    'starlette.middleware',
    'starlette.routing',

    # Database
    'sqlmodel',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'pydantic',
    'pydantic_core',
    'pydantic_settings',

    # Workers
    'arq',
    'redis',
    'redis.asyncio',

    # AI/ML
    'faster_whisper',
    'ctranslate2',
    'google.generativeai',
    'google.ai.generativelanguage',
    'onnxruntime',
    'onnxruntime.capi',
    'cv2',
    'numpy',

    # Video
    'ffmpeg_python',
    'ffmpeg',
    'yt_dlp',

    # Utilities
    'httpx',
    'python_multipart',
    'python_dotenv',
    'cryptography',
    'keyring',
    'win32crypt',
    'pywintypes',
    'watchdog',
    'watchdog.observers',
    'watchdog.events',

    # Stdlib
    'asyncio',
    'json',
    'pathlib',
    'subprocess',
    'threading',
    'tempfile',
    'shutil',
    'urllib.parse',
    'dataclasses',
    'typing',
    'datetime',
    'uuid',
    'hashlib',
    'base64',
    'mimetypes',
]

# Exclude modules to reduce size
excludes = [
    'pytest', 'pytest_asyncio', 'ruff', 'black', 'isort', 'mypy',
    'jupyter', 'ipython', 'notebook', 'matplotlib', 'pandas',
    'scipy', 'sklearn', 'tensorflow', 'torch', 'transformers',
    'sphinx', 'docutils', 'setuptools', 'pip', 'wheel',
    'tkinter', 'tcl', 'ttk',
    'unittest', 'doctest', 'pdb', 'profile',
]

a = Analysis(
    ['src/main.py'],
    pathex=[str(SRC_ROOT), str(BACKEND_ROOT)],
    binaries=collect_binaries(),
    datas=collect_data_files(),
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(RESOURCES_ROOT / 'icon.ico') if (RESOURCES_ROOT / 'icon.ico').exists() else None,
)