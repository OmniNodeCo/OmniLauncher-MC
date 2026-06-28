"""Entry point for OmniLauncher-MC."""

import sys
import os

# Always add the directory containing main.py to sys.path
# This works both when run from source and when frozen by PyInstaller
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Launch OmniLauncher-MC."""
    from launcher import OmniLauncher
    app = OmniLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()