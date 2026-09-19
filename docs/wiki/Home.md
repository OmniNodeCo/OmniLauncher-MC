# OmniLauncher wiki

**OmniLauncher** is a from-scratch, dependency-free Minecraft launcher in pure
Java 17 + Swing with a modern UI modeled on the official Minecraft launcher —
no Python, no HTML/Electron. It integrates with Mojang's APIs for versions,
game files and news, signs in with Microsoft accounts, and packages as native
installers for Windows (custom Inno Setup EXE), macOS (dmg) and Linux (deb/rpm).

## Pages

- **[Changelog](Changelog)** — every release and what changed, with commit links
- **[Commits](Commits)** — the complete commit history

## Latest release: v0.3.5

| Platform | Download | Size |
|---|---|---|
| Windows (custom installer) | [OmniLauncher-0.3.5.exe](https://github.com/OmniNodeCo/OmniLauncher-MC/releases/download/v0.3.5/OmniLauncher-0.3.5.exe) | 31.9 MB |
| macOS | [OmniLauncher-0.3.5.dmg](https://github.com/OmniNodeCo/OmniLauncher-MC/releases/download/v0.3.5/OmniLauncher-0.3.5.dmg) | 52.2 MB |
| Linux (Debian/Ubuntu) | [omnilauncher_0.3.5-1_amd64.deb](https://github.com/OmniNodeCo/OmniLauncher-MC/releases/download/v0.3.5/omnilauncher_0.3.5-1_amd64.deb) | ~35.8 MB |
| Linux (Fedora/RHEL) | [omnilauncher-0.3.5-1.x86_64.rpm](https://github.com/OmniNodeCo/OmniLauncher-MC/releases/download/v0.3.5/omnilauncher-0.3.5-1.x86_64.rpm) | ~50.5 MB |

Installers **upgrade in place**: running a new installer removes the previous
OmniLauncher and reinstalls into the same folder; user data always lives outside
the app (`%APPDATA%\OmniLauncher` / `~/Library/Application Support/OmniLauncher`
/ `~/.config/omnilauncher`) and is never removed.

## Highlights

- Pure Java 17 + Swing, bundled JRE in every installer — nothing else to install
- Full Mojang integration: version manifest, version JSON, assets & libraries with SHA-1 verification, bundled Java runtimes (auto-download)
- Microsoft sign-in (device code flow), offline accounts
- Official Minecraft news feed with card/banner images, full blog-style article reader and Copy-text
- Automatic Java detection: PATH, JAVA_HOME, vendor directories and the bundled runtime — best major wins
- 181-test built-in selftest suite; CI (GitHub Actions) gates every push with lint + build + selftests and ships installers on version tags

## Building

```bash
./scripts/build.sh        # jar -> build/OmniLauncher.jar
./scripts/package.sh      # native installer for the current OS -> build/dist
java -cp build/classes:resources com.omninode.omnilauncher.Main --selftest
```

See the README for the full development guide.
