"""Tests for operation highlighting and event processing (T013)."""

from src.execution.events import EventType, ExecutionEvent
from src.visualization.array_state import ElementHighlight
from src.visualization.event_processor import EventProcessor


def test_comparison_highlighting() -> None:
    """Verify comparisons highlight affected indices as COMPARING."""
    event = ExecutionEvent(
        step_index=1,
        event_type=EventType.COMPARISON,
        line_number=4,
        array_state=[5, 2, 8],
        indices=[0, 1],
        values=[5, 2],
    )
    state = EventProcessor.process_event(event)
    assert state.elements[0].highlight == ElementHighlight.COMPARING
    assert state.elements[1].highlight == ElementHighlight.COMPARING
    assert state.elements[2].highlight == ElementHighlight.DEFAULT


def test_swap_highlighting() -> None:
    """Verify swaps highlight swapped indices as SWAPPING."""
    event = ExecutionEvent(
        step_index=2,
        event_type=EventType.SWAP,
        line_number=5,
        array_state=[2, 5, 8],
        indices=[0, 1],
        values=[2, 5],
    )
    state = EventProcessor.process_event(event)
    assert state.elements[0].highlight == ElementHighlight.SWAPPING
    assert state.elements[1].highlight == ElementHighlight.SWAPPING
    assert state.elements[2].highlight == ElementHighlight.DEFAULT


def test_write_and_read_highlighting() -> None:
    """Verify writes and reads produce WRITING and READING highlights."""
    write_ev = ExecutionEvent(
        step_index=3,
        event_type=EventType.WRITE,
        line_number=6,
        array_state=[2, 99, 8],
        indices=[1],
        values=[99],
    )
    w_state = EventProcessor.process_event(write_ev)
    assert w_state.elements[1].highlight == ElementHighlight.WRITING

    read_ev = ExecutionEvent(
        step_index=4,
        event_type=EventType.READ,
        line_number=7,
        array_state=[2, 99, 8],
        indices=[2],
        values=[8],
    )
    r_state = EventProcessor.process_event(read_ev)
    assert r_state.elements[2].highlight == ElementHighlight.READING


def test_line_event_clears_highlights() -> None:
    """Verify regular line execution events reset active highlights."""
    event = ExecutionEvent(
        step_index=5,
        event_type=EventType.LINE,
        line_number=8,
        array_state=[1, 2, 3],
    )
    state = EventProcessor.process_event(event)
    for elem in state.elements:
        assert elem.highlight == ElementHighlight.DEFAULT
