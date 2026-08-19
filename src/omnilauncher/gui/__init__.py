"""OmniLauncher-MC GUI package - PySide6."""

try:
    from omnilauncher.gui.app import main
except Exception as exc:
    _GUI_IMPORT_ERROR = exc

    def main():
        raise RuntimeError(f"GUI not available (PySide6 missing): {_GUI_IMPORT_ERROR}") from _GUI_IMPORT_ERROR

__all__ = ["main"]
