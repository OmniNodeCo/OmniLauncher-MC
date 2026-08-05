"""Tests for AccountService."""

import tempfile
from pathlib import Path

from omnilauncher.config.settings import SettingsManager
from omnilauncher.services.accounts import AccountService


def test_account_service_list():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = AccountService(sm)
        lst = svc.list_accounts()
        assert len(lst) >= 1
        assert "username" in lst[0]


def test_account_service_add_offline():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = AccountService(sm)
        acc = svc.add_offline("TestPlayer", "steve")
        assert acc["username"] == "TestPlayer"
        assert acc["skin_type"] == "steve"


def test_account_service_select():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = AccountService(sm)
        svc.add_offline("SecondAccount", "alex")
        svc.select(1)
        selected = svc.get_selected()
        assert selected["username"] == "SecondAccount"


def test_account_service_remove():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = AccountService(sm)
        acc = svc.add_offline("ToDelete", "steve")
        # find uuid
        uuid_to_del = acc["uuid"]
        svc.remove(uuid_to_del)
        lst = svc.list_accounts()
        assert all(a["uuid"] != uuid_to_del for a in lst)


def test_account_invalid_username():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.json"
        sm = SettingsManager(path)
        svc = AccountService(sm)
        # should raise for too short or empty?
        try:
            svc.add_offline("ab", "steve")
            # if not raising, at least it adds but we check len
            # The service currently allows 3-16, so "ab" should raise
            assert False, "Should have raised ValueError for short username"
        except ValueError:
            pass
