"""Tests for updater module."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_parse_version_basic():
    from updater import parse_version
    assert parse_version("1.0.0") == (1, 0, 0)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("10.20.30") == (10, 20, 30)


def test_parse_version_with_v_prefix():
    from updater import parse_version
    assert parse_version("v1.0.0") == (1, 0, 0)
    assert parse_version("V2.3.4") == (2, 3, 4)


def test_parse_version_short():
    from updater import parse_version
    assert parse_version("1") == (1, 0, 0)
    assert parse_version("1.2") == (1, 2, 0)


def test_parse_version_prerelease():
    from updater import parse_version
    result = parse_version("1.2.3-beta1")
    assert result[0] == 1
    assert result[1] == 2
    assert result[2] == 3


def test_is_newer_true():
    from updater import is_newer
    assert is_newer("2.0.0", "1.0.0") is True
    assert is_newer("1.1.0", "1.0.0") is True
    assert is_newer("1.0.1", "1.0.0") is True
    assert is_newer("v1.1.0", "1.0.0") is True


def test_is_newer_false():
    from updater import is_newer
    assert is_newer("1.0.0", "1.0.0") is False
    assert is_newer("1.0.0", "2.0.0") is False
    assert is_newer("0.9.0", "1.0.0") is False


def test_update_info_to_dict():
    from updater import UpdateInfo
    info = UpdateInfo()
    info.available = True
    info.latest_version = "v2.0.0"
    d = info.to_dict()
    assert d["available"] is True
    assert d["latest_version"] == "v2.0.0"


def test_update_info_from_dict():
    from updater import UpdateInfo
    data = {
        "available": True,
        "latest_version": "v3.0.0",
        "release_name": "Big Update",
    }
    info = UpdateInfo.from_dict(data)
    assert info.available is True
    assert info.latest_version == "v3.0.0"
    assert info.release_name == "Big Update"


def test_update_checker_init():
    from updater import UpdateChecker
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        checker = UpdateChecker(appdata_mgr=mgr)
        assert checker.cache_file.parent.exists()


def test_update_checker_skip_version():
    from updater import UpdateChecker
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        checker = UpdateChecker(appdata_mgr=mgr)

        assert checker.is_version_skipped("v9.9.9") is False
        checker.skip_version("v9.9.9")
        assert checker.is_version_skipped("v9.9.9") is True
        assert checker.is_version_skipped("v1.0.0") is False


def test_update_checker_cache():
    from updater import UpdateChecker, UpdateInfo
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        checker = UpdateChecker(appdata_mgr=mgr)

        info = UpdateInfo()
        info.available = True
        info.latest_version = "v5.0.0"
        checker._save_cache(info)

        cached = checker._load_cache()
        assert cached is not None
        assert cached.available is True
        assert cached.latest_version == "v5.0.0"


def test_current_version_set():
    from updater import CURRENT_VERSION
    assert CURRENT_VERSION is not None
    assert len(CURRENT_VERSION) > 0
    parts = CURRENT_VERSION.split(".")
    assert len(parts) >= 2