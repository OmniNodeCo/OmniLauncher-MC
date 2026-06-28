"""Entry point for OmniLauncher-MC."""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Launch OmniLauncher-MC."""
    from launcher import OmniLauncher

    app = OmniLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()