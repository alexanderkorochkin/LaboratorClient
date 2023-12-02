# -*- mode: python ; coding: utf-8 -*-


from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

site_packages_dir = 'D:/PythonProjects/Laborator/LaboratorClient/venv/Lib/site-packages/'

block_cipher = None

datass=[('./libs/effects/*.*', 'libs/effects'), ('./libs/iapws/VERSION', 'libs/iapws'), ('./libs/kivy.ini', 'libs'), ('./libs/kv/*.*', 'libs/kv'), ('./help.json', '.')]
datas_names = ['opcua', 'numpy', 'scipy']

for name in datas_names:
	datass.append((site_packages_dir+name, f'./{name}'))


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datass,
    hiddenimports=datas_names,
    hookspath=[kivymd_hooks_path],
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
    name='LaboratorClient',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
	hide_console='hide-late',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
	*[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LaboratorClient',
)
