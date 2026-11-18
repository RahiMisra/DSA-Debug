"""Execution engine for Trace."""

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory
from src.execution.instrumentation import TraceInstrumenter, instrument_code
from src.execution.models import Graph, ListNode, TreeNode
from src.execution.parsers import parse_leetcode_inputs
from src.execution.result import ExecutionError, ExecutionResult, ExecutionStatus
from src.execution.runner import CodeRunner, execute_code
from src.execution.tracer import (
    ExecutionTracer,
    classify_auxiliary_container,
    classify_auxiliary_hash,
    extract_auxiliary_hash_state,
    extract_auxiliary_linear_state,
    extract_auxiliary_state,
    extract_graph_state,
    extract_linked_list_state,
    extract_tree_state,
)

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
    "extract_linked_list_state",
    "extract_tree_state",
    "extract_graph_state",
    "classify_auxiliary_container",
    "classify_auxiliary_hash",
    "extract_auxiliary_hash_state",
    "extract_auxiliary_linear_state",
    "extract_auxiliary_state",
    "ListNode",
    "TreeNode",
    "Graph",
    "parse_leetcode_inputs",
]
