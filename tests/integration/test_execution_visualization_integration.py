"""Integration tests connecting editor, execution engine, history, and visualization (T016)."""

import tkinter as tk
from src.ui.main_window import MainWindow


def test_integration_run_and_step_synchronization(session_tk_root: tk.Tk) -> None:
    """Verify executing code, stepping forward/backward, and synchronization across UI components."""
    window = MainWindow(root=session_tk_root)

    # Set code and array
    code = """def simple_swap(arr):
    if arr[0] > arr[1]:
        arr[0], arr[1] = arr[1], arr[0]
"""
    window.editor.set_code(code)
    window.input_panel.set_array_text("50, 10")

    # Run algorithm
    window.handle_run()

    assert window.history is not None
    assert len(window.history) > 0
    assert window.current_step_index == -1

    # Verify initial array in ArrayView
    assert window.array_view.current_state.get_values() == [50, 10]

    # Step forward through all events
    total_steps = len(window.history)
    for _ in range(total_steps):
        window.step_forward()
        # Verify editor line is highlighted
        assert window.editor.current_highlighted_line is not None
        # Verify ArrayView has values
        assert len(window.array_view.current_state.get_values()) == 2

    # At the end, array should be sorted
    assert window.array_view.current_state.get_values() == [10, 50]
    assert window.current_step_index == total_steps - 1

    # Step backward
    window.step_backward()
    assert window.current_step_index == total_steps - 2

    # Reset
    window.reset_execution()
    assert window.current_step_index == -1
    assert window.array_view.current_state.get_values() == [50, 10]
    assert window.editor.current_highlighted_line is None


def test_integration_error_handling_in_ui(session_tk_root: tk.Tk) -> None:
    """Verify syntax or execution errors display an error message and highlight error line."""
    window = MainWindow(root=session_tk_root)
    broken_code = "def broken(arr):\n    x = 1 / 0\n"
    window.editor.set_code(broken_code)
    window.input_panel.set_array_text("1, 2")

    window.handle_run()

    # Verify error banner displayed
    assert "ZeroDivisionError" in window.error_banner["text"]
    # Verify error line highlighted
    assert window.editor.current_highlighted_line == 2
