"""Entry point for OmniLauncher-MC."""

import sys
import os

if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

if bundle_dir not in sys.path:
    sys.path.insert(0, bundle_dir)


def main():
    """Launch OmniLauncher-MC."""
    from launcher import OmniLauncher

    app = OmniLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()