# OmniLauncher-MC v0.2.0

A modern, open-source Minecraft launcher built with Python & PySide6.

![Dark Theme](https://img.shields.io/badge/theme-dark%20%7C%20midnight%20%7C%20amoled-%23e94560) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-0.2.0-brightgreen) ![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt)-green)

## ✨ What's new in 0.2.0

Complete GUI remake from tkinter to **PySide6 (Qt 6)** for a much smoother, native-feeling experience:

### GUI Framework
- **PySide6** replaces tkinter — native Qt widgets, better rendering, smoother animations
- **QSS Stylesheets** (Qt Style Sheets) for rich theming — similar to CSS
- **Signal/Slot architecture** for clean inter-component communication
- **QThread workers** for background tasks (version fetching, Java detection)
- **QStackedWidget** for page switching with zero flicker
- **QScrollArea** with native scroll bars

### UI / Layout (preserved from 0.2.0 + enhanced)
- **Sidebar navigation** (240px) with logo `O`, 11 sections with active indicator border
- **Themes**: Dark, Midnight, Light, AMOLED + accent color picker with 14 presets
- **Header** with refresh + open .minecraft
- **Footer** with status, progress bar, version label, big PLAY button
- **All 11 pages** fully preserved: Play, Instances, Accounts, Mods, Explorer, Servers, Friends, Skins, Settings, Console, About

### Pages (all preserved)
- **Play**: banner, selected instance card, version/account selectors, RAM slider, quick play, favorites, news
- **Instances**: search, sort, grid/list toggle, grouped InstanceCard widgets, context menu
- **Accounts**: add offline, AccountCard widgets, select/delete
- **Mods & Addons**: placeholder with 5 category cards
- **File Explorer**: bookmarks, file list, double-click navigation, up/refresh/open-in-OS
- **Server Browser**: search, server cards with join
- **Friends List**: experimental toggle, friend cards
- **Skins**: preview, skin type selector
- **Settings**: 7 sub-pages (60+ options) — General, Java, Game, Appearance, Network, Launcher, Advanced
- **Console**: real-time log, search, filters, crash analyzer, export/copy
- **About**: changelog, license, system info

### Technical
- Removed tkinter dependency entirely
- PySide6 >= 6.6 required
- All backend services unchanged (settings, accounts, instances, java, versions, launcher, file_explorer, crash_analyzer)
- Version stays at 0.2.0

## 📦 Installation

```bash
pip install -e .
# or
uv sync
python main.py
```

Requires `minecraft-launcher-lib` and `PySide6>=6.6`.

## 🚀 Usage

1. Add offline account (3-16 chars)
2. Create/select instance, pick version (enable snapshots in General if needed)
3. Adjust RAM in Play or Java settings
4. Launch with PLAY — progress in footer, logs in Console
5. If crash, Console > Analyze Crash
6. Explore files via File Explorer bookmarks

Settings persist in:
- Windows: `%APPDATA%/OmniLauncher-MC/settings.json`
- Linux/macOS: `~/.config/omnilauncher/settings.json`
- Fallback: project root `settings.json`

## 🔒 Security
- Fractureiser malware pattern detection
- Offline UUID uses Java's OfflinePlayer:<username> MD5 v3

## 🗺️ Roadmap
- Modrinth & CurseForge API search + one-click install + dependency resolve
- Real server browser ping + favorites
- Friends list with Microsoft auth
- Drag-drop in file explorer, file watcher
- Animated gradient background
- Skin upload and cape support

## 📜 Credits
- Original OmniLauncher-MC authors
- Modern launcher UX inspirations (dark themes, sidebar, instance management)
- PySide6 / Qt for the GUI framework

## License
MIT - see LICENSE.txt
