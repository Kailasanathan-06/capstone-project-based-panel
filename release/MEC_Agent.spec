# pyinstaller spec for the SecureDT MEC agent (single-file executable).

import os

block_cipher = None

a = Analysis(
    ["mec_agent/agent.py"],
    pathex=[os.path.abspath(".")],
    binaries=[],
    datas=[
        ("engine", "engine"),
    ],
    hiddenimports=[
        "psutil",
        "requests",
        "urllib3",
        "PIL",
        "PIL.Image",
        "PIL.ImageOps",
        "numpy",
        "engine",
        "engine.image_processor",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "django",
        "pandas",
        "sklearn",
        "torch",
        "matplotlib",
        "fpdf",
        "reportlab",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="MEC_Agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
)