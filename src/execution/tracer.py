"""Execution tracer for recording algorithm execution events."""

from __future__ import annotations

import re
import sys
import types
from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any, Optional

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory
from src.execution.models import Graph


LINKED_LIST_VAR_NAMES = {
    "head", "curr", "prev", "slow", "fast", "nxt", "next", "tail", "node", "p", "q", "p1", "p2", "dummy", "l1", "l2"
}

TREE_VAR_NAMES = {
    "root", "curr", "node", "p", "q", "parent", "child", "sub", "target", "leaf"
}

# Structural graph variable names, most specific first.
GRAPH_VAR_NAMES = (
    "graph",
    "g",
    "adj",
    "adj_list",
    "adjList",
    "adjacency",
    "isConnected",
    "is_connected",
    "edges",
    "edge_list",
    "edgeList",
    "connections",
    "network",
    "prerequisites",
    "prereqs",
    "dependencies",
)

GRAPH_ACTIVE_VAR_NAMES = ("curr", "current", "node", "start", "u", "v")
GRAPH_NEIGHBOR_VAR_NAMES = (
    "neighbor", "neighbour", "nbr", "nxt", "next_node", "nextNode", "w"
)
GRAPH_VISITED_VAR_NAMES = ("visited", "seen", "explored")
GRAPH_FRONTIER_VAR_NAMES = (
    "queue", "q", "stack", "st", "frontier", "to_visit", "toVisit"
)

# Auxiliary linear container heuristics (Phase 11).
AUX_STACK_NAMES = {"stack", "st", "s"}
AUX_QUEUE_NAMES = {"queue", "q", "fifo", "deque", "dq"}

# Auxiliary hash structure heuristics (Phase 11, T032/T033).
AUX_MAP_NAME_TOKENS = {
    "visited",
    "seen",
    "count",
    "counts",
    "counter",
    "freq",
    "freqs",
    "frequency",
    "memo",
    "cache",
    "dp",
    "table",
    "lookup",
    "map",
    "mapping",
    "histogram",
}
AUX_SET_NAME_TOKENS = {"visited", "seen", "unique"}


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


def _label_in(value: Any, labels: set[Any]) -> Optional[Any]:
    """Return value if it is a valid vertex label, otherwise None."""
    try:
        return value if value in labels else None
    except TypeError:
        return None


def _find_graph(f_locals: dict[str, Any]) -> Optional[Graph]:
    """Locate the primary graph-shaped local variable in a frame."""
    for name in GRAPH_VAR_NAMES:
        if name not in f_locals:
            continue
        try:
            graph = Graph.from_value(f_locals[name], name=name)
        except (TypeError, ValueError):
            continue
        if graph is not None and graph.nodes:
            return graph

    for value in f_locals.values():
        if isinstance(value, Graph) and value.nodes:
            return value

    # Fall back to any collection whose variable name suggests a graph.
    for name, value in f_locals.items():
        lower_name = name.lower()
        if not any(
            token in lower_name
            for token in ("graph", "adj", "edge", "network", "connection")
        ):
            continue
        try:
            graph = Graph.from_value(value, name=name)
        except (TypeError, ValueError):
            continue
        if graph is not None and graph.nodes:
            return graph

    return None


def _collect_vertex_labels(
    f_locals: dict[str, Any],
    names: tuple[str, ...],
    labels: set[Any],
) -> set[Any]:
    """Collect known vertex labels from named local sets, lists, or mapping keys."""
    collected: set[Any] = set()

    for name in names:
        value = f_locals.get(name)
        if value is None:
            continue

        if isinstance(value, Mapping):
            candidates: Iterable[Any] = value.keys()
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            candidates = value
        else:
            continue

        for candidate in candidates:
            label = _label_in(candidate, labels)
            if label is not None:
                collected.add(label)

    return collected


def _collect_visited(f_locals: dict[str, Any], labels: list[Any]) -> set[Any]:
    """Collect explored vertices, including index-aligned boolean visited lists."""
    label_set = set(labels)
    visited: set[Any] = set()

    for name in GRAPH_VISITED_VAR_NAMES:
        value = f_locals.get(name)
        if value is None:
            continue

        if (
            isinstance(value, (list, tuple))
            and len(value) == len(labels)
            and all(isinstance(flag, bool) for flag in value)
        ):
            visited.update(
                label for label, flag in zip(labels, value) if flag
            )
            continue

        if isinstance(value, Mapping):
            candidates: Iterable[Any] = value.keys()
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            candidates = value
        else:
            continue

        for candidate in candidates:
            label = _label_in(candidate, label_set)
            if label is not None:
                visited.add(label)

    return visited


def extract_graph_state(f_locals: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract serializable graph structure, traversal states, and active edges.

    Traversal state is inferred from common local variable names:
    ``visited``/``seen`` marks explored vertices, ``queue``/``stack`` marks the
    frontier, and ``curr``/``node`` plus ``neighbor`` marks the active edge.
    """
    graph = _find_graph(f_locals)
    if graph is None:
        return None

    state = graph.to_state()
    labels = graph.nodes
    label_set = set(labels)
    explored = _collect_visited(f_locals, labels)
    frontier = _collect_vertex_labels(f_locals, GRAPH_FRONTIER_VAR_NAMES, label_set)

    pointers: dict[str, Any] = {}
    for name in GRAPH_ACTIVE_VAR_NAMES:
        label = _label_in(f_locals.get(name), label_set)
        if label is not None:
            pointers[name] = label

    active_nodes = {
        label
        for name, label in pointers.items()
        if name in ("curr", "current", "node", "start")
    }

    neighbor = None
    for name in GRAPH_NEIGHBOR_VAR_NAMES:
        label = _label_in(f_locals.get(name), label_set)
        if label is not None:
            neighbor = label
            break

    def edge_key(source: Any, target: Any) -> Any:
        return (source, target) if graph.directed else frozenset((source, target))

    active_edges: set[Any] = set()
    if neighbor is not None:
        for active in active_nodes:
            active_edges.add(edge_key(active, neighbor))
    if "u" in pointers and "v" in pointers:
        active_edges.add(edge_key(pointers["u"], pointers["v"]))

    for node in state["nodes"]:
        node_id = node["id"]
        node["explored"] = node_id in explored
        node["frontier"] = node_id in frontier
        node["active"] = node_id in active_nodes

        if node["active"]:
            node["state"] = "active"
        elif node["frontier"]:
            node["state"] = "frontier"
        elif node["explored"]:
            node["state"] = "explored"
        else:
            node["state"] = "unvisited"

    for edge in state["edges"]:
        edge["active"] = edge_key(edge["source"], edge["target"]) in active_edges

    state["pointers"] = pointers
    return state


def _normalized_container_name(name: str) -> str:
    """Normalize a variable name for auxiliary container heuristics."""
    return re.sub(r"[\d_]+$", "", name.strip().lower())


def classify_auxiliary_container(name: str, value: Any) -> Optional[str]:
    """Return ``"stack"``, ``"queue"``, or None for a local variable.

    Names provide the primary signal (``stack``/``st``/``s`` versus
    ``queue``/``q``/``fifo``). ``collections.deque`` values without a matching
    name are treated as queues because deques are predominantly used as FIFO
    containers. Plain lists without a matching name are ignored to avoid
    surfacing every intermediate result list as an auxiliary container.
    """
    is_list = isinstance(value, list)
    is_deque = isinstance(value, deque)
    if not (is_list or is_deque):
        return None

    base = _normalized_container_name(name)
    if not base:
        return None

    if base in AUX_QUEUE_NAMES or base.endswith("queue") or base.endswith("_q"):
        return "queue"
    if base in AUX_STACK_NAMES or base.endswith("stack") or base.endswith("_st"):
        return "stack"
    if is_deque:
        return "queue"
    return None


def _linear_container_snapshot(name: str, kind: str, container: Any) -> dict[str, Any]:
    """Build a serializable snapshot for one stack or queue."""
    items = list(container)
    snapshot: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "items": items,
        "size": len(items),
    }
    if kind == "stack":
        snapshot["top"] = items[-1] if items else None
    else:
        snapshot["front"] = items[0] if items else None
        snapshot["rear"] = items[-1] if items else None
    return snapshot


def extract_auxiliary_linear_state(
    f_locals: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Extract auxiliary stacks and queues with their current item snapshots."""
    stacks: list[dict[str, Any]] = []
    queues: list[dict[str, Any]] = []

    for name, value in f_locals.items():
        kind = classify_auxiliary_container(name, value)
        if kind == "stack":
            stacks.append(_linear_container_snapshot(name, kind, value))
        elif kind == "queue":
            queues.append(_linear_container_snapshot(name, kind, value))

    if not stacks and not queues:
        return None
    return {"stacks": stacks, "queues": queues}


def _auxiliary_name_tokens(name: str) -> set[str]:
    """Split a variable name into lowercase identifier tokens."""
    split_camel = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    tokens: set[str] = set()
    for token in re.split(r"[^A-Za-z0-9]+", split_camel.lower()):
        token = re.sub(r"\d+", "", token)
        if token:
            tokens.add(token)
    return tokens


def classify_auxiliary_hash(name: str, value: Any) -> Optional[str]:
    """Return ``"map"``, ``"set"``, or None for a local variable.

    Hash containers are discovered by name heuristics validated against the
    runtime type: dictionaries (including ``Counter``/``defaultdict``) become
    maps, and sets become sets. Unmatched dictionaries and sets are ignored to
    avoid surfacing graph adjacency maps and unrelated lookup tables.
    """
    is_map = isinstance(value, dict)
    is_set = isinstance(value, (set, frozenset))
    if not (is_map or is_set):
        return None

    tokens = _auxiliary_name_tokens(name)
    if not tokens:
        return None

    if tokens & AUX_MAP_NAME_TOKENS or tokens & AUX_SET_NAME_TOKENS:
        return "map" if is_map else "set"
    return None


def _map_snapshot(name: str, mapping: dict[Any, Any]) -> dict[str, Any]:
    """Build a serializable key/value snapshot for one hash map."""
    entries = [
        {"key": key, "value": value}
        for key, value in mapping.items()
    ]
    return {
        "name": name,
        "kind": "map",
        "entries": entries,
        "size": len(entries),
    }


def _set_snapshot(name: str, values: Any) -> dict[str, Any]:
    """Build a deterministic, serializable membership snapshot for one set."""
    try:
        items = sorted(values, key=lambda item: (type(item).__name__, repr(item)))
    except TypeError:  # pragma: no cover - sorting uses repr as a stable fallback
        items = list(values)
    return {
        "name": name,
        "kind": "set",
        "items": items,
        "size": len(items),
    }


def extract_auxiliary_hash_state(
    f_locals: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Extract auxiliary hash maps and sets with their current contents."""
    maps: list[dict[str, Any]] = []
    sets: list[dict[str, Any]] = []

    for name, value in f_locals.items():
        kind = classify_auxiliary_hash(name, value)
        if kind == "map":
            maps.append(_map_snapshot(name, value))
        elif kind == "set":
            sets.append(_set_snapshot(name, value))

    if not maps and not sets:
        return None
    return {"maps": maps, "sets": sets}


def extract_auxiliary_state(f_locals: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract all auxiliary stacks, queues, maps, and sets from locals."""
    linear_state = extract_auxiliary_linear_state(f_locals)
    hash_state = extract_auxiliary_hash_state(f_locals)
    if linear_state is None and hash_state is None:
        return None

    state: dict[str, Any] = {"stacks": [], "queues": [], "maps": [], "sets": []}
    if linear_state is not None:
        state.update(linear_state)
    if hash_state is not None:
        state.update(hash_state)
    return state


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
        self.current_graph_state: Optional[dict[str, Any]] = None
        self.current_aux_state: Optional[dict[str, Any]] = None

    def bind_array(self, target_array: list[int]) -> None:
        """Bind the active mutable array passed into the user function."""
        self.tracked_array = target_array

    def get_array_snapshot(self) -> list[int]:
        """Return a copy of the current array state."""
        return list(self.tracked_array)

    def _structure_metadata(self) -> dict[str, Any]:
        """Return metadata for the structures currently being visualized.

        Every recorded event carries these snapshots so the UI can keep showing
        a linked list, tree, graph, or auxiliary container instead of falling
        back to the array view on events that do not touch array elements
        (e.g. reads and writes).
        """
        metadata: dict[str, Any] = {}
        if self.current_ll_state is not None:
            metadata["linked_list"] = self.current_ll_state
        if self.current_tree_state is not None:
            metadata["tree"] = self.current_tree_state
        if self.current_graph_state is not None:
            metadata["graph"] = self.current_graph_state
        if self.current_aux_state is not None:
            metadata["auxiliary"] = self.current_aux_state
        return metadata

    def _add_event(
        self,
        event_type: EventType,
        line_number: Optional[int],
        array_state: list[int],
        indices: Optional[list[int]] = None,
        values: Optional[list[Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ExecutionEvent:
        """Append an event with the current structure snapshots attached."""
        merged_metadata = self._structure_metadata()
        if metadata:
            merged_metadata.update(metadata)

        return self.history.add_event(
            event_type=event_type,
            line_number=line_number,
            array_state=array_state,
            indices=indices,
            values=values,
            metadata=merged_metadata,
        )

    def _caller_frame(self) -> Optional[types.FrameType]:
        """Return the instrumented user frame calling a trace helper, if any."""
        try:
            frame = sys._getframe(2)
        except ValueError:  # pragma: no cover - interpreter without frame access
            return None
        return frame if frame.f_code.co_filename == self.target_filename else None

    def _refresh_structure_states(self, frame: types.FrameType) -> None:
        """Refresh snapshots for structures this execution is already tracking.

        Writes mutate traversal state between line events (for example
        ``visited[node] = True``). Refreshing keeps the event that performs the
        change in sync with the visualized structure. Structures that are not
        being tracked are skipped so array-heavy runs pay no extra extraction
        cost.
        """
        if self.current_ll_state is not None:
            ll_state = extract_linked_list_state(frame.f_locals)
            if ll_state is not None:
                self.current_ll_state = ll_state
        if self.current_tree_state is not None:
            tree_state = extract_tree_state(frame.f_locals)
            if tree_state is not None:
                self.current_tree_state = tree_state
        if self.current_graph_state is not None:
            graph_state = extract_graph_state(frame.f_locals)
            if graph_state is not None:
                self.current_graph_state = graph_state
        if self.current_aux_state is not None:
            aux_state = extract_auxiliary_state(frame.f_locals)
            if aux_state is not None:
                self.current_aux_state = aux_state

    def _sync_structure_states(self, frame: types.FrameType) -> None:
        """Refresh tracked structures, including first-time auxiliary state."""
        self._refresh_structure_states(frame)
        if self.current_aux_state is None:
            aux_state = extract_auxiliary_state(frame.f_locals)
            if aux_state is not None:
                self.current_aux_state = aux_state

    def trace_line(
        self,
        lineno: int,
        frame: Optional[types.FrameType] = None,
    ) -> ExecutionEvent:
        """Record line-level execution."""
        self.current_line = lineno
        if frame is not None:
            ll_state = extract_linked_list_state(frame.f_locals)
            if ll_state is not None:
                self.current_ll_state = ll_state
            tree_state = extract_tree_state(frame.f_locals)
            if tree_state is not None:
                self.current_tree_state = tree_state
            graph_state = extract_graph_state(frame.f_locals)
            if graph_state is not None:
                self.current_graph_state = graph_state
            aux_state = extract_auxiliary_state(frame.f_locals)
            if aux_state is not None:
                self.current_aux_state = aux_state

        return self._add_event(
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
        container_name: Optional[str] = None,
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

        if container_name and op_str in ("in", "not in"):
            container_op: Optional[dict[str, Any]] = None
            kind = classify_auxiliary_hash(container_name, right_val)
            key = left_val
            if kind is None:
                kind = classify_auxiliary_hash(container_name, left_val)
                key = right_val

            if kind is not None:
                frame = self._caller_frame()
                if frame is not None:
                    self._sync_structure_states(frame)
                present = result if op_str == "in" else not result
                container_op = {
                    "name": container_name,
                    "kind": kind,
                    "action": "lookup",
                    "key": key,
                    "value": present,
                    "present": present,
                }

            if container_op is not None:
                meta["container_op"] = container_op

        self._add_event(
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
        self._add_event(
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
        arr: Any,
        idx: Any,
        val: Any,
        lineno: Optional[int] = None,
        container_name: Optional[str] = None,
    ) -> Any:
        """Perform and record an array or hash-map write arr[idx] = val."""
        effective_line = lineno if lineno is not None else self.current_line

        is_mapping = isinstance(arr, dict)
        if is_mapping:
            prev_exists = idx in arr
            prev_val = arr[idx] if prev_exists else None
        else:
            prev_val = arr[idx] if (0 <= idx < len(arr)) else None

        arr[idx] = val

        frame = self._caller_frame()
        if frame is not None:
            self._sync_structure_states(frame)

        if is_mapping:
            hash_kind = classify_auxiliary_hash(container_name or "", arr)
            if hash_kind == "map":
                self._add_event(
                    event_type=EventType.CONTAINER,
                    line_number=effective_line,
                    array_state=self.get_array_snapshot(),
                    values=[val],
                    metadata={
                        "container_op": {
                            "name": container_name,
                            "kind": "map",
                            "action": "update" if prev_exists else "insert",
                            "key": idx,
                            "value": val,
                            "previous_value": prev_val,
                        }
                    },
                )
                return val

        self._add_event(
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
        arr: Any,
        idx: Any,
        lineno: Optional[int] = None,
        container_name: Optional[str] = None,
    ) -> Any:
        """Perform and record an array or hash-map read arr[idx]."""
        effective_line = lineno if lineno is not None else self.current_line
        val = arr[idx]

        if isinstance(arr, dict):
            hash_kind = classify_auxiliary_hash(container_name or "", arr)
            if hash_kind == "map":
                frame = self._caller_frame()
                if frame is not None:
                    self._sync_structure_states(frame)
                self._add_event(
                    event_type=EventType.CONTAINER,
                    line_number=effective_line,
                    array_state=self.get_array_snapshot(),
                    values=[val],
                    metadata={
                        "container_op": {
                            "name": container_name,
                            "kind": "map",
                            "action": "lookup",
                            "key": idx,
                            "value": val,
                        }
                    },
                )
            return val

        # Only record read event if reading from a list (e.g. array being inspected)
        if isinstance(arr, list):
            self._add_event(
                event_type=EventType.READ,
                line_number=effective_line,
                array_state=self.get_array_snapshot(),
                indices=[idx],
                values=[val],
                metadata={"index": idx, "value": val},
            )
        return val

    def trace_container_call(
        self,
        container: Any,
        name: str,
        method: str,
        args: tuple[Any, ...] = (),
        lineno: Optional[int] = None,
    ) -> Any:
        """Perform and record a stack, queue, map, or set operation.

        Wraps calls such as ``stack.append(x)``, ``queue.popleft()``,
        ``seen.add(x)``, and ``memo.pop(k)`` so the original return value is
        preserved while auxiliary container state is captured for
        visualization.
        """
        effective_line = lineno if lineno is not None else self.current_line
        result = getattr(container, method)(*args)

        linear_kind = classify_auxiliary_container(name, container)
        hash_kind = classify_auxiliary_hash(name, container)
        if linear_kind is None and hash_kind is None:
            return result

        frame = self._caller_frame()
        if frame is not None:
            self._sync_structure_states(frame)

        if hash_kind == "map":
            if method != "pop":
                return result
            kind = "map"
            action = "remove"
            key = args[0] if args else None
            value = result
        elif hash_kind == "set":
            if method not in ("add", "remove", "discard"):
                return result
            kind = "set"
            action = method
            key = args[0] if args else None
            value = key
        else:
            kind = linear_kind
            key = None
            if method == "append":
                action = "push" if kind == "stack" else "enqueue"
                value = args[0] if args else None
            elif method == "popleft" or kind == "queue":
                action = "dequeue"
                value = result
            else:
                action = "pop"
                value = result

        operation: dict[str, Any] = {
            "name": name,
            "kind": kind,
            "action": action,
            "value": value,
        }
        if key is not None:
            operation["key"] = key

        self._add_event(
            event_type=EventType.CONTAINER,
            line_number=effective_line,
            array_state=self.get_array_snapshot(),
            values=[value],
            metadata={"container_op": operation},
        )
        return result

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
