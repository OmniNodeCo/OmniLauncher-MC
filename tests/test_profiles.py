"""Tests for profiles module."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_profile_creation():
    from profiles import Profile
    p = Profile(name="Test", version="1.20.4")
    assert p.name == "Test"
    assert p.version == "1.20.4"
    assert p.loader == "vanilla"
    assert len(p.id) > 0


def test_profile_to_dict():
    from profiles import Profile
    p = Profile(name="Test", version="1.20.4", loader="fabric")
    d = p.to_dict()
    assert d["name"] == "Test"
    assert d["version"] == "1.20.4"
    assert d["loader"] == "fabric"
    assert "id" in d
    assert "created" in d


def test_profile_from_dict():
    from profiles import Profile
    data = {
        "id": "abc123",
        "name": "FromDict",
        "version": "1.19.2",
        "loader": "forge",
        "java_args": "-Xmx4G",
    }
    p = Profile.from_dict(data)
    assert p.id == "abc123"
    assert p.name == "FromDict"
    assert p.version == "1.19.2"
    assert p.loader == "forge"
    assert p.java_args == "-Xmx4G"


def test_profile_manager_init():
    from profiles import ProfileManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        pm = ProfileManager(appdata_mgr=mgr)
        assert len(pm.profiles) >= 1
        assert pm.get_active() is not None


def test_profile_manager_add_remove():
    from profiles import Profile, ProfileManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        pm = ProfileManager(appdata_mgr=mgr)

        initial_count = len(pm.profiles)
        new_profile = Profile(name="TestProfile", version="1.20.4")
        pm.add(new_profile)
        assert len(pm.profiles) == initial_count + 1

        pm.remove(new_profile.id)
        assert len(pm.profiles) == initial_count


def test_profile_manager_get_by_name():
    from profiles import Profile, ProfileManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        pm = ProfileManager(appdata_mgr=mgr)

        p = Profile(name="Unique123", version="1.20.4")
        pm.add(p)
        found = pm.get_by_name("Unique123")
        assert found is not None
        assert found.id == p.id

        not_found = pm.get_by_name("DoesNotExist999")
        assert not_found is None


def test_profile_manager_set_active():
    from profiles import Profile, ProfileManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)
        pm = ProfileManager(appdata_mgr=mgr)

        p = Profile(name="Active Test", version="1.20.4")
        pm.add(p)
        pm.set_active(p.id)
        assert pm.get_active().id == p.id


def test_profile_manager_persistence():
    from profiles import Profile, ProfileManager
    with tempfile.TemporaryDirectory() as tmpdir:
        from appdata import AppDataManager
        mgr = AppDataManager(custom_root=tmpdir)

        pm1 = ProfileManager(appdata_mgr=mgr)
        p = Profile(name="Persist", version="1.20.4")
        pm1.add(p)

        pm2 = ProfileManager(appdata_mgr=mgr)
        found = pm2.get_by_name("Persist")
        assert found is not None
        assert found.version == "1.20.4"