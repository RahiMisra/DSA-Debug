"""Test suite for Box-Style Array and String Visualization (T020)."""

import tkinter as tk
from src.ui.array_view import ArrayView
from src.visualization.array_state import (
    BOX_BORDER_COLORS,
    BOX_FILL_COLORS,
    ArrayViewState,
    ElementHighlight,
)


def test_box_view_state_supports_integers_and_characters() -> None:
    """Verify ArrayViewState accepts both numeric values and string characters."""
    num_state = ArrayViewState.from_array([10, -5, 42])
    assert num_state.get_values() == [10, -5, 42]
    assert num_state.elements[0].value == 10

    # String characters
    str_state = ArrayViewState.from_array(list("HELLO"))
    assert str_state.get_values() == ["H", "E", "L", "L", "O"]
    assert str_state.elements[0].value == "H"
    assert len(str_state.elements) == 5


def test_box_color_mappings() -> None:
    """Verify fill and border color definitions exist for all highlight states."""
    for hl in ElementHighlight:
        assert hl in BOX_FILL_COLORS
        assert hl in BOX_BORDER_COLORS
        assert BOX_FILL_COLORS[hl].startswith("#")
        assert BOX_BORDER_COLORS[hl].startswith("#")


def test_array_view_defaults_to_box_style(session_tk_root: tk.Tk) -> None:
    """Verify ArrayView initializes with 'box' view style by default."""
    view = ArrayView(master=session_tk_root)
    assert view.view_style == "box"
    view.destroy()


def test_array_view_switch_view_style(session_tk_root: tk.Tk) -> None:
    """Verify switching between 'box' and 'bar' view styles."""
    view = ArrayView(master=session_tk_root)
    view.set_array([1, 2, 3])

    # Switch to bar
    view.set_view_style("bar")
    assert view.view_style == "bar"

    # Switch back to box
    view.set_view_style("box")
    assert view.view_style == "box"

    view.destroy()


def test_box_rendering_creates_boxes_and_labels(session_tk_root: tk.Tk) -> None:
    """Verify box rendering generates canvas rectangles for boxes and text for values and indices."""
    view = ArrayView(master=session_tk_root, view_style="box")
    view.set_array([42, 99])

    # Canvas items should include rectangles and text items
    items = view.canvas.find_all()
    item_types = [view.canvas.type(item) for item in items]

    assert "rectangle" in item_types
    assert "text" in item_types

    # Find text items and verify values are rendered
    text_values = [view.canvas.itemcget(item, "text") for item in items if view.canvas.type(item) == "text"]
    assert "42" in text_values
    assert "99" in text_values
    # Indices 0 and 1
    assert "0" in text_values
    assert "1" in text_values

    view.destroy()


def test_box_rendering_string_characters(session_tk_root: tk.Tk) -> None:
    """Verify string character boxes render characters properly."""
    view = ArrayView(master=session_tk_root, view_style="box")
    view.set_array(list("cat"))

    items = view.canvas.find_all()
    text_values = [view.canvas.itemcget(item, "text") for item in items if view.canvas.type(item) == "text"]

    assert "c" in text_values
    assert "a" in text_values
    assert "t" in text_values

    view.destroy()


def test_box_operation_highlighting(session_tk_root: tk.Tk) -> None:
    """Verify highlighted boxes use appropriate highlight colors."""
    view = ArrayView(master=session_tk_root, view_style="box")
    highlights = {0: ElementHighlight.COMPARING, 1: ElementHighlight.SWAPPING}
    view.set_array([10, 20], highlights=highlights)

    # Check tags / items
    assert view.current_state.elements[0].highlight == ElementHighlight.COMPARING
    assert view.current_state.elements[1].highlight == ElementHighlight.SWAPPING

    view.destroy()


def test_box_rendering_empty_and_large_arrays(session_tk_root: tk.Tk) -> None:
    """Verify box view handles empty arrays and scales cleanly for larger arrays."""
    view = ArrayView(master=session_tk_root, view_style="box")

    # Empty array
    view.set_array([])
    items = view.canvas.find_all()
    assert len(items) > 0  # Shows empty message

    # Larger array (25 elements)
    view.set_array(list(range(25)))
    large_items = view.canvas.find_all()
    rect_count = sum(1 for item in large_items if view.canvas.type(item) == "rectangle")
    assert rect_count == 25

    view.destroy()
