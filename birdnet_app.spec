# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

# 1. Collect Streamlit metadata and data
datas = copy_metadata('streamlit')
datas += collect_data_files('streamlit')

# 2. Add your custom project folders
# Format: (Source Folder, Destination Folder inside the EXE)
datas += [
    ('fonts', 'fonts'),
    ('assets', 'assets'),
    ('models', 'models'),
    ('.streamlit', '.streamlit'),
    ('bird_app.py', '.') 
]

block_cipher = None

a = Analysis(
    ['run_app.py'], # This is your bootstrap/wrapper script
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pygbif', 'birdnetlib', 'pyarrow.vendored.version'],
    hookspath=['./hooks'], # Points to your hook-streamlit.py
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BirdSightAnalytics', # The name of your .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # Set to True if you need to debug errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements=None,
    icon='assets/gazelle_logo.png' # Optional: Add an icon file here
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BirdSightAnalytics',
)