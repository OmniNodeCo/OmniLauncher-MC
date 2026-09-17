#!/usr/bin/env bash
# Converts ECJ diagnostic blocks into GitHub workflow annotations.
#   ----------                  <- optional separator
#   1. ERROR in path/File.java (at line 42)
#   <source line>
#   <caret line>
#   <message>                   <- may span lines until the next block/separator
log="${1:?usage: ecj-annotations.sh <ecj.log>}"

awk -v ws="${GITHUB_WORKSPACE:-}" '
function emit(sev, file, line, msg) {
    if (ws != "" && index(file, ws) == 1)
        file = substr(file, length(ws) + 2);
    gsub(/%/, "%25", msg);
    gsub(/\r/, "", msg);
    gsub(/,/, "%2C", msg);
    cmd = (sev == "ERROR") ? "::error" : "::warning";
    print cmd " file=" file ",line=" line ",title=" sev "::" msg;
}
/^[0-9]+\. (ERROR|WARNING) in / {
    rest = $0;
    sub(/^[0-9]+\. /, "", rest);
    sev = rest; sub(/ in .*/, "", sev);
    loc = rest; sub(/^[A-Z]+ in /, "", loc);
    file = loc; sub(/ \(at line [0-9]+\)$/, "", file);
    line = loc;
    if (match(loc, /\(at line [0-9]+\)/))
        line = substr(loc, RSTART + 9, RLENGTH - 10);
    getline src; getline caret; getline msg;
    emit(sev, file, line, msg);
}
' "$log"

errors=$(grep -c "ERROR in" "$log" 2>/dev/null || true)
warnings=$(grep -c "WARNING in" "$log" 2>/dev/null || true)
echo "Static analysis: ${errors:-0} error(s), ${warnings:-0} warning(s)"
