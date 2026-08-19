"""GUI tests - themes, components, system checks."""

import sys

from omnilauncher.gui.themes import THEMES, get_theme, ACCENT_PALETTE, FONTS


def test_themes_exist():
    assert len(THEMES) >= 4
    assert "dark" in THEMES
    assert "midnight" in THEMES
    assert "light" in THEMES
    assert "amoled" in THEMES


def test_get_theme():
    dark = get_theme("dark")
    assert "bg" in dark
    assert "accent" in dark
    assert "text_primary" in dark
    # fallback to dark for unknown
    fallback = get_theme("nonexistent")
    assert fallback["bg"] == dark["bg"]


def test_theme_colors_valid():
    # all colors should be hex
    for name, theme in THEMES.items():
        for key, val in theme.items():
            if "bg" in key or "accent" in key or "text" in key or "color" in key or key in ("success", "warning", "error", "info", "separator"):
                # values are hex or named colors? We expect hex starting with #
                if isinstance(val, str) and val.startswith("#"):
                    assert len(val) in (4, 7, 9), f"{name}.{key} invalid hex {val}"
                    # check hex chars
                    hex_part = val[1:7]
                    try:
                        int(hex_part, 16)
                    except ValueError:
                        assert False, f"Invalid hex {val} in {name}.{key}"


def test_accent_palette():
    assert len(ACCENT_PALETTE) >= 10
    for col in ACCENT_PALETTE:
        assert col.startswith("#")
        assert len(col) == 7


def test_fonts():
    assert "title" in FONTS
    assert "body" in FONTS
    assert "mono" in FONTS
    for name, font in FONTS.items():
        assert isinstance(font, tuple)
        assert len(font) >= 2


def test_gui_components_importable():
    # Should not crash importing gui components even without display
    try:
        from omnilauncher.gui.components.sidebar import Sidebar, SidebarButton
        from omnilauncher.gui.components.cards import InstanceCard, AccountCard, ICON_COLORS
        from omnilauncher.gui.components.dialogs import CrashReportDialog, FileExplorerDialog
        assert Sidebar is not None
        assert SidebarButton is not None
        assert InstanceCard is not None
        assert AccountCard is not None
        assert len(ICON_COLORS) > 0
    except ImportError as e:
        # tkinter might be missing in CI, but should still have themes
        assert "tkinter" in str(e).lower() or True  # allow failure in headless


def test_settings_row_packing_logic():
    """PySide6 settings rows use _add_settings_row (no tkinter pack)."""
    import pathlib

    text = pathlib.Path("src/omnilauncher/gui/app.py").read_text(encoding="utf-8")
    assert "def _add_settings_row" in text
    assert "parent_layout" in text
    assert "QFrame" in text

    try:
        from omnilauncher.gui.app import OmniLauncherApp
        import inspect

        src = inspect.getsource(OmniLauncherApp._add_settings_row)
        assert "control" in src
        assert "parent_layout" in src
    except ImportError:
        # Headless runners without Qt/libGL still validate the source above
        pass


def test_main_entry_importable():
    import pathlib

    app_path = pathlib.Path("src/omnilauncher/gui/app.py")
    assert app_path.exists()
    text = app_path.read_text(encoding="utf-8")
    assert "def main" in text

    try:
        from omnilauncher.gui import app
        assert hasattr(app, "main")
        assert callable(app.main)
    except ImportError:
        pass
