"""Tests for Linked List execution tracing, state extraction, and canvas visualization (T024)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

import pytest

from src.execution.events import EventType, ExecutionEvent
from src.execution.models import ListNode
from src.execution.tracer import ExecutionTracer, extract_linked_list_state
from src.visualization.linked_list_canvas import LinkedListCanvas


def test_extract_linked_list_state_empty() -> None:
    """Verify state extraction when head is None or locals have no ListNode."""
    f_locals: dict[str, Any] = {"head": None, "x": 10}
    state = extract_linked_list_state(f_locals)
    assert state is not None
    assert state["nodes"] == []
    assert state["pointers"] == {"head": None}
    assert state["has_cycle"] is False
    assert state["cycle_start"] is None


def test_extract_linked_list_state_single_node() -> None:
    """Verify state extraction for a single-node list."""
    node = ListNode(42)
    f_locals: dict[str, Any] = {"head": node, "curr": node}
    state = extract_linked_list_state(f_locals)
    assert state is not None
    assert len(state["nodes"]) == 1
    assert state["nodes"][0]["val"] == 42
    assert state["nodes"][0]["next"] is None
    assert state["pointers"]["head"] == state["nodes"][0]["id"]
    assert state["pointers"]["curr"] == state["nodes"][0]["id"]
    assert state["has_cycle"] is False


def test_extract_linked_list_state_multi_node_and_pointers() -> None:
    """Verify state extraction for a multi-node list with multiple distinct pointers."""
    head = ListNode.from_list([10, 20, 30])
    curr = head.next  # Node with val 20
    prev = head       # Node with val 10

    f_locals: dict[str, Any] = {"head": head, "curr": curr, "prev": prev}
    state = extract_linked_list_state(f_locals)
    assert state is not None
    assert len(state["nodes"]) == 3
    assert [n["val"] for n in state["nodes"]] == [10, 20, 30]

    node_map = {n["val"]: n["id"] for n in state["nodes"]}
    assert state["pointers"]["head"] == node_map[10]
    assert state["pointers"]["prev"] == node_map[10]
    assert state["pointers"]["curr"] == node_map[20]
    assert state["has_cycle"] is False


def test_pointer_assignment_and_mutation_tracking() -> None:
    """Verify tracking pointer advancement and next-pointer reassignment."""
    # Simulating reversal step: prev = None, curr = head
    n1 = ListNode(1)
    n2 = ListNode(2)
    n1.next = n2

    f_locals: dict[str, Any] = {"head": n1, "curr": n1, "prev": None}
    s1 = extract_linked_list_state(f_locals)
    assert s1 is not None
    assert s1["pointers"]["prev"] is None
    assert s1["pointers"]["curr"] == s1["nodes"][0]["id"]

    # Mutation: curr.next = prev, prev = curr, curr = n2
    n1.next = None
    f_locals = {"head": n1, "prev": n1, "curr": n2}
    s2 = extract_linked_list_state(f_locals)
    assert s2 is not None
    assert len(s2["nodes"]) == 2
    # n1.next is now None
    n1_state = next(n for n in s2["nodes"] if n["val"] == 1)
    assert n1_state["next"] is None
    assert s2["pointers"]["prev"] == n1_state["id"]
    n2_state = next(n for n in s2["nodes"] if n["val"] == 2)
    assert s2["pointers"]["curr"] == n2_state["id"]


def test_node_value_mutation_tracking() -> None:
    """Verify node value updates are reflected in extracted state."""
    head = ListNode(10)
    f_locals: dict[str, Any] = {"head": head}
    s1 = extract_linked_list_state(f_locals)
    assert s1["nodes"][0]["val"] == 10

    # In-place value update
    head.val = 99
    s2 = extract_linked_list_state(f_locals)
    assert s2["nodes"][0]["val"] == 99


def test_cycle_detection_in_linked_list() -> None:
    """Verify cyclic list detection and cycle_start identification."""
    n1 = ListNode(1)
    n2 = ListNode(2)
    n3 = ListNode(3)
    n1.next = n2
    n2.next = n3
    n3.next = n2  # Cycle back to node 2

    f_locals: dict[str, Any] = {"head": n1, "curr": n3}
    state = extract_linked_list_state(f_locals)
    assert state is not None
    assert state["has_cycle"] is True
    node2_id = next(n for n in state["nodes"] if n["val"] == 2)["id"]
    assert state["cycle_start"] == node2_id


def test_linked_list_canvas_rendering_empty(session_tk_root: tk.Tk) -> None:
    """Verify LinkedListCanvas handles empty list state without errors."""
    canvas_view = LinkedListCanvas(session_tk_root)
    empty_state = {"nodes": [], "pointers": {"head": None}, "has_cycle": False, "cycle_start": None}
    canvas_view.render_state(empty_state)

    items = canvas_view.canvas.find_all()
    assert len(items) > 0  # Displays "None" or "[Empty List]"
    canvas_view.destroy()


def test_linked_list_canvas_rendering_single_and_multi_node(session_tk_root: tk.Tk) -> None:
    """Verify LinkedListCanvas renders nodes, values, and arrow connections."""
    canvas_view = LinkedListCanvas(session_tk_root)
    state = {
        "nodes": [
            {"id": 1, "val": 10, "next": 2},
            {"id": 2, "val": 20, "next": None},
        ],
        "pointers": {"head": 1, "curr": 2},
        "has_cycle": False,
        "cycle_start": None,
    }
    canvas_view.render_state(state)

    # Check node rectangles and arrows created
    items = canvas_view.canvas.find_all()
    assert len(items) >= 6  # At least 2 boxes, 2 texts, 1 arrow, pointer labels
    canvas_view.destroy()


def test_linked_list_canvas_pointer_labels(session_tk_root: tk.Tk) -> None:
    """Verify variable pointer labels are placed on canvas."""
    canvas_view = LinkedListCanvas(session_tk_root)
    state = {
        "nodes": [{"id": 1, "val": 100, "next": None}],
        "pointers": {"head": 1, "slow": 1, "fast": 1},
        "has_cycle": False,
        "cycle_start": None,
    }
    canvas_view.render_state(state)

    text_contents = [
        canvas_view.canvas.itemcget(item, "text")
        for item in canvas_view.canvas.find_all()
        if canvas_view.canvas.type(item) == "text"
    ]
    # Check that labels appear in text elements
    assert "100" in text_contents
    assert any("head" in t or "slow" in t for t in text_contents)
    canvas_view.destroy()


def test_linked_list_canvas_cycle_rendering(session_tk_root: tk.Tk) -> None:
    """Verify cyclic arrow representation is drawn when has_cycle is True."""
    canvas_view = LinkedListCanvas(session_tk_root)
    state = {
        "nodes": [
            {"id": 1, "val": 1, "next": 2},
            {"id": 2, "val": 2, "next": 1},
        ],
        "pointers": {"head": 1},
        "has_cycle": True,
        "cycle_start": 1,
    }
    canvas_view.render_state(state)

    tags = set()
    for item in canvas_view.canvas.find_all():
        tags.update(canvas_view.canvas.gettags(item))
    assert "cycle_arrow" in tags or "arrow" in tags
    canvas_view.destroy()


def test_linked_list_canvas_render_event(session_tk_root: tk.Tk) -> None:
    """Verify LinkedListCanvas can render directly from an ExecutionEvent with metadata."""
    canvas_view = LinkedListCanvas(session_tk_root)
    event = ExecutionEvent(
        step_index=0,
        event_type=EventType.LINE,
        line_number=5,
        metadata={
            "linked_list": {
                "nodes": [{"id": 1, "val": 7, "next": None}],
                "pointers": {"curr": 1},
                "has_cycle": False,
                "cycle_start": None,
            }
        },
    )
    canvas_view.render_event(event)
    items = canvas_view.canvas.find_all()
    assert len(items) > 0
    canvas_view.destroy()
