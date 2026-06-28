# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# Resolve icon path based on platform
def get_icon():
    if sys.platform == "darwin":
        return "assets/icon.icns"
    elif sys.platform == "win32":
        return "assets/icon.ico"
    else:
        return "assets/icon.png"

a = Analysis(
    ["src/main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("assets", "assets"),
    ],
    hiddenimports=[
        "customtkinter",
        "PIL",
        "minecraft_launcher_lib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_file = get_icon()

if sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="OmniLauncher-MC",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon=icon_file,
    )
    app = BUNDLE(
        exe,
        name="OmniLauncher-MC.app",
        icon=icon_file,
        bundle_identifier="dev.omninodeco.omnilauncher-mc",
        info_plist={
            "CFBundleName": "OmniLauncher-MC",
            "CFBundleDisplayName": "OmniLauncher-MC",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="OmniLauncher-MC",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon=icon_file if sys.platform == "win32" else None,
    )