import sys

from cx_Freeze import setup, Executable
import os

build_options = {
    "packages": [
        "tkinter",
        "minecraft_launcher_lib",
        "json",
        "os",
        "subprocess",
    ],
    "include_files": [
        "launcher.py",
        "Changelog.txt",
        "LICENSE.txt",
        "TERMS.txt",
        "settings.json"
    ]
}

base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="OmniLauncher-MC",
    version="1.0.0",
    options={"build_exe": build_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            target_name="OmniLauncher-MC",
        )
    ]
)