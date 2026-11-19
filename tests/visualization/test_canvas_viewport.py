"""Tests for scrollable visualization viewports (T040/T042)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import tkinter as tk

from src.ui.array_view import ArrayView
from src.visualization.auxiliary_canvas import AuxiliaryLinearCanvas
from src.visualization.graph_canvas import GraphCanvas
from src.visualization.hash_canvas import AuxiliaryHashCanvas
from src.visualization.linked_list_canvas import LinkedListCanvas
from src.visualization.recursion_canvas import RecursionCanvas
from src.visualization.tree_canvas import BinaryTreeCanvas
from src.visualization.viewport import ScrollableCanvas


@pytest.fixture
def mapped_root(session_tk_root: tk.Tk):
    """Provide a mapped Toplevel so scroll fractions reflect real viewport sizes."""
    top = tk.Toplevel(session_tk_root)
    top.geometry("900x600")
    top.deiconify()
    top.update()
    yield top
    try:
        top.destroy()
    except tk.TclError:
        pass


def _mapped(view: tk.Widget, root: tk.Tk) -> None:
    view.pack(fill=tk.BOTH, expand=True)
    root.update_idletasks()


def _linked_state(count: int) -> dict:
    return {
        "nodes": [
            {"id": index, "val": index, "next": index + 1 if index < count else None}
            for index in range(1, count + 1)
        ],
        "pointers": {"head": 1},
        "has_cycle": False,
        "cycle_start": None,
    }


def test_large_array_scrolls_instead_of_shrinking_below_readable_cells(
    mapped_root: tk.Tk,
) -> None:
    """Verify a wide array exposes a horizontal scrollbar and scrolls."""
    view = ArrayView(mapped_root)
    _mapped(view, mapped_root)
    view.set_array(list(range(90)))
    mapped_root.update_idletasks()

    viewport = view.viewport
    width = viewport.viewport_size()[0]
    region = viewport.scrollregion

    assert region[2] - region[0] > width
    assert viewport.h_scrollbar.winfo_manager() == "grid"

    before = viewport.canvas.xview()
    viewport.scroll_by(10, 0)
    mapped_root.update_idletasks()
    after = viewport.canvas.xview()
    assert after[0] > before[0]

    view.destroy()


def test_viewport_wheel_shift_wheel_and_drag_change_visible_region(
    mapped_root: tk.Tk,
) -> None:
    """Verify mouse wheel, Shift+wheel, and drag panning move the viewport."""
    viewport = ScrollableCanvas(mapped_root)
    viewport.pack(fill=tk.BOTH, expand=True)
    viewport.canvas.create_rectangle(0, 0, 2400, 1800, fill="#313244")
    viewport.update_scrollregion()
    mapped_root.update_idletasks()

    start = viewport.visible_region()
    viewport._on_mousewheel(SimpleNamespace(delta=-120, state=0))
    mapped_root.update_idletasks()
    scrolled_down = viewport.visible_region()
    assert scrolled_down[1] > start[1]

    viewport._on_shift_mousewheel(SimpleNamespace(delta=-120, state=1))
    mapped_root.update_idletasks()
    scrolled_right = viewport.visible_region()
    assert scrolled_right[0] > start[0]

    viewport.reset_view()
    mapped_root.update_idletasks()
    viewport._on_pan_start(SimpleNamespace(x=120, y=120))
    viewport._on_pan_drag(SimpleNamespace(x=60, y=50))
    viewport._on_pan_end(SimpleNamespace(x=60, y=50))
    mapped_root.update_idletasks()
    dragged = viewport.visible_region()
    assert dragged[0] > 0 or dragged[1] > 0

    viewport.destroy()


def test_linked_list_uses_natural_width_and_scrolls(
    mapped_root: tk.Tk,
) -> None:
    """Verify a long linked list keeps natural node spacing and scrolls."""
    view = LinkedListCanvas(mapped_root)
    _mapped(view, mapped_root)
    view.render_state(_linked_state(35))
    mapped_root.update_idletasks()

    region = view.viewport.scrollregion
    width = view.viewport.viewport_size()[0]
    assert region[2] - region[0] > width
    assert view.canvas.find_withtag("node_box")

    view.destroy()


def test_large_tree_and_graph_scroll_in_both_directions(
    mapped_root: tk.Tk,
) -> None:
    """Verify trees and graphs compute a natural canvas larger than the viewport."""
    tree = BinaryTreeCanvas(mapped_root)
    _mapped(tree, mapped_root)
    tree_state = {
        "root_id": 1,
        "nodes": {
            node_id: {
                "id": node_id,
                "val": node_id,
                "left": None,
                "right": node_id + 1 if node_id < 24 else None,
            }
            for node_id in range(1, 25)
        },
        "pointers": {"root": 1},
    }
    tree.render_state(tree_state)
    mapped_root.update_idletasks()
    tree_region = tree.viewport.scrollregion
    tree_width, tree_height = tree.viewport.viewport_size()
    assert tree_region[2] - tree_region[0] > tree_width
    assert tree_region[3] - tree_region[1] > tree_height

    graph = GraphCanvas(mapped_root)
    _mapped(graph, mapped_root)
    graph.render_state(
        {
            "nodes": [
                {"id": node_id, "val": node_id, "state": "unvisited"}
                for node_id in range(40)
            ],
            "edges": [],
            "pointers": {},
            "directed": False,
        }
    )
    mapped_root.update_idletasks()
    graph_region = graph.viewport.scrollregion
    graph_width, graph_height = graph.viewport.viewport_size()
    assert graph_region[2] - graph_region[0] > graph_width
    assert graph_region[3] - graph_region[1] > graph_height

    tree.destroy()
    graph.destroy()


def test_auxiliary_and_hash_panels_render_all_items_in_scrollable_content(
    mapped_root: tk.Tk,
) -> None:
    """Verify stack queues and hash tables grow their content instead of truncating."""
    linear = AuxiliaryLinearCanvas(mapped_root)
    _mapped(linear, mapped_root)
    linear.render_state(
        {
            "stacks": [{"name": "stack", "items": list(range(40))}],
            "queues": [{"name": "queue", "items": list(range(30))}],
        }
    )
    mapped_root.update_idletasks()
    linear_region = linear.viewport.scrollregion
    linear_width, linear_height = linear.viewport.viewport_size()
    assert linear_region[2] - linear_region[0] > linear_width
    assert linear_region[3] - linear_region[1] > linear_height

    hashes = AuxiliaryHashCanvas(mapped_root)
    _mapped(hashes, mapped_root)
    hashes.render_state(
        {
            "maps": [
                {
                    "name": "freq",
                    "entries": [
                        {"key": f"key-{index}", "value": index}
                        for index in range(35)
                    ],
                }
            ],
            "sets": [
                {
                    "name": "seen",
                    "items": [f"member-{index}" for index in range(24)],
                }
            ],
        }
    )
    mapped_root.update_idletasks()
    hash_region = hashes.viewport.scrollregion
    hash_width, hash_height = hashes.viewport.viewport_size()
    assert hash_region[2] - hash_region[0] > hash_width
    assert hash_region[3] - hash_region[1] > hash_height

    linear.destroy()
    hashes.destroy()


def test_recursion_panel_scrolls_through_deep_call_stacks(
    mapped_root: tk.Tk,
) -> None:
    """Verify deep recursion content extends beyond the viewport."""
    view = RecursionCanvas(mapped_root)
    _mapped(view, mapped_root)
    frames = [
        {
            "function": "recurse",
            "depth": depth,
            "args": {"n": depth},
            "line": 2,
            "returning": False,
            "return_value": None,
            "chosen": {},
        }
        for depth in range(26)
    ]
    view.render_state(
        {
            "frames": frames,
            "subarrays": [],
            "return_structure": None,
            "last_return": None,
        }
    )
    mapped_root.update_idletasks()

    region = view.viewport.scrollregion
    width, height = view.viewport.viewport_size()
    assert region[2] - region[0] > width
    assert region[3] - region[1] > height
    assert len(view.canvas.find_withtag("recursion_frame_label")) == 26

    view.destroy()


def test_scroll_offset_is_preserved_for_unchanged_bounds_and_reset_when_smaller(
    mapped_root: tk.Tk,
) -> None:
    """Verify stepping with the same structure keeps the user's scroll position."""
    view = ArrayView(mapped_root)
    _mapped(view, mapped_root)
    view.set_array(list(range(80)))
    mapped_root.update_idletasks()

    view.viewport.canvas.xview_moveto(0.5)
    mapped_root.update_idletasks()
    before = view.viewport.visible_region()[0]
    assert before > 0

    view.set_array(list(range(80)))
    mapped_root.update_idletasks()
    assert view.viewport.visible_region()[0] == before

    view.set_array([1, 2, 3])
    mapped_root.update_idletasks()
    assert view.viewport.visible_region()[0] == 0

    view.destroy()


def test_small_content_hides_scrollbars(mapped_root: tk.Tk) -> None:
    """Verify scrollbars appear only when the rendered content needs them."""
    view = ArrayView(mapped_root)
    _mapped(view, mapped_root)
    view.set_array([1, 2, 3])
    mapped_root.update_idletasks()

    assert view.viewport.h_scrollbar.winfo_manager() == ""
    assert view.viewport.v_scrollbar.winfo_manager() == ""

    view.destroy()
