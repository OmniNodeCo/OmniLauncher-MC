"""OmniLauncher-MC launcher service."""

import subprocess
import threading

import minecraft_launcher_lib

# ---- Shared state for UI polling ----
current_status: str = "Ready"
current_progress: int = 0
current_max: int = 100
console_lines: list[str] = []


# ---- Callback setters ----

def _set_status(status: str) -> None:
    global current_status
    current_status = status


def _set_progress(progress: int) -> None:
    global current_progress
    current_progress = progress


def _set_max(max_value: int) -> None:
    global current_max
    current_max = max_value


# ---- Minecraft helpers ----

def get_minecraft_dir() -> str:
    return minecraft_launcher_lib.utils.get_minecraft_directory()


def get_release_versions() -> list[str]:
    versions = []
    for version in minecraft_launcher_lib.utils.get_version_list():
        if version["type"] == "release":
            versions.append(version["id"])
    return versions


def get_latest_version() -> str:
    return minecraft_launcher_lib.utils.get_latest_version()["release"]


def install_version(version: str) -> None:
    callback = {
        "setStatus": _set_status,
        "setProgress": _set_progress,
        "setMax": _set_max,
    }
    minecraft_launcher_lib.install.install_minecraft_version(
        version,
        get_minecraft_dir(),
        callback=callback,
    )


# ---- Launch ----

def launch(username: str, version: str, ram: int) -> None:
    thread = threading.Thread(
        target=run_game,
        args=(username, version, ram),
        daemon=True,
    )
    thread.start()


def run_game(username: str, version: str, ram: int) -> None:
    global current_status

    current_status = "Checking version..."
    install_version(version)

    current_status = "Building launch command..."
    options = {
        "username": username,
        "jvmArguments": [f"-Xmx{ram}G", f"-Xms{ram}G"],
    }

    command = minecraft_launcher_lib.command.get_minecraft_command(
        version,
        get_minecraft_dir(),
        options,
    )

    current_status = "Starting Minecraft..."
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    current_status = "Running"

    threading.Thread(
        target=_read_stream,
        args=(process.stdout,),
        daemon=True,
    ).start()

    threading.Thread(
        target=_read_stream,
        args=(process.stderr,),
        daemon=True,
    ).start()

    process.wait()
    current_status = "Done"


def _read_stream(stream) -> None:
    for line in stream:
        console_lines.append(line)