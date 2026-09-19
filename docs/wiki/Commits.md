# Commit history

Every commit on `main`, newest first (86 total). Per-release summaries live in the [Changelog](Changelog).

| Date | Commit | Author | Message |
|---|---|---|---|
| 2026-09-19 | [`33692d5`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/33692d5) | OmniNodeCo | Java lookup: search PATH properly, bundled runtime, best-major wins (0.3.5) |
| 2026-09-19 | [`4fa584d`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/4fa584d) | OmniNodeCo | News reader: single hero image + readable/copyable article text (0.3.4) |
| 2026-09-19 | [`97ea375`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/97ea375) | OmniNodeCo | News reader: full blog-style article view (0.3.3) |
| 2026-09-19 | [`9b4f966`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/9b4f966) | OmniNodeCo | package.sh: Inno iss paths relative to the .iss (Inno resolves paths against the script dir, not cwd — cygpath fallback produced build/inno/build/icons/...) |
| 2026-09-19 | [`8d3769f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/8d3769f) | OmniNodeCo | Windows: custom setup EXE (Inno Setup) instead of MSI |
| 2026-09-18 | [`3794b00`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/3794b00) | OmniNodeCo | News images: map the real feed's playPageImage/newsPageImage fields |
| 2026-09-18 | [`30d4ed8`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/30d4ed8) | OmniNodeCo | Upgrade experience: dmg drag-to-Install layout + upgrade/uninstall docs |
| 2026-09-18 | [`99529b5`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/99529b5) | OmniNodeCo | Bump version to 0.3.1 (news API fix) |
| 2026-09-18 | [`e5b511e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/e5b511e) | OmniNodeCo | News: parse the real Minecraft news API payload |
| 2026-09-17 | [`ceed0f2`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ceed0f2) | OmniNodeCo | package.sh: bundle-legal app-version on macOS (0.3.0 -> 1.3.0, dmg filename stays 0.3.0); bump actions to v5 |
| 2026-09-17 | [`4d6b3a2`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/4d6b3a2) | OmniNodeCo | package.sh: macOS dmg via jpackage app-image + hdiutil (jpackage DMG bundler flaky on CI); broaden failure-report patterns |
| 2026-09-17 | [`ff1aa5e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ff1aa5e) | OmniNodeCo | package.sh: fix run_jpackage passing $1 twice via "$@" — jpackage got a stray bare type token (Invalid Option: [deb]) |
| 2026-09-17 | [`d63d16f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/d63d16f) | OmniNodeCo | CI: shell: bash for packaging steps (pwsh broke Windows); ERR trap in package.sh for exact failure location; richer failure report |
| 2026-09-17 | [`a57ef1e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/a57ef1e) | OmniNodeCo | CI: create build/ dir before tee in packaging step (root cause: tee failed on fresh runners) |
| 2026-09-17 | [`8261878`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/8261878) | OmniNodeCo | CI: fix annotation emission in packaging failure report |
| 2026-09-17 | [`c983f5b`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/c983f5b) | OmniNodeCo | package.sh: bash-3.2 safe empty-array expansion; CI packaging failure self-reports via annotations |
| 2026-09-17 | [`cd4fb97`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/cd4fb97) | OmniNodeCo | Release CI: install WiX for Windows jpackage, rpm tooling for Linux rpm |
| 2026-09-17 | [`e7b803b`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/e7b803b) | OmniNodeCo | Native packages (exe/dmg/deb/rpm), news retry UX, version 0.3.0 |
| 2026-09-17 | [`ab96b2f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ab96b2f) | OmniNodeCo | Add lint/test/release workflows that surface code errors as PR annotations |
| 2026-09-17 | [`96a5eca`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/96a5eca) | OmniNodeCo | Verify Microsoft auth chain end-to-end; desktop polish + offline status |
| 2026-09-17 | [`48dec28`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/48dec28) | OmniNodeCo | Add automatic Mojang Java runtime download + CI workflows |
| 2026-09-17 | [`f2785b8`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/f2785b8) | OmniNodeCo | Add end-to-end install pipeline test, accounts/version-picker polish |
| 2026-08-25 | [`7ee8009`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/7ee8009) | OmniNodeCo | Set Linux package maintainer email for electron-builder. |
| 2026-08-25 | [`ecabad8`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ecabad8) | OmniNode | Update build.yml |
| 2026-08-25 | [`acf15c6`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/acf15c6) | OmniNode | Update build.yml |
| 2026-08-25 | [`c955b1f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/c955b1f) | OmniNodeCo | Remove leftover Python launcher files. |
| 2026-08-25 | [`d765488`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/d765488) | OmniNodeCo | Replace the Python launcher with the OmniLauncher-MC Electron app. |
| 2026-08-20 | [`66d82fc`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/66d82fc) | OmniNodeCo | Fix servers page NameError that blocked startup |
| 2026-08-20 | [`41beca2`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/41beca2) | OmniNodeCo | Use textActivated for play combos so UI rebuild cannot recurse |
| 2026-08-20 | [`8683666`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/8683666) | OmniNodeCo | Stop play-page account combo from recursing until stack overflow |
| 2026-08-20 | [`c6b4f4f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/c6b4f4f) | OmniNodeCo | Load Qt plugins from _internal so qwindows.dll can find Qt6 DLLs |
| 2026-08-19 | [`5bc4c5c`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/5bc4c5c) | OmniNodeCo | Ship a folder build so the Windows exe can find Qt plugins |
| 2026-08-19 | [`1e21075`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/1e21075) | OmniNodeCo | Fix frozen Windows exe so PySide6 actually starts |
| 2026-08-19 | [`58bd2f8`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/58bd2f8) | OmniNodeCo | Fix PySide6 GUI tests so the tests/ suite passes in CI |
| 2026-08-19 | [`91b2ee3`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/91b2ee3) | OmniNode | Update test.yml |
| 2026-08-19 | [`2b513e7`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/2b513e7) | OmniNode | Update test.yml |
| 2026-08-11 | [`d22c2e6`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/d22c2e6) | OmniNode | Update test.yml |
| 2026-08-11 | [`e970239`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/e970239) | OmniNode | Update test.yml |
| 2026-08-11 | [`d3473b7`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/d3473b7) | OmniNode | Update test.yml |
| 2026-08-11 | [`7f80586`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/7f80586) | arena-ai-coding-agent[bot] | ci: add workflow_dispatch trigger |
| 2026-08-11 | [`942aec5`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/942aec5) | OmniNode | Create test.yml |
| 2026-08-10 | [`fa09609`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/fa09609) | OmniNodeCo | fix: use regex to parse window_geometry, handles corrupted values |
| 2026-08-06 | [`b8a5001`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/b8a5001) | OmniNodeCo | fix: handle corrupted window_geometry setting gracefully |
| 2026-08-06 | [`d0c6e7d`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/d0c6e7d) | OmniNodeCo | v0.2.0: Complete GUI remake - tkinter to PySide6 (Qt 6) |
| 2026-08-05 | [`19443c9`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/19443c9) | OmniNodeCo | fix: resolve TclError in settings UI and add comprehensive tests v0.2.0 |
| 2026-08-05 | [`efccdf7`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/efccdf7) | OmniNodeCo | feat: v0.2.0 major rebuild - modern dark UI with extensive settings |
| 2026-07-24 | [`7ed5516`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/7ed5516) | OmniNode | increased size of iss |
| 2026-07-24 | [`7a01069`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/7a01069) | OmniNode | edit installer.iss |
| 2026-07-23 | [`b961c3f`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/b961c3f) | OmniNode | updated iss |
| 2026-07-23 | [`7415727`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/7415727) | OmniNode | fixes |
| 2026-07-23 | [`32adc45`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/32adc45) | OmniNode | Update installer.iss |
| 2026-07-23 | [`03c0e1e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/03c0e1e) | OmniNode | Update installer.iss |
| 2026-07-23 | [`acfe061`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/acfe061) | OmniNode | updated scripts |
| 2026-07-23 | [`4774fba`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/4774fba) | OmniNode | fixed yml |
| 2026-07-23 | [`1e563fe`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/1e563fe) | OmniNode | added convert |
| 2026-07-23 | [`18ba1ed`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/18ba1ed) | OmniNode | Update release.yml |
| 2026-07-23 | [`f3c6bf3`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/f3c6bf3) | OmniNode | updated .gitignore |
| 2026-07-23 | [`ff204f4`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ff204f4) | github-actions | Update file tree |
| 2026-07-23 | [`481023a`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/481023a) | OmniNode | added logos |
| 2026-07-23 | [`ec26474`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ec26474) | github-actions | Update file tree |
| 2026-07-23 | [`9b1d8b6`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/9b1d8b6) | OmniNode | Update icon.svg |
| 2026-07-23 | [`3a020fb`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/3a020fb) | OmniNode | Create icon.svg |
| 2026-07-23 | [`2af8be3`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/2af8be3) | OmniNode | Create installer.iss |
| 2026-07-23 | [`0ae759e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/0ae759e) | OmniNode | Update release.yml |
| 2026-07-23 | [`b02800e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/b02800e) | OmniNode | updated to 0.1.1 |
| 2026-07-21 | [`459aa3e`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/459aa3e) | github-actions | Update file tree |
| 2026-07-21 | [`6d4f076`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/6d4f076) | OmniNode | Create tree.yml |
| 2026-07-21 | [`55464aa`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/55464aa) | voyager-2021 | refactor: update Python version to 3.14 and modify dependency installation in build and release workflows |
| 2026-07-21 | [`132bb4d`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/132bb4d) | voyager-2021 | Merge branch 'main' of https://github.com/OmniNodeCo/OmniLauncher-MC |
| 2026-07-21 | [`958f41b`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/958f41b) | voyager-2021 | refactor: enhance build script with directory cleanup and spec file handling |
| 2026-07-21 | [`44bbb65`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/44bbb65) | voyager-2021 | refactor: restructure project and update build process with PyInstaller |
| 2026-07-21 | [`829acad`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/829acad) | OmniNode | updated main.py |
| 2026-07-21 | [`3314722`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/3314722) | OmniNode | added error handler fixes |
| 2026-07-21 | [`0cd9dc1`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/0cd9dc1) | OmniNode | fixed error exec |
| 2026-07-21 | [`da47138`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/da47138) | OmniNode | fixed typo |
| 2026-07-21 | [`de7e1e5`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/de7e1e5) | OmniNode | fixed gitignore and update setup.py |
| 2026-07-21 | [`837d369`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/837d369) | OmniNode | added error handler test |
| 2026-07-19 | [`166b26d`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/166b26d) | OmniNode | applied change errors |
| 2026-07-11 | [`ad8ce23`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/ad8ce23) | OmniNodeCo | Fix |
| 2026-07-10 | [`a9ae825`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/a9ae825) | OmniNodeCo | Upates |
| 2026-07-09 | [`402d8d0`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/402d8d0) | OmniNodeCo | fix yml |
| 2026-07-09 | [`351acae`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/351acae) | OmniNodeCo | Initial |
| 2026-07-09 | [`2d2b1da`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/2d2b1da) | OmniNodeCo | Initial |
| 2026-07-09 | [`970a810`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/970a810) | OmniNodeCo | Initial |
| 2026-07-09 | [`b7c6d29`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/b7c6d29) | OmniNodeCo | Initial |
| 2026-07-07 | [`1e6003d`](https://github.com/OmniNodeCo/OmniLauncher-MC/commit/1e6003d) | OmniNode | Create requirements.txt |
