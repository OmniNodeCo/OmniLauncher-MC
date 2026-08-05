"""OmniLauncher-MC GUI package."""

try:
    from omnilauncher.gui.app import main
except Exception as e:  # tkinter may be missing in headless CI
    def main():
        raise RuntimeError(f"GUI not available (tkinter missing): {e}")

__all__ = ["main"]
