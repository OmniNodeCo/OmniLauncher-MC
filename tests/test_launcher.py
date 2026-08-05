"""Tests for launcher service - core launch logic."""

import tempfile
from pathlib import Path

from omnilauncher.services.launcher import (
    get_minecraft_dir,
    _get_uuid_for_username,
    current_status,
    current_progress,
    current_max,
    console_lines,
)
from omnilauncher.config.settings import SettingsManager


def test_get_minecraft_dir():
    d = get_minecraft_dir()
    assert isinstance(d, str)
    assert len(d) > 0


def test_get_minecraft_dir_with_settings():
    with tempfile.TemporaryDirectory() as tmp:
        settings_path = Path(tmp) / "settings.json"
        sm = SettingsManager(settings_path)
        sm.set(tmp, "general", "minecraft_directory")
        d = get_minecraft_dir(sm)
        assert d == tmp


def test_uuid_generation():
    # Should generate consistent offline UUID for same username
    uuid1 = _get_uuid_for_username("Steve", None)
    uuid2 = _get_uuid_for_username("Steve", None)
    assert uuid1 == uuid2
    assert isinstance(uuid1, str)
    # different username should give different uuid
    uuid3 = _get_uuid_for_username("Alex", None)
    assert uuid1 != uuid3


def test_uuid_from_settings():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        # current account should have uuid
        sm.add_account("TestUser123", "steve")
        sm.select_account(1)
        uuid_val = _get_uuid_for_username("TestUser123", sm)
        # should return the stored uuid from accounts list
        lst = sm.get("accounts", "list")
        stored = next((a["uuid"] for a in lst if a["username"] == "TestUser123"), None)
        assert uuid_val == stored


def test_shared_state_initial():
    # initial state should be Ready
    assert isinstance(current_status, str)
    assert isinstance(current_progress, int)
    assert isinstance(current_max, int)
    assert isinstance(console_lines, list)


def test_launcher_callbacks():
    from omnilauncher.services import launcher as launcher_svc

    called = []

    def status_cb(s):
        called.append(("status", s))

    def progress_cb(p, m):
        called.append(("progress", p, m))

    def console_cb(line):
        called.append(("console", line))

    launcher_svc.add_status_listener(status_cb)
    launcher_svc.add_progress_listener(progress_cb)
    launcher_svc.add_console_listener(console_cb)

    # simulate internal calls
    launcher_svc._set_status("Testing")
    launcher_svc._set_progress(50)
    launcher_svc._set_max(100)
    launcher_svc._add_console("Test line\n")

    # callbacks should have been called
    assert any(c[0] == "status" and c[1] == "Testing" for c in called)
    assert any(c[0] == "progress" for c in called)
    assert any(c[0] == "console" for c in called)

    # cleanup - remove listeners to not affect other tests
    launcher_svc._status_callbacks.clear()
    launcher_svc._progress_callbacks.clear()
    launcher_svc._console_callbacks.clear()
    launcher_svc._set_status("Ready")
