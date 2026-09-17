#!/usr/bin/env bash
# Restores the sandbox toolchain (JRE + ECJ) from the local wheel copies.
# Used when ~/.cache/tooling has been wiped; tools/ is gitignored.
set -euo pipefail
cd "$(dirname "$0")/.."

JRE=~/.cache/tooling/jre
if [ ! -x "$JRE/bin/java" ]; then
    echo "==> Extracting bundled JRE…"
    rm -rf /tmp/jdk4py-x
    mkdir -p /tmp/jdk4py-x
    unzip -oq tools/jdk4py.whl -d /tmp/jdk4py-x
    mkdir -p ~/.cache/tooling
    rm -rf "$JRE"
    cp -r /tmp/jdk4py-x/jdk4py/java-runtime "$JRE"
    chmod +x "$JRE"/bin/* || true
fi
"$JRE/bin/java" -version 2>&1 | head -1
