#!/usr/bin/env bash
# Publishes docs/wiki/*.md to the GitHub wiki (OmniLauncher-MC.wiki).
#
# GitHub wikis cannot be created through the API — open the repo's Wiki tab
# once in a browser and create any page; afterwards this script keeps the
# wiki in sync with docs/wiki/.
set -euo pipefail
cd "$(dirname "$0")/.."

WIKI="https://github.com/OmniNodeCo/OmniLauncher-MC.wiki.git"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

git clone "$WIKI" "$TMP/wiki" 2>/dev/null || {
    echo "error: wiki repo not found. Open https://github.com/OmniNodeCo/OmniLauncher-MC/wiki" >&2
    echo "       in a browser and create the first page, then re-run this script." >&2
    exit 1
}
cp docs/wiki/*.md "$TMP/wiki/"
cd "$TMP/wiki"
git add -A
if git diff --cached --quiet; then
    echo "wiki already up to date"
    exit 0
fi
git -c user.name="OmniNodeCo" -c user.email="omninodeco@users.noreply.github.com" \
    commit -q -m "Sync wiki from docs/wiki ($(date -u +%Y-%m-%d))"
git push origin master
echo "wiki published"
