"""Tests for ExecutionHistory model and step reconstruction (T011)."""

import pytest
from src.execution.events import EventType, ExecutionHistory
from src.execution.runner import CodeRunner


def test_history_event_ordering_and_initial_state() -> None:
    """Verify history maintains chronological event order and preserves initial array state."""
    history = ExecutionHistory(initial_array=[5, 3, 1])

    history.add_event(EventType.LINE, line_number=1, array_state=[5, 3, 1])
    history.add_event(
        EventType.COMPARISON,
        line_number=2,
        array_state=[5, 3, 1],
        indices=[0, 1],
        values=[5, 3],
    )
    history.add_event(
        EventType.SWAP,
        line_number=3,
        array_state=[3, 5, 1],
        indices=[0, 1],
        values=[3, 5],
    )

    assert len(history) == 3
    assert history.initial_array == [5, 3, 1]

    # Verify event ordering
    assert history[0].event_type == EventType.LINE
    assert history[1].event_type == EventType.COMPARISON
    assert history[2].event_type == EventType.SWAP


def test_history_step_retrieval_and_boundaries() -> None:
    """Verify retrieving steps and out-of-bounds error handling."""
    history = ExecutionHistory(initial_array=[10, 20])
    history.add_event(EventType.LINE, line_number=1, array_state=[10, 20])
    history.add_event(EventType.WRITE, line_number=2, array_state=[10, 99], indices=[1], values=[99])

    # Index -1 returns initial array
    assert history.get_array_at_step(-1) == [10, 20]

    # Step 0
    step0 = history.get_step(0)
    assert step0.event_type == EventType.LINE
    assert history.get_array_at_step(0) == [10, 20]

    # Step 1
    step1 = history.get_step(1)
    assert step1.event_type == EventType.WRITE
    assert history.get_array_at_step(1) == [10, 99]

    # Out of bounds
    with pytest.raises(IndexError):
        history.get_step(2)
    with pytest.raises(IndexError):
        history.get_array_at_step(5)


def test_history_json_serialization() -> None:
    """Verify full ExecutionHistory serialization and deserialization."""
    history = ExecutionHistory(initial_array=[4, 2])
    history.add_event(EventType.LINE, line_number=1, array_state=[4, 2])
    history.add_event(
        EventType.SWAP,
        line_number=2,
        array_state=[2, 4],
        indices=[0, 1],
        values=[2, 4],
        metadata={"op": "swap"},
    )

    json_str = history.to_json()
    restored = ExecutionHistory.from_json(json_str)

    assert restored.initial_array == [4, 2]
    assert len(restored) == 2
    assert restored[0].event_type == EventType.LINE
    assert restored[1].event_type == EventType.SWAP
    assert restored.get_array_at_step(1) == [2, 4]


def test_history_reconstruction_from_runner_execution() -> None:
    """Verify that subprocess execution produces a complete ExecutionHistory."""
    runner = CodeRunner()
    code = """def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
"""
    initial = [4, 3, 2, 1]
    result = runner.run(code, initial)

    assert result.is_success is True
    assert result.final_array == [1, 2, 3, 4]

    # Reconstruct ExecutionHistory from the result events
    history = ExecutionHistory.from_dict({
        "initial_array": initial,
        "events": result.events,
    })

    assert len(history) > 0
    # Step -1 gives initial array
    assert history.get_array_at_step(-1) == [4, 3, 2, 1]
    # Final step gives sorted array
    assert history.get_array_at_step(len(history) - 1) == [1, 2, 3, 4]

    # Every step's array state is accessible and consistent
    for step_idx in range(len(history)):
        arr_state = history.get_array_at_step(step_idx)
        assert len(arr_state) == 4
