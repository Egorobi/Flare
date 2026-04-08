# -*- mode: python ; coding: utf-8 -*-

import platform
if platform.system() == "Windows":
    venv_path = './venv/Lib/'
else:
    venv_path = './venv/lib/python3.13/'

a = Analysis(
    ['flare/main.py'],
    pathex=[],
    binaries=[],
    datas=[(venv_path + '/site-packages/nicegui', 'nicegui'),
    ('./data/assets', './assets'),
    ('./data/elements', './elements'),
    ('./data/tips.md', '.'),
    ('./data/saves/colors.json', './saves')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)
splash = Splash(
    './data/assets/splash.png',
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=12,
    minify_script=True,
    always_on_top=False,
)

exe = EXE(
    pyz,
    splash,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Flare',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory="data",
    icon = "./data/assets/favicon2.ico",
)
coll = COLLECT(
    exe,
    splash.binaries,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Flare',
)
