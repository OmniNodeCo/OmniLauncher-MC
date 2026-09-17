#!/usr/bin/env bash
# Packages native installers with jpackage (bundled with JDK 17+).
#
# Usage:
#   ./scripts/package.sh                # best bundle for the current OS
#   ./scripts/package.sh app-image      # plain folder with a runnable app
#   ./scripts/package.sh exe|msi        # Windows (exe needs WiX, auto-falls back to msi)
#   ./scripts/package.sh dmg            # macOS
#   ./scripts/package.sh deb|rpm        # Linux
#
# Output lands in build/dist/.
set -euo pipefail
cd "$(dirname "$0")/.."

TYPE="${1:-auto}"

# ---- version from the single source of truth in the source tree
VERSION=$(sed -n 's/.*LAUNCHER_VERSION = "\([^"]*\)".*/\1/p' \
    src/com/omninode/omnilauncher/core/GameLauncher.java | head -1)
if [ -z "$VERSION" ]; then
    echo "error: could not determine LAUNCHER_VERSION from GameLauncher.java" >&2
    exit 1
fi
echo "==> OmniLauncher $VERSION"

# ---- locate jpackage (JDK 17+ ships it; the sandbox JRE does not)
JP="${JPACKAGE:-$(command -v jpackage || true)}"
if [ -z "$JP" ]; then
    for d in "${JAVA_HOME:-}" /usr/lib/jvm/*/ /Library/Java/JavaVirtualMachines/*/Contents/Home; do
        [ -x "${d}bin/jpackage" ] && JP="${d}bin/jpackage" && break
    done
fi
if [ -z "$JP" ]; then
    echo "error: jpackage not found. Install a full JDK 17+ (not a JRE)." >&2
    echo "       (macOS: use a non-JRE build; Windows: Temurin/Adoptium includes it)" >&2
    exit 1
fi

# ---- build the jar and the icons everything needs
./scripts/build.sh
java -jar build/OmniLauncher.jar --export-icon build/icons | sed 's/^/  /'

mkdir -p build/dist
rm -f build/dist/OmniLauncher-* 2>/dev/null || true

OS_NAME="$(uname -s)"
case "$OS_NAME" in
    MINGW*|MSYS*|CYGWIN*|Windows*) OS=windows ;;
    Darwin) OS=macos ;;
    *) OS=linux ;;
esac
if [ "$TYPE" = "auto" ]; then
    case "$OS" in
        windows) TYPE=exe ;;
        macos)   TYPE=dmg ;;
        *)       TYPE=deb ;;
    esac
fi

COMMON_ARGS=(
    --name OmniLauncher
    --app-version "$VERSION"
    --vendor OmniNodeCo
    --description "Native, dependency-free Minecraft launcher"
    --input build/jpackage-input
    --dest build/dist
)

# stage the jar exactly as jpackage expects (flat input dir)
mkdir -p build/jpackage-input
cp build/OmniLauncher.jar build/jpackage-input/

run_jpackage() {
    echo "==> jpackage --type $1"
    "$JP" --type "$1" "${COMMON_ARGS[@]}" \
        --main-jar OmniLauncher.jar \
        --main-class com.omninode.omnilauncher.Main \
        "$@"
}

case "$TYPE" in
    app-image)
        run_jpackage app-image
        ;;
    exe|msi)
        ICON_ARGS=()
        [ -f build/icons/OmniLauncher.ico ] && ICON_ARGS=(--icon build/icons/OmniLauncher.ico)
        if [ "$TYPE" = "exe" ]; then
            if ! run_jpackage exe --win-menu --win-shortcut --win-dir-chooser "${ICON_ARGS[@]}"; then
                echo "!! exe packaging failed (WiX missing?) — falling back to msi"
                run_jpackage msi --win-menu --win-shortcut --win-dir-chooser "${ICON_ARGS[@]}"
            fi
        else
            run_jpackage msi --win-menu --win-shortcut --win-dir-chooser "${ICON_ARGS[@]}"
        fi
        ;;
    dmg)
        ICON_ARGS=()
        [ -f build/icons/OmniLauncher.icns ] && ICON_ARGS=(--icon build/icons/OmniLauncher.icns)
        run_jpackage dmg --mac-package-name OmniLauncher \
            --mac-package-identifier com.omninode.omnilauncher "${ICON_ARGS[@]}"
        ;;
    deb|rpm)
        ICON_ARGS=()
        [ -f build/icons/icon-512.png ] && ICON_ARGS=(--icon build/icons/icon-512.png)
        run_jpackage "$TYPE" --linux-shortcut --linux-menu-group Game \
            --license-file LICENSE "${ICON_ARGS[@]}"
        ;;
    *)
        echo "error: unknown package type '$TYPE'" >&2
        exit 2
        ;;
esac

echo "==> Done — build/dist:"
ls -la build/dist
