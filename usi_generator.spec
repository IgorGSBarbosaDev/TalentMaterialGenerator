# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH)
pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all("PySide6")
template_datas = [
    (str(path), "carometros")
    for path in sorted((project_root / "carometros").glob("*.pptx"))
]
icon_datas = [
    (str(project_root / "assets" / "iconeUsiGenerator.ico"), "assets"),
    (str(project_root / "assets" / "iconeUsiGenerator.png"), "assets"),
]
if not template_datas:
    raise SystemExit("Nenhum template PPTX foi encontrado em 'carometros'.")


a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=pyside_binaries,
    datas=pyside_datas + template_datas + icon_datas,
    hiddenimports=pyside_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="USI Generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(project_root / "assets" / "iconeUsiGenerator.ico"),
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="USI Generator",
)
