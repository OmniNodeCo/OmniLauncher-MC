"""Tests for SettingsManager - extensive settings like launcher."""

import json
import tempfile
from pathlib import Path

from omnilauncher.config.settings import SettingsManager, DEFAULT_SETTINGS


def test_default_settings_structure():
    assert "general" in DEFAULT_SETTINGS
    assert "java" in DEFAULT_SETTINGS
    assert "game" in DEFAULT_SETTINGS
    assert "appearance" in DEFAULT_SETTINGS
    assert "network" in DEFAULT_SETTINGS
    assert "launcher" in DEFAULT_SETTINGS
    assert "advanced" in DEFAULT_SETTINGS
    assert "accounts" in DEFAULT_SETTINGS
    assert "instances" in DEFAULT_SETTINGS
    assert "meta" in DEFAULT_SETTINGS


def test_settings_manager_load_save():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        assert sm.get("general", "language") == "en_US"
        sm.set("fr_FR", "general", "language")
        sm.save()
        assert path.exists()
        sm2 = SettingsManager(path)
        assert sm2.get("general", "language") == "fr_FR"


def test_settings_manager_minecraft_dir():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        # should have default mc dir filled
        assert sm.minecraft_dir != ""
        assert isinstance(sm.minecraft_dir, str)


def test_settings_manager_accounts():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        initial = len(sm.get("accounts", "list"))
        acc = sm.add_account("TestUser", "alex")
        assert acc["username"] == "TestUser"
        assert len(sm.get("accounts", "list")) == initial + 1
        sm.select_account(0)
        assert sm.get("accounts", "selected_index") == 0


def test_settings_manager_instances():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        initial = len(sm.get("instances", "list"))
        inst = sm.add_instance("My Instance", "1.21.1", "grass", "Custom")
        assert inst["name"] == "My Instance"
        assert len(sm.get("instances", "list")) == initial + 1
        sm.set_selected_instance(inst["id"])
        assert sm.get("instances", "selected") == inst["id"]
        sm.remove_instance(inst["id"])
        assert len(sm.get("instances", "list")) == initial


def test_settings_get_set_nested():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        sm.set(True, "general", "show_snapshots")
        assert sm.get("general", "show_snapshots") is True
        sm.set(8192, "java", "max_ram_mb")
        assert sm.get("java", "max_ram_mb") == 8192
        assert sm.get("nonexistent", "key", default="fallback") == "fallback"


def test_settings_ram_gb_property():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        sm.set(4096, "java", "max_ram_mb")
        assert sm.ram_max_gb == 4.0
        sm.set(6144, "java", "max_ram_mb")
        assert sm.ram_max_gb == 6.0
