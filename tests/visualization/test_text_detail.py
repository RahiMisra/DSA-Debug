"""Tests for truncated text and the click-to-expand detail popup (T043)."""

from __future__ import annotations

import tkinter as tk

from src.visualization.hash_canvas import AuxiliaryHashCanvas
from src.visualization.linked_list_canvas import LinkedListCanvas
from src.visualization.recursion_canvas import RecursionCanvas
from src.visualization.text_detail import (
    TextDetailController,
    format_value,
    truncate_text,
)


def _frame(function: str, args: dict) -> dict:
    return {
        "function": function,
        "depth": 0,
        "args": args,
        "line": 1,
        "returning": False,
        "return_value": None,
        "chosen": {},
    }


def test_truncate_text_returns_ellipsis_and_flag() -> None:
    """Verify short text is unchanged and long text is visibly truncated."""
    short, short_truncated = truncate_text("arr[0]", 20)
    assert short == "arr[0]"
    assert short_truncated is False

    long_text = "a" * 80
    display, truncated = truncate_text(long_text, 20)
    assert truncated is True
    assert len(display) == 20
    assert display.endswith("\u2026")


def test_format_value_preserves_nested_lists_and_dicts() -> None:
    """Verify nested state renders without flattening its structure."""
    value = {"chosen": [1, [2, 3]], "path": {"left": 1, "right": 2}}
    assert format_value(value) == (
        "{chosen: [1, [2, 3]], path: {left: 1, right: 2}}"
    )


def test_long_recursion_labels_and_returns_open_detail_popup(
    session_tk_root: tk.Tk,
) -> None:
    """Verify long call-stack labels and returned structures are expandable."""
    view = RecursionCanvas(session_tk_root)
    long_return = {"answer": list(range(60)), "path": {"left": "x" * 40}}
    view.render_state(
        {
            "frames": [
                _frame(
                    "compute_path",
                    {"grid": list(range(40)), "target": "value-" * 20},
                )
            ],
            "subarrays": [
                {
                    "label": "arr[:mid] with an extremely long descriptive label",
                    "items": list(range(50)),
                }
            ],
            "return_structure": long_return,
            "last_return": None,
        }
    )

    expandable = view.canvas.find_withtag("expandable")
    assert len(expandable) >= 3
    frame_label = view.canvas.find_withtag("recursion_frame_label")[0]
    assert view.canvas.itemcget(frame_label, "text").endswith("\u2026")

    view.details.open(format_value(long_return))
    assert view.details.popup is not None
    assert (
        view.details.popup.text_widget.get("1.0", "end-1c")
        == format_value(long_return)
    )

    view.details.popup.close_button.invoke()
    session_tk_root.update_idletasks()
    assert view.details.popup is None
    view.destroy()


def test_hash_keys_and_values_are_truncated_and_expandable(
    session_tk_root: tk.Tk,
) -> None:
    """Verify map keys/values and set members get detail affordances."""
    view = AuxiliaryHashCanvas(session_tk_root)
    long_key = "a_really_long_identifier_that_will_not_fit"
    long_value = "value-" * 20
    long_member = "member-" * 12
    view.render_state(
        {
            "maps": [{"name": "freq", "entries": [{"key": long_key, "value": long_value}]}],
            "sets": [{"name": "seen", "items": [long_member]}],
        }
    )

    assert len(view.canvas.find_withtag("expandable")) >= 3
    key_item = view.canvas.find_withtag("hash_map_key")[0]
    assert view.canvas.itemcget(key_item, "text").endswith("\u2026")

    view.details.open(long_key)
    assert view.details.popup is not None
    assert view.details.popup.text_widget.get("1.0", "end-1c") == long_key

    view.details.open(long_member)
    assert view.details.popup is not None
    assert view.details.popup.text_widget.get("1.0", "end-1c") == long_member

    view.details.close()
    assert view.details.popup is None
    view.destroy()


def test_long_linked_list_values_are_expandable(session_tk_root: tk.Tk) -> None:
    """Verify long node values are truncated with an expandable affordance."""
    view = LinkedListCanvas(session_tk_root)
    long_value = "node-value-" * 10
    view.render_state(
        {
            "nodes": [{"id": 1, "val": long_value, "next": None}],
            "pointers": {"head": 1},
            "has_cycle": False,
            "cycle_start": None,
        }
    )

    assert view.canvas.find_withtag("expandable")
    node_text = view.canvas.find_withtag("node_val")[0]
    assert view.canvas.itemcget(node_text, "text").endswith("\u2026")

    view.details.open(long_value)
    assert view.details.popup is not None
    assert (
        view.details.popup.text_widget.get("1.0", "end-1c")
        == long_value
    )
    view.details.close()
    view.destroy()


def test_detail_popup_escape_and_click_away_close_it(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the popup closes via Escape and by clicking elsewhere."""
    controller = TextDetailController(session_tk_root, title="Details")
    controller.open("some full value")
    assert controller.popup is not None

    popup = controller.popup
    popup.focus_force()
    popup.update()
    popup.event_generate("<Escape>")
    session_tk_root.update_idletasks()
    assert controller.popup is None

    controller.open("another value")
    assert controller.popup is not None
    session_tk_root.update()
    session_tk_root.event_generate("<Button-1>", x=2, y=2)
    session_tk_root.update_idletasks()
    assert controller.popup is None
