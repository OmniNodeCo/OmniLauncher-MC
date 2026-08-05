"""Tests for InstanceService."""

import tempfile
from pathlib import Path

from omnilauncher.config.settings import SettingsManager
from omnilauncher.services.instances import InstanceService, BLOCK_ICONS


def test_instance_service_list():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        lst = svc.list_instances()
        assert len(lst) >= 1


def test_instance_service_create():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        inst = svc.create("Test Instance", "1.21.1", "grass", "Custom")
        assert inst["name"] == "Test Instance"
        assert inst["version"] == "1.21.1"
        assert inst["icon"] == "grass"


def test_instance_service_delete():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        inst = svc.create("ToDelete", "1.20.1", "diamond", "Test")
        inst_id = inst["id"]
        svc.delete(inst_id)
        lst = svc.list_instances()
        assert all(i["id"] != inst_id for i in lst)


def test_instance_service_select():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        inst = svc.create("SelectMe", "1.19.4", "tnt", "Custom")
        svc.select(inst["id"])
        assert svc.get_selected_id() == inst["id"]
        assert svc.get_selected()["name"] == "SelectMe"


def test_instance_service_favorite():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        inst = svc.create("FavTest", "1.21.1", "grass", "Custom")
        initial_fav = inst.get("favorite", False)
        svc.toggle_favorite(inst["id"])
        lst = svc.list_instances()
        toggled = next(i for i in lst if i["id"] == inst["id"])
        assert toggled["favorite"] != initial_fav


def test_instance_service_groups():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = InstanceService(sm)
        svc.create("GroupA", "1.21.1", "grass", "GroupA")
        svc.create("GroupB", "1.21.1", "grass", "GroupB")
        groups = svc.get_groups()
        assert "GroupA" in groups
        assert "GroupB" in groups


def test_block_icons_valid():
    assert "grass" in BLOCK_ICONS
    assert "diamond" in BLOCK_ICONS
    assert len(BLOCK_ICONS) > 10
