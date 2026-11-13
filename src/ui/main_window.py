"""Main application window for Trace."""

import tkinter as tk
from typing import Optional


class MainWindow:
    """Root application window for Trace."""

    DEFAULT_TITLE = "Trace — Algorithm Execution Visualizer"
    DEFAULT_WIDTH = 1024
    DEFAULT_HEIGHT = 720
    MIN_WIDTH = 800
    MIN_HEIGHT = 600

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        if root is None:
            self.root = tk.Tk()
            self._owns_root = True
        else:
            self.root = root
            self._owns_root = False

        self._configure_window()

    def _configure_window(self) -> None:
        self.root.title(self.DEFAULT_TITLE)
        self.root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    @property
    def is_alive(self) -> bool:
        """Return True if the underlying window exists and has not been destroyed."""
        try:
            return bool(self.root and self.root.winfo_exists())
        except (tk.TclError, AttributeError):
            return False

    def close(self) -> None:
        """Close the application window cleanly."""
        if self.root:
            try:
                self.root.destroy()
            except tk.TclError:
                pass

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
