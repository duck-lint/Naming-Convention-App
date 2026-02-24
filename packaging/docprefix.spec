# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for DocPrefix (Tkinter GUI).

Notes:
- ONEDIR is the default output (portable folder) because corporate AV tools often
  flag ONEFILE self-extracting executables more aggressively.
- Tkinter/Tcl/Tk runtime assets are typically collected by PyInstaller's built-in
  hooks, so hiddenimports are left empty unless a concrete build/runtime issue
  requires them.
"""

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve().parent.parent


a = Analysis(
    [str(PROJECT_ROOT / "doc_prefix_gui.pyw")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    name="DocPrefix",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DocPrefix",
)
