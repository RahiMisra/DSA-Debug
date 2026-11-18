"""Standard data structure models for LeetCode-style problem execution."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any, Optional

# Variable names commonly used for edge-list graph inputs in LeetCode problems.
GRAPH_EDGE_VAR_NAMES = {
    "edges",
    "edge_list",
    "edgelist",
    "connections",
    "prerequisites",
    "prereqs",
    "dependencies",
}

# Edge-list variable names whose pairs represent directed edges.
GRAPH_DIRECTED_VAR_NAMES = {
    "prerequisites",
    "prereqs",
    "dependencies",
    "directed_edges",
}

# Grid-shaped graph inputs (for example LeetCode Number of Islands).
GRID_VAR_NAMES = {"grid", "island_grid", "islandgrid"}

# Cell values that represent water / absent vertices in grid graphs.
GRID_WATER_VALUES = {None, 0, False, "", "0", "."}



def _is_node_label(value: Any) -> bool:
    """Return True for primitive, hashable graph vertex labels."""
    return isinstance(value, (int, str)) and not isinstance(value, bool)


class ListNode:
    """Singly-linked list node compatible with LeetCode conventions."""

    def __init__(self, val: Any = 0, next: Optional[ListNode] = None) -> None:
        self.val = val
        self.next = next

    def to_list(self) -> list[Any]:
        """Convert linked list to Python list, handling cycles safely."""
        result: list[Any] = []
        visited = set()
        curr: Optional[ListNode] = self
        while curr is not None:
            if id(curr) in visited:
                break
            visited.add(id(curr))
            result.append(curr.val)
            curr = curr.next
        return result

    @classmethod
    def from_list(cls, values: list[Any]) -> Optional[ListNode]:
        """Construct a linked list from a Python list."""
        if not values:
            return None
        head = cls(values[0])
        curr = head
        for val in values[1:]:
            curr.next = cls(val)
            curr = curr.next
        return head

    def __repr__(self) -> str:
        items = []
        visited = set()
        curr: Optional[ListNode] = self
        while curr is not None:
            if id(curr) in visited:
                items.append(f"[Cycle to {curr.val}]")
                break
            visited.add(id(curr))
            items.append(str(curr.val))
            curr = curr.next
        return " -> ".join(items) if items else "Empty"

    def to_dict(self) -> dict[str, Any]:
        """Serialize linked list node for IPC."""
        return {"val": self.val, "values": self.to_list()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Optional[ListNode]:
        """Deserialize linked list from dict."""
        values = data.get("values", [])
        return cls.from_list(values)


class TreeNode:
    """Binary tree node compatible with LeetCode conventions."""

    def __init__(
        self,
        val: Any = 0,
        left: Optional[TreeNode] = None,
        right: Optional[TreeNode] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    @classmethod
    def from_level_order(cls, values: list[Any]) -> Optional[TreeNode]:
        """Construct binary tree from level-order array with nulls."""
        if not values or values[0] is None:
            return None

        root = cls(values[0])
        queue: deque[TreeNode] = deque([root])
        idx = 1
        n = len(values)

        while queue and idx < n:
            curr = queue.popleft()

            # Left child
            if idx < n:
                left_val = values[idx]
                idx += 1
                if left_val is not None:
                    curr.left = cls(left_val)
                    queue.append(curr.left)

            # Right child
            if idx < n:
                right_val = values[idx]
                idx += 1
                if right_val is not None:
                    curr.right = cls(right_val)
                    queue.append(curr.right)

        return root

    def to_level_order(self) -> list[Any]:
        """Convert binary tree to level-order list with None for nulls."""
        result: list[Any] = []
        queue: deque[Optional[TreeNode]] = deque([self])

        while queue:
            curr = queue.popleft()
            if curr is not None:
                result.append(curr.val)
                queue.append(curr.left)
                queue.append(curr.right)
            else:
                result.append(None)

        # Trim trailing None values
        while result and result[-1] is None:
            result.pop()
        return result

    def __repr__(self) -> str:
        return f"TreeNode({self.to_level_order()})"

    def to_dict(self) -> dict[str, Any]:
        """Serialize tree node for IPC."""
        return {"val": self.val, "values": self.to_level_order()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Optional[TreeNode]:
        """Deserialize tree from dict."""
        values = data.get("values", [])
        return cls.from_level_order(values)


class Graph:
    """Normalized graph model used for graph tracing and circular visualization.

    Adjacency matrices, adjacency lists, and edge lists are converted into a
    common set of labeled vertices and edges. Vertex labels are preserved so the
    visualization matches the labels used by the user's code.
    """

    def __init__(
        self,
        adjacency: Mapping[Any, Iterable[Any]],
        directed: bool = False,
    ) -> None:
        self.directed = directed
        self._adjacency: dict[Any, list[Any]] = {}
        self._edges: list[tuple[Any, Any]] = []
        self._edge_keys: set[Any] = set()

        for source, neighbors in adjacency.items():
            self._ensure_node(source)
            for target in neighbors:
                self._add_edge(source, target)

    @property
    def nodes(self) -> list[Any]:
        """Return vertex labels in insertion order."""
        return list(self._adjacency.keys())

    @property
    def edges(self) -> list[tuple[Any, Any]]:
        """Return normalized (source, target) edges in insertion order."""
        return list(self._edges)

    @property
    def adjacency(self) -> dict[Any, list[Any]]:
        """Return a copy of the adjacency mapping."""
        return {node: list(neighbors) for node, neighbors in self._adjacency.items()}

    def _ensure_node(self, node: Any) -> None:
        if node not in self._adjacency:
            self._adjacency[node] = []

    def _add_edge(self, source: Any, target: Any) -> None:
        self._ensure_node(source)
        self._ensure_node(target)

        key = (source, target) if self.directed else frozenset((source, target))
        if key in self._edge_keys:
            return

        self._edge_keys.add(key)
        self._edges.append((source, target))
        self._adjacency[source].append(target)
        if not self.directed and source not in self._adjacency[target]:
            self._adjacency[target].append(source)

    def has_edge(self, source: Any, target: Any) -> bool:
        """Return True if the graph contains an edge from source to target."""
        if self.directed:
            return (source, target) in self._edge_keys
        return frozenset((source, target)) in self._edge_keys

    @classmethod
    def from_adjacency_matrix(
        cls,
        matrix: Iterable[Iterable[Any]],
        directed: Optional[bool] = None,
    ) -> Graph:
        """Build a graph from a square adjacency matrix of 0/1 (or weighted) values.

        Symmetric matrices are treated as undirected unless ``directed`` is set.
        """
        rows = [list(row) for row in matrix]
        if not rows:
            return cls({}, directed=bool(directed))

        size = len(rows)
        if any(len(row) != size for row in rows):
            raise ValueError("Adjacency matrix must be square.")

        if directed is None:
            directed = any(
                rows[i][j] != rows[j][i]
                for i in range(size)
                for j in range(size)
            )

        adjacency: dict[int, list[int]] = {index: [] for index in range(size)}
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                if value:
                    adjacency[i].append(j)

        return cls(adjacency, directed=directed)

    @classmethod
    def from_adjacency_list(
        cls,
        adjacency: Mapping[Any, Iterable[Any]] | Iterable[Iterable[Any]],
        directed: Optional[bool] = None,
    ) -> Graph:
        """Build a graph from an adjacency mapping or a list-of-neighbor-lists.

        Reverse-edge reciprocity is used to infer directedness when not specified.
        """
        if isinstance(adjacency, Mapping):
            raw = {node: list(neighbors) for node, neighbors in adjacency.items()}
        else:
            raw = {index: list(neighbors) for index, neighbors in enumerate(adjacency)}

        # Neighbor-only vertices still need an adjacency entry.
        for node in list(raw.keys()):
            for neighbor in raw[node]:
                raw.setdefault(neighbor, [])

        if directed is None:
            directed = any(
                node not in raw.get(neighbor, [])
                for node, neighbors in raw.items()
                for neighbor in neighbors
            )

        return cls(raw, directed=directed)

    @classmethod
    def from_edge_list(
        cls,
        edges: Iterable[Iterable[Any]],
        directed: bool = False,
    ) -> Graph:
        """Build a graph from an edge list of (source, target) pairs."""
        raw: dict[Any, list[Any]] = {}
        for edge in edges:
            if not isinstance(edge, (list, tuple)) or len(edge) != 2:
                raise ValueError(f"Edge must be a pair of vertices, got: {edge!r}")
            source, target = edge
            if not _is_node_label(source) or not _is_node_label(target):
                raise ValueError(f"Unsupported edge vertex labels: {edge!r}")
            raw.setdefault(source, []).append(target)
            raw.setdefault(target, [])

        return cls(raw, directed=directed)

    @classmethod
    def from_grid(cls, grid: Iterable[Iterable[Any]]) -> Graph:
        """Build an undirected graph from a rectangular grid of land/water cells.

        Every non-water cell becomes a vertex labeled ``row * width + column``
        and connects to its four orthogonally adjacent land cells. This keeps
        grid-based problems such as Number of Islands visible in the graph
        viewport without changing the user's grid input.
        """
        rows = [list(row) for row in grid]
        height = len(rows)
        width = len(rows[0]) if rows else 0

        adjacency: dict[int, list[int]] = {}
        for r in range(height):
            for c in range(width):
                try:
                    is_water = rows[r][c] in GRID_WATER_VALUES
                except TypeError:  # unhashable cell values are treated as land
                    is_water = False
                if is_water:
                    continue
                adjacency[r * width + c] = []

        for r in range(height):
            for c in range(width):
                label = r * width + c
                if label not in adjacency:
                    continue
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        neighbor = nr * width + nc
                        if neighbor in adjacency:
                            adjacency[label].append(neighbor)

        return cls(adjacency, directed=False)


    @classmethod
    def from_value(cls, value: Any, name: Optional[str] = None) -> Optional[Graph]:
        """Convert a graph-shaped value into a Graph, or return None if unrecognized.

        Square numeric lists are treated as adjacency matrices unless the variable
        name identifies an edge list (e.g. ``edges`` or ``prerequisites``).
        """
        if isinstance(value, Graph):
            return value

        lower_name = (name or "").lower()

        if isinstance(value, Mapping):
            try:
                return cls.from_adjacency_list(value)
            except (TypeError, ValueError):
                return None

        if not isinstance(value, (list, tuple)) or not value:
            return None

        if lower_name in GRID_VAR_NAMES and cls._looks_like_grid(value):
            return cls.from_grid(value)

        if lower_name in GRAPH_EDGE_VAR_NAMES and cls._looks_like_edge_list(value):
            return cls.from_edge_list(
                value,
                directed=lower_name in GRAPH_DIRECTED_VAR_NAMES,
            )

        if cls._looks_like_adjacency_matrix(value):
            return cls.from_adjacency_matrix(value)

        if cls._looks_like_edge_list(value):
            return cls.from_edge_list(value, directed=False)

        if cls._looks_like_adjacency_list(value):
            return cls.from_adjacency_list(value)

        return None

    @staticmethod
    def _looks_like_adjacency_matrix(value: Iterable[Any]) -> bool:
        rows = list(value)
        if not rows:
            return False
        if not all(isinstance(row, (list, tuple)) for row in rows):
            return False
        size = len(rows)
        if any(len(row) != size for row in rows):
            return False
        return all(
            isinstance(entry, (int, float, bool))
            for row in rows
            for entry in row
        )

    @staticmethod
    def _looks_like_grid(value: Iterable[Any]) -> bool:
        """Return True for a rectangular grid of primitive cell values."""
        rows = list(value)
        if not rows or not all(isinstance(row, (list, tuple)) for row in rows):
            return False
        width = len(rows[0])
        if width == 0 or any(len(row) != width for row in rows):
            return False
        return all(
            not isinstance(cell, (list, tuple, dict, set, frozenset))
            for row in rows
            for cell in row
        )

    @staticmethod
    def _looks_like_edge_list(value: Iterable[Any]) -> bool:
        edges = list(value)
        if not edges:
            return False
        return all(
            isinstance(edge, (list, tuple))
            and len(edge) == 2
            and _is_node_label(edge[0])
            and _is_node_label(edge[1])
            for edge in edges
        )

    @staticmethod
    def _looks_like_adjacency_list(value: Iterable[Any]) -> bool:
        rows = list(value)
        if not rows:
            return False
        return all(
            isinstance(row, (list, tuple, set, frozenset))
            and all(_is_node_label(neighbor) for neighbor in row)
            for row in rows
        )

    def to_state(self) -> dict[str, Any]:
        """Return the baseline serializable state consumed by GraphCanvas."""
        return {
            "directed": self.directed,
            "nodes": [
                {
                    "id": node,
                    "val": node,
                    "state": "unvisited",
                    "active": False,
                    "frontier": False,
                    "explored": False,
                }
                for node in self.nodes
            ],
            "edges": [
                {"source": source, "target": target, "active": False}
                for source, target in self.edges
            ],
            "pointers": {},
        }
