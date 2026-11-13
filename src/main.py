"""Application entry point for Trace."""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ui.main_window import MainWindow


def main() -> int:
    """Launch the Trace application."""
    app = MainWindow()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
