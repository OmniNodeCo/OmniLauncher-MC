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
from omnilauncher.services.versions import (
    get_version_list,
    get_all_version_ids,
    refresh_cache,
)
from omnilauncher.services.accounts import AccountService
from omnilauncher.services.instances import InstanceService
from omnilauncher.services.java import find_java_executables
from omnilauncher.services.file_explorer import list_files, get_bookmarks
from omnilauncher.services.crash_analyzer import analyze_crash, format_report

__all__ = [
    "get_minecraft_dir",
    "get_release_versions",
    "get_latest_version",
    "install_version",
    "launch",
    "run_game",
    "handle_error",
    "get_version_list",
    "get_all_version_ids",
    "refresh_cache",
    "AccountService",
    "InstanceService",
    "find_java_executables",
    "list_files",
    "get_bookmarks",
    "analyze_crash",
    "format_report",
]
