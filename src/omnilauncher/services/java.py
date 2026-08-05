"""Java detection and management."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict


def find_java_executables() -> List[Dict[str, str]]:
    """Try to find java installations."""
    results: List[Dict[str, str]] = []

    # check PATH
    for cmd in ["java", "javaw"]:
        p = shutil.which(cmd)
        if p:
            real = str(Path(p).resolve())
            if not any(r["path"] == real for r in results):
                ver = _get_java_version(real)
                results.append({"path": real, "version": ver, "source": "PATH"})

    # common locations
    candidates = []
    sys_name = platform.system()
    if sys_name == "Windows":
        bases = [
            Path("C:/Program Files/Java"),
            Path("C:/Program Files (x86)/Java"),
            Path("C:/Program Files/Eclipse Adoptium"),
            Path("C:/Program Files/Microsoft/jdk"),
            Path(os.environ.get("JAVA_HOME", "")) if os.environ.get("JAVA_HOME") else None,
        ]
        for base in bases:
            if base and base.exists():
                for sub in base.iterdir():
                    for exe in [sub / "bin" / "java.exe", sub / "bin" / "javaw.exe"]:
                        if exe.exists():
                            candidates.append(exe)
    elif sys_name == "Darwin":
        bases = [
            Path("/Library/Java/JavaVirtualMachines"),
            Path("/opt/homebrew/opt/openjdk/bin"),
            Path("/usr/local/opt/openjdk/bin"),
        ]
        for base in bases:
            if base.exists():
                if base.is_file():
                    candidates.append(base)
                else:
                    for sub in base.iterdir():
                        exe = sub / "Contents" / "Home" / "bin" / "java"
                        if exe.exists():
                            candidates.append(exe)
    else:
        bases = [
            Path("/usr/lib/jvm"),
            Path("/usr/lib64/jvm"),
            Path("/opt/jvm"),
            Path("/opt/java"),
        ]
        for base in bases:
            if base.exists():
                for sub in base.iterdir():
                    for exe in [sub / "bin" / "java", sub / "jre" / "bin" / "java"]:
                        if exe.exists():
                            candidates.append(exe)

    for exe in candidates:
        s = str(exe.resolve())
        if not any(r["path"] == s for r in results):
            ver = _get_java_version(s)
            results.append({"path": s, "version": ver, "source": "filesystem"})

    # deduplicate and sort
    return sorted(results, key=lambda x: x["version"], reverse=True)


def _get_java_version(java_path: str) -> str:
    try:
        out = subprocess.run(
            [java_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        txt = out.stderr + out.stdout
        # parse version like '17.0.8' or '1.8.0_392'
        import re

        m = re.search(r'version "?([\d._]+)"?', txt)
        if m:
            return m.group(1)
        m2 = re.search(r'(\d+\.\d+\.\d+)', txt)
        if m2:
            return m2.group(1)
        return "unknown"
    except Exception:
        return "unknown"


def estimate_max_ram() -> int:
    """Estimate safe max RAM in MB based on system."""
    try:
        import psutil  # type: ignore

        total = psutil.virtual_memory().total // (1024 * 1024)
        # leave 2GB or 30%
        safe = max(1024, int(total * 0.6))
        return min(safe, total - 1024)
    except Exception:
        # fallback 4GB
        return 4096
