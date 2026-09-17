#!/usr/bin/env bash
# Builds OmniLauncher with a stock JDK (javac + jar). No Maven/Gradle needed.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=build
mkdir -p "$OUT/classes"

echo "==> Collecting sources…"
find src -name '*.java' > "$OUT/sources.txt"
echo "    $(wc -l < "$OUT/sources.txt") files"

JAVA_BIN="${JAVA_BIN:-}"
if [ -z "$JAVA_BIN" ]; then
    if command -v java >/dev/null 2>&1; then JAVA_BIN="java"
    elif [ -x "${JAVA_HOME:-/nonexistent}/bin/java" ]; then JAVA_BIN="$JAVA_HOME/bin/java"
    elif [ -x "$HOME/.cache/tooling/jre/bin/java" ]; then JAVA_BIN="$HOME/.cache/tooling/jre/bin/java"
    fi
fi

if command -v javac >/dev/null 2>&1; then
    echo "==> Compiling with javac…"
    javac --release 17 -encoding UTF-8 -nowarn -d "$OUT/classes" @"$OUT/sources.txt"
else
    echo "!! javac not found on PATH — falling back to ECJ if present…"
    ECJ="${ECJ:-tools/ecj.jar}"
    if [ ! -f "$ECJ" ]; then
        echo "error: no javac and no ECJ at $ECJ" >&2
        exit 1
    fi
    "$JAVA_BIN" -jar "$ECJ" -source 17 -target 17 -nowarn -proc:none -d "$OUT/classes" @"$OUT/sources.txt"
fi

echo "==> Packaging $OUT/OmniLauncher.jar…"
if command -v jar >/dev/null 2>&1; then
    jar --create --file "$OUT/OmniLauncher.jar" \
        --main-class com.omninode.omnilauncher.Main \
        -C "$OUT/classes" . -C resources .
else
    echo "!! jar tool not found — creating a runnable zip (launch with: java -cp $OUT/OmniLauncher.jar com.omninode.omnilauncher.Main)"
    cp resources/fonts/*.ttf "$OUT/classes/fonts_backup/" 2>/dev/null || true
    (cd "$OUT/classes" && zip -qr ../OmniLauncher.jar .)
    (cd resources && zip -qr "../$OUT/OmniLauncher.jar" .)
fi

echo "==> Done: $OUT/OmniLauncher.jar"
echo "    run:  java -jar $OUT/OmniLauncher.jar"
echo "    test: java -jar $OUT/OmniLauncher.jar --selftest"
