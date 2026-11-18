"""Tests for recursion frames, returns, and sub-array tracking (T034)."""

from __future__ import annotations

import json
from typing import Any

from src.execution.events import EventType, ExecutionEvent
from src.execution.worker import execute_code


FACTORIAL_CODE = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""

SUM_CODE = """
def sum_list(nums):
    res = 0
    for n in nums:
        res += n
    return res
"""

MERGE_SORT_CODE = """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    merged = []
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged
"""


def _events(result: Any, event_type: EventType) -> list[ExecutionEvent]:
    """Return events of one type from an execution result."""
    return [event for event in result.events if event.event_type == event_type]


def _recursion_states(result: Any) -> list[dict[str, Any]]:
    """Return every distinct recorded recursion snapshot."""
    return [
        event.metadata["recursion"]
        for event in result.events
        if event.metadata.get("recursion")
    ]


def _all_subarrays(result: Any) -> list[dict[str, Any]]:
    """Return every sub-array snapshot across the recorded recursion states."""
    subarrays: list[dict[str, Any]] = []
    for state in _recursion_states(result):
        for subarray in state.get("subarrays", []):
            if subarray not in subarrays:
                subarrays.append(subarray)
    return subarrays


# ---------------------------------------------------------------------------
# 1. Call stack frames
# ---------------------------------------------------------------------------


def test_recursive_calls_record_function_arguments_and_depth() -> None:
    """Verify CALL events capture recursive frames, arguments, and depth."""
    result = execute_code(FACTORIAL_CODE, 3)

    assert result.is_success is True
    assert result.final_array == 6

    call_events = _events(result, EventType.CALL)
    assert len(call_events) == 3
    assert [event.metadata["call"]["function"] for event in call_events] == [
        "factorial",
        "factorial",
        "factorial",
    ]
    assert [event.metadata["call"]["depth"] for event in call_events] == [0, 1, 2]
    assert [event.metadata["call"]["args"]["n"] for event in call_events] == [3, 2, 1]
    assert all(event.line_number is not None for event in call_events)


def test_line_events_carry_the_active_call_stack() -> None:
    """Verify active frames and arguments are attached while recursion is running."""
    result = execute_code(FACTORIAL_CODE, 3)

    deepest_events = [
        event
        for event in result.events
        if event.metadata.get("recursion", {}).get("active_depth") == 2
    ]
    assert deepest_events

    state = deepest_events[0].metadata["recursion"]
    assert [frame["depth"] for frame in state["frames"]] == [0, 1, 2]
    assert [frame["function"] for frame in state["frames"]] == [
        "factorial",
        "factorial",
        "factorial",
    ]
    assert [frame["args"]["n"] for frame in state["frames"]] == [3, 2, 1]
    assert state["active_function"] == "factorial"
    assert state["active_depth"] == 2


# ---------------------------------------------------------------------------
# 2. Returns and returned structures
# ---------------------------------------------------------------------------


def test_returns_record_values_depth_and_chosen_locals() -> None:
    """Verify RETURN events capture values, depths, and chosen result locals."""
    result = execute_code(SUM_CODE, [1, 2, 3])

    assert result.is_success is True
    assert result.final_array == 6

    call_event = _events(result, EventType.CALL)[0]
    assert call_event.metadata["call"]["args"] == {"nums": [1, 2, 3]}

    return_events = _events(result, EventType.RETURN)
    assert len(return_events) == 1
    returned = return_events[0].metadata["return"]
    assert returned["function"] == "sum_list"
    assert returned["value"] == 6
    assert returned["depth"] == 0
    assert returned["chosen"]["res"] == 6


def test_final_return_structure_is_attached_to_the_last_step() -> None:
    """Verify the outermost return is exposed as the chosen returned structure."""
    result = execute_code(FACTORIAL_CODE, 3)

    last_event = result.events[-1]
    assert last_event.event_type == EventType.RETURN
    state = last_event.metadata["recursion"]
    assert state["return_structure"] == 6
    assert state["last_return"]["function"] == "factorial"
    assert state["last_return"]["value"] == 6

    later_states = [
        event.metadata["recursion"]
        for event in result.events
        if event.metadata.get("recursion", {}).get("return_structure") is not None
    ]
    assert later_states
    assert later_states[-1]["return_structure"] == 6


# ---------------------------------------------------------------------------
# 3. Intermediate sub-arrays
# ---------------------------------------------------------------------------


def test_slices_and_recursive_arguments_record_intermediate_subarrays() -> None:
    """Verify list slices and recursive list parameters are captured."""
    result = execute_code(MERGE_SORT_CODE, [3, 1, 2])

    assert result.is_success is True
    assert result.final_array == [1, 2, 3]

    subarrays = _all_subarrays(result)
    assert any(subarray["source"] == "slice" for subarray in subarrays)
    assert any(subarray["source"] == "argument" for subarray in subarrays)

    slice_items = {
        tuple(subarray["items"])
        for subarray in subarrays
        if subarray["source"] == "slice"
    }
    assert (3,) in slice_items or (1,) in slice_items or (2,) in slice_items

    argument_items = {
        tuple(subarray["items"])
        for subarray in subarrays
        if subarray["source"] == "argument"
    }
    assert (3,) in argument_items or (1, 2) in argument_items
    assert (3, 1, 2) not in argument_items


def test_subarray_snapshots_include_labels_bounds_and_depth() -> None:
    """Verify sub-array snapshots carry display labels and recursion depth."""
    result = execute_code(MERGE_SORT_CODE, [3, 1, 2])

    slice_subarray = next(
        subarray
        for subarray in _all_subarrays(result)
        if subarray["source"] == "slice"
    )
    assert slice_subarray["name"] == "arr"
    assert slice_subarray["label"].startswith("arr[")
    assert isinstance(slice_subarray["items"], list)
    assert slice_subarray["size"] == len(slice_subarray["items"])
    assert slice_subarray["depth"] >= 0
    assert any(
        subarray["source"] == "slice" and subarray["depth"] >= 1
        for subarray in _all_subarrays(result)
    )
    assert slice_subarray["line"] is not None

    argument_subarray = next(
        subarray
        for subarray in _all_subarrays(result)
        if subarray["source"] == "argument"
    )
    assert argument_subarray["name"] == "arr"
    assert argument_subarray["items"] in ([3], [1, 2], [1], [2])
    assert argument_subarray["depth"] >= 1


# ---------------------------------------------------------------------------
# 4. Event model
# ---------------------------------------------------------------------------


def test_call_and_return_event_serialization_roundtrip() -> None:
    """Verify recursion metadata survives JSON serialization."""
    assert EventType.CALL.value == "CALL"
    assert EventType.RETURN.value == "RETURN"

    event = ExecutionEvent(
        step_index=5,
        event_type=EventType.CALL,
        line_number=2,
        metadata={
            "recursion": {
                "frames": [
                    {
                        "function": "merge_sort",
                        "depth": 1,
                        "args": {"arr": [1, 2]},
                        "line": 2,
                        "returning": False,
                        "return_value": None,
                        "chosen": {},
                    }
                ],
                "active_function": "merge_sort",
                "active_depth": 1,
                "subarrays": [
                    {
                        "name": "arr",
                        "label": "arr[0:1]",
                        "items": [1],
                        "size": 1,
                        "start": 0,
                        "stop": 1,
                        "step": None,
                        "source": "slice",
                        "depth": 1,
                        "line": 4,
                    }
                ],
                "return_structure": None,
                "last_return": None,
            }
        },
    )

    restored = ExecutionEvent.from_dict(json.loads(json.dumps(event.to_dict())))

    assert restored.event_type == EventType.CALL
    assert restored.metadata["recursion"]["frames"][0]["args"]["arr"] == [1, 2]
    assert restored.metadata["recursion"]["subarrays"][0]["items"] == [1]
    assert restored.metadata["recursion"]["active_depth"] == 1
