"""Tests for the recursion call-stack and subwork panel (T035)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from src.execution.events import EventType
from src.ui.main_window import MainWindow
from src.visualization.recursion_canvas import RecursionCanvas


FACTORIAL_CODE = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

SUBWORK_CODE = """
def subwork(nums):
    mid = len(nums) // 2
    left = nums[:mid]
    right = nums[mid:]
    return len(left) + len(right)
"""


def _frame(
    function: str,
    depth: int,
    args: dict[str, Any],
    line: int = 1,
    returning: bool = False,
    return_value: Any = None,
) -> dict[str, Any]:
    return {
        "function": function,
        "depth": depth,
        "args": args,
        "line": line,
        "returning": returning,
        "return_value": return_value,
        "chosen": {},
    }


def _state(
    frames: list[dict[str, Any]],
    subarrays: list[dict[str, Any]] | None = None,
    return_structure: Any = None,
    last_return: dict[str, Any] | None = None,
) -> dict[str, Any]:
    active = frames[-1] if frames else None
    return {
        "frames": frames,
        "active_function": active["function"] if active else None,
        "active_depth": active["depth"] if active else None,
        "max_depth": max((frame["depth"] for frame in frames), default=None),
        "subarrays": subarrays or [],
        "return_structure": return_structure,
        "last_return": last_return,
    }


def _subarray(
    name: str,
    label: str,
    items: list[Any],
    source: str = "slice",
    depth: int = 1,
) -> dict[str, Any]:
    return {
        "name": name,
        "label": label,
        "items": items,
        "size": len(items),
        "start": None,
        "stop": None,
        "step": None,
        "source": source,
        "depth": depth,
        "line": 4,
    }


def _tags(view: RecursionCanvas) -> set[str]:
    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    return tags


def _texts(view: RecursionCanvas, tag: str) -> list[str]:
    return [
        view.canvas.itemcget(item, "text")
        for item in view.canvas.find_withtag(tag)
    ]


def _text_y(view: RecursionCanvas, tag: str, text: str) -> float:
    for item in view.canvas.find_withtag(tag):
        if view.canvas.itemcget(item, "text") == text:
            return float(view.canvas.coords(item)[1])
    raise AssertionError(f"text {text!r} not found under tag {tag!r}")


# ---------------------------------------------------------------------------
# 1. Call stack rendering
# ---------------------------------------------------------------------------


def test_recursion_canvas_renders_frames_deepest_first(
    session_tk_root: tk.Tk,
) -> None:
    """Verify frames show depth/arguments and stack upward toward the active call."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state(
            [
                _frame("merge_sort", 0, {"arr": [3, 1, 2]}),
                _frame("merge_sort", 1, {"arr": [3]}),
            ]
        )
    )

    tags = _tags(view)
    assert {"recursion_frame", "recursion_active_frame", "recursion_title"} <= tags
    assert _texts(view, "recursion_frame_label") == [
        "#1 merge_sort(arr=[3])",
        "#0 merge_sort(arr=[3, 1, 2])",
    ]
    assert _text_y(view, "recursion_frame_label", "#1 merge_sort(arr=[3])") < _text_y(
        view, "recursion_frame_label", "#0 merge_sort(arr=[3, 1, 2])"
    )

    active = view.canvas.find_withtag("recursion_active_frame")
    assert len(active) == 1
    assert (
        view.canvas.itemcget(active[0], "outline").lower()
        == RecursionCanvas.OP_COLOR.lower()
    )
    active_center = (
        view.canvas.coords(active[0])[1] + view.canvas.coords(active[0])[3]
    ) / 2.0
    assert (
        abs(
            _text_y(view, "recursion_frame_label", "#1 merge_sort(arr=[3])")
            - active_center
        )
        < 2.0
    )
    view.destroy()


def test_recursion_canvas_renders_frame_return_values(
    session_tk_root: tk.Tk,
) -> None:
    """Verify returning frames display their captured return value."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state(
            [
                _frame(
                    "factorial",
                    0,
                    {"n": 3},
                    returning=True,
                    return_value=6,
                )
            ]
        )
    )

    assert _texts(view, "recursion_frame_label") == ["#0 factorial(n=3)"]
    assert _texts(view, "recursion_frame_return") == ["→ 6"]
    view.destroy()


# ---------------------------------------------------------------------------
# 2. Sub-arrays and returned structure
# ---------------------------------------------------------------------------


def test_recursion_canvas_renders_intermediate_subarrays(
    session_tk_root: tk.Tk,
) -> None:
    """Verify sub-array labels and contents are rendered as rows."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state(
            [_frame("merge_sort", 1, {"arr": [3, 1, 2]})],
            subarrays=[
                _subarray("arr", "arr[:1]", [3]),
                _subarray("arr", "arr[1:]", [1, 2]),
            ],
        )
    )

    tags = _tags(view)
    assert {"recursion_subarray", "recursion_subarray_label"} <= tags
    assert _texts(view, "recursion_subarray_label") == ["arr[:1]", "arr[1:]"]
    assert _texts(view, "recursion_subarray_items") == ["[3]", "[1, 2]"]
    view.destroy()


def test_recursion_canvas_renders_returned_structure(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the dedicated return panel shows the final/chosen structure."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state(
            [_frame("sum_list", 0, {"nums": [1, 2, 3]})],
            return_structure=6,
        )
    )

    tags = _tags(view)
    assert {"recursion_return", "recursion_return_value"} <= tags
    assert _texts(view, "recursion_return_value") == ["6"]
    assert _texts(view, "recursion_return_label") == ["returned structure"]
    view.destroy()


def test_recursion_canvas_falls_back_to_last_return(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the return panel can render the most recent inner return."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state(
            [_frame("factorial", 0, {"n": 3})],
            last_return={"function": "factorial", "value": 2, "depth": 1},
        )
    )

    assert _texts(view, "recursion_return_value") == ["2"]
    view.destroy()


def test_recursion_canvas_renders_empty_state(
    session_tk_root: tk.Tk,
) -> None:
    """Verify an empty recursion snapshot renders a placeholder."""
    view = RecursionCanvas(session_tk_root)
    view.render_state(
        _state([], subarrays=[], return_structure=None)
    )

    assert view.canvas.find_withtag("recursion_empty")
    view.destroy()


# ---------------------------------------------------------------------------
# 3. Main window integration
# ---------------------------------------------------------------------------


def test_main_window_shows_recursion_panel_while_recursing(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the panel appears for nested frames and disappears on reset."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(FACTORIAL_CODE)
    window.input_panel.set_array_text("n = 3")

    window.handle_run()

    assert window.history is not None
    assert window.recursion_view.winfo_manager() != "pack"

    saw_active_frame = False
    for _ in range(len(window.history)):
        window.step_forward()
        if window.recursion_view.winfo_manager() == "pack":
            tags = _tags(window.recursion_view)
            if "recursion_active_frame" in tags:
                saw_active_frame = True
                event = window.history.get_step(window.current_step_index)
                state = event.metadata["recursion"]
                assert window.editor.current_highlighted_line == event.line_number
                assert state["active_function"] == "factorial"
                labels = _texts(window.recursion_view, "recursion_frame_label")
                assert any(
                    f"#{state['active_depth']} factorial" in label for label in labels
                )

    assert saw_active_frame is True
    assert _texts(window.recursion_view, "recursion_return_value") == ["6"]

    window.reset_execution()
    assert window.current_step_index == -1
    assert window.recursion_view.winfo_manager() != "pack"


def test_main_window_shows_subarrays_and_return_panel(
    session_tk_root: tk.Tk,
) -> None:
    """Verify slice sub-work and the final result are visible in the UI."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(SUBWORK_CODE)
    window.input_panel.set_array_text("nums = [1, 2, 3]")

    window.handle_run()

    saw_subarray = False
    for _ in range(len(window.history)):
        window.step_forward()
        if window.recursion_view.winfo_manager() == "pack":
            if window.recursion_view.canvas.find_withtag("recursion_subarray"):
                saw_subarray = True

    assert saw_subarray is True
    assert _texts(window.recursion_view, "recursion_return_value") == ["3"]

    window.reset_execution()
    assert window.recursion_view.winfo_manager() != "pack"
