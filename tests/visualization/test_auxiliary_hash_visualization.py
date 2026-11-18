"""Tests for auxiliary hash map and set canvas rendering (T033)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from src.ui.main_window import MainWindow
from src.visualization.hash_canvas import AuxiliaryHashCanvas


COUNT_CODE = """
def count(nums):
    freq = {}
    for n in nums:
        if n in freq:
            freq[n] += 1
        else:
            freq[n] = 1
    return len(freq)
"""

QUEUE_SET_CODE = """
from collections import deque

def explore(nums):
    queue = deque()
    visited = set()
    for n in nums:
        queue.append(n)
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
    return len(visited)
"""


def _map_state(entries: list[tuple[Any, Any]], name: str = "freq") -> dict:
    return {
        "stacks": [],
        "queues": [],
        "maps": [
            {
                "name": name,
                "kind": "map",
                "entries": [{"key": key, "value": value} for key, value in entries],
                "size": len(entries),
            }
        ],
        "sets": [],
    }


def _set_state(items: list[Any], name: str = "seen") -> dict:
    return {
        "stacks": [],
        "queues": [],
        "maps": [],
        "sets": [
            {
                "name": name,
                "kind": "set",
                "items": items,
                "size": len(items),
            }
        ],
    }


def _tags(view: AuxiliaryHashCanvas) -> set[str]:
    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    return tags


def _texts(view: AuxiliaryHashCanvas, tag: str) -> list[str]:
    return [
        view.canvas.itemcget(item, "text")
        for item in view.canvas.find_withtag(tag)
    ]


def _text_y(view: AuxiliaryHashCanvas, tag: str, text: str) -> float:
    for item in view.canvas.find_withtag(tag):
        if view.canvas.itemcget(item, "text") == text:
            return float(view.canvas.coords(item)[1])
    raise AssertionError(f"text {text!r} not found under tag {tag!r}")


# ---------------------------------------------------------------------------
# 1. Hash map rendering
# ---------------------------------------------------------------------------


def test_hash_canvas_renders_key_value_rows(session_tk_root: tk.Tk) -> None:
    """Verify map entries render as key/value table rows in insertion order."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(_map_state([("a", 2), ("b", 1)]))

    tags = _tags(view)
    assert {"hash_map", "hash_map_row", "hash_title", "hash_map_title"} <= tags
    assert _texts(view, "hash_map_key") == ["a", "b"]
    assert _texts(view, "hash_map_value") == ["2", "1"]
    assert len(view.canvas.find_withtag("hash_map_row")) == 2
    assert "freq" in view.canvas.itemcget(
        view.canvas.find_withtag("hash_map_title")[0], "text"
    )
    view.destroy()


def test_hash_canvas_highlights_active_map_key(session_tk_root: tk.Tk) -> None:
    """Verify the key touched by the current map operation is highlighted."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(
        _map_state([("a", 2), ("b", 1)]),
        operation={
            "name": "freq",
            "kind": "map",
            "action": "lookup",
            "key": "a",
            "value": 2,
        },
    )

    active_rows = view.canvas.find_withtag("hash_map_active_row")
    assert len(active_rows) == 1
    row = active_rows[0]
    assert (
        view.canvas.itemcget(row, "outline").lower()
        == AuxiliaryHashCanvas.OP_COLOR.lower()
    )

    row_center = (view.canvas.coords(row)[1] + view.canvas.coords(row)[3]) / 2.0
    assert abs(_text_y(view, "hash_map_key", "a") - row_center) < 2.0
    assert _texts(view, "hash_op") == ["lookup a -> 2"]
    view.destroy()


def test_hash_canvas_renders_empty_map_placeholder(
    session_tk_root: tk.Tk,
) -> None:
    """Verify an empty map still renders its panel with an empty label."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(_map_state([]))

    assert view.canvas.find_withtag("hash_map")
    assert view.canvas.find_withtag("hash_map_empty")
    view.destroy()


# ---------------------------------------------------------------------------
# 2. Hash set rendering
# ---------------------------------------------------------------------------


def test_hash_canvas_renders_set_membership_badges(
    session_tk_root: tk.Tk,
) -> None:
    """Verify set members render as individual badges."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(_set_state(["a", "b", "c"]))

    tags = _tags(view)
    assert {"hash_set", "hash_set_badge", "hash_title", "hash_set_title"} <= tags
    assert len(view.canvas.find_withtag("hash_set_badge")) == 3
    assert set(_texts(view, "hash_set_badge_label")) == {"a", "b", "c"}
    assert "seen" in view.canvas.itemcget(
        view.canvas.find_withtag("hash_set_title")[0], "text"
    )
    view.destroy()


def test_hash_canvas_highlights_active_set_member(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the badge affected by the current set operation is highlighted."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(
        _set_state(["a", "b"]),
        operation={
            "name": "seen",
            "kind": "set",
            "action": "add",
            "key": "b",
            "value": "b",
        },
    )

    active_badges = view.canvas.find_withtag("hash_set_active_badge")
    assert len(active_badges) == 1
    badge = active_badges[0]
    assert (
        view.canvas.itemcget(badge, "outline").lower()
        == AuxiliaryHashCanvas.OP_COLOR.lower()
    )

    badge_center = (
        view.canvas.coords(badge)[1] + view.canvas.coords(badge)[3]
    ) / 2.0
    assert abs(_text_y(view, "hash_set_badge_label", "b") - badge_center) < 2.0
    assert _texts(view, "hash_op") == ["add b"]
    view.destroy()


def test_hash_canvas_renders_empty_set_placeholder(
    session_tk_root: tk.Tk,
) -> None:
    """Verify an empty set still renders its panel with an empty label."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(_set_state([]))

    assert view.canvas.find_withtag("hash_set")
    assert view.canvas.find_withtag("hash_set_empty")
    view.destroy()


# ---------------------------------------------------------------------------
# 3. Combined and empty states
# ---------------------------------------------------------------------------


def test_hash_canvas_renders_maps_and_sets_side_by_side(
    session_tk_root: tk.Tk,
) -> None:
    """Verify maps and sets from one snapshot are both rendered."""
    state = _map_state([(1, 2)])
    state["sets"] = _set_state([1, 2])["sets"]

    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state(state)

    tags = _tags(view)
    assert "hash_map_row" in tags
    assert "hash_set_badge" in tags
    map_left = view.canvas.coords(view.canvas.find_withtag("hash_map")[0])[0]
    set_left = view.canvas.coords(view.canvas.find_withtag("hash_set")[0])[0]
    assert map_left < set_left
    view.destroy()


def test_hash_canvas_renders_empty_auxiliary_state(
    session_tk_root: tk.Tk,
) -> None:
    """Verify a snapshot with no hash containers renders a placeholder."""
    view = AuxiliaryHashCanvas(session_tk_root)
    view.render_state({"stacks": [], "queues": [], "maps": [], "sets": []})

    assert view.canvas.find_withtag("hash_empty")
    view.destroy()


# ---------------------------------------------------------------------------
# 4. Main window integration
# ---------------------------------------------------------------------------


def test_main_window_shows_and_hides_hash_panel(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the hash panel follows recorded map state while stepping."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(COUNT_CODE)
    window.input_panel.set_array_text("nums = [1, 2, 1]")

    window.handle_run()

    assert window.history is not None
    assert len(window.history) > 0
    assert window.hash_view.winfo_manager() != "pack"

    panel_visible = False
    descriptions: list[str] = []
    for _ in range(len(window.history)):
        window.step_forward()
        descriptions.append(window.controls.lbl_details.cget("text"))
        if window.hash_view.winfo_manager() == "pack":
            panel_visible = True
            assert "hash_map" in _tags(window.hash_view)

    assert panel_visible is True
    assert any("freq[1] = 1" in text for text in descriptions)
    assert any("1 in freq" in text for text in descriptions)

    window.reset_execution()
    assert window.current_step_index == -1
    assert window.hash_view.winfo_manager() != "pack"


def test_main_window_shows_queue_and_set_panels_together(
    session_tk_root: tk.Tk,
) -> None:
    """Verify a BFS-style algorithm can show queue and visited set panels together."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(QUEUE_SET_CODE)
    window.input_panel.set_array_text("nums = [1, 2, 1]")

    window.handle_run()

    assert window.history is not None
    both_visible_with_content = False
    descriptions: list[str] = []
    for _ in range(len(window.history)):
        window.step_forward()
        descriptions.append(window.controls.lbl_details.cget("text"))
        if (
            window.auxiliary_view.winfo_manager() == "pack"
            and window.hash_view.winfo_manager() == "pack"
        ):
            linear_tags = _tags(window.auxiliary_view)
            hash_tags = _tags(window.hash_view)
            if "queue_item" in linear_tags and "hash_set_badge" in hash_tags:
                both_visible_with_content = True

    assert both_visible_with_content is True
    assert any("visited added 1" in text for text in descriptions)
    assert any("1 not in visited" in text for text in descriptions)
