"""Tests for array access and mutation tracking (T009)."""

from src.execution.events import EventType
from src.execution.worker import execute_code


def test_array_write_tracking() -> None:
    """Verify that writing to an array records WRITE events with affected index and value."""
    code = """def write_test(arr):
    arr[0] = 99
    arr[2] = 42
"""
    initial = [1, 2, 3]
    result = execute_code(code, initial)

    assert result.is_success is True
    write_events = [e for e in result.events if e.get("event_type") == EventType.WRITE.value]

    assert len(write_events) == 2

    # First write: arr[0] = 99
    assert write_events[0]["indices"] == [0]
    assert write_events[0]["values"] == [99]
    assert write_events[0]["metadata"]["previous_value"] == 1
    assert write_events[0]["array_state"] == [99, 2, 3]

    # Second write: arr[2] = 42
    assert write_events[1]["indices"] == [2]
    assert write_events[1]["values"] == [42]
    assert write_events[1]["metadata"]["previous_value"] == 3
    assert write_events[1]["array_state"] == [99, 2, 42]


def test_array_read_tracking() -> None:
    """Verify that standalone reads from the array record READ events."""
    code = """def read_test(arr):
    x = arr[1]
    y = arr[0]
"""
    result = execute_code(code, [10, 20, 30])
    assert result.is_success is True

    read_events = [e for e in result.events if e.get("event_type") == EventType.READ.value]
    assert len(read_events) == 2

    assert read_events[0]["indices"] == [1]
    assert read_events[0]["values"] == [20]

    assert read_events[1]["indices"] == [0]
    assert read_events[1]["values"] == [10]


def test_reconstruct_array_state_from_mutations() -> None:
    """Verify that array state reconstructed from recorded mutations matches final array."""
    code = """def mutate_sequence(arr):
    arr[1] = 5
    arr[0] = -1
    arr[2] = 100
"""
    initial = [0, 0, 0]
    result = execute_code(code, initial)
    assert result.is_success is True

    # Reconstruct array from initial state and write events
    reconstructed = list(initial)
    write_events = [e for e in result.events if e.get("event_type") == EventType.WRITE.value]

    for event in write_events:
        idx = event["indices"][0]
        val = event["values"][0]
        reconstructed[idx] = val
        # Check against snapshot stored in the event
        assert reconstructed == event["array_state"]

    assert reconstructed == result.final_array


def test_augmented_assignment_tracking() -> None:
    """Verify augmented assignments like arr[i] += 5 are tracked as writes."""
    code = """def aug_test(arr):
    arr[0] += 5
"""
    result = execute_code(code, [10])
    assert result.is_success is True

    writes = [e for e in result.events if e.get("event_type") == EventType.WRITE.value]
    assert len(writes) == 1
    assert writes[0]["indices"] == [0]
    assert writes[0]["values"] == [15]
    assert writes[0]["array_state"] == [15]
