"""Services package for OmniLauncher-MC."""

from omnilauncher.services.launcher import (
    get_minecraft_dir,
    get_release_versions,
    get_latest_version,
    install_version,
    launch,
    run_game,
)

from omnilauncher.services.error_handler import handle_error

__all__ = [
    "get_minecraft_dir",
    "get_release_versions",
    "get_latest_version",
    "install_version",
    "launch",
    "run_game",
    "handle_error",
]