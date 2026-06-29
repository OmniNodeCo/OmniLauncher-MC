"""
Full application data directory management for OmniLauncher-MC.
Handles creation, migration, cleanup, and validation of all app data.
"""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

import platform
import shutil
import json
import time
import logging
from pathlib import Path
from datetime import datetime


APP_NAME = "OmniLauncher-MC"
APP_VERSION = "1.0.0"

# Directory structure inside appdata
DIRECTORIES = {
    "root": "",
    "cache": "cache",
    "logs": "logs",
    "profiles": "profiles",
    "instances": "instances",
    "skins": "skins",
    "backups": "backups",
    "temp": "temp",
}

# Files managed by appdata
MANAGED_FILES = {
    "settings": "settings.json",
    "profiles": "profiles.json",
    "auth": "auth.json",
    "update_cache": "cache/update_cache.json",
    "app_state": "app_state.json",
}

logger = logging.getLogger("OmniLauncher-MC")


class AppDataManager:
    """
    Manages the full application data directory.
    Creates required directories, handles backups, cleanup, migration.
    """

    def __init__(self, custom_root=None):
        """
        Initialize the AppData manager.
        custom_root: optional override for the base directory.
        """
        if custom_root:
            self.root = Path(custom_root)
        else:
            self.root = self._get_default_root()

        self._ensure_structure()
        self._setup_logging()
        self._write_app_state()

    @staticmethod
    def _get_default_root():
        """Get the default app data root for this OS."""
        system = platform.system()
        if system == "Windows":
            base = Path(os.getenv("APPDATA", str(Path.home())))
        elif system == "Darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
        return base / APP_NAME

    def _ensure_structure(self):
        """Create all required directories."""
        for name, subpath in DIRECTORIES.items():
            directory = self.root / subpath if subpath else self.root
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Set up file logging in the logs directory."""
        log_dir = self.get_dir("logs")
        log_file = log_dir / ("launcher_%s.log" % datetime.now().strftime("%Y%m%d"))

        handler = logging.FileHandler(str(log_file), encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            logger.addHandler(handler)
            logger.addHandler(logging.StreamHandler(sys.stdout))

        logger.info("OmniLauncher-MC v%s starting" % APP_VERSION)
        logger.info("App data root: %s" % self.root)
        logger.info("Platform: %s" % platform.platform())

    def _write_app_state(self):
        """Write current app state to file."""
        state = {
            "version": APP_VERSION,
            "last_launched": datetime.now().isoformat(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "app_root": str(self.root),
        }
        state_file = self.root / MANAGED_FILES["app_state"]
        try:
            with open(str(state_file), "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error("Failed to write app state: %s" % str(e))

    def get_dir(self, name):
        """Get a named directory path. Creates it if needed."""
        subpath = DIRECTORIES.get(name, name)
        directory = self.root / subpath if subpath else self.root
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def get_file(self, name):
        """Get a managed file path."""
        rel_path = MANAGED_FILES.get(name, name)
        filepath = self.root / rel_path
        filepath.parent.mkdir(parents=True, exist_ok=True)
        return filepath

    def load_json(self, name):
        """Load a JSON file by managed name or relative path."""
        filepath = self.get_file(name)
        try:
            with open(str(filepath), "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def save_json(self, name, data):
        """Save data to a JSON file by managed name or relative path."""
        filepath = self.get_file(name)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(str(filepath), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            logger.error("Failed to save %s: %s" % (name, str(e)))
            return False

    def backup(self, name=None):
        """
        Create a backup of a specific file or entire app data.
        Returns the backup path.
        """
        backup_dir = self.get_dir("backups")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if name:
            src = self.get_file(name)
            if src.exists():
                dest = backup_dir / ("%s_%s%s" % (src.stem, timestamp, src.suffix))
                shutil.copy2(str(src), str(dest))
                logger.info("Backed up %s to %s" % (name, dest))
                return dest
        else:
            dest = backup_dir / ("full_backup_%s" % timestamp)
            ignore = shutil.ignore_patterns("backups", "temp", "cache", "logs")
            shutil.copytree(str(self.root), str(dest), ignore=ignore)
            logger.info("Full backup created at %s" % dest)
            return dest
        return None

    def clean_temp(self):
        """Remove all temporary files."""
        temp_dir = self.get_dir("temp")
        count = 0
        for item in temp_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    count += 1
                elif item.is_dir():
                    shutil.rmtree(str(item))
                    count += 1
            except OSError:
                pass
        logger.info("Cleaned %d temp items" % count)
        return count

    def clean_old_logs(self, max_days=30):
        """Remove log files older than max_days."""
        log_dir = self.get_dir("logs")
        now = time.time()
        cutoff = now - (max_days * 86400)
        count = 0
        for log_file in log_dir.glob("*.log"):
            try:
                if log_file.stat().st_mtime < cutoff:
                    log_file.unlink()
                    count += 1
            except OSError:
                pass
        logger.info("Cleaned %d old log files" % count)
        return count

    def clean_old_backups(self, max_count=10):
        """Keep only the most recent max_count backups."""
        backup_dir = self.get_dir("backups")
        items = sorted(backup_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        removed = 0
        for item in items[max_count:]:
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(str(item))
                removed += 1
            except OSError:
                pass
        logger.info("Cleaned %d old backups" % removed)
        return removed

    def get_size(self):
        """Get total size of app data directory in bytes."""
        total = 0
        for dirpath, dirnames, filenames in os.walk(str(self.root)):
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except OSError:
                    pass
        return total

    def get_size_formatted(self):
        """Get human readable size of app data."""
        size = self.get_size()
        for unit in ("B", "KB", "MB", "GB"):
            if abs(size) < 1024.0:
                return "%.1f %s" % (size, unit)
            size /= 1024.0
        return "%.1f TB" % size

    def reset(self):
        """Reset all app data (keeps backups)."""
        logger.warning("Resetting all app data!")
        self.backup()
        for name, subpath in DIRECTORIES.items():
            if name in ("backups", "root"):
                continue
            directory = self.root / subpath if subpath else self.root
            if directory.exists() and directory != self.root:
                shutil.rmtree(str(directory), ignore_errors=True)
        self._ensure_structure()
        self._write_app_state()
        logger.info("App data reset complete")

    def export_data(self, export_path):
        """Export all app data to a zip file."""
        export_path = Path(export_path)
        if export_path.suffix != ".zip":
            export_path = export_path.with_suffix(".zip")
        base_name = str(export_path.with_suffix(""))
        shutil.make_archive(base_name, "zip", str(self.root))
        logger.info("Exported app data to %s" % export_path)
        return export_path

    def import_data(self, import_path):
        """Import app data from a zip file."""
        import_path = Path(import_path)
        if not import_path.exists():
            logger.error("Import file not found: %s" % import_path)
            return False
        self.backup()
        try:
            shutil.unpack_archive(str(import_path), str(self.root))
            logger.info("Imported app data from %s" % import_path)
            return True
        except Exception as e:
            logger.error("Failed to import data: %s" % str(e))
            return False

    def validate(self):
        """
        Validate the app data directory structure.
        Returns dict with status of each component.
        """
        results = {}
        for name, subpath in DIRECTORIES.items():
            directory = self.root / subpath if subpath else self.root
            results["dir_%s" % name] = directory.exists() and directory.is_dir()

        for name, rel_path in MANAGED_FILES.items():
            filepath = self.root / rel_path
            if filepath.exists():
                try:
                    with open(str(filepath), "r", encoding="utf-8") as f:
                        json.load(f)
                    results["file_%s" % name] = True
                except (json.JSONDecodeError, OSError):
                    results["file_%s" % name] = False
            else:
                results["file_%s" % name] = None  # Not yet created

        results["all_ok"] = all(
            v is True or v is None for v in results.values()
        )
        return results

    def get_minecraft_dir(self):
        """Get the default Minecraft directory."""
        system = platform.system()
        if system == "Windows":
            return Path(os.getenv("APPDATA", str(Path.home()))) / ".minecraft"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / "minecraft"
        else:
            return Path.home() / ".minecraft"