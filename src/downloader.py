"""Download and install Minecraft versions."""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

import threading
from pathlib import Path
from typing import Callable, Optional

import minecraft_launcher_lib as mll


class DownloadManager:
    """Handles downloading and installing Minecraft versions."""

    def __init__(self, minecraft_dir):
        self.minecraft_dir = minecraft_dir
        self._cancel = False

    def get_versions(self, include_snapshots=False):
        try:
            versions = mll.utils.get_version_list()
            if not include_snapshots:
                versions = [v for v in versions if v["type"] == "release"]
            return versions
        except Exception:
            return []

    def get_installed_versions(self):
        try:
            installed = mll.utils.get_installed_versions(self.minecraft_dir)
            return [v["id"] for v in installed]
        except Exception:
            return []

    def is_installed(self, version_id):
        return version_id in self.get_installed_versions()

    def install_version(self, version_id, progress_callback=None,
                        done_callback=None, error_callback=None):
        self._cancel = False

        def _worker():
            try:
                callback_dict = {}
                if progress_callback:
                    callback_dict["setStatus"] = lambda text: progress_callback("status", text)
                    callback_dict["setProgress"] = lambda val: progress_callback("progress", val)
                    callback_dict["setMax"] = lambda val: progress_callback("max", val)
                mll.install.install_minecraft_version(
                    version_id, self.minecraft_dir, callback=callback_dict
                )
                if done_callback:
                    done_callback(version_id)
            except Exception as e:
                if error_callback:
                    error_callback(str(e))

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def cancel(self):
        self._cancel = True

    def get_launch_command(self, version_id, username, uuid_str, token,
                           java_path="java", jvm_args=None):
        options = mll.types.MinecraftOptions(
            username=username,
            uuid=uuid_str,
            token=token if token else "0",
        )
        if jvm_args:
            options.jvmArguments = jvm_args
        if java_path:
            options.executablePath = java_path
        try:
            command = mll.command.get_minecraft_command(
                version_id, self.minecraft_dir, options
            )
            return command
        except Exception:
            return []

    def resolve_version(self, version_str):
        if version_str == "latest-release":
            versions = self.get_versions(include_snapshots=False)
            return versions[0]["id"] if versions else ""
        elif version_str == "latest-snapshot":
            versions = self.get_versions(include_snapshots=True)
            return versions[0]["id"] if versions else ""
        return version_str