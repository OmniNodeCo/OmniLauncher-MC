"""Minecraft launcher service module."""

import subprocess
import threading

import minecraft_launcher_lib


def get_minecraft_dir():
    """Get the Minecraft directory path."""
    return minecraft_launcher_lib.utils.get_minecraft_directory()


def get_release_versions():
    """Get list of release versions."""
    versions = []
    for version in minecraft_launcher_lib.utils.get_version_list():
        if version["type"] == "release":
            versions.append(version["id"])
    return versions


def get_latest_version():
    """Get the latest release version."""
    return minecraft_launcher_lib.utils.get_latest_version()["release"]


def install_version(version: str):
    """Install a specific Minecraft version."""
    minecraft_launcher_lib.install.install_minecraft_version(
        version, get_minecraft_dir()
    )


def launch(username: str, version: str, ram: int):
    """Launch Minecraft in a separate thread."""
    thread = threading.Thread(target=run_game, args=(username, version, ram))
    thread.start()


def run_game(username: str, version: str, ram: int):
    """Run the Minecraft game."""
    install_version(version)
    options = {"username": username, "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"]}

    command = minecraft_launcher_lib.command.get_minecraft_command(
        version, get_minecraft_dir(), options
    )

    subprocess.Popen(command)
