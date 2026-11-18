"""Tests for auxiliary stack and queue tracing (T030)."""

from __future__ import annotations

import json
from collections import deque
from typing import Any

from src.execution.events import EventType, ExecutionEvent
from src.execution.tracer import (
    classify_auxiliary_container,
    extract_auxiliary_linear_state,
)
from src.execution.worker import execute_code


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

QUEUE_CODE = """
from collections import deque

def run_queue(nums):
    q = deque()
    for n in nums:
        q.append(n)
    order = []
    while q:
        order.append(q.popleft())
    return order
"""

LIST_QUEUE_CODE = """
def run_queue(nums):
    queue = []
    for n in nums:
        queue.append(n)
    order = []
    while queue:
        order.append(queue.pop(0))
    return order
"""


def _container_events(result: Any) -> list[ExecutionEvent]:
    """Return only auxiliary container operation events."""
    return [
        event
        for event in result.events
        if event.get("event_type") == EventType.CONTAINER.value
    ]


def _operations(result: Any) -> list[dict[str, Any]]:
    """Return the recorded stack/queue operations in execution order."""
    return [
        event["metadata"]["container_op"]
        for event in _container_events(result)
    ]


# ---------------------------------------------------------------------------
# 1. Classification and extraction
# ---------------------------------------------------------------------------


def test_classify_stack_by_name_and_list_type() -> None:
    """Verify stack names are recognized only for list-like containers."""
    assert classify_auxiliary_container("stack", []) == "stack"
    assert classify_auxiliary_container("st", [1, 2]) == "stack"
    assert classify_auxiliary_container("s", []) == "stack"
    assert classify_auxiliary_container("my_stack", []) == "stack"
    assert classify_auxiliary_container("stack_2", []) == "stack"

    assert classify_auxiliary_container("stack", "not a container") is None
    assert classify_auxiliary_container("s", "abc") is None
    assert classify_auxiliary_container("temp", []) is None


def test_classify_queue_by_name_and_deque_type() -> None:
    """Verify queue names are recognized for lists and deques."""
    assert classify_auxiliary_container("queue", []) == "queue"
    assert classify_auxiliary_container("q", deque([1])) == "queue"
    assert classify_auxiliary_container("fifo", deque()) == "queue"
    assert classify_auxiliary_container("bfs_queue", []) == "queue"

    # deques are treated as queues even without a matching name.
    assert classify_auxiliary_container("work", deque([1])) == "queue"
    assert classify_auxiliary_container("queue", "abc") is None


def test_extract_auxiliary_linear_state_separates_and_snapshots() -> None:
    """Verify stacks and queues are extracted with top/front/rear snapshots."""
    state = extract_auxiliary_linear_state(
        {
            "stack": [1, 2, 3],
            "q": deque(["a", "b"]),
            "nums": [9, 9],
            "text": "abc",
        }
    )

    assert state is not None
    assert [stack["name"] for stack in state["stacks"]] == ["stack"]
    assert [queue["name"] for queue in state["queues"]] == ["q"]

    stack = state["stacks"][0]
    assert stack["kind"] == "stack"
    assert stack["items"] == [1, 2, 3]
    assert stack["size"] == 3
    assert stack["top"] == 3

    queue = state["queues"][0]
    assert queue["kind"] == "queue"
    assert queue["items"] == ["a", "b"]
    assert queue["size"] == 2
    assert queue["front"] == "a"
    assert queue["rear"] == "b"


def test_extract_auxiliary_linear_state_empty_containers() -> None:
    """Verify empty recognized containers are still reported for rendering."""
    state = extract_auxiliary_linear_state({"stack": [], "queue": deque()})

    assert state is not None
    assert state["stacks"][0]["items"] == []
    assert state["stacks"][0]["top"] is None
    assert state["queues"][0]["front"] is None
    assert state["queues"][0]["rear"] is None


def test_extract_auxiliary_linear_state_without_candidates() -> None:
    """Verify ordinary locals do not produce auxiliary state."""
    assert extract_auxiliary_linear_state({}) is None
    assert extract_auxiliary_linear_state({"nums": [1, 2], "x": 5}) is None


def test_container_event_serialization_roundtrip() -> None:
    """Verify CONTAINER events and auxiliary metadata survive JSON serialization."""
    event = ExecutionEvent(
        step_index=3,
        event_type=EventType.CONTAINER,
        line_number=7,
        values=[42],
        metadata={
            "auxiliary": {
                "stacks": [
                    {"name": "stack", "kind": "stack", "items": [42], "size": 1, "top": 42}
                ],
                "queues": [],
            },
            "container_op": {
                "name": "stack",
                "kind": "stack",
                "action": "push",
                "value": 42,
            },
        },
    )

    restored = ExecutionEvent.from_dict(json.loads(json.dumps(event.to_dict())))

    assert restored.event_type == EventType.CONTAINER
    assert restored.metadata["container_op"]["action"] == "push"
    assert restored.metadata["auxiliary"]["stacks"][0]["top"] == 42


# ---------------------------------------------------------------------------
# 2. Stack tracking
# ---------------------------------------------------------------------------


def test_stack_operations_are_traced_in_lifo_order() -> None:
    """Verify push/pop events capture LIFO values and container snapshots."""
    result = execute_code(STACK_CODE, [1, 2, 3])

    assert result.is_success is True
    assert result.final_array == [3, 2, 1]

    operations = _operations(result)
    assert [op["action"] for op in operations] == [
        "push",
        "push",
        "push",
        "pop",
        "pop",
        "pop",
    ]
    assert [op["value"] for op in operations] == [1, 2, 3, 3, 2, 1]
    assert {op["kind"] for op in operations} == {"stack"}

    snapshots = [
        event["metadata"]["auxiliary"]["stacks"][0]
        for event in _container_events(result)
    ]
    assert [snapshot["items"] for snapshot in snapshots] == [
        [1],
        [1, 2],
        [1, 2, 3],
        [1, 2],
        [1],
        [],
    ]
    assert [snapshot["size"] for snapshot in snapshots] == [1, 2, 3, 2, 1, 0]
    assert snapshots[-1]["top"] is None


def test_line_events_keep_auxiliary_stack_state() -> None:
    """Verify auxiliary state is attached to non-container events after setup."""
    result = execute_code(STACK_CODE, [1, 2])

    assert result.is_success is True
    line_events = [
        event
        for event in result.events
        if event.get("event_type") == EventType.LINE.value
        and event["metadata"].get("auxiliary", {}).get("stacks")
    ]
    assert line_events
    assert line_events[-1]["metadata"]["auxiliary"]["stacks"][0]["name"] == "stack"


# ---------------------------------------------------------------------------
# 3. Queue tracking
# ---------------------------------------------------------------------------


def test_deque_operations_are_traced_in_fifo_order() -> None:
    """Verify enqueue/dequeue events capture FIFO values and snapshots."""
    result = execute_code(QUEUE_CODE, [1, 2, 3])

    assert result.is_success is True
    assert result.final_array == [1, 2, 3]

    operations = _operations(result)
    assert [op["action"] for op in operations] == [
        "enqueue",
        "enqueue",
        "enqueue",
        "dequeue",
        "dequeue",
        "dequeue",
    ]
    assert [op["value"] for op in operations] == [1, 2, 3, 1, 2, 3]
    assert {op["kind"] for op in operations} == {"queue"}

    snapshots = [
        event["metadata"]["auxiliary"]["queues"][0]
        for event in _container_events(result)
    ]
    assert [snapshot["items"] for snapshot in snapshots] == [
        [1],
        [1, 2],
        [1, 2, 3],
        [2, 3],
        [3],
        [],
    ]
    assert snapshots[2]["front"] == 1
    assert snapshots[2]["rear"] == 3
    assert snapshots[-1]["front"] is None


def test_list_based_queue_pop_is_traced_as_dequeue() -> None:
    """Verify a list named queue using pop(0) records FIFO removals."""
    result = execute_code(LIST_QUEUE_CODE, [5, 6])

    assert result.is_success is True
    assert result.final_array == [5, 6]

    operations = _operations(result)
    assert [op["action"] for op in operations] == [
        "enqueue",
        "enqueue",
        "dequeue",
        "dequeue",
    ]
    assert [op["value"] for op in operations] == [5, 6, 5, 6]


# ---------------------------------------------------------------------------
# 4. No false positives
# ---------------------------------------------------------------------------


def test_plain_lists_and_array_algorithms_have_no_auxiliary_state() -> None:
    """Verify ordinary result lists and sorting arrays are not surfaced."""
    list_code = """
def build(nums):
    result = []
    for value in nums:
        result.append(value)
    return result
"""
    result = execute_code(list_code, [1, 2])
    assert result.is_success is True
    assert _container_events(result) == []
    assert all("auxiliary" not in event.metadata for event in result.events)

    sort_code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""
    sort_result = execute_code(sort_code, [3, 1, 2])
    assert sort_result.is_success is True
    assert _container_events(sort_result) == []
    assert all("auxiliary" not in event.metadata for event in sort_result.events)
