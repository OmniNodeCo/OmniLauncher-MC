"""OmniLauncher-MC launcher service - rewritten with full feature set."""

from __future__ import annotations

import datetime
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:
    import minecraft_launcher_lib
    import minecraft_launcher_lib.utils
    import minecraft_launcher_lib.command
    import minecraft_launcher_lib.install

    HAS_LIB = True
except Exception:
    HAS_LIB = False

# ---- Shared state for UI polling ----
current_status: str = "Ready"
current_progress: int = 0
current_max: int = 100
console_lines: List[str] = []
_install_lock = threading.Lock()
_launch_thread: Optional[threading.Thread] = None

# callbacks for UI (set by GUI)
_status_callbacks: List[Callable[[str], None]] = []
_progress_callbacks: List[Callable[[int, int], None]] = []
_console_callbacks: List[Callable[[str], None]] = []


def add_status_listener(cb: Callable[[str], None]) -> None:
    _status_callbacks.append(cb)


def add_progress_listener(cb: Callable[[int, int], None]) -> None:
    _progress_callbacks.append(cb)


def add_console_listener(cb: Callable[[str], None]) -> None:
    _console_callbacks.append(cb)


# ---- internal setters ----

def _set_status(status: str) -> None:
    global current_status
    current_status = status
    for cb in _status_callbacks:
        try:
            cb(status)
        except Exception:
            pass


def _set_progress(progress: int) -> None:
    global current_progress
    current_progress = progress
    for cb in _progress_callbacks:
        try:
            cb(progress, current_max)
        except Exception:
            pass


def _set_max(max_value: int) -> None:
    global current_max
    current_max = max_value
    for cb in _progress_callbacks:
        try:
            cb(current_progress, max_value)
        except Exception:
            pass


def _add_console(line: str) -> None:
    console_lines.append(line)
    # keep only last 5000 lines to avoid memory blow
    if len(console_lines) > 5000:
        del console_lines[0 : len(console_lines) - 5000]
    for cb in _console_callbacks:
        try:
            cb(line)
        except Exception:
            pass


# ---- utils ----

def get_minecraft_dir(settings=None) -> str:
    if settings:
        d = settings.get("general", "minecraft_directory")
        if d:
            return d
    if HAS_LIB:
        return minecraft_launcher_lib.utils.get_minecraft_directory()
    return str(Path.home() / ".minecraft")


def get_release_versions():
    # kept for backward compat, delegates to versions service
    from omnilauncher.services.versions import get_release_versions as _grv

    try:
        from omnilauncher.config.settings import get_settings_manager

        return _grv(get_settings_manager())
    except Exception:
        return _grv()


def get_latest_version():
    from omnilauncher.services.versions import get_latest_version as _glv

    try:
        from omnilauncher.config.settings import get_settings_manager

        return _glv(get_settings_manager())
    except Exception:
        return _glv()


def install_version(version: str, minecraft_dir: Optional[str] = None, settings=None) -> None:
    if not HAS_LIB:
        _set_status("minecraft_launcher_lib not installed")
        time.sleep(1)
        _set_status("Ready")
        return
    mc_dir = minecraft_dir or get_minecraft_dir(settings)
    callback = {
        "setStatus": _set_status,
        "setProgress": _set_progress,
        "setMax": _set_max,
    }
    try:
        minecraft_launcher_lib.install.install_minecraft_version(
            version,
            mc_dir,
            callback=callback,
        )
    except Exception as e:
        _set_status(f"Install failed: {e}")
        _add_console(f"[ERROR] Install failed: {e}\n")
        raise


# ---- Launch logic ----

def launch(username: str, version: str, ram_mb: int, settings=None, instance_id: Optional[str] = None) -> None:
    """Start async launch thread."""
    global _launch_thread
    if _launch_thread and _launch_thread.is_alive():
        _set_status("Already launching")
        return
    _launch_thread = threading.Thread(
        target=run_game,
        args=(username, version, ram_mb, settings, instance_id),
        daemon=True,
    )
    _launch_thread.start()


def run_game(
    username: str,
    version: str,
    ram_mb: int,
    settings=None,
    instance_id: Optional[str] = None,
) -> None:
    """Blocking game runner - meant to run in thread."""
    with _install_lock:
        _set_status("Checking version...")
        _set_progress(0)
        _set_max(100)

        mc_dir = get_minecraft_dir(settings)

        # support per-instance minecraft dir suffix
        if instance_id and settings:
            try:
                inst = next(
                    (i for i in settings.get("instances", "list", default=[]) if i.get("id") == instance_id),
                    None,
                )
                if inst and inst.get("minecraft_dir_suffix"):
                    suffix = inst["minecraft_dir_suffix"]
                    # if instance wants isolated dir, use subfolder
                    mc_dir = os.path.join(mc_dir, "instances", suffix)
                    os.makedirs(mc_dir, exist_ok=True)
            except Exception:
                pass

        # attempt install
        try:
            install_version(version, mc_dir, settings)
        except Exception as e:
            _set_status(f"Install error: {e}")
            time.sleep(2)
            _set_status("Ready")
            return

        _set_status("Building launch command...")

        # build options
        # RAM handling: ram_mb is MB, launcher expects Xmx in G or M. We'll use M.
        # Also take into account settings overrides
        effective_ram = ram_mb
        jvm_args_list: List[str] = []

        if settings:
            # JVM args from settings
            if settings.get("java", "use_custom_args") and settings.get("java", "jvm_args"):
                custom = settings.get("java", "jvm_args", default="").strip()
                if custom:
                    jvm_args_list.extend(custom.split())

            # game resolution
            res_cfg = settings.get("game", "resolution", default={})
            # options dict for minecraft_launcher_lib
            game_opts: Dict = {
                "username": username,
                "uuid": _get_uuid_for_username(username, settings),
                "token": "",
            }

            # instance overrides
            if instance_id:
                inst = next(
                    (i for i in settings.get("instances", "list", default=[]) if i.get("id") == instance_id),
                    None,
                )
                if inst:
                    if inst.get("ram_override"):
                        try:
                            effective_ram = int(inst["ram_override"])
                        except Exception:
                            pass
                    if inst.get("jvm_args_override"):
                        jvm_args_list.extend(inst["jvm_args_override"].split())

            # clamp ram
            effective_ram = max(512, min(effective_ram, 32768))

            # JVM args min/max
            jvm_args_list.insert(0, f"-Xmx{effective_ram}M")
            jvm_args_list.insert(0, f"-Xms{max(256, effective_ram // 4)}M")

            # resolution
            if res_cfg.get("enabled"):
                if res_cfg.get("fullscreen"):
                    game_opts["enableFullscreen"] = True
                else:
                    w = res_cfg.get("width", 854)
                    h = res_cfg.get("height", 480)
                    game_opts["resolutionWidth"] = str(w)
                    game_opts["resolutionHeight"] = str(h)

            # demo
            if settings.get("game", "demo", default=False):
                game_opts["demo"] = True

            # game args
            if settings.get("game", "use_custom_args") and settings.get("game", "game_args"):
                # minecraft_launcher_lib supports customGameArgs?
                # We'll put into launcherVersion? For now store but not use directly; we will append manually
                pass

            # java path override
            java_path = None
            if not settings.get("java", "auto_detect", default=True):
                java_path = settings.get("java", "java_path")
                if instance_id and inst and inst.get("java_override"):
                    java_path = inst["java_override"]
                if java_path and os.path.exists(java_path):
                    game_opts["executablePath"] = java_path

            # special: merge JVM args into jvmArguments
            game_opts["jvmArguments"] = jvm_args_list

            options = game_opts
        else:
            options = {
                "username": username,
                "uuid": _get_uuid_for_username(username, None),
                "token": "",
                "jvmArguments": [f"-Xmx{effective_ram}M", f"-Xms{effective_ram // 4}M"],
            }

        # pre-launch command
        try:
            if settings and settings.get("advanced", "pre_launch_command"):
                cmd = settings.get("advanced", "pre_launch_command")
                if cmd:
                    subprocess.Popen(cmd, shell=True)
        except Exception:
            pass

        if not HAS_LIB:
            _set_status("Cannot launch without minecraft_launcher_lib")
            _add_console("[ERROR] minecraft-launcher-lib not installed\n")
            return

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(
                version,
                mc_dir,
                options,
            )
        except Exception as e:
            _set_status(f"Command build failed: {e}")
            _add_console(f"[ERROR] {e}\n")
            return

        # append custom game args if present
        if settings and settings.get("game", "use_custom_args"):
            ga = settings.get("game", "game_args", default="").strip()
            if ga:
                command.extend(ga.split())

        # wrapper command
        if settings and settings.get("advanced", "wrapper_command"):
            wrap = settings.get("advanced", "wrapper_command", "").strip()
            if wrap:
                command = wrap.split() + command

        _set_status("Starting Minecraft...")
        _add_console(f"[INFO] Launching {version} as {username} with {effective_ram}MB\n")
        _add_console(f"[INFO] Command: {' '.join(command[:5])} ...\n")

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=mc_dir,
            )
        except Exception as e:
            _set_status(f"Failed to start: {e}")
            _add_console(f"[ERROR] Failed to start process: {e}\n")
            return

        _set_status("Running")

        threading.Thread(target=_read_stream, args=(process.stdout, False), daemon=True).start()
        threading.Thread(target=_read_stream, args=(process.stderr, True), daemon=True).start()

        # update last played etc
        if settings and instance_id:
            try:
                for inst in settings.data["instances"]["list"]:
                    if inst.get("id") == instance_id:
                        inst["last_played"] = datetime.datetime.now().isoformat()
                        settings.save()
                        break
            except Exception:
                pass

        process.wait()
        rc = process.returncode
        if rc == 0:
            _set_status("Done")
            _add_console(f"[INFO] Game exited with code {rc}\n")
        else:
            _set_status(f"Exited ({rc})")
            _add_console(f"[WARN] Game exited with code {rc}\n")

        # post exit command
        try:
            if settings and settings.get("advanced", "post_exit_command"):
                cmd = settings.get("advanced", "post_exit_command")
                if cmd:
                    subprocess.Popen(cmd, shell=True)
        except Exception:
            pass

        time.sleep(1.5)
        _set_status("Ready")


def _read_stream(stream, is_error: bool) -> None:
    try:
        for line in stream:
            prefix = "[ERR] " if is_error else ""
            _add_console(prefix + line)
    except Exception:
        pass


def _get_uuid_for_username(username: str, settings) -> str:
    # try to find uuid from accounts
    if settings:
        lst = settings.get("accounts", "list", default=[])
        for acc in lst:
            if acc.get("username") == username and acc.get("uuid"):
                # strip dashes? minecraft expects with dashes? lib accepts without? Provide as needed
                return acc["uuid"]
    # offline uuid generation - hash username? use deterministic-ish uuid
    import hashlib

    # offline player uuid v3 based on username like Java does: UUID.nameUUIDFromBytes("OfflinePlayer:" + name)
    # Python implementation: md5 hash and set version
    try:
        hs = hashlib.md5(f"OfflinePlayer:{username}".encode("utf-8")).digest()
        # set version 3
        ba = bytearray(hs)
        ba[6] = (ba[6] & 0x0F) | 0x30
        ba[8] = (ba[8] & 0x3F) | 0x80
        import uuid as _uuid

        return str(_uuid.UUID(bytes=bytes(ba)))
    except Exception:
        import uuid as _uuid

        return str(_uuid.uuid4())
