"""Tests for Graph tracing, circular layout, and canvas visualization (T028)."""

from __future__ import annotations

import math
import tkinter as tk
from collections import deque
from typing import Any

import pytest

from src.execution.events import EventType, ExecutionEvent
from src.execution.models import Graph
from src.execution.parsers import parse_leetcode_inputs
from src.execution.runner import CodeRunner
from src.execution.tracer import extract_graph_state
from src.ui.main_window import MainWindow
from src.visualization.graph_canvas import GraphCanvas, compute_graph_layout


COUNT_PROVINCES_CODE = """
def count_provinces(isConnected):
    n = len(isConnected)
    visited = [False] * n
    provinces = 0
    for start in range(n):
        if not visited[start]:
            provinces += 1
            stack = [start]
            while stack:
                node = stack.pop()
                visited[node] = True
                for neighbor in range(n):
                    if isConnected[node][neighbor] == 1 and not visited[neighbor]:
                        stack.append(neighbor)
    return provinces
"""


BFS_CODE = """
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    while queue:
        node = queue.popleft()
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return len(visited)
"""


# ---------------------------------------------------------------------------
# 1. Graph model parsing
# ---------------------------------------------------------------------------


def test_graph_from_adjacency_matrix_is_undirected() -> None:
    """Verify a symmetric adjacency matrix becomes an undirected graph."""
    graph = Graph.from_adjacency_matrix(
        [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
    )

    assert graph.directed is False
    assert graph.nodes == [0, 1, 2]
    assert len(graph.edges) == 2
    assert graph.has_edge(0, 1)
    assert graph.has_edge(1, 0)
    assert graph.has_edge(1, 2)


def test_graph_from_asymmetric_adjacency_matrix_is_directed() -> None:
    """Verify an asymmetric matrix is inferred to be directed."""
    graph = Graph.from_adjacency_matrix(
        [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    )

    assert graph.directed is True
    assert graph.edges == [(0, 1), (1, 2)]
    assert graph.has_edge(0, 1)
    assert not graph.has_edge(1, 0)


def test_graph_from_adjacency_list_infers_direction() -> None:
    """Verify reciprocal adjacency lists are undirected and one-way lists are directed."""
    undirected = Graph.from_adjacency_list({0: [1, 2], 1: [0], 2: [0]})
    assert undirected.directed is False
    assert len(undirected.edges) == 2

    directed = Graph.from_adjacency_list({0: [1], 1: [2], 2: []})
    assert directed.directed is True
    assert directed.edges == [(0, 1), (1, 2)]


def test_graph_from_edge_list_preserves_self_loops() -> None:
    """Verify edge-list parsing supports disconnected vertices and self-loops."""
    graph = Graph.from_edge_list([[0, 1], [1, 2], [2, 0], [2, 2]])

    assert graph.directed is False
    assert graph.nodes == [0, 1, 2]
    assert len(graph.edges) == 4
    assert graph.has_edge(2, 2)


def test_graph_from_value_detects_leetcode_input_shapes() -> None:
    """Verify matrix, edge-list, adjacency-list, and directed-input heuristics."""
    matrix = Graph.from_value([[0, 1], [1, 0]], "isConnected")
    assert matrix is not None
    assert matrix.directed is False
    assert len(matrix.edges) == 1

    edges = Graph.from_value([[0, 1], [1, 2]], "edges")
    assert edges is not None
    assert edges.directed is False
    assert len(edges.edges) == 2

    prerequisites = Graph.from_value([[1, 0], [2, 1]], "prerequisites")
    assert prerequisites is not None
    assert prerequisites.directed is True
    assert prerequisites.edges == [(1, 0), (2, 1)]

    adjacency = Graph.from_value([[1, 2], [0], [0]], "adj")
    assert adjacency is not None
    assert adjacency.nodes == [0, 1, 2]

    assert Graph.from_value([3, 1, 2], "nums") is None
    assert Graph.from_value("not a graph", "graph") is None


def test_graph_rejects_non_square_matrix() -> None:
    """Verify malformed adjacency matrices raise a descriptive error."""
    with pytest.raises(ValueError):
        Graph.from_adjacency_matrix([[0, 1], [1]])


def test_graph_to_state_has_visualization_shape() -> None:
    """Verify the baseline state contains serializable nodes, edges, and pointers."""
    state = Graph.from_edge_list([[0, 1]]).to_state()

    assert state["directed"] is False
    assert [node["id"] for node in state["nodes"]] == [0, 1]
    assert all(node["state"] == "unvisited" for node in state["nodes"])
    assert all(node["active"] is False for node in state["nodes"])
    assert state["edges"] == [{"source": 0, "target": 1, "active": False}]
    assert state["pointers"] == {}


# ---------------------------------------------------------------------------
# 2. Graph state extraction
# ---------------------------------------------------------------------------


def test_extract_graph_state_none_without_graph() -> None:
    """Verify non-graph locals do not produce a graph state."""
    assert extract_graph_state({}) is None
    assert extract_graph_state({"nums": [3, 1, 2], "x": 5}) is None


def test_extract_graph_state_ignores_linked_list_and_tree_nodes() -> None:
    """Verify standard ListNode/TreeNode values are not treated as object graphs."""
    from src.execution.models import ListNode, TreeNode

    assert extract_graph_state({"head": ListNode.from_list([1, 2, 3])}) is None
    assert (
        extract_graph_state({"root": TreeNode.from_level_order([1, 2, 3])})
        is None
    )


def test_extract_graph_state_from_matrix() -> None:
    """Verify a raw adjacency-matrix argument produces an unvisited graph state."""
    state = extract_graph_state(
        {"isConnected": [[0, 1, 0], [1, 0, 1], [0, 1, 0]]}
    )

    assert state is not None
    assert state["directed"] is False
    assert [node["id"] for node in state["nodes"]] == [0, 1, 2]
    assert len(state["edges"]) == 2
    assert all(node["state"] == "unvisited" for node in state["nodes"])
    assert state["pointers"] == {}


def test_extract_graph_state_tracks_visited_frontier_and_active_edge() -> None:
    """Verify visited/queue/neighbor locals map to traversal visualization state."""
    state = extract_graph_state(
        {
            "graph": {0: [1, 2], 1: [0], 2: [0]},
            "visited": {0},
            "queue": deque([1, 2]),
            "curr": 1,
            "neighbor": 0,
        }
    )

    assert state is not None
    states = {node["id"]: node["state"] for node in state["nodes"]}
    assert states == {0: "explored", 1: "active", 2: "frontier"}

    active_edges = [
        (edge["source"], edge["target"])
        for edge in state["edges"]
        if edge["active"]
    ]
    assert active_edges == [(0, 1)]
    assert state["pointers"] == {"curr": 1}


def test_extract_graph_state_supports_boolean_visited_lists() -> None:
    """Verify index-aligned visited boolean lists are mapped to explored vertices."""
    state = extract_graph_state(
        {
            "isConnected": [[1, 1, 0], [1, 1, 0], [0, 0, 1]],
            "visited": [True, False, True],
            "node": 0,
        }
    )

    assert state is not None
    states = {node["id"]: node["state"] for node in state["nodes"]}
    assert states[0] == "active"
    assert states[1] == "unvisited"
    assert states[2] == "explored"


def test_extract_graph_state_handles_disconnected_components() -> None:
    """Verify disconnected vertices are all represented without errors."""
    state = extract_graph_state(
        {
            "isConnected": [
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0],
            ]
        }
    )

    assert state is not None
    assert len(state["nodes"]) == 4
    assert {(edge["source"], edge["target"]) for edge in state["edges"]} == {
        (0, 1),
        (2, 3),
    }


def test_extract_graph_state_supports_directed_prerequisites() -> None:
    """Verify prerequisite edge lists are tracked as directed edges."""
    state = extract_graph_state({"prerequisites": [[1, 0], [2, 1]]})

    assert state is not None
    assert state["directed"] is True
    assert {(edge["source"], edge["target"]) for edge in state["edges"]} == {
        (1, 0),
        (2, 1),
    }


# ---------------------------------------------------------------------------
# 3. Circular layout
# ---------------------------------------------------------------------------


def test_compute_graph_layout_uses_equidistant_circle() -> None:
    """Verify vertices are placed at equal radius around the canvas center."""
    coords = compute_graph_layout([10, 20, 30, 40], 400, 300)

    assert set(coords) == {10, 20, 30, 40}
    assert len(set(coords.values())) == 4

    center_x, center_y = 200.0, 150.0
    radii = [
        math.hypot(x - center_x, y - center_y)
        for x, y in coords.values()
    ]
    assert radii[0] == pytest.approx(radii[1])
    assert radii[1] == pytest.approx(radii[2])
    assert radii[2] == pytest.approx(radii[3])


def test_compute_graph_layout_handles_empty_and_single_vertex() -> None:
    """Verify empty graphs have no coordinates and a single vertex is centered."""
    assert compute_graph_layout([], 400, 300) == {}
    assert compute_graph_layout(["a"], 400, 300) == {"a": (200.0, 150.0)}


# ---------------------------------------------------------------------------
# 4. Canvas rendering
# ---------------------------------------------------------------------------


def _node_state(*states: str) -> dict[str, Any]:
    return {
        "directed": False,
        "nodes": [
            {
                "id": index,
                "val": index,
                "state": state,
                "active": state == "active",
                "frontier": state == "frontier",
                "explored": state == "explored",
            }
            for index, state in enumerate(states)
        ],
        "edges": [
            {"source": index, "target": index + 1, "active": False}
            for index in range(max(0, len(states) - 1))
        ],
        "pointers": {},
    }


def test_graph_canvas_renders_empty_state(session_tk_root: tk.Tk) -> None:
    """Verify an empty graph renders a placeholder without errors."""
    view = GraphCanvas(session_tk_root)
    view.render_state(
        {"directed": False, "nodes": [], "edges": [], "pointers": {}}
    )

    assert len(view.canvas.find_all()) > 0
    view.destroy()


def test_graph_canvas_renders_vertices_edges_and_pointers(
    session_tk_root: tk.Tk,
) -> None:
    """Verify vertex circles, value labels, edges, and pointer labels are drawn."""
    view = GraphCanvas(session_tk_root)
    state = _node_state("unvisited", "active", "frontier")
    state["pointers"] = {"node": 1}
    view.render_state(state)

    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    assert "graph_node" in tags
    assert "graph_edge" in tags
    assert "pointer_label" in tags

    node_items = [
        item
        for item in view.canvas.find_all()
        if "graph_node" in view.canvas.gettags(item)
    ]
    assert len(node_items) == 3

    edge_items = [
        item
        for item in view.canvas.find_all()
        if "graph_edge" in view.canvas.gettags(item)
    ]
    assert len(edge_items) == 2

    text_values = [
        view.canvas.itemcget(item, "text")
        for item in view.canvas.find_all()
        if view.canvas.type(item) == "text"
    ]
    assert "0" in text_values
    assert "1" in text_values
    assert any("node" in text for text in text_values)
    view.destroy()


def test_graph_canvas_distinguishes_traversal_states(
    session_tk_root: tk.Tk,
) -> None:
    """Verify active, frontier, and explored vertices use distinct outlines."""
    view = GraphCanvas(session_tk_root)
    view.render_state(_node_state("active", "frontier", "explored"))

    node_items = [
        item
        for item in view.canvas.find_all()
        if "graph_node" in view.canvas.gettags(item)
    ]
    outlines = [
        view.canvas.itemcget(item, "outline").lower() for item in node_items
    ]
    assert outlines == [
        GraphCanvas.ACTIVE_OUTLINE.lower(),
        GraphCanvas.FRONTIER_OUTLINE.lower(),
        GraphCanvas.EXPLORED_OUTLINE.lower(),
    ]
    view.destroy()


def test_graph_canvas_uses_arrows_only_for_directed_edges(
    session_tk_root: tk.Tk,
) -> None:
    """Verify directed edges render arrowheads while undirected edges do not."""
    view = GraphCanvas(session_tk_root)

    undirected = _node_state("unvisited", "unvisited")
    view.render_state(undirected)
    edge_items = [
        item
        for item in view.canvas.find_all()
        if "graph_edge" in view.canvas.gettags(item)
    ]
    assert view.canvas.itemcget(edge_items[0], "arrow").lower() == "none"

    directed = _node_state("unvisited", "unvisited")
    directed["directed"] = True
    view.render_state(directed)
    edge_items = [
        item
        for item in view.canvas.find_all()
        if "graph_edge" in view.canvas.gettags(item)
    ]
    assert view.canvas.itemcget(edge_items[0], "arrow").lower() == "last"
    view.destroy()


def test_graph_canvas_highlights_active_edges(session_tk_root: tk.Tk) -> None:
    """Verify active edges use the highlight color and a thicker stroke."""
    view = GraphCanvas(session_tk_root)
    state = _node_state("active", "unvisited")
    state["edges"] = [{"source": 0, "target": 1, "active": True}]
    view.render_state(state)

    edge_item = next(
        item
        for item in view.canvas.find_all()
        if "graph_edge" in view.canvas.gettags(item)
    )
    assert (
        view.canvas.itemcget(edge_item, "fill").lower()
        == GraphCanvas.ACTIVE_EDGE_COLOR.lower()
    )
    assert float(view.canvas.itemcget(edge_item, "width")) >= 3
    view.destroy()


def test_graph_canvas_renders_self_loops(session_tk_root: tk.Tk) -> None:
    """Verify self-loop edges are drawn as looped lines."""
    view = GraphCanvas(session_tk_root)
    state = _node_state("unvisited")
    state["edges"] = [{"source": 0, "target": 0, "active": False}]
    view.render_state(state)

    tags: set[str] = set()
    for item in view.canvas.find_all():
        tags.update(view.canvas.gettags(item))
    assert "self_loop" in tags
    view.destroy()


def test_graph_canvas_renders_from_execution_event(session_tk_root: tk.Tk) -> None:
    """Verify GraphCanvas consumes graph metadata from an ExecutionEvent."""
    view = GraphCanvas(session_tk_root)
    state = _node_state("active", "unvisited")
    event = ExecutionEvent(
        step_index=0,
        event_type=EventType.LINE,
        line_number=3,
        metadata={"graph": state},
    )

    view.render_event(event)

    assert view._current_state is state
    assert len(view.canvas.find_all()) > 0
    view.destroy()


# ---------------------------------------------------------------------------
# 5. End-to-end tracing and interactive stepping
# ---------------------------------------------------------------------------


def test_graph_tracing_records_bfs_traversal_states() -> None:
    """Verify BFS execution metadata exposes frontier, explored, and active edges."""
    result = CodeRunner().run(
        BFS_CODE,
        {"graph": {0: [1, 2], 1: [0], 2: [0]}, "start": 0},
        function_name="bfs",
    )

    assert result.is_success is True
    assert result.final_array == 3

    graph_events = [event for event in result.events if event.metadata.get("graph")]
    assert graph_events

    all_nodes = [
        node
        for event in graph_events
        for node in event.metadata["graph"]["nodes"]
    ]
    assert any(node["state"] == "frontier" for node in all_nodes)
    assert any(node["state"] == "explored" for node in all_nodes)

    all_edges = [
        edge
        for event in graph_events
        for edge in event.metadata["graph"]["edges"]
    ]
    assert any(edge["active"] for edge in all_edges)

    final_state = graph_events[-1].metadata["graph"]
    assert all(node["state"] != "unvisited" for node in final_state["nodes"])


def test_graph_metadata_is_attached_to_every_event() -> None:
    """Regression: READ/WRITE events must not lose graph metadata.

    Reads such as ``visited[start]`` and writes such as
    ``visited[node] = True`` previously produced events without a graph
    snapshot, which made the UI fall back to the array view mid-traversal.
    """
    result = CodeRunner().run(
        COUNT_PROVINCES_CODE,
        parse_leetcode_inputs("isConnected = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]"),
        function_name="count_provinces",
    )

    assert result.is_success is True
    assert result.final_array == 2
    assert result.events

    missing = [event for event in result.events if "graph" not in event.metadata]
    assert missing == []

    event_types = {event.event_type for event in result.events}
    assert EventType.LINE in event_types
    assert EventType.READ in event_types
    assert EventType.WRITE in event_types


def test_graph_write_event_reflects_traversal_mutation() -> None:
    """Verify a visited write is reflected in the graph snapshot of that event."""
    result = CodeRunner().run(
        COUNT_PROVINCES_CODE,
        parse_leetcode_inputs("isConnected = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]"),
        function_name="count_provinces",
    )

    assert result.is_success is True
    write_events = [
        event for event in result.events if event.event_type == EventType.WRITE
    ]
    assert write_events

    for event in write_events:
        node_id = event.indices[0]
        node = next(
            node
            for node in event.metadata["graph"]["nodes"]
            if node["id"] == node_id
        )
        assert node["explored"] is True


def test_main_window_steps_through_graph_execution(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the UI selects the graph view and stays synchronized while stepping."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(BFS_CODE)
    window.input_panel.set_array_text(
        "graph = {0: [1, 2], 1: [0], 2: [0]}, start = 0"
    )

    window.handle_run()

    assert window.history is not None
    assert len(window.history) > 0
    assert window.graph_view.winfo_manager() == "pack"
    assert window.graph_view._current_state is not None
    assert "Graph" in window.lbl_viz["text"]

    for _ in range(len(window.history)):
        window.step_forward()
        assert window.graph_view.winfo_manager() == "pack"
        assert window.array_view.winfo_manager() != "pack"
        assert window.graph_view._current_state is not None
        assert "Graph" in window.lbl_viz["text"]
        assert window.editor.current_highlighted_line is not None

    assert window.current_step_index == len(window.history) - 1

    window.step_backward()
    assert window.current_step_index == len(window.history) - 2
    assert window.graph_view.winfo_manager() == "pack"

    window.reset_execution()
    assert window.current_step_index == -1
    assert window.graph_view.winfo_manager() == "pack"
    assert window.graph_view._current_state is not None


def test_main_window_keeps_graph_view_for_count_provinces(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the reported scenario: every step of count_provinces stays a graph."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(COUNT_PROVINCES_CODE)
    window.input_panel.set_array_text(
        "isConnected = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]"
    )

    window.handle_run()

    assert window.history is not None
    assert len(window.history) > 0

    for step in range(len(window.history)):
        window.step_forward()
        assert window.graph_view.winfo_manager() == "pack", (
            f"step {step} switched away from the graph view"
        )
        assert window.array_view.winfo_manager() != "pack"
        assert "Graph" in window.lbl_viz["text"]
        assert window.graph_view._current_state is not None
