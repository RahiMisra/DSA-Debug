"""Execution result and error models for Trace."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ExecutionStatus(str, Enum):
    """Status outcomes for user code execution."""

    SUCCESS = "SUCCESS"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class ExecutionError:
    """Details regarding an error encountered during execution."""

    error_type: str
    message: str
    line_number: Optional[int] = None
    column_offset: Optional[int] = None
    traceback_text: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the error to a JSON-serializable dictionary."""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "line_number": self.line_number,
            "column_offset": self.column_offset,
            "traceback_text": self.traceback_text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionError:
        """Create an ExecutionError from a dictionary."""
        return cls(
            error_type=data.get("error_type", "UnknownError"),
            message=data.get("message", ""),
            line_number=data.get("line_number"),
            column_offset=data.get("column_offset"),
            traceback_text=data.get("traceback_text"),
        )


@dataclass
class ExecutionResult:
    """Represents the complete result of executing user code."""

    status: ExecutionStatus
    final_array: Optional[list[int]] = None
    error: Optional[ExecutionError] = None
    execution_time_ms: float = 0.0
    events: list[Any] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """Return True if execution completed successfully."""
        return self.status == ExecutionStatus.SUCCESS

    @property
    def has_error(self) -> bool:
        """Return True if execution encountered any error or timeout."""
        return self.status != ExecutionStatus.SUCCESS or self.error is not None

    def to_dict(self) -> dict[str, Any]:
        """Convert the execution result to a JSON-serializable dictionary."""
        serialized_events = []
        for event in self.events:
            if hasattr(event, "to_dict") and callable(event.to_dict):
                serialized_events.append(event.to_dict())
            elif isinstance(event, dict):
                serialized_events.append(event)
            else:
                serialized_events.append(str(event))

        return {
            "status": self.status.value,
            "final_array": self.final_array,
            "error": self.error.to_dict() if self.error else None,
            "execution_time_ms": self.execution_time_ms,
            "events": serialized_events,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionResult:
        """Create an ExecutionResult from a dictionary."""
        status_val = data.get("status", ExecutionStatus.INTERNAL_ERROR.value)
        status = ExecutionStatus(status_val) if isinstance(status_val, str) else status_val

        error_data = data.get("error")
        error = ExecutionError.from_dict(error_data) if error_data else None

        return cls(
            status=status,
            final_array=data.get("final_array"),
            error=error,
            execution_time_ms=data.get("execution_time_ms", 0.0),
            events=data.get("events", []),
        )

    def to_json(self) -> str:
        """Serialize the execution result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> ExecutionResult:
        """Deserialize an ExecutionResult from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def success(
        cls,
        final_array: list[int],
        execution_time_ms: float = 0.0,
        events: Optional[list[Any]] = None,
    ) -> ExecutionResult:
        """Convenience constructor for a successful execution."""
        return cls(
            status=ExecutionStatus.SUCCESS,
            final_array=final_array,
            error=None,
            execution_time_ms=execution_time_ms,
            events=events if events is not None else [],
        )

    @classmethod
    def syntax_error(
        cls,
        message: str,
        line_number: Optional[int] = None,
        column_offset: Optional[int] = None,
        traceback_text: Optional[str] = None,
    ) -> ExecutionResult:
        """Convenience constructor for syntax errors."""
        return cls(
            status=ExecutionStatus.SYNTAX_ERROR,
            final_array=None,
            error=ExecutionError(
                error_type="SyntaxError",
                message=message,
                line_number=line_number,
                column_offset=column_offset,
                traceback_text=traceback_text,
            ),
        )

    @classmethod
    def runtime_error(
        cls,
        error_type: str,
        message: str,
        line_number: Optional[int] = None,
        traceback_text: Optional[str] = None,
        partial_array: Optional[list[int]] = None,
        events: Optional[list[Any]] = None,
    ) -> ExecutionResult:
        """Convenience constructor for runtime errors."""
        return cls(
            status=ExecutionStatus.RUNTIME_ERROR,
            final_array=partial_array,
            error=ExecutionError(
                error_type=error_type,
                message=message,
                line_number=line_number,
                traceback_text=traceback_text,
            ),
            events=events if events is not None else [],
        )

    @classmethod
    def timeout(
        cls,
        timeout_seconds: float,
        partial_array: Optional[list[int]] = None,
        events: Optional[list[Any]] = None,
    ) -> ExecutionResult:
        """Convenience constructor for execution timeouts."""
        return cls(
            status=ExecutionStatus.TIMEOUT,
            final_array=partial_array,
            error=ExecutionError(
                error_type="TimeoutError",
                message=f"Execution exceeded time limit of {timeout_seconds:.1f} seconds",
            ),
            events=events if events is not None else [],
        )

    @classmethod
    def internal_error(
        cls,
        message: str,
        traceback_text: Optional[str] = None,
    ) -> ExecutionResult:
        """Convenience constructor for internal execution errors."""
        return cls(
            status=ExecutionStatus.INTERNAL_ERROR,
            final_array=None,
            error=ExecutionError(
                error_type="InternalError",
                message=message,
                traceback_text=traceback_text,
            ),
        )
