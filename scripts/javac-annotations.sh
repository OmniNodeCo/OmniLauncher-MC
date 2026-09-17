#!/usr/bin/env bash
# Converts javac diagnostics (file:line: error|warning: msg) into
# GitHub workflow annotations.
log="${1:?usage: javac-annotations.sh <javac.log>}"

grep -E '^[^ ].*\.java:[0-9]+: (error|warning): ' "$log" | while IFS= read -r l; do
    file=$(printf '%s' "$l" | sed -E 's/^([^:]+\.java):[0-9]+:.*/\1/')
    line=$(printf '%s' "$l" | sed -E 's/^[^:]+\.java:([0-9]+):.*/\1/')
    msg=$(printf '%s' "$l" | sed -E 's/^[^ ]+\.java:[0-9]+: (error|warning): //')
    sev=$(printf '%s' "$l" | grep -q ': error: ' && echo error || echo warning)
    if [ -n "${GITHUB_WORKSPACE:-}" ]; then
        file="${file#"$GITHUB_WORKSPACE"/}"
    fi
    msg=${msg//%/%25}
    msg=${msg//,/%2C}
    echo "::$sev file=$file,line=$line,severity=$sev::$msg"
done

errors=$(grep -cE ': error: ' "$log" 2>/dev/null || true)
warnings=$(grep -cE ': warning: ' "$log" 2>/dev/null || true)
echo "Static analysis: ${errors:-0} error(s), ${warnings:-0} warning(s)"
