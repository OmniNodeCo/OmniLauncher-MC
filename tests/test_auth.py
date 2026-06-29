"""Tests for auth module."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_auth_manager_init():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)
        assert am.username == "Player"
        assert am.auth_type == "offline"
        assert len(am.uuid) > 0


def test_auth_login_offline():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)

        assert am.login_offline("Steve") is True
        assert am.username == "Steve"
        assert am.is_logged_in() is True


def test_auth_login_invalid():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)

        assert am.login_offline("") is False
        assert am.login_offline("ab") is False
        assert am.login_offline("a" * 17) is False
        assert am.login_offline("inv@lid!") is False


def test_auth_login_valid_underscore():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)

        assert am.login_offline("Player_One") is True
        assert am.username == "Player_One"


def test_auth_logout():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)

        am.login_offline("TestUser")
        am.logout()
        assert am.username == ""
        assert am.is_logged_in() is False


def test_auth_get_login_data():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        am = AuthManager(appdata_mgr=mgr)
        am.login_offline("DataTest")

        data = am.get_login_data()
        assert data["username"] == "DataTest"
        assert len(data["uuid"]) > 0
        assert data["token"] == "0"


def test_auth_uuid_consistent():
    from auth import AuthManager
    uuid1 = AuthManager._generate_offline_uuid("SamePlayer")
    uuid2 = AuthManager._generate_offline_uuid("SamePlayer")
    assert uuid1 == uuid2

    uuid3 = AuthManager._generate_offline_uuid("Different")
    assert uuid1 != uuid3


def test_auth_persistence():
    from auth import AuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)

        am1 = AuthManager(appdata_mgr=mgr)
        am1.login_offline("Persistent")

        am2 = AuthManager(appdata_mgr=mgr)
        assert am2.username == "Persistent"