<div align="center">

# OmniLauncher-MC

**A modern, beautiful Minecraft launcher built with Python**

[![Build](https://github.com/OmniNodeCo/OmniLauncher-MC/actions/workflows/build.yml/badge.svg)](https://github.com/OmniNodeCo/OmniLauncher-MC/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/OmniNodeCo/OmniLauncher-MC?color=6C3BF5)](https://github.com/OmniNodeCo/OmniLauncher-MC/releases)
[![License](https://img.shields.io/github/license/OmniNodeCo/OmniLauncher-MC?color=3B82F6)](LICENSE)

*No Electron. No bloat. Just a fast, clean launcher.*

[Website](https://omninodeco.github.io/OmniLauncher-MC) | [Download](https://github.com/OmniNodeCo/OmniLauncher-MC/releases) | [Issues](https://github.com/OmniNodeCo/OmniLauncher-MC/issues)

</div>

---

## Features

- **Lightning Fast** - Python + CustomTkinter, launches instantly
- **Modern Dark UI** - Beautiful interface with gradients and clean design
- **Profile System** - Create and manage multiple game profiles
- **Version Manager** - Browse, install, manage all Minecraft versions
- **Auto Updates** - Background update checking with skip/download options
- **Full AppData** - Structured data directory with backup, export, validation
- **Configurable** - Java path, JVM args, RAM allocation
- **Cross Platform** - Windows, macOS, Linux
- **Tested** - Import tests, unit tests, GUI tests in CI

## Getting Started

### Download

| Platform | File |
|----------|------|
| Windows  | `OmniLauncher-MC.exe` |
| macOS    | `OmniLauncher-MC-macOS.zip` |
| Linux    | `OmniLauncher-MC-Linux.tar.gz` |

### From Source

```bash
git clone https://github.com/OmniNodeCo/OmniLauncher-MC.git
cd OmniLauncher-MC
pip install -r requirements.txt
python src/main.py
Run Tests
Bash

pip install pytest
cd src && python -m pytest ../tests/ -v
Build
Bash

pip install pyinstaller
python scripts/generate_icons.py
pyinstaller build.spec
Project Structure
text

OmniLauncher-MC/
├── .github/workflows/   # CI/CD with tests
├── assets/              # SVG icons
├── docs/                # Website
├── scripts/             # Icon generation
├── tests/               # All tests
│   ├── test_imports.py  # Import validation
│   ├── test_gui.py      # GUI widget tests
│   ├── test_settings.py # Settings tests
│   ├── test_profiles.py # Profile tests
│   ├── test_auth.py     # Auth tests
│   └── test_updater.py  # Update checker tests
├── src/
│   ├── main.py          # Entry point
│   ├── launcher.py      # Main UI
│   ├── appdata.py       # App data management
│   ├── auth.py          # Authentication
│   ├── downloader.py    # Version downloads
│   ├── profiles.py      # Profile system
│   ├── settings.py      # Settings
│   ├── updater.py       # Update checker
│   └── utils.py         # Utilities
├── requirements.txt
├── build.spec
└── setup.py
License
MIT License - see LICENSE

Disclaimer
Not affiliated with Mojang Studios or Microsoft.

<div align="center">Built by <a href="https://github.com/OmniNodeCo">OmniNodeCo</a></div> ```