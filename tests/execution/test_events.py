"""Unit tests for ExecutionEvent models (T007)."""

import json
from src.execution.events import EventType, ExecutionEvent


def test_event_types_defined() -> None:
    """Verify all required EventType enum values exist."""
    assert EventType.LINE.value == "LINE"
    assert EventType.COMPARISON.value == "COMPARISON"
    assert EventType.SWAP.value == "SWAP"
    assert EventType.WRITE.value == "WRITE"
    assert EventType.READ.value == "READ"


def test_execution_event_creation_and_defaults() -> None:
    """Verify creating an ExecutionEvent with default and custom values."""
    event = ExecutionEvent(
        step_index=0,
        event_type=EventType.LINE,
        line_number=5,
        array_state=[3, 1, 2],
    )
    assert event.step_index == 0
    assert event.event_type == EventType.LINE
    assert event.line_number == 5
    assert event.array_state == [3, 1, 2]
    assert event.indices == []
    assert event.values == []
    assert event.metadata == {}


def test_execution_event_serialization_roundtrip() -> None:
    """Verify to_dict and from_dict roundtrip."""
    original = ExecutionEvent(
        step_index=4,
        event_type=EventType.COMPARISON,
        line_number=10,
        array_state=[1, 4, 3],
        indices=[1, 2],
        values=[4, 3],
        metadata={"op": ">", "result": True},
    )
    data = original.to_dict()
    assert data["step_index"] == 4
    assert data["event_type"] == "COMPARISON"
    assert data["indices"] == [1, 2]
    assert data["metadata"]["op"] == ">"

    # Verify JSON serializability
    json_str = json.dumps(data)
    restored = ExecutionEvent.from_dict(json.loads(json_str))

    assert restored.step_index == original.step_index
    assert restored.event_type == original.event_type
    assert restored.line_number == original.line_number
    assert restored.array_state == original.array_state
    assert restored.indices == original.indices
    assert restored.values == original.values
    assert restored.metadata == original.metadata


def test_execution_event_swap_and_write_structure() -> None:
    """Verify swap and write events hold correct operational details."""
    swap_event = ExecutionEvent(
        step_index=2,
        event_type=EventType.SWAP,
        line_number=8,
        array_state=[1, 2],
        indices=[0, 1],
        values=[1, 2],
        metadata={"val_before": [2, 1], "val_after": [1, 2]},
    )
    assert swap_event.indices == [0, 1]
    assert swap_event.metadata["val_before"] == [2, 1]

    write_event = ExecutionEvent(
        step_index=3,
        event_type=EventType.WRITE,
        line_number=12,
        array_state=[1, 99],
        indices=[1],
        values=[99],
        metadata={"previous_value": 2},
    )
    assert write_event.indices == [1]
    assert write_event.values == [99]
    assert write_event.metadata["previous_value"] == 2
