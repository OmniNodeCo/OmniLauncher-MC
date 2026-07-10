import minecraft_launcher_lib
import subprocess
import tkinter

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

def launch():
    username = username_entry.get()
    version = version_combobox.get()

    # Run in thread so UI doesnt freeze
    thread = threading.Thread(target=run_game, args=(username, version))
    thread.start()

def run_game(username, version):
    install_version(version)
    launch_game(username, version)

    command = minecraft_launcher_lib.command.get_minecraft_command(
        version,
        get_minecraft_dir(),
        options
    )

    subprocess.Popen(command)
