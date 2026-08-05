"""Tests for Java detection and management."""

from omnilauncher.services.java import find_java_executables, estimate_max_ram


def test_find_java_executables_no_crash():
    # Should not crash even if no java found
    result = find_java_executables()
    assert isinstance(result, list)
    # each entry should have path, version, source
    for entry in result:
        assert "path" in entry
        assert "version" in entry
        assert "source" in entry
        assert isinstance(entry["path"], str)


def test_estimate_max_ram():
    ram = estimate_max_ram()
    assert isinstance(ram, int)
    assert ram >= 512  # at least 512MB
    assert ram <= 32768 * 2  # reasonable upper bound


def test_java_version_parsing():
    # The helper is internal, but we test via find_java
    javas = find_java_executables()
    # If javas found, versions should be non-empty strings
    for j in javas:
        assert isinstance(j["version"], str)
        assert len(j["version"]) > 0
