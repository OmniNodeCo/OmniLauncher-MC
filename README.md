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

- **Lightning Fast** - Built with Python and CustomTkinter, launches instantly
- **Modern Dark UI** - Beautiful interface with smooth gradients and clean design
- **Profile System** - Create and manage multiple game profiles
- **Version Manager** - Browse, install, and manage all Minecraft versions
- **Configurable** - Custom Java path, JVM arguments, RAM allocation
- **Cross Platform** - Windows, macOS, and Linux support
- **Lightweight** - ~50MB app size, minimal resource usage
- **Open Source** - MIT licensed, community driven

## Getting Started

### Download

Head to [Releases](https://github.com/OmniNodeCo/OmniLauncher-MC/releases) and download for your platform:

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
Build Executable
Bash

pip install pyinstaller
python scripts/generate_icons.py
pyinstaller build.spec
Tech Stack
Python 3.11+
CustomTkinter - Modern UI toolkit
minecraft-launcher-lib - Minecraft installation and launching
Pillow - Image processing
PyInstaller - Native executables
Project Structure
text

OmniLauncher-MC/
├── .github/workflows/   # CI/CD
├── assets/              # Icons and images
├── docs/                # Website
├── scripts/             # Build scripts
├── src/
│   ├── main.py          # Entry point
│   ├── launcher.py      # Main UI
│   ├── auth.py          # Authentication
│   ├── downloader.py    # Version management
│   ├── profiles.py      # Profile system
│   ├── settings.py      # Settings
│   └── utils.py         # Utilities
├── requirements.txt
├── build.spec
└── setup.py
Contributing
Fork the repository
Create your feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
License
This project is licensed under the MIT License - see the LICENSE file for details.

Disclaimer
OmniLauncher-MC is not affiliated with Mojang Studios, Microsoft, or the Minecraft brand.

<div align="center"> Built by <a href="https://github.com/OmniNodeCo">OmniNodeCo</a> </div> ```