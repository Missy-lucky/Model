# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


base_dir = Path(SPECPATH)


a = Analysis(
    [str(base_dir / "desktop_app.py")],
    pathex=[str(base_dir)],
    binaries=[],
    datas=[
        (str(base_dir / "assets" / "app-icon.ico"), "assets"),
        (str(base_dir / "assets" / "models" / "u2netp.onnx"), str(Path("assets") / "models")),
    ],
    hiddenimports=[
        "apparel_studio",
        "studio_core",
        "segmentation",
        "pillow_heif",
        "onnxruntime",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "pandas",
        "pytest",
        "pygame",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "torch",
        "torchvision",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LongY_Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(base_dir / "assets" / "app-icon.ico"),
    version=str(base_dir / "version_info.txt"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LongY_Studio",
)
