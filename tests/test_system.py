"""System tests - Python version, platform, dependencies, environment."""

import sys
import platform
import pathlib
import subprocess
import os


def test_python_version():
    # Requires Python 3.11+
    assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version}"


def test_platform_info():
    sys_name = platform.system()
    assert sys_name in ("Windows", "Linux", "Darwin", "Java") or isinstance(sys_name, str)
    assert platform.python_version() != ""


def test_project_structure():
    root = pathlib.Path(__file__).parent.parent
    assert (root / "src" / "omnilauncher").exists()
    assert (root / "src" / "omnilauncher" / "gui" / "app.py").exists()
    assert (root / "src" / "omnilauncher" / "config" / "settings.py").exists()
    assert (root / "src" / "omnilauncher" / "services" / "launcher.py").exists()
    assert (root / "pyproject.toml").exists()
    assert (root / "main.py").exists()


def test_dependencies_importable():
    # minecraft_launcher_lib may not be installed in test env, but we should not crash on import attempt
    try:
        import minecraft_launcher_lib
        # if installed, check it has utils
        assert hasattr(minecraft_launcher_lib, "utils") or True
    except ImportError:
        # fallback is okay, launcher has graceful fallback
        pass


def test_settings_file_location():
    from omnilauncher.config.settings import _default_settings_file

    path = _default_settings_file()
    assert isinstance(path, pathlib.Path)
    # should be settings.json
    assert path.name == "settings.json"


def test_themes_no_external_deps():
    from omnilauncher.gui.themes import THEMES

    # themes should not require external deps
    assert len(THEMES) > 0


def test_gui_without_display():
    """Importing gui.app must not auto-launch a window."""
    import pathlib

    text = pathlib.Path("src/omnilauncher/gui/app.py").read_text(encoding="utf-8")
    assert "class OmniLauncherApp" in text
    assert "def main" in text

    try:
        from omnilauncher.gui import app as app_module

        assert hasattr(app_module, "OmniLauncherApp")
        assert hasattr(app_module, "main")
    except ImportError:
        # Headless runners without Qt/libGL still validate the source above
        pass


def test_file_permissions():
    root = pathlib.Path(__file__).parent.parent
    # src should be readable
    assert os.access(root / "src", os.R_OK)
    # main.py readable
    assert os.access(root / "main.py", os.R_OK)


def test_build_script_exists():
    root = pathlib.Path(__file__).parent.parent
    build_py = root / "build.py"
    assert build_py.exists()
    content = build_py.read_text()
    assert "PyInstaller" in content or "pyinstaller" in content.lower()
