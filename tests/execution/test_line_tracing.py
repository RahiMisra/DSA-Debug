"""Tests for line-level execution tracing (T008)."""

from src.execution.events import EventType
from src.execution.worker import execute_code


def test_line_tracing_captures_executed_lines_in_order() -> None:
    """Verify that source-code lines are recorded in chronological order."""
    code = """def simple(arr):
    x = 10
    y = 20
    if len(arr) > 0:
        z = x + y
"""
    result = execute_code(code, [1])
    assert result.is_success is True

    line_events = [e for e in result.events if e.get("event_type") == EventType.LINE.value]
    assert len(line_events) >= 4

    # Lines should correspond to lines 2, 3, 4, 5
    recorded_lines = [e["line_number"] for e in line_events]
    assert 2 in recorded_lines
    assert 3 in recorded_lines
    assert 4 in recorded_lines
    assert 5 in recorded_lines

    # Verify execution order: line 2 executed before line 3, then 4, then 5
    idx_line2 = recorded_lines.index(2)
    idx_line3 = recorded_lines.index(3)
    idx_line4 = recorded_lines.index(4)
    idx_line5 = recorded_lines.index(5)
    assert idx_line2 < idx_line3 < idx_line4 < idx_line5


def test_line_tracing_in_loops() -> None:
    """Verify that lines inside loops are recorded for each iteration."""
    code = """def count_loops(arr):
    total = 0
    for i in range(len(arr)):
        total += 1
"""
    result = execute_code(code, [10, 20, 30])
    assert result.is_success is True

    line_events = [e for e in result.events if e.get("event_type") == EventType.LINE.value]
    loop_body_lines = [e for e in line_events if e["line_number"] == 4]

    # Body executed 3 times for a 3-element list
    assert len(loop_body_lines) == 3


def test_line_tracing_independent_of_ui() -> None:
    """Verify line tracing works purely within the execution engine."""
    code = """def test_func(arr):
    arr.reverse()
"""
    result = execute_code(code, [1, 2])
    assert result.is_success is True
    assert len(result.events) > 0
    line_events = [
        event for event in result.events if event.event_type == EventType.LINE
    ]
    assert line_events[0]["line_number"] == 2
