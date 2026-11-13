"""Execution engine for Trace."""

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory
from src.execution.instrumentation import TraceInstrumenter, instrument_code
from src.execution.result import ExecutionError, ExecutionResult, ExecutionStatus
from src.execution.runner import CodeRunner, execute_code
from src.execution.tracer import ExecutionTracer

__all__ = [
    "ExecutionStatus",
    "ExecutionError",
    "ExecutionResult",
    "CodeRunner",
    "execute_code",
    "EventType",
    "ExecutionEvent",
    "ExecutionHistory",
    "TraceInstrumenter",
    "instrument_code",
    "ExecutionTracer",
]
