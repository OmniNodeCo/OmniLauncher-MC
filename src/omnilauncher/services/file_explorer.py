"""Built-in file explorer with modern features - bookmarks for quick access."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Dict
from omnilauncher.config.settings import SettingsManager


BOOKMARKS = [
    {"name": "Saves", "path": "saves", "icon": "🌍"},
    {"name": "Resource Packs", "path": "resourcepacks", "icon": "🎨"},
    {"name": "Mods", "path": "mods", "icon": "⬢"},
    {"name": "Screenshots", "path": "screenshots", "icon": "📸"},
    {"name": "Logs", "path": "logs", "icon": "📝"},
    {"name": "Config", "path": "config", "icon": "⚙"},
    {"name": "Shaderpacks", "path": "shaderpacks", "icon": "💡"},
    {"name": "Crash Reports", "path": "crash-reports", "icon": "💥"},
]


def list_files(mc_dir: str, subpath: str = "") -> List[Dict]:
    base = Path(mc_dir) / subpath if subpath else Path(mc_dir)
    if not base.exists():
        return []
    items: List[Dict] = []
    try:
        for entry in sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            try:
                stat = entry.stat()
                items.append(
                    {
                        "name": entry.name,
                        "path": str(entry),
                        "relative": str(entry.relative_to(mc_dir)) if Path(mc_dir) in entry.parents or entry.parent == Path(mc_dir) else entry.name,
                        "is_dir": entry.is_dir(),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                    }
                )
            except Exception:
                continue
    except Exception:
        pass
    return items


def get_bookmarks(mc_dir: str) -> List[Dict]:
    result = []
    for bm in BOOKMARKS:
        full = Path(mc_dir) / bm["path"]
        result.append(
            {
                "name": bm["name"],
                "icon": bm["icon"],
                "path": str(full),
                "relative": bm["path"],
                "exists": full.exists(),
            }
        )
    return result


def delete_path(path: str) -> None:
    p = Path(path)
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink(missing_ok=True)


def rename_path(old: str, new_name: str) -> str:
    p = Path(old)
    new_p = p.parent / new_name
    p.rename(new_p)
    return str(new_p)


def create_folder(mc_dir: str, name: str) -> str:
    p = Path(mc_dir) / name
    p.mkdir(parents=True, exist_ok=True)
    return str(p)
