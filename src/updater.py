"""
Auto-update checker for OmniLauncher-MC.
Checks GitHub releases for new versions.
"""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

import threading
import platform
import webbrowser
import logging
import json
import time
from pathlib import Path
from typing import Callable, Optional

try:
    import requests
except ImportError:
    requests = None

from utils import get_app_dir

logger = logging.getLogger("OmniLauncher-MC")

CURRENT_VERSION = "1.0.0"
GITHUB_OWNER = "OmniNodeCo"
GITHUB_REPO = "OmniLauncher-MC"
API_URL = "https://api.github.com/repos/%s/%s/releases/latest" % (
    GITHUB_OWNER,
    GITHUB_REPO,
)
RELEASES_URL = "https://github.com/%s/%s/releases/latest" % (
    GITHUB_OWNER,
    GITHUB_REPO,
)
CHECK_INTERVAL = 3600  # seconds between checks (1 hour)


def parse_version(version_str):
    """Parse version string like 'v1.2.3' or '1.2.3' into tuple of ints."""
    clean = version_str.strip().lstrip("vV")
    parts = []
    for part in clean.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            # Handle pre-release tags like '1.2.3-beta1'
            numeric = ""
            for ch in part:
                if ch.isdigit():
                    numeric += ch
                else:
                    break
            if numeric:
                parts.append(int(numeric))
            else:
                parts.append(0)
    # Pad to at least 3 components
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_newer(remote_version, local_version):
    """Check if remote_version is newer than local_version."""
    remote = parse_version(remote_version)
    local = parse_version(local_version)
    return remote > local


class UpdateInfo:
    """Container for update information."""

    def __init__(self):
        self.available = False
        self.current_version = CURRENT_VERSION
        self.latest_version = ""
        self.release_name = ""
        self.release_notes = ""
        self.release_url = RELEASES_URL
        self.download_url = ""
        self.published_at = ""
        self.error = ""
        self.checked_at = ""

    def to_dict(self):
        return {
            "available": self.available,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "release_name": self.release_name,
            "release_notes": self.release_notes,
            "release_url": self.release_url,
            "download_url": self.download_url,
            "published_at": self.published_at,
            "error": self.error,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, data):
        info = cls()
        info.available = data.get("available", False)
        info.current_version = data.get("current_version", CURRENT_VERSION)
        info.latest_version = data.get("latest_version", "")
        info.release_name = data.get("release_name", "")
        info.release_notes = data.get("release_notes", "")
        info.release_url = data.get("release_url", RELEASES_URL)
        info.download_url = data.get("download_url", "")
        info.published_at = data.get("published_at", "")
        info.error = data.get("error", "")
        info.checked_at = data.get("checked_at", "")
        return info


class UpdateChecker:
    """
    Checks GitHub releases for new versions of OmniLauncher-MC.
    Caches results and supports background checking.
    """

    def __init__(self, appdata_mgr=None):
        self.appdata = appdata_mgr
        if self.appdata:
            self.cache_file = self.appdata.get_file("update_cache")
        else:
            self.cache_file = get_app_dir() / "cache" / "update_cache.json"
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        self._last_check = 0
        self._cached_info = None

    def _load_cache(self):
        """Load cached update info from disk."""
        try:
            with open(str(self.cache_file), "r", encoding="utf-8") as f:
                data = json.load(f)
            self._cached_info = UpdateInfo.from_dict(data)
            self._last_check = data.get("_check_timestamp", 0)
            return self._cached_info
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def _save_cache(self, info):
        """Save update info to disk cache."""
        data = info.to_dict()
        data["_check_timestamp"] = time.time()
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(str(self.cache_file), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.error("Failed to save update cache: %s" % str(e))

    def _get_platform_asset_url(self, assets):
        """Find the download URL for the current platform from release assets."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        platform_keys = {
            "windows": ["windows", "win", ".exe"],
            "darwin": ["macos", "darwin", "mac", ".zip"],
            "linux": ["linux", ".tar.gz", ".appimage"],
        }

        keys = platform_keys.get(system, [])

        for asset in assets:
            name = asset.get("name", "").lower()
            for key in keys:
                if key in name:
                    return asset.get("browser_download_url", "")
        return ""

    def check_now(self):
        """
        Check for updates synchronously.
        Returns UpdateInfo.
        """
        info = UpdateInfo()

        if requests is None:
            info.error = "requests library not available"
            logger.warning("Update check skipped: requests not available")
            return info

        try:
            logger.info("Checking for updates...")
            response = requests.get(
                API_URL,
                timeout=10,
                headers={"Accept": "application/vnd.github.v3+json"},
            )
            response.raise_for_status()
            data = response.json()

            tag = data.get("tag_name", "")
            info.latest_version = tag
            info.release_name = data.get("name", tag)
            info.release_notes = data.get("body", "")[:500]
            info.release_url = data.get("html_url", RELEASES_URL)
            info.published_at = data.get("published_at", "")
            info.checked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            assets = data.get("assets", [])
            info.download_url = self._get_platform_asset_url(assets)

            if tag and is_newer(tag, CURRENT_VERSION):
                info.available = True
                logger.info(
                    "Update available: %s -> %s" % (CURRENT_VERSION, tag)
                )
            else:
                info.available = False
                logger.info("No update available (current: %s)" % CURRENT_VERSION)

            self._cached_info = info
            self._last_check = time.time()
            self._save_cache(info)

        except requests.exceptions.Timeout:
            info.error = "Connection timed out"
            logger.warning("Update check timed out")
        except requests.exceptions.ConnectionError:
            info.error = "No internet connection"
            logger.warning("Update check failed: no connection")
        except requests.exceptions.HTTPError as e:
            info.error = "HTTP error: %s" % str(e)
            logger.warning("Update check HTTP error: %s" % str(e))
        except Exception as e:
            info.error = "Unexpected error: %s" % str(e)
            logger.error("Update check error: %s" % str(e))

        return info

    def check_async(self, callback=None):
        """
        Check for updates in a background thread.
        callback(UpdateInfo) is called when done.
        """

        def _worker():
            info = self.check_now()
            if callback:
                callback(info)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

    def check_if_needed(self, callback=None):
        """
        Check for updates only if enough time has passed since last check.
        Uses cache if recent enough.
        """
        cached = self._load_cache()
        now = time.time()

        if cached and (now - self._last_check) < CHECK_INTERVAL:
            logger.info("Using cached update info (age: %ds)" % int(now - self._last_check))
            if callback:
                callback(cached)
            return

        self.check_async(callback=callback)

    def get_cached(self):
        """Get cached update info without checking."""
        if self._cached_info:
            return self._cached_info
        return self._load_cache()

    def skip_version(self, version):
        """Mark a version as skipped (user chose to ignore it)."""
        skip_file = self.cache_file.parent / "skipped_versions.json"
        try:
            with open(str(skip_file), "r", encoding="utf-8") as f:
                skipped = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            skipped = []
        if version not in skipped:
            skipped.append(version)
        try:
            with open(str(skip_file), "w", encoding="utf-8") as f:
                json.dump(skipped, f)
        except OSError:
            pass

    def is_version_skipped(self, version):
        """Check if a version was previously skipped."""
        skip_file = self.cache_file.parent / "skipped_versions.json"
        try:
            with open(str(skip_file), "r", encoding="utf-8") as f:
                skipped = json.load(f)
            return version in skipped
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return False

    @staticmethod
    def open_download_page():
        """Open the releases page in the default browser."""
        webbrowser.open(RELEASES_URL)