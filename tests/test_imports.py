"""Test that all modules can be imported without errors."""

import sys
import os

# Add src/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_import_utils():
    import utils
    assert hasattr(utils, "get_app_dir")
    assert hasattr(utils, "get_minecraft_dir")
    assert hasattr(utils, "get_asset_path")
    assert hasattr(utils, "load_json")
    assert hasattr(utils, "save_json")
    assert hasattr(utils, "format_bytes")
    assert hasattr(utils, "get_java_executable")


def test_import_appdata():
    import appdata
    assert hasattr(appdata, "AppDataManager")
    assert hasattr(appdata, "APP_NAME")
    assert hasattr(appdata, "DIRECTORIES")
    assert hasattr(appdata, "MANAGED_FILES")


def test_import_settings():
    import settings
    assert hasattr(settings, "SettingsManager")
    assert hasattr(settings, "DEFAULT_SETTINGS")


def test_import_profiles():
    import profiles
    assert hasattr(profiles, "Profile")
    assert hasattr(profiles, "ProfileManager")


def test_import_auth():
    import auth
    assert hasattr(auth, "AuthManager")


def test_import_downloader():
    import downloader
    assert hasattr(downloader, "DownloadManager")


def test_import_updater():
    import updater
    assert hasattr(updater, "UpdateChecker")
    assert hasattr(updater, "UpdateInfo")
    assert hasattr(updater, "parse_version")
    assert hasattr(updater, "is_newer")
    assert hasattr(updater, "CURRENT_VERSION")


def test_import_launcher():
    import launcher
    assert hasattr(launcher, "OmniLauncher")
    assert hasattr(launcher, "COLORS")


def test_import_customtkinter():
    import customtkinter
    assert hasattr(customtkinter, "CTk")
    assert hasattr(customtkinter, "CTkFrame")
    assert hasattr(customtkinter, "CTkButton")
    assert hasattr(customtkinter, "CTkLabel")


def test_import_pil():
    from PIL import Image, ImageDraw, ImageTk
    assert Image is not None
    assert ImageDraw is not None
    assert ImageTk is not None


def test_import_requests():
    import requests
    assert hasattr(requests, "get")
    assert hasattr(requests, "post")


def test_import_minecraft_launcher_lib():
    import minecraft_launcher_lib
    assert hasattr(minecraft_launcher_lib, "utils")
    assert hasattr(minecraft_launcher_lib, "install")
    assert hasattr(minecraft_launcher_lib, "command")
    assert hasattr(minecraft_launcher_lib, "types")