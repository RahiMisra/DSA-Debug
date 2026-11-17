"""Tests for auxiliary hash map and set tracing (T032)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict, deque
from typing import Any

from src.execution.events import EventType, ExecutionEvent
from src.execution.tracer import (
    classify_auxiliary_hash,
    extract_auxiliary_hash_state,
    extract_auxiliary_state,
)
from src.execution.worker import execute_code


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

LOOKUP_CODE = """
def lookup_total(nums):
    table = {1: 10, 2: 20}
    total = 0
    for n in nums:
        total += table[n]
    return total
"""

SET_CODE = """
def unique(nums):
    seen = set()
    for n in nums:
        if n not in seen:
            seen.add(n)
    seen.remove(nums[0])
    return len(seen)
"""


def _container_events(result: Any) -> list[ExecutionEvent]:
    """Return only auxiliary container operation events."""
    return [
        event
        for event in result.events
        if event.get("event_type") == EventType.CONTAINER.value
    ]


def _hash_operations(result: Any) -> list[dict[str, Any]]:
    """Return hash container operations in execution order."""
    return [
        event["metadata"]["container_op"]
        for event in _container_events(result)
        if event["metadata"].get("container_op", {}).get("kind") in ("map", "set")
    ]


def _membership_events(result: Any) -> list[ExecutionEvent]:
    """Return comparison events that recorded a hash membership lookup."""
    return [
        event
        for event in result.events
        if event.get("event_type") == EventType.COMPARISON.value
        and event["metadata"].get("container_op", {}).get("action") == "lookup"
    ]


# ---------------------------------------------------------------------------
# 1. Classification and extraction
# ---------------------------------------------------------------------------


def test_classify_hash_maps_by_name_and_type() -> None:
    """Verify map names are recognized for dictionaries and dict subclasses."""
    assert classify_auxiliary_hash("freq", {}) == "map"
    assert classify_auxiliary_hash("counts", {1: 2}) == "map"
    assert classify_auxiliary_hash("memo", defaultdict(int)) == "map"
    assert classify_auxiliary_hash("counter", Counter("aab")) == "map"
    assert classify_auxiliary_hash("dp", {}) == "map"
    assert classify_auxiliary_hash("lookup_table", {}) == "map"
    assert classify_auxiliary_hash("word_count", {}) == "map"
    assert classify_auxiliary_hash("charFreq", {}) == "map"

    assert classify_auxiliary_hash("count", 3) is None
    assert classify_auxiliary_hash("nums", {1: 2}) is None


def test_classify_hash_sets_and_type_overrides() -> None:
    """Verify set names are recognized and container type decides map vs set."""
    assert classify_auxiliary_hash("seen", set()) == "set"
    assert classify_auxiliary_hash("unique", {"a"}) == "set"
    assert classify_auxiliary_hash("visited", set()) == "set"
    assert classify_auxiliary_hash("visited", {}) == "map"

    assert classify_auxiliary_hash("visited", [True, False]) is None
    assert classify_auxiliary_hash("items", {"a"}) is None


def test_extract_hash_state_snapshots() -> None:
    """Verify maps preserve entries and sets render deterministic membership."""
    state = extract_auxiliary_hash_state(
        {
            "freq": {"a": 2, "b": 1},
            "seen": {"b", "a"},
            "nums": [1, 2],
        }
    )

    assert state is not None
    assert len(state["maps"]) == 1
    assert len(state["sets"]) == 1

    freq = state["maps"][0]
    assert freq["name"] == "freq"
    assert freq["kind"] == "map"
    assert freq["size"] == 2
    assert freq["entries"] == [
        {"key": "a", "value": 2},
        {"key": "b", "value": 1},
    ]

    seen = state["sets"][0]
    assert seen["name"] == "seen"
    assert seen["kind"] == "set"
    assert seen["size"] == 2
    assert seen["items"] == ["a", "b"]


def test_extract_hash_state_without_candidates() -> None:
    """Verify ordinary mappings and sets are not surfaced."""
    assert extract_auxiliary_hash_state({}) is None
    assert extract_auxiliary_hash_state({"nums": [1, 2]}) is None
    assert extract_auxiliary_hash_state({"config": {"a": 1}}) is None


def test_extract_combined_auxiliary_state() -> None:
    """Verify linear and hash containers share one auxiliary snapshot."""
    state = extract_auxiliary_state(
        {
            "stack": [1, 2],
            "queue": deque([3]),
            "freq": {1: 1},
            "seen": {1},
        }
    )

    assert state is not None
    assert state["stacks"][0]["name"] == "stack"
    assert state["queues"][0]["name"] == "queue"
    assert state["maps"][0]["name"] == "freq"
    assert state["sets"][0]["name"] == "seen"


def test_hash_container_event_serialization_roundtrip() -> None:
    """Verify map/set metadata survives JSON serialization."""
    event = ExecutionEvent(
        step_index=4,
        event_type=EventType.CONTAINER,
        line_number=6,
        metadata={
            "auxiliary": {
                "stacks": [],
                "queues": [],
                "maps": [
                    {
                        "name": "freq",
                        "kind": "map",
                        "entries": [{"key": "a", "value": 2}],
                        "size": 1,
                    }
                ],
                "sets": [
                    {"name": "seen", "kind": "set", "items": ["a"], "size": 1}
                ],
            },
            "container_op": {
                "name": "freq",
                "kind": "map",
                "action": "insert",
                "key": "a",
                "value": 2,
            },
        },
    )

    restored = ExecutionEvent.from_dict(json.loads(json.dumps(event.to_dict())))

    assert restored.event_type == EventType.CONTAINER
    assert restored.metadata["container_op"]["key"] == "a"
    assert restored.metadata["auxiliary"]["maps"][0]["entries"][0]["value"] == 2
    assert restored.metadata["auxiliary"]["sets"][0]["items"] == ["a"]


# ---------------------------------------------------------------------------
# 2. Dictionary insert, update, lookup, and membership
# ---------------------------------------------------------------------------


def test_dict_insert_and_update_operations() -> None:
    """Verify dict writes distinguish inserts from updates."""
    result = execute_code(COUNT_CODE, [1, 2, 1])

    assert result.is_success is True
    assert result.final_array == 2

    operations = _hash_operations(result)
    assert [(op["action"], op["key"], op["value"]) for op in operations] == [
        ("insert", 1, 1),
        ("insert", 2, 1),
        ("update", 1, 2),
    ]
    assert operations[-1]["previous_value"] == 1

    snapshots = [
        event["metadata"]["auxiliary"]["maps"][0]
        for event in _container_events(result)
        if event["metadata"].get("container_op", {}).get("kind") == "map"
    ]
    assert snapshots[0]["entries"] == [{"key": 1, "value": 1}]
    assert snapshots[-1]["entries"] == [
        {"key": 1, "value": 2},
        {"key": 2, "value": 1},
    ]


def test_dict_membership_comparisons_record_lookups() -> None:
    """Verify ``k in d`` comparisons mark the key as an active lookup."""
    result = execute_code(COUNT_CODE, [1, 2, 1])

    lookups = _membership_events(result)
    assert lookups
    assert all(
        event["metadata"]["container_op"]["kind"] == "map"
        for event in lookups
    )
    assert [event["metadata"]["container_op"]["key"] for event in lookups] == [
        1,
        2,
        1,
    ]
    assert [event["metadata"]["container_op"]["present"] for event in lookups] == [
        False,
        False,
        True,
    ]


def test_dict_subscript_lookup_operations() -> None:
    """Verify dict reads record lookup events with key, value, and snapshots."""
    result = execute_code(LOOKUP_CODE, [1, 2, 1])

    assert result.is_success is True
    assert result.final_array == 40

    operations = _hash_operations(result)
    assert [(op["action"], op["key"], op["value"]) for op in operations] == [
        ("lookup", 1, 10),
        ("lookup", 2, 20),
        ("lookup", 1, 10),
    ]
    last_snapshot = [
        event["metadata"]["auxiliary"]["maps"][0]
        for event in _container_events(result)
        if event["metadata"].get("container_op", {}).get("kind") == "map"
    ][-1]
    assert last_snapshot["entries"] == [
        {"key": 1, "value": 10},
        {"key": 2, "value": 20},
    ]


# ---------------------------------------------------------------------------
# 3. Set add, remove, and membership
# ---------------------------------------------------------------------------


def test_set_add_and_remove_operations() -> None:
    """Verify set mutations record membership snapshots."""
    result = execute_code(SET_CODE, [1, 2, 1])

    assert result.is_success is True
    assert result.final_array == 1

    operations = _hash_operations(result)
    assert [(op["action"], op["key"]) for op in operations] == [
        ("add", 1),
        ("add", 2),
        ("remove", 1),
    ]
    assert {op["kind"] for op in operations} == {"set"}

    snapshots = [
        event["metadata"]["auxiliary"]["sets"][0]
        for event in _container_events(result)
        if event["metadata"].get("container_op", {}).get("kind") == "set"
    ]
    assert snapshots[0]["items"] == [1]
    assert snapshots[1]["items"] == [1, 2]
    assert snapshots[2]["items"] == [2]


def test_set_membership_comparisons_record_lookups() -> None:
    """Verify ``x in s`` and ``x not in s`` mark set membership lookups."""
    result = execute_code(SET_CODE, [1, 2, 1])

    lookups = _membership_events(result)
    assert lookups
    assert all(
        event["metadata"]["container_op"]["kind"] == "set"
        for event in lookups
    )
    assert [event["metadata"]["container_op"]["key"] for event in lookups] == [
        1,
        2,
        1,
    ]
    assert [event["metadata"]["container_op"]["present"] for event in lookups] == [
        False,
        False,
        True,
    ]


# ---------------------------------------------------------------------------
# 4. No false positives
# ---------------------------------------------------------------------------


def test_graph_adjacency_dicts_are_not_surfaced_as_auxiliary() -> None:
    """Verify ordinary graph maps and result dictionaries stay hidden."""
    code = """
def adjacency(nums):
    graph = {0: [1], 1: [0]}
    result = {}
    result["size"] = len(graph)
    return graph[0][0] + result["size"]
"""
    result = execute_code(code, [0])

    assert result.is_success is True
    assert _container_events(result) == []
    assert all(
        not event.metadata.get("auxiliary", {}).get("maps")
        and not event.metadata.get("auxiliary", {}).get("sets")
        for event in result.events
    )
