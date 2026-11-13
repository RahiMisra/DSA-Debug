"""Execution tracer for recording algorithm execution events."""

from __future__ import annotations

import sys
import types
from typing import Any, Optional

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory


def evaluate_comparison(left_val: Any, right_val: Any, op_str: str) -> bool:
    """Evaluate comparison operator between two values."""
    if op_str == "<":
        return bool(left_val < right_val)
    elif op_str == "<=":
        return bool(left_val <= right_val)
    elif op_str == ">":
        return bool(left_val > right_val)
    elif op_str == ">=":
        return bool(left_val >= right_val)
    elif op_str == "==":
        return bool(left_val == right_val)
    elif op_str == "!=":
        return bool(left_val != right_val)
    elif op_str == "is":
        return bool(left_val is right_val)
    elif op_str == "is not":
        return bool(left_val is not right_val)
    elif op_str == "in":
        return bool(left_val in right_val)
    elif op_str == "not in":
        return bool(left_val not in right_val)
    raise ValueError(f"Unsupported comparison operator: {op_str}")


class ExecutionTracer:
    """Records line executions, comparisons, element accesses, and mutations."""

    def __init__(
        self,
        initial_array: list[int],
        target_filename: str = "<user_code>",
    ) -> None:
        self.target_filename = target_filename
        self.tracked_array = list(initial_array)
        self.history = ExecutionHistory(initial_array=list(initial_array))
        self.current_line: Optional[int] = None
        self._installed = False

    def bind_array(self, target_array: list[int]) -> None:
        """Bind the active mutable array passed into the user function."""
        self.tracked_array = target_array

    def get_array_snapshot(self) -> list[int]:
        """Return a copy of the current array state."""
        return list(self.tracked_array)

    def trace_line(self, lineno: int) -> ExecutionEvent:
        """Record line-level execution."""
        self.current_line = lineno
        return self.history.add_event(
            event_type=EventType.LINE,
            line_number=lineno,
            array_state=self.get_array_snapshot(),
        )

    def trace_compare(
        self,
        left_val: Any,
        right_val: Any,
        op_str: str,
        lineno: Optional[int] = None,
        left_arr: Any = None,
        left_idx: Any = None,
        right_arr: Any = None,
        right_idx: Any = None,
    ) -> bool:
        """Evaluate and record a comparison event."""
        effective_line = lineno if lineno is not None else self.current_line
        result = evaluate_comparison(left_val, right_val, op_str)

        indices: list[int] = []
        if isinstance(left_idx, int) and left_arr is not None:
            indices.append(left_idx)
        if isinstance(right_idx, int) and right_arr is not None:
            indices.append(right_idx)

        self.history.add_event(
            event_type=EventType.COMPARISON,
            line_number=effective_line,
            array_state=self.get_array_snapshot(),
            indices=indices,
            values=[left_val, right_val],
            metadata={
                "op": op_str,
                "result": result,
                "left_val": left_val,
                "right_val": right_val,
            },
        )
        return result

    def trace_swap(
        self,
        arr1: list[Any],
        idx1: int,
        arr2: list[Any],
        idx2: int,
        lineno: Optional[int] = None,
    ) -> None:
        """Perform and record an element swap between arr1[idx1] and arr2[idx2]."""
        effective_line = lineno if lineno is not None else self.current_line
        val1 = arr1[idx1]
        val2 = arr2[idx2]

        arr1[idx1], arr2[idx2] = val2, val1

        indices = [idx1, idx2] if arr1 is arr2 else [idx1]
        self.history.add_event(
            event_type=EventType.SWAP,
            line_number=effective_line,
            array_state=self.get_array_snapshot(),
            indices=indices,
            values=[arr1[idx1], arr2[idx2]],
            metadata={
                "idx_a": idx1,
                "idx_b": idx2,
                "val_before": [val1, val2],
                "val_after": [val2, val1],
            },
        )

    def trace_write(
        self,
        arr: list[Any],
        idx: int,
        val: Any,
        lineno: Optional[int] = None,
    ) -> Any:
        """Perform and record an array write arr[idx] = val."""
        effective_line = lineno if lineno is not None else self.current_line
        prev_val = arr[idx] if (0 <= idx < len(arr)) else None
        arr[idx] = val

        self.history.add_event(
            event_type=EventType.WRITE,
            line_number=effective_line,
            array_state=self.get_array_snapshot(),
            indices=[idx],
            values=[val],
            metadata={
                "index": idx,
                "value": val,
                "previous_value": prev_val,
            },
        )
        return val

    def trace_read(
        self,
        arr: list[Any],
        idx: int,
        lineno: Optional[int] = None,
    ) -> Any:
        """Perform and record an array read arr[idx]."""
        effective_line = lineno if lineno is not None else self.current_line
        val = arr[idx]

        # Only record read event if reading from a list (e.g. array being inspected)
        if isinstance(arr, list):
            self.history.add_event(
                event_type=EventType.READ,
                line_number=effective_line,
                array_state=self.get_array_snapshot(),
                indices=[idx],
                values=[val],
                metadata={"index": idx, "value": val},
            )
        return val

    def _trace_dispatch(self, frame: types.FrameType, event: str, arg: Any) -> Any:
        """Trace dispatch function invoked by sys.settrace."""
        if frame.f_code.co_filename == self.target_filename:
            if event == "line":
                self.trace_line(frame.f_lineno)
        return self._trace_dispatch

    def install(self) -> None:
        """Install sys.settrace hook for line tracing."""
        if not self._installed:
            sys.settrace(self._trace_dispatch)
            self._installed = True

    def uninstall(self) -> None:
        """Uninstall sys.settrace hook."""
        if self._installed:
            sys.settrace(None)
            self._installed = False
