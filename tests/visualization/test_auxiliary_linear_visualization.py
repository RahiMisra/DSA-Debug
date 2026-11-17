"""Tests for auxiliary stack and queue canvas rendering (T031)."""

from __future__ import annotations

import tkinter as tk

from src.ui.main_window import MainWindow
from src.visualization.auxiliary_canvas import AuxiliaryLinearCanvas


STACK_CODE = """
def run_stack(nums):
    stack = []
    for n in nums:
        stack.append(n)
    order = []
    while stack:
        order.append(stack.pop())
    return order
"""


def _stack_state(items: list[int]) -> dict:
    return {
        "stacks": [
            {
                "name": "stack",
                "kind": "stack",
                "items": items,
                "size": len(items),
                "top": items[-1] if items else None,
            }
        ],
        "queues": [],
    }


def _queue_state(items: list[int]) -> dict:
    return {
        "stacks": [],
        "queues": [
            {
                "name": "queue",
                "kind": "queue",
                "items": items,
                "size": len(items),
                "front": items[0] if items else None,
                "rear": items[-1] if items else None,
            }
        ],
    }


def _text_positions(view: AuxiliaryLinearCanvas, tag: str) -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {}
    for item in view.canvas.find_withtag(tag):
        text = view.canvas.itemcget(item, "text")
        x, y = view.canvas.coords(item)
        positions[text] = (float(x), float(y))
    return positions


def test_auxiliary_canvas_renders_stack_top_at_top(
    session_tk_root: tk.Tk,
) -> None:
    """Verify stack items are drawn vertically with the top item above earlier items."""
    view = AuxiliaryLinearCanvas(session_tk_root)
    view.render_state(_stack_state([1, 2, 3]))

    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    assert "stack_container" in tags
    assert "stack_item" in tags

    positions = _text_positions(view, "stack_item_label")
    assert set(positions) == {"1", "2", "3"}
    assert positions["3"][1] < positions["2"][1] < positions["1"][1]
    assert positions["1"][0] == positions["2"][0] == positions["3"][0]

    view.destroy()


def test_auxiliary_canvas_renders_queue_front_to_rear(
    session_tk_root: tk.Tk,
) -> None:
    """Verify queue items are drawn horizontally from front to rear."""
    view = AuxiliaryLinearCanvas(session_tk_root)
    view.render_state(_queue_state(["a", "b", "c"]))

    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    assert "queue_container" in tags
    assert "queue_item" in tags

    positions = _text_positions(view, "queue_item_label")
    assert set(positions) == {"a", "b", "c"}
    assert positions["a"][0] < positions["b"][0] < positions["c"][0]
    assert positions["a"][1] == positions["b"][1] == positions["c"][1]

    labels = _text_positions(view, "queue_front_label")
    assert "front" in labels
    view.destroy()


def test_auxiliary_canvas_highlights_active_operation(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the active container and operation label are highlighted."""
    view = AuxiliaryLinearCanvas(session_tk_root)
    view.render_state(
        _stack_state([1, 2]),
        operation={
            "name": "stack",
            "kind": "stack",
            "action": "push",
            "value": 2,
        },
    )

    operation_items = view.canvas.find_withtag("aux_op")
    assert operation_items
    assert view.canvas.itemcget(operation_items[0], "text") == "push 2"

    container = view.canvas.find_withtag("stack_container")[0]
    assert (
        view.canvas.itemcget(container, "outline").lower()
        == AuxiliaryLinearCanvas.OP_COLOR.lower()
    )
    view.destroy()


def test_auxiliary_canvas_renders_empty_state(
    session_tk_root: tk.Tk,
) -> None:
    """Verify empty stacks and queues render placeholders without errors."""
    view = AuxiliaryLinearCanvas(session_tk_root)
    view.render_state({"stacks": [], "queues": []})

    assert view.canvas.find_withtag("aux_empty")
    view.destroy()


def test_main_window_shows_and_hides_auxiliary_panel(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the UI panel follows recorded stack state while stepping."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(STACK_CODE)
    window.input_panel.set_array_text("nums = [1, 2, 3]")

    window.handle_run()

    assert window.history is not None
    assert len(window.history) > 0
    assert window.auxiliary_view.winfo_manager() != "pack"

    panel_visible = False
    for _ in range(len(window.history)):
        window.step_forward()
        if window.auxiliary_view.winfo_manager() == "pack":
            panel_visible = True
            tags: set[str] = set()
            for item in window.auxiliary_view.canvas.find_all():
                tags.update(window.auxiliary_view.canvas.gettags(item))
            assert "stack_container" in tags

    assert panel_visible is True

    window.reset_execution()
    assert window.current_step_index == -1
    assert window.auxiliary_view.winfo_manager() != "pack"
