"""Tests for crash analyzer."""

from omnilauncher.services.crash_analyzer import analyze_crash, format_report


def test_analyze_oom():
    log = "Exception: java.lang.OutOfMemoryError: Java heap space at net.minecraft"
    findings = analyze_crash(log)
    assert len(findings) >= 1
    assert any("Out of Memory" in f["title"] for f in findings)


def test_analyze_java_mismatch():
    log = "java.lang.UnsupportedClassVersionError: Unsupported major.minor version 65.0"
    findings = analyze_crash(log)
    assert any("Java" in f["title"] for f in findings)


def test_analyze_glfw():
    log = "GLFW error 65542: WGL: The driver does not appear to support OpenGL"
    findings = analyze_crash(log)
    assert any("OpenGL" in f["title"] or "Graphics" in f["title"] for f in findings)


def test_analyze_mod_fail():
    log = "ModLoadingException: Mod file testmod failed to load"
    findings = analyze_crash(log)
    assert any("Mod" in f["title"] for f in findings)


def test_analyze_malware():
    log = "Detected Fractureiser stage2 client.jar malware credential stealer"
    findings = analyze_crash(log)
    assert any("Malware" in f["title"] for f in findings)
    assert findings[0]["severity"] == "critical"


def test_analyze_exit_code_1():
    log = "Process exited with code 1\nSome stacktrace"
    findings = analyze_crash(log)
    # should detect generic crash
    assert any("Exit Code 1" in f["title"] or "Generic" in f["title"] for f in findings)


def test_analyze_no_crash():
    log = "Everything is fine, no errors here, just info logs"
    findings = analyze_crash(log)
    # may be empty
    assert isinstance(findings, list)


def test_format_report():
    findings = [
        {"title": "Out of Memory", "description": "Ran out of memory", "fix": "Increase RAM", "severity": "error"}
    ]
    report = format_report(findings)
    assert "Out of Memory" in report
    assert "Increase RAM" in report


def test_format_empty():
    report = format_report([])
    assert isinstance(report, str)
    assert len(report) > 0
