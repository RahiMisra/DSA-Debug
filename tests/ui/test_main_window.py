"""Tests for the initial MainWindow desktop shell."""

import tkinter as tk
from src.ui.main_window import MainWindow


def test_main_window_initialization_and_properties(session_tk_root: tk.Tk) -> None:
    """Verify window title, initial dimensions, resizability, and clean close."""
    window = MainWindow(root=session_tk_root)

    # Title check
    assert window.root.title() == MainWindow.DEFAULT_TITLE

    # Window geometry/minsize check
    min_w, min_h = window.root.minsize()
    assert min_w == MainWindow.MIN_WIDTH
    assert min_h == MainWindow.MIN_HEIGHT

    # Resizability check
    resizable_x, resizable_y = window.root.resizable()
    assert resizable_x is True or resizable_x == 1
    assert resizable_y is True or resizable_y == 1

    # Verify window is alive
    assert window.is_alive


def test_main_window_close_behavior() -> None:
    """Verify MainWindow close behavior on an isolated Toplevel/window."""
    root = tk.Toplevel()
    window = MainWindow(root=root)
    assert window.is_alive
    window.close()
    assert not window.is_alive
