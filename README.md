# OmniLauncher-MC v0.2.0

A modern, open-source Minecraft launcher built with Python.

![Dark Theme](https://img.shields.io/badge/theme-dark%20%7C%20midnight%20%7C%20amoled-%23e94560) ![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Version](https://img.shields.io/badge/version-0.2.0-brightgreen)

## ✨ What's new in 0.2.0

Completely rebuilt from the old Notebook UI to a full sidebar, dark-modern layout:

### UI / Layout
- **Sidebar navigation** (240px) with logo `O`, 11 sections: Play, Instances, Accounts, Mods, File Explorer, Servers, Friends [Exp], Skins, Settings, Console, About
- **Themes**: Dark, Midnight, Light, AMOLED + accent color picker with 14 presets (#e94560 brand)
- **Header** with refresh + open .minecraft
- **Footer** with status, progress bar, version label, big PLAY button
- **Scrollable frames** with mouse-wheel support everywhere

### Pages
- **Play**: banner, selected instance card (icon canvas, playtime, last played), version filter (snapshots/beta/alpha checkboxes), account selector, RAM quick slider (1024-12288 MB), quick play tiles, favorites list, news/changelog panel
- **Instances**: search, sort (last_played/name/version/playtime), grid/list toggle, groups, 3-column grid, context menu (play, edit, duplicate, favorite, open folder, delete), colored block icons
- **Accounts**: add offline accounts with steve/alex skin type, avatar canvas, selected indicator, remove
- **Mods & Addons**: placeholder for Modrinth & CurseForge integration (mods, resource packs, shaders, data packs, worlds)
- **File Explorer**: built-in explorer - bookmarks (saves, resourcepacks, mods, screenshots, logs, config, shaderpacks, crash-reports), up/refresh, double-click nav, open in OS
- **Server Browser [Experimental]**: server list with players/ping/motd, join sets auto-connect
- **Friends List [Experimental]**: toggle, online/offline, invite button
- **Skins**: canvas preview (steve/alex), skin type apply to current account, open skins folder
- **Settings**: 7 sub-pages with 60+ options
- **Console**: colored logs (error/warn/info), search highlight, filter level, auto-scroll, timestamp, clear/copy/export, crash analyzer, file explorer open
- **About**: logo, GitHub links, changelog, license/terms/tree viewers, system info

### Settings – Lots of options
- **General**: language (en_US/es_ES/fr_FR/de_DE/pt_BR/ru_RU), minecraft dir browse, show snapshots/beta/alpha/experimental, sort newest first, check updates, keep launcher open (hide/close/keep_open/minimize), concurrent downloads 1-8, minimize to tray
- **Java**: auto-detect toggle, java path browse, detected javas listbox (PATH + filesystem scan), min RAM 256-4096, max RAM 1024-16384, use custom JVM args, JVM args entry, GC logging
- **Game**: custom resolution toggle, width/height, fullscreen, use custom game args, game args entry, demo, disable multiplayer, logging, chat preview, auto-connect server
- **Appearance**: theme dropdown (dark/midnight/light/amoled), accent color entry + palette, background style (gradient/solid/image/animated), layout (modern/classic), animations, compact modes, show instance icons, font scale 0.8-1.4
- **Network**: offline mode, parallel downloads, proxy type (http/socks5/system), host/port/user/pass, timeout 5-120s
- **Launcher**: console visible, auto-scroll, word wrap, timestamp, keep logs, debug mode, file watcher, close after crash report, font size 8-18, filter level, max log days 1-30
- **Advanced**: enable advanced toggle, env vars, pre/post launch commands, wrapper (gamemoderun, prime-run), process monitor, kill on crash, crash analyzer, scan mods for malware, ignore java check + actions (open settings file, export settings, reset, delete ALL data)

### Services
- **SettingsManager**: JSON persistence in AppData/.config, deep merge defaults, account/instance CRUD
- **versions**: caching 30min, filtering (snapshots/beta/alpha)
- **java**: auto-detection across OS
- **launcher**: progress callbacks, instance isolated dirs, ram/java overrides, pre/post commands, offline UUID generation
- **file_explorer**: list_files, bookmarks, delete/rename/create
- **crash_analyzer**: detects OOM, Java mismatch, GLFW OpenGL, mod fail, Fractureiser malware, permission errors with fix suggestions

## 📦 Installation

```bash
pip install -e .
# or
uv sync
python main.py
```

Requires `minecraft-launcher-lib` and tkinter (`python3-tk` on Linux).

## 🚀 Usage

1. Add offline account (3-16 chars)
2. Create/select instance, pick version (enable snapshots in General if needed)
3. Adjust RAM in Play or Java settings
4. Launch with PLAY - progress in footer, logs in Console
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
- Tray minimization freeing RAM
- Animated gradient background
- Skin upload and cape support

## 📜 Credits
- Original OmniLauncher-MC authors
- Modern launcher UX inspirations (dark themes, sidebar, instance management)

## License
MIT - see LICENSE.txt
