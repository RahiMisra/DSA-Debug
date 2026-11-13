"""Tests for CodeEditor component (T014)."""

import tkinter as tk
from src.ui.code_editor import CodeEditor


def test_code_editor_get_and_set_code(session_tk_root: tk.Tk) -> None:
    """Verify entering, modifying, and getting code."""
    editor = CodeEditor(master=session_tk_root)
    custom_code = "def test_sort(arr):\n    arr.sort()\n"
    editor.set_code(custom_code)

    assert editor.get_code().strip() == custom_code.strip()
    editor.destroy()


def test_code_editor_line_highlighting(session_tk_root: tk.Tk) -> None:
    """Verify highlighting lines and clearing highlights."""
    editor = CodeEditor(master=session_tk_root)
    code = "line1 = 1\nline2 = 2\nline3 = 3\n"
    editor.set_code(code)

    # Highlight line 2
    editor.highlight_line(2)
    assert editor.current_highlighted_line == 2

    # Highlight line 3
    editor.highlight_line(3)
    assert editor.current_highlighted_line == 3

    # Clear highlight
    editor.clear_highlight()
    assert editor.current_highlighted_line is None

    # Handle invalid or out-of-bounds lines safely
    editor.highlight_line(999)
    assert editor.current_highlighted_line is None

    editor.highlight_line(0)
    assert editor.current_highlighted_line is None

    editor.destroy()
