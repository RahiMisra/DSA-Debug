"""Tests for Binary Tree execution tracing, hierarchical layout, and canvas visualization (T026)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import pytest

from src.execution.events import EventType, ExecutionEvent
from src.execution.models import TreeNode
from src.execution.tracer import extract_tree_state
from src.visualization.tree_canvas import BinaryTreeCanvas, compute_tree_layout


def test_extract_tree_state_empty() -> None:
    """Verify tree state extraction when root is None."""
    f_locals: dict[str, Any] = {"root": None, "x": 5}
    state = extract_tree_state(f_locals)
    assert state is not None
    assert state["root_id"] is None
    assert state["nodes"] == {}
    assert state["pointers"] == {"root": None}


def test_extract_tree_state_single_node() -> None:
    """Verify state extraction for a single root node."""
    root = TreeNode(42)
    f_locals: dict[str, Any] = {"root": root, "curr": root}
    state = extract_tree_state(f_locals)
    assert state is not None
    assert state["root_id"] is not None
    assert len(state["nodes"]) == 1
    root_node = state["nodes"][state["root_id"]]
    assert root_node["val"] == 42
    assert root_node["left"] is None
    assert root_node["right"] is None
    assert state["pointers"]["root"] == state["root_id"]
    assert state["pointers"]["curr"] == state["root_id"]


def test_extract_tree_state_complete_tree() -> None:
    """Verify state extraction for standard level-order complete tree [3, 9, 20, None, None, 15, 7]."""
    root = TreeNode.from_level_order([3, 9, 20, None, None, 15, 7])
    assert root is not None
    f_locals: dict[str, Any] = {"root": root}
    state = extract_tree_state(f_locals)
    assert state is not None
    assert len(state["nodes"]) == 5

    # Check root
    root_rec = state["nodes"][state["root_id"]]
    assert root_rec["val"] == 3
    left_id = root_rec["left"]
    right_id = root_rec["right"]
    assert left_id is not None and right_id is not None
    assert state["nodes"][left_id]["val"] == 9
    assert state["nodes"][right_id]["val"] == 20

    # Right child's children
    r_left = state["nodes"][right_id]["left"]
    r_right = state["nodes"][right_id]["right"]
    assert state["nodes"][r_left]["val"] == 15
    assert state["nodes"][r_right]["val"] == 7


def test_extract_tree_state_skewed_tree() -> None:
    """Verify state extraction for a heavily left-skewed tree."""
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.left.left = TreeNode(3)

    f_locals: dict[str, Any] = {"root": root}
    state = extract_tree_state(f_locals)
    assert state is not None
    assert len(state["nodes"]) == 3
    n1 = state["nodes"][state["root_id"]]
    assert n1["val"] == 1
    n2 = state["nodes"][n1["left"]]
    assert n2["val"] == 2
    n3 = state["nodes"][n2["left"]]
    assert n3["val"] == 3
    assert n3["left"] is None and n3["right"] is None


def test_tree_traversal_and_pointer_tracking() -> None:
    """Verify tracking pointer movement during tree traversal."""
    root = TreeNode(10)
    root.left = TreeNode(5)
    root.right = TreeNode(15)

    # Initial step: curr at root
    f_locals: dict[str, Any] = {"root": root, "curr": root}
    s1 = extract_tree_state(f_locals)
    assert s1 is not None
    assert s1["pointers"]["curr"] == s1["root_id"]

    # Traversal step: curr = curr.left
    curr = root.left
    f_locals = {"root": root, "curr": curr}
    s2 = extract_tree_state(f_locals)
    assert s2 is not None
    assert s2["pointers"]["curr"] == s2["nodes"][s2["root_id"]]["left"]


def test_tree_node_mutation_and_child_modification() -> None:
    """Verify value mutation and child insertion are captured in state."""
    root = TreeNode(10)
    f_locals: dict[str, Any] = {"root": root}

    # In-place value change
    root.val = 99
    s1 = extract_tree_state(f_locals)
    assert s1["nodes"][s1["root_id"]]["val"] == 99

    # Insert child
    root.right = TreeNode(200)
    s2 = extract_tree_state(f_locals)
    assert len(s2["nodes"]) == 2
    right_id = s2["nodes"][s2["root_id"]]["right"]
    assert right_id is not None
    assert s2["nodes"][right_id]["val"] == 200


def test_tree_canvas_layout_coordinates() -> None:
    """Verify hierarchical in-order coordinates prevent overlaps and maintain tree structure."""
    nodes = {
        1: {"id": 1, "val": 10, "left": 2, "right": 3},
        2: {"id": 2, "val": 5, "left": None, "right": None},
        3: {"id": 3, "val": 15, "left": None, "right": None},
    }
    coords = compute_tree_layout(nodes, root_id=1, canvas_width=400, canvas_height=300)
    assert len(coords) == 3

    # Left child must have x < root.x, right child x > root.x
    x_root, y_root = coords[1]
    x_left, y_left = coords[2]
    x_right, y_right = coords[3]

    assert x_left < x_root < x_right
    assert y_root < y_left
    assert y_root < y_right
    assert y_left == y_right  # Same depth level


def test_tree_canvas_rendering_empty(session_tk_root: tk.Tk) -> None:
    """Verify BinaryTreeCanvas handles empty tree state cleanly."""
    tree_view = BinaryTreeCanvas(session_tk_root)
    tree_view.render_state({"root_id": None, "nodes": {}, "pointers": {"root": None}})
    items = tree_view.canvas.find_all()
    assert len(items) > 0  # Displays "Empty Tree"
    tree_view.destroy()


def test_tree_canvas_rendering_nodes_and_branches(session_tk_root: tk.Tk) -> None:
    """Verify BinaryTreeCanvas creates circle nodes, value text, branch lines, and pointer labels."""
    tree_view = BinaryTreeCanvas(session_tk_root)
    state = {
        "root_id": 1,
        "nodes": {
            1: {"id": 1, "val": 1, "left": 2, "right": 3},
            2: {"id": 2, "val": 2, "left": None, "right": None},
            3: {"id": 3, "val": 3, "left": None, "right": None},
        },
        "pointers": {"root": 1, "curr": 2},
    }
    tree_view.render_state(state)

    tags = set()
    for item in tree_view.canvas.find_all():
        tags.update(tree_view.canvas.gettags(item))

    assert "tree_node" in tags
    assert "tree_val" in tags
    assert "branch_line" in tags
    assert "pointer_label" in tags
    tree_view.destroy()


def test_tree_canvas_active_node_highlighting(session_tk_root: tk.Tk) -> None:
    """Verify active node pointed to by curr has distinct highlight outline."""
    tree_view = BinaryTreeCanvas(session_tk_root)
    state = {
        "root_id": 1,
        "nodes": {
            1: {"id": 1, "val": 100, "left": None, "right": None},
        },
        "pointers": {"root": 1, "curr": 1},
    }
    tree_view.render_state(state)

    node_items = [
        item for item in tree_view.canvas.find_all()
        if "tree_node" in tree_view.canvas.gettags(item)
    ]
    assert len(node_items) == 1
    # Check width or color indicating active highlight
    width = float(tree_view.canvas.itemcget(node_items[0], "width"))
    assert width >= 2
    tree_view.destroy()


def test_tree_canvas_render_event(session_tk_root: tk.Tk) -> None:
    """Verify BinaryTreeCanvas can render directly from an ExecutionEvent with tree metadata."""
    tree_view = BinaryTreeCanvas(session_tk_root)
    event = ExecutionEvent(
        step_index=0,
        event_type=EventType.LINE,
        line_number=3,
        metadata={
            "tree": {
                "root_id": 1,
                "nodes": {1: {"id": 1, "val": 50, "left": None, "right": None}},
                "pointers": {"root": 1},
            }
        },
    )
    tree_view.render_event(event)
    items = tree_view.canvas.find_all()
    assert len(items) > 0
    tree_view.destroy()
