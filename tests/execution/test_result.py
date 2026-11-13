"""Unit tests for ExecutionResult and ExecutionError models."""

import json
from src.execution.result import ExecutionError, ExecutionResult, ExecutionStatus


class DummyEvent:
    """Mock event object supporting to_dict for testing event history accommodation."""

    def __init__(self, event_type: str, line: int) -> None:
        self.event_type = event_type
        self.line = line

    def to_dict(self) -> dict[str, int | str]:
        return {"event_type": self.event_type, "line": self.line}


def test_execution_status_values() -> None:
    """Verify ExecutionStatus enum members."""
    assert ExecutionStatus.SUCCESS.value == "SUCCESS"
    assert ExecutionStatus.SYNTAX_ERROR.value == "SYNTAX_ERROR"
    assert ExecutionStatus.RUNTIME_ERROR.value == "RUNTIME_ERROR"
    assert ExecutionStatus.TIMEOUT.value == "TIMEOUT"
    assert ExecutionStatus.INTERNAL_ERROR.value == "INTERNAL_ERROR"


def test_execution_error_serialization() -> None:
    """Verify ExecutionError to_dict and from_dict roundtrip."""
    error = ExecutionError(
        error_type="IndexError",
        message="list index out of range",
        line_number=12,
        column_offset=4,
        traceback_text="Traceback (most recent call last):\n  File ...",
    )
    error_dict = error.to_dict()
    assert error_dict["error_type"] == "IndexError"
    assert error_dict["line_number"] == 12

    restored = ExecutionError.from_dict(error_dict)
    assert restored.error_type == error.error_type
    assert restored.message == error.message
    assert restored.line_number == error.line_number
    assert restored.column_offset == error.column_offset
    assert restored.traceback_text == error.traceback_text


def test_execution_result_success() -> None:
    """Verify successful execution result model."""
    result = ExecutionResult.success(
        final_array=[1, 2, 3, 4],
        execution_time_ms=12.5,
    )
    assert result.is_success is True
    assert result.has_error is False
    assert result.status == ExecutionStatus.SUCCESS
    assert result.final_array == [1, 2, 3, 4]
    assert result.error is None
    assert result.execution_time_ms == 12.5
    assert result.events == []


def test_execution_result_syntax_error() -> None:
    """Verify syntax error result model."""
    result = ExecutionResult.syntax_error(
        message="invalid syntax",
        line_number=5,
        column_offset=10,
    )
    assert result.is_success is False
    assert result.has_error is True
    assert result.status == ExecutionStatus.SYNTAX_ERROR
    assert result.final_array is None
    assert result.error is not None
    assert result.error.error_type == "SyntaxError"
    assert result.error.line_number == 5
    assert result.error.column_offset == 10


def test_execution_result_runtime_error() -> None:
    """Verify runtime error result model with partial array."""
    result = ExecutionResult.runtime_error(
        error_type="ZeroDivisionError",
        message="division by zero",
        line_number=8,
        partial_array=[3, 1, 2],
    )
    assert result.is_success is False
    assert result.has_error is True
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.final_array == [3, 1, 2]
    assert result.error is not None
    assert result.error.error_type == "ZeroDivisionError"
    assert result.error.line_number == 8


def test_execution_result_timeout() -> None:
    """Verify timeout execution result model."""
    result = ExecutionResult.timeout(timeout_seconds=2.0, partial_array=[5, 4, 3])
    assert result.is_success is False
    assert result.has_error is True
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.final_array == [5, 4, 3]
    assert result.error is not None
    assert result.error.error_type == "TimeoutError"
    assert "2.0 seconds" in result.error.message


def test_execution_result_internal_error() -> None:
    """Verify internal error execution result model."""
    result = ExecutionResult.internal_error(message="Unexpected runner failure")
    assert result.is_success is False
    assert result.has_error is True
    assert result.status == ExecutionStatus.INTERNAL_ERROR
    assert result.error is not None
    assert result.error.error_type == "InternalError"
    assert result.error.message == "Unexpected runner failure"


def test_execution_result_json_serialization_roundtrip() -> None:
    """Verify JSON serialization and deserialization of ExecutionResult."""
    result = ExecutionResult.success(
        final_array=[-5, 0, 10],
        execution_time_ms=8.2,
    )
    json_str = result.to_json()
    # Confirm it is valid JSON
    parsed = json.loads(json_str)
    assert parsed["status"] == "SUCCESS"
    assert parsed["final_array"] == [-5, 0, 10]

    restored = ExecutionResult.from_json(json_str)
    assert restored.status == ExecutionStatus.SUCCESS
    assert restored.final_array == [-5, 0, 10]
    assert restored.execution_time_ms == 8.2
    assert restored.error is None


def test_accommodate_future_execution_events() -> None:
    """Verify ExecutionResult accommodates execution event history objects and dicts."""
    events = [
        DummyEvent("LINE_EXECUTION", 3),
        DummyEvent("COMPARISON", 4),
        {"event_type": "SWAP", "indices": [0, 1]},
    ]
    result = ExecutionResult.success(
        final_array=[1, 2, 3],
        execution_time_ms=15.0,
        events=events,
    )
    assert len(result.events) == 3

    # Serialize to dict / JSON
    result_dict = result.to_dict()
    assert len(result_dict["events"]) == 3
    assert result_dict["events"][0] == {"event_type": "LINE_EXECUTION", "line": 3}
    assert result_dict["events"][1] == {"event_type": "COMPARISON", "line": 4}
    assert result_dict["events"][2] == {"event_type": "SWAP", "indices": [0, 1]}

    # Roundtrip from JSON
    json_str = result.to_json()
    restored = ExecutionResult.from_json(json_str)
    assert len(restored.events) == 3
    assert restored.events[0]["event_type"] == "LINE_EXECUTION"
