"""Tests for version handling with caching and filtering."""

import tempfile
from pathlib import Path

from omnilauncher.services.versions import (
    get_version_list,
    get_release_versions,
    get_latest_version,
    is_mod_loader_version,
    refresh_cache,
)
from omnilauncher.config.settings import SettingsManager


def test_version_list_basic():
    versions = get_version_list()
    assert isinstance(versions, list)
    assert len(versions) > 0
    # each should have id and type
    for v in versions[:3]:
        assert "id" in v
        assert "type" in v


def test_version_filtering_snapshots():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        sm.set(False, "general", "show_snapshots")
        sm.set(False, "general", "show_beta")
        sm.set(False, "general", "show_alpha")
        # without snapshots, only release should be present (or mostly)
        versions = get_version_list(sm)
        # at least releases exist
        assert len(versions) > 0
        # enable snapshots
        sm.set(True, "general", "show_snapshots")
        versions_with_snap = get_version_list(sm)
        # should be >= without snapshots
        assert len(versions_with_snap) >= len(versions)


def test_release_versions():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        rel = get_release_versions(sm)
        assert isinstance(rel, list)
        assert len(rel) > 0
        assert all(isinstance(x, str) for x in rel)


def test_latest_version():
    # should not crash, return string
    v = get_latest_version()
    assert isinstance(v, str)
    assert len(v) > 0


def test_is_mod_loader():
    assert is_mod_loader_version("1.20.1-forge-47.1.0")
    assert is_mod_loader_version("1.20.1-fabric-0.92.0")
    assert is_mod_loader_version("fabric-loader-0.14.0-1.20.1")
    assert not is_mod_loader_version("1.21.1")
    assert not is_mod_loader_version("24w14a")


def test_refresh_cache_no_crash():
    # should not raise
    refresh_cache()
    versions = get_version_list()
    assert len(versions) > 0
