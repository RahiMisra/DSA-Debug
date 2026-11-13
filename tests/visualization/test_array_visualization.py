"""Tests for array visualization model and view component (T012)."""

import tkinter as tk
from src.ui.array_view import ArrayView
from src.visualization.array_state import ArrayViewState, ElementHighlight


def test_array_view_state_creation_and_values() -> None:
    """Verify ArrayViewState reflects elements and values."""
    state = ArrayViewState.from_array([10, -5, 20])
    assert len(state.elements) == 3
    assert state.get_values() == [10, -5, 20]
    assert state.elements[0].index == 0
    assert state.elements[1].index == 1
    assert state.elements[2].index == 2
    assert state.elements[0].highlight == ElementHighlight.DEFAULT


def test_array_view_state_empty_and_single() -> None:
    """Verify ArrayViewState handles empty and single-element arrays."""
    empty_state = ArrayViewState.from_array([])
    assert len(empty_state.elements) == 0
    assert empty_state.get_values() == []

    single_state = ArrayViewState.from_array([99])
    assert len(single_state.elements) == 1
    assert single_state.elements[0].value == 99


def test_array_view_canvas_rendering(session_tk_root: tk.Tk) -> None:
    """Verify ArrayView canvas creates visual elements without error."""
    view = ArrayView(master=session_tk_root)
    view.set_array([30, 10, 50, 20])

    # Verify bar items created on canvas
    items = view.canvas.find_all()
    assert len(items) > 0

    # Update with empty array
    view.set_array([])
    empty_items = view.canvas.find_all()
    assert len(empty_items) > 0  # Contains "(Empty array)" text

    # Update with single negative element
    view.set_array([-10])
    single_items = view.canvas.find_all()
    assert len(single_items) > 0

    view.destroy()
