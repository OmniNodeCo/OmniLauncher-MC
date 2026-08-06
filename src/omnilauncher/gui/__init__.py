"""OmniLauncher-MC GUI package - PySide6."""

try:
    from omnilauncher.gui.app import main
except Exception as e:
    def main():
        raise RuntimeError(f"GUI not available (PySide6 missing): {e}")

__all__ = ["main"]
