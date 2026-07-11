import subprocess
import threading

import minecraft_launcher_lib


def get_minecraft_dir():
    return minecraft_launcher_lib.utils.get_minecraft_directory()

def get_release_versions():
    versions = []
    for version in minecraft_launcher_lib.utils.get_version_list():
        if version["type"] == "release":
            versions.append(version["id"])
    return versions

def get_latest_version():
    return minecraft_launcher_lib.utils.get_latest_version()["release"]


def install_version(version):
    minecraft_launcher_lib.install.install_minecraft_version(
        version,
        get_minecraft_dir()
    )

def launch(username, version, ram):
    thread = threading.Thread(target=run_game, args=(username, version, ram))

    thread.start()

def run_game(username, version, ram):
    install_version(version)
    options = {
        "username": username,
        "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"]
    }

    command = minecraft_launcher_lib.command.get_minecraft_command(
        version,
        get_minecraft_dir(),
        options
    )


    subprocess.Popen(command)
