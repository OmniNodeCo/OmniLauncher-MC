"""Tests for settings module."""

import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_default_settings():
    from settings import DEFAULT_SETTINGS
    assert "minecraft_dir" in DEFAULT_SETTINGS
    assert "java_path" in DEFAULT_SETTINGS
    assert "ram_max" in DEFAULT_SETTINGS
    assert "ram_min" in DEFAULT_SETTINGS
    assert "theme" in DEFAULT_SETTINGS
    assert "close_on_launch" in DEFAULT_SETTINGS
    assert "show_snapshots" in DEFAULT_SETTINGS
    assert "check_updates_on_start" in DEFAULT_SETTINGS


def test_settings_manager_init():
    from settings import SettingsManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        sm = SettingsManager(appdata_mgr=mgr)
        assert sm.get("ram_max") == 2048
        assert sm.get("theme") == "dark"
        assert sm.get("close_on_launch") is False


def test_settings_save_load():
    from settings import SettingsManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        sm = SettingsManager(appdata_mgr=mgr)
        sm.set("ram_max", 4096)
        sm.set("theme", "light")

        sm2 = SettingsManager(appdata_mgr=mgr)
        assert sm2.get("ram_max") == 4096
        assert sm2.get("theme") == "light"


def test_settings_reset():
    from settings import SettingsManager, DEFAULT_SETTINGS
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        sm = SettingsManager(appdata_mgr=mgr)
        sm.set("ram_max", 9999)
        sm.reset()
        assert sm.get("ram_max") == DEFAULT_SETTINGS["ram_max"]


def test_settings_get_default():
    from settings import SettingsManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        sm = SettingsManager(appdata_mgr=mgr)
        assert sm.get("nonexistent_key") is None
        assert sm.get("nonexistent_key", "fallback") == "fallback"