"""Execution tracer for recording algorithm execution events."""

from __future__ import annotations

import sys
import types
from typing import Any, Optional

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory


LINKED_LIST_VAR_NAMES = {
    "head", "curr", "prev", "slow", "fast", "nxt", "next", "tail", "node", "p", "q", "p1", "p2", "dummy", "l1", "l2"
}

TREE_VAR_NAMES = {
    "root", "curr", "node", "p", "q", "parent", "child", "sub", "target", "leaf"
}


def extract_linked_list_state(f_locals: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract serializable linked list structure, pointer variables, and cycle state from frame locals."""
    from src.execution.models import ListNode

    list_nodes: dict[str, ListNode] = {}
    null_pointers: dict[str, None] = {}

    for k, v in f_locals.items():
        if isinstance(v, ListNode):
            list_nodes[k] = v
        elif v is None and k.lower() in LINKED_LIST_VAR_NAMES:
            null_pointers[k] = None

    if not list_nodes and not null_pointers:
        return None

    if not list_nodes:
        return {
            "nodes": [],
            "pointers": null_pointers,
            "has_cycle": False,
            "cycle_start": None,
        }

    node_id_map: dict[int, int] = {}
    assigned_nodes: list[dict[str, Any]] = []
    has_cycle = False
    cycle_start = None

    start_nodes: list[ListNode] = []
    for preferred in ("dummy", "head", "l1", "l2", "curr", "prev"):
        if preferred in list_nodes and list_nodes[preferred] not in start_nodes:
            start_nodes.append(list_nodes[preferred])
    for n in list_nodes.values():
        if n not in start_nodes:
            start_nodes.append(n)

    global_visited: set[int] = set()

    for start in start_nodes:
        curr: Optional[ListNode] = start
        path_visited: set[int] = set()
        while curr is not None:
            curr_id = id(curr)
            if curr_id in global_visited:
                if curr_id in path_visited:
                    has_cycle = True
                    cycle_start = node_id_map[curr_id]
                break

            global_visited.add(curr_id)
            path_visited.add(curr_id)

            assigned_id = len(node_id_map) + 1
            node_id_map[curr_id] = assigned_id

            next_node = getattr(curr, "next", None)
            if next_node is not None and id(next_node) in path_visited:
                has_cycle = True
                cycle_start = node_id_map[id(next_node)]
                break

            curr = next_node

    node_obj_lookup: dict[int, ListNode] = {}
    for n in start_nodes:
        c: Optional[ListNode] = n
        seen: set[int] = set()
        while c is not None and id(c) not in seen:
            seen.add(id(c))
            if id(c) in node_id_map:
                node_obj_lookup[node_id_map[id(c)]] = c
            c = getattr(c, "next", None)

    for assigned_id in sorted(node_obj_lookup.keys()):
        obj = node_obj_lookup[assigned_id]
        nxt = getattr(obj, "next", None)
        nxt_id = node_id_map.get(id(nxt)) if nxt is not None else None
        assigned_nodes.append({
            "id": assigned_id,
            "val": obj.val,
            "next": nxt_id,
        })

    pointers: dict[str, Any] = dict(null_pointers)
    for k, v in list_nodes.items():
        if id(v) in node_id_map:
            pointers[k] = node_id_map[id(v)]

    return {
        "nodes": assigned_nodes,
        "pointers": pointers,
        "has_cycle": has_cycle,
        "cycle_start": cycle_start,
    }


def extract_tree_state(f_locals: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract serializable binary tree hierarchy, child pointers, and variable references."""
    from collections import deque
    from src.execution.models import TreeNode

    tree_nodes: dict[str, TreeNode] = {}
    null_pointers: dict[str, None] = {}

    for k, v in f_locals.items():
        if isinstance(v, TreeNode):
            tree_nodes[k] = v
        elif v is None and k.lower() in TREE_VAR_NAMES:
            null_pointers[k] = None

    if not tree_nodes and not null_pointers:
        return None

    if not tree_nodes:
        return {
            "root_id": None,
            "nodes": {},
            "pointers": null_pointers,
        }

    primary_root = tree_nodes.get("root")
    if primary_root is None:
        primary_root = next(iter(tree_nodes.values()))

    node_id_map: dict[int, int] = {}
    nodes_record: dict[int, dict[str, Any]] = {}

    queue: deque[TreeNode] = deque([primary_root])
    seen: set[int] = {id(primary_root)}

    for tn in tree_nodes.values():
        if id(tn) not in seen:
            queue.append(tn)
            seen.add(id(tn))

    all_nodes: list[TreeNode] = []
    while queue:
        curr = queue.popleft()
        assigned_id = len(node_id_map) + 1
        node_id_map[id(curr)] = assigned_id
        all_nodes.append(curr)

        left = getattr(curr, "left", None)
        if left is not None and id(left) not in seen:
            seen.add(id(left))
            queue.append(left)

        right = getattr(curr, "right", None)
        if right is not None and id(right) not in seen:
            seen.add(id(right))
            queue.append(right)

    for obj in all_nodes:
        assigned_id = node_id_map[id(obj)]
        left = getattr(obj, "left", None)
        right = getattr(obj, "right", None)

        left_id = node_id_map.get(id(left)) if left is not None else None
        right_id = node_id_map.get(id(right)) if right is not None else None

        nodes_record[assigned_id] = {
            "id": assigned_id,
            "val": obj.val,
            "left": left_id,
            "right": right_id,
        }

    pointers: dict[str, Any] = dict(null_pointers)
    for k, v in tree_nodes.items():
        if id(v) in node_id_map:
            pointers[k] = node_id_map[id(v)]

    root_id = node_id_map.get(id(primary_root))

    return {
        "root_id": root_id,
        "nodes": nodes_record,
        "pointers": pointers,
    }


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
        self.current_ll_state: Optional[dict[str, Any]] = None
        self.current_tree_state: Optional[dict[str, Any]] = None

    def bind_array(self, target_array: list[int]) -> None:
        """Bind the active mutable array passed into the user function."""
        self.tracked_array = target_array

    def get_array_snapshot(self) -> list[int]:
        """Return a copy of the current array state."""
        return list(self.tracked_array)

    def trace_line(
        self,
        lineno: int,
        frame: Optional[types.FrameType] = None,
    ) -> ExecutionEvent:
        """Record line-level execution."""
        self.current_line = lineno
        metadata: dict[str, Any] = {}
        if frame is not None:
            ll_state = extract_linked_list_state(frame.f_locals)
            if ll_state is not None:
                self.current_ll_state = ll_state
            tree_state = extract_tree_state(frame.f_locals)
            if tree_state is not None:
                self.current_tree_state = tree_state

        if self.current_ll_state is not None:
            metadata["linked_list"] = self.current_ll_state
        if self.current_tree_state is not None:
            metadata["tree"] = self.current_tree_state

        return self.history.add_event(
            event_type=EventType.LINE,
            line_number=lineno,
            array_state=self.get_array_snapshot(),
            metadata=metadata,
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

        meta: dict[str, Any] = {
            "op": op_str,
            "result": result,
            "left_val": left_val,
            "right_val": right_val,
        }
        if self.current_ll_state is not None:
            meta["linked_list"] = self.current_ll_state
        if self.current_tree_state is not None:
            meta["tree"] = self.current_tree_state

        self.history.add_event(
            event_type=EventType.COMPARISON,
            line_number=effective_line,
            array_state=self.get_array_snapshot(),
            indices=indices,
            values=[left_val, right_val],
            metadata=meta,
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
                self.trace_line(frame.f_lineno, frame=frame)
            elif event == "return":
                self.trace_line(frame.f_lineno, frame=frame)
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
