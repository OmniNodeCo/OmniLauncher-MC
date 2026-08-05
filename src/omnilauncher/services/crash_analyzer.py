"""Crash analyzer with modern features - tries to explain what went wrong."""

from __future__ import annotations

import re
from typing import Dict, List


KNOWN_CRASHES = [
    {
        "pattern": r"OutOfMemoryError|Java heap space|GC overhead limit exceeded",
        "title": "Out of Memory",
        "description": "Minecraft ran out of memory. Increase RAM allocation in Java settings.",
        "fix": "Go to Settings > Java > Increase Max RAM to at least 4GB.",
        "severity": "error",
    },
    {
        "pattern": r"Invalid Java|Unsupported Java|java\.lang\.UnsupportedClassVersionError|Unsupported major.minor",
        "title": "Incompatible Java Version",
        "description": "The selected Java version is incompatible with this Minecraft version.",
        "fix": "Install Java 17+ for 1.18+, Java 21 for 1.20.5+, or enable Auto-detect Java.",
        "severity": "error",
    },
    {
        "pattern": r"Could not reserve enough space|Could not create the Java Virtual Machine",
        "title": "JVM Creation Failed",
        "description": "Too much RAM allocated or Java not found.",
        "fix": "Reduce RAM allocation or check Java path.",
        "severity": "error",
    },
    {
        "pattern": r"GLFW error|Pixel format not accelerated|OpenGL",
        "title": "Graphics / OpenGL Error",
        "description": "GPU driver or OpenGL issue.",
        "fix": "Update graphics drivers, try different GPU, or disable custom resolution.",
        "severity": "warn",
    },
    {
        "pattern": r"Failed to download|Unable to download|Download failed",
        "title": "Download Failed",
        "description": "Launcher failed to download Minecraft assets. Network issue.",
        "fix": "Check internet, disable proxy, or try offline mode.",
        "severity": "error",
    },
    {
        "pattern": r"mod.*failed|ModLoadingException|Caused by.*mod",
        "title": "Mod Loading Failed",
        "description": "A mod failed to load. Conflict or missing dependency.",
        "fix": "Remove recently added mods, check dependencies, or view mods folder.",
        "severity": "error",
    },
    {
        "pattern": r"Fractureiser|stage2|client\.jar.*malware|credential stealer",
        "title": "Potential Malware Detected",
        "description": "Possible Fractureiser malware in a mod. This steals credentials.",
        "fix": "Immediately remove suspicious mods, change passwords, and scan with antivirus.",
        "severity": "critical",
    },
    {
        "pattern": r"AccessDeniedException|Permission denied|Could not create directory",
        "title": "Permission Error",
        "description": "Launcher cannot write to Minecraft folder.",
        "fix": "Run launcher as admin, or change Minecraft directory to a writable location.",
        "severity": "error",
    },
]


def analyze_crash(log: str) -> List[Dict]:
    """Analyze log text and return list of findings."""
    findings: List[Dict] = []
    for crash in KNOWN_CRASHES:
        if re.search(crash["pattern"], log, re.IGNORECASE):
            findings.append(crash)

    # generic exit code analysis
    exit_match = re.search(r"Process exited with code (-?\d+)", log, re.IGNORECASE)
    if exit_match:
        code = int(exit_match.group(1))
        if code == 1:
            findings.append(
                {
                    "title": "Generic Crash (Exit Code 1)",
                    "description": "Minecraft crashed with exit code 1 - often Java version mismatch or mod issue.",
                    "fix": "Check Java version, RAM, and recent mod changes.",
                    "severity": "error",
                }
            )
        elif code == -805306344:
            findings.append(
                {
                    "title": "Exit Code -805306344 (Out of Memory)",
                    "description": "Memory issue, typical for modded Minecraft.",
                    "fix": "Increase RAM to 6-8GB for modded packs.",
                    "severity": "error",
                }
            )

    if not findings:
        # fallback: try to extract last exception
        exc_match = re.search(r"(?m)^.*Exception.*$", log)
        if exc_match:
            findings.append(
                {
                    "title": "Unhandled Exception",
                    "description": f"Found exception: {exc_match.group(0)[:120]}",
                    "fix": "Share log with support or try reinstall.",
                    "severity": "warn",
                }
            )

    return findings


def format_report(findings: List[Dict]) -> str:
    if not findings:
        return "No specific crash cause detected. Check full log for details."
    report = []
    for f in findings:
        report.append(f"[{f.get('severity','info').upper()}] {f['title']}\n  {f['description']}\n  Fix: {f['fix']}\n")
    return "\n".join(report)
