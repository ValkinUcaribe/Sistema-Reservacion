# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ingresoToken.py'],
    pathex=[],
    binaries=[],
    datas=[('Fondo1.jpg', '.'), ('Logo V1_1.jpg', '.'), ('LogoValkin.png', '.')],
    hiddenimports=['mysql.connector'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['opentelemetry'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ingresoToken',
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
)
