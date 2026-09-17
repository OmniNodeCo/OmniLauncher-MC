#!/usr/bin/env bash
# Static analysis pass: compiles with warnings enabled and converts every
# error/warning into a GitHub workflow annotation (inline on the PR).
# Exits non-zero when compile errors are found.
set -uo pipefail
cd "$(dirname "$0")/.."

OUT=build/lint
mkdir -p "$OUT/classes"
find src -name '*.java' > "$OUT/sources.txt"

ECJ_JAR="${ECJ_JAR:-tools/ecj.jar}"
if [ ! -f "$ECJ_JAR" ] && command -v curl >/dev/null 2>&1; then
    echo "==> Fetching the Eclipse compiler…"
    mkdir -p tools
    curl -fsSL "https://repo1.maven.org/maven2/org/eclipse/jdt/ecj/${ECJ_VERSION:-3.37.0}/ecj-${ECJ_VERSION:-3.37.0}.jar" \
        -o "$ECJ_JAR" || true
fi

# Locate a JVM: PATH → JAVA_HOME → sandbox bootstrap
JAVA_BIN="${JAVA_BIN:-}"
if [ -z "$JAVA_BIN" ]; then
    if command -v java >/dev/null 2>&1; then JAVA_BIN="java"
    elif [ -x "${JAVA_HOME:-/nonexistent}/bin/java" ]; then JAVA_BIN="$JAVA_HOME/bin/java"
    elif [ -x "$HOME/.cache/tooling/jre/bin/java" ]; then JAVA_BIN="$HOME/.cache/tooling/jre/bin/java"
    fi
fi

# Warnings that point at real defects (not style noise).
WARN="unusedImport,unusedLocal,unusedPrivate,unusedThrown,unusedArgument,unusedAllocation,nullDereference,fallthrough,syncOverride,typeHiding,raw"

rm -f "$OUT/ecj.log" "$OUT/javac.log"
if [ -f "$ECJ_JAR" ]; then
    echo "==> Linting with ECJ ($(basename "$ECJ_JAR"))…"
    "$JAVA_BIN" -jar "$ECJ_JAR" -source 17 -target 17 -proc:none \
        "-warn:$WARN" -d "$OUT/classes" @"$OUT/sources.txt" > "$OUT/ecj.log" 2>&1
    status=$?
    if [ -s "$OUT/ecj.log" ]; then
        cat "$OUT/ecj.log"
        if [ -n "${GITHUB_ACTIONS:-}" ]; then bash scripts/ecj-annotations.sh "$OUT/ecj.log"; fi
    fi
else
    echo "==> Linting with javac -Xlint:all…"
    javac --release 17 -Xlint:all -d "$OUT/classes" @"$OUT/sources.txt" > "$OUT/javac.log" 2>&1
    status=$?
    if [ -s "$OUT/javac.log" ]; then
        cat "$OUT/javac.log"
        if [ -n "${GITHUB_ACTIONS:-}" ]; then bash scripts/javac-annotations.sh "$OUT/javac.log"; fi
    fi
fi

if [ "$status" -eq 0 ]; then
    echo "✔ no compile errors"
else
    echo "✘ compile errors found (see annotations above)"
fi
exit "$status"
