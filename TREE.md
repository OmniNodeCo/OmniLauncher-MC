.
├── src
│   └── omnilauncher
│       ├── __init__.py
│       ├── config
│       │   ├── __init__.py
│       │   └── settings.py               # SettingsManager with 60+ options (General, Java, Game, Appearance, Network, Launcher, Advanced)
│       ├── gui
│       │   ├── __init__.py
│       │   ├── app.py                    # Main app v0.2.0 - dark UI with sidebar, play, instances, accounts, skins, mods, explorer, servers, friends, settings, console, about
│       │   ├── themes.py                 # Theme definitions (dark, midnight, light, amoled) + accent palette + fonts
│       │   └── components
│       │       ├── __init__.py
│       │       ├── sidebar.py            # Sidebar navigation with logo, nav buttons, user preview (11 items)
│       │       ├── cards.py              # InstanceCard, AccountCard, SettingsRow
│       │       └── dialogs.py            # CrashReportDialog, ConfirmDialog, FileExplorerDialog
│       └── services
│           ├── __init__.py
│           ├── error_handler.py
│           ├── launcher.py               # Launch service with callbacks, instance dir isolation, ram/java overrides, pre/post commands
│           ├── versions.py               # Version list caching, filtering (snapshots/beta/alpha)
│           ├── accounts.py               # Offline multi-account management
│           ├── instances.py              # Instance/profiles management with groups, favorites, playtime
│           ├── java.py                   # Java auto-detection (PATH + common locations)
│           ├── file_explorer.py          # Built-in file explorer with bookmarks (saves, mods, screenshots, logs...)
│           └── crash_analyzer.py         # Crash analyzer detecting OOM, java mismatch, GLFW, mod fails, malware
├── tests
│   └── __init__.py
├── Changelog.txt
├── LICENSE.txt
├── TERMS.txt
├── TREE.md
├── build.py
├── convert_assets.py
├── icon.svg
├── installer-banner.svg
├── installer-logo.svg
├── installer.iss
├── main.py
├── pyproject.toml
└── README.md

12 directories, 28+ files

Notes v0.2.0:
- UI modern layout: sidebar 240px dark #12141d, main #1a1d27, cards #242836, accent #e94560
- Settings extensive: 7 categories, 60+ toggles
- Features: Light/Dark + custom accent, transitions, animated bg placeholder,
  Modrinth/CurseForge ready, instance grid/list, account swapping offline working,
  real-time console with search/filter, built-in file explorer bookmarks,
  server browser + friends list experimental, malware scanner, parallel downloads, tray minimization concept
