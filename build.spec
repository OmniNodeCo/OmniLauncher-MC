# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

src_path = os.path.join(os.path.dirname(os.path.abspath(SPEC)), "src")


def get_icon():
    if sys.platform == "darwin":
        return "assets/icon.icns"
    elif sys.platform == "win32":
        return "assets/icon.ico"
    else:
        return None


a = Analysis(
    [os.path.join(src_path, "main.py")],
    pathex=[src_path],
    binaries=[],
    datas=[
        ("assets", "assets"),
    ],
    hiddenimports=[
        "customtkinter",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageTk",
        "minecraft_launcher_lib",
        "minecraft_launcher_lib.utils",
        "minecraft_launcher_lib.install",
        "minecraft_launcher_lib.command",
        "minecraft_launcher_lib.types",
        "requests",
        "certifi",
        "charset_normalizer",
        "idna",
        "urllib3",
        "launcher",
        "auth",
        "downloader",
        "profiles",
        "settings",
        "updater",
        "appdata",
        "utils",
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
        icon=icon_file,
    )