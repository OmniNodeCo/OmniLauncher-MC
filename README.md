# OmniLauncher-MC

A modern, open-source Minecraft launcher for Windows, macOS, and Linux.

![License](https://img.shields.io/badge/license-MIT-green)
![Electron](https://img.shields.io/badge/ui-Electron%20%2B%20Vue-42b883)
![Node](https://img.shields.io/badge/node-22%2B-brightgreen)

**Not an official Minecraft product. Not approved by or associated with Mojang or Microsoft.**

## Features

- Download and launch Minecraft, Forge, Fabric, Quilt, NeoForge, OptiFine, and JVM runtimes
- Fast concurrent downloads with connection reuse
- Multiple isolated instances (mods, versions, and launch settings)
- Resource linking so mods are not copied everywhere
- Built-in CurseForge and Modrinth browsing, install, and modpack import/export
- Microsoft, Mojang Yggdrasil, and third-party auth servers
- Peer-to-peer multiplayer over LAN-style connections
- Appearance, Java, and launch settings with a dark UI

## Install

Releases: [github.com/OmniNodeCo/OmniLauncher-MC/releases](https://github.com/OmniNodeCo/OmniLauncher-MC/releases)

Data is stored under:

- Windows: `%APPDATA%\OmniLauncher-MC`
- macOS / Linux: `~/Library/Application Support/OmniLauncher-MC` or `~/.config` / app data as provided by Electron

## Develop

Requires **Node.js 22.16+** and **pnpm 11**.

```bash
pnpm install
pnpm dev:renderer   # UI (Vite)
pnpm dev:main       # Electron main process
```

Build:

```bash
pnpm build:renderer
pnpm build
```

Tests:

```bash
pnpm test
pnpm check
```

Workspace layout:

| Path | Role |
| --- | --- |
| `omnilauncher-electron-app` | Electron shell, packaging |
| `omnilauncher-ui` | Vue UI |
| `omnilauncher-runtime` | Launcher services |
| `omnilauncher-runtime-api` | Shared API types |
| `packages/*` | Minecraft libraries |

## License

[MIT](LICENSE) — Copyright OmniNodeCo, including MIT-licensed work originally published by ci010.

## Credits

Core launch, install, and UI architecture is derived from the MIT-licensed
[X Minecraft Launcher](https://github.com/Voxelum/x-minecraft-launcher) by ci010 and contributors.
OmniLauncher-MC is a separate product with its own name, branding, and GitHub project.
