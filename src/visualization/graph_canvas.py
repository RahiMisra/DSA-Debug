"""Canvas visualization component for graphs (T028/T029)."""

from __future__ import annotations

import math
import tkinter as tk
from typing import Any, Optional, Sequence

from src.execution.events import ExecutionEvent
from src.visualization.text_detail import TextDetailController, truncate_text
from src.visualization.theme import GRAPH_STATE_FILL_COLORS, PALETTE
from src.visualization.viewport import ScrollableCanvas


def compute_graph_layout(
    node_ids: Sequence[Any],
    canvas_width: float = 600.0,
    canvas_height: float = 400.0,
    margin: float = 70.0,
) -> dict[Any, tuple[float, float]]:
    """Compute equidistant circular coordinates for graph vertices.

    Vertices are distributed evenly around the canvas center, starting at the
    top and proceeding clockwise. Disconnected components share the same ring.
    """
    ids = list(node_ids)
    if not ids:
        return {}

    center_x = canvas_width / 2.0
    center_y = canvas_height / 2.0

    if len(ids) == 1:
        return {ids[0]: (center_x, center_y)}

    radius = max(40.0, min(canvas_width, canvas_height) / 2.0 - margin)
    step = (2.0 * math.pi) / len(ids)

    coordinates: dict[Any, tuple[float, float]] = {}
    for index, node_id in enumerate(ids):
        angle = -math.pi / 2.0 + index * step
        coordinates[node_id] = (
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle),
        )
    return coordinates


class GraphCanvas(tk.Frame):
    """Visualizes graphs with circular vertex placement, edges, and traversal states."""

    BG_COLOR = PALETTE.canvas_bg
    NODE_BG = PALETTE.node_bg
    TEXT_COLOR = PALETTE.canvas_text
    POINTER_COLOR = PALETTE.pointer
    EDGE_COLOR = PALETTE.edge
    ACTIVE_EDGE_COLOR = PALETTE.pointer
    NULL_COLOR = PALETTE.null
    SHADOW_COLOR = PALETTE.shadow

    UNVISITED_OUTLINE = PALETTE.null
    FRONTIER_OUTLINE = PALETTE.pointer
    EXPLORED_OUTLINE = PALETTE.success
    ACTIVE_OUTLINE = PALETTE.danger

    STATE_OUTLINE = {
        "unvisited": UNVISITED_OUTLINE,
        "frontier": FRONTIER_OUTLINE,
        "explored": EXPLORED_OUTLINE,
        "active": ACTIVE_OUTLINE,
    }

    STATE_FILL = {
        "unvisited": NODE_BG,
        "frontier": GRAPH_STATE_FILL_COLORS["frontier"],
        "explored": GRAPH_STATE_FILL_COLORS["explored"],
        "active": GRAPH_STATE_FILL_COLORS["active"],
    }

    NODE_RADIUS = 18.0

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self.details = TextDetailController(
            self,
            title="Graph Vertex",
            on_activate=self.viewport.suppress_pan_for_next_press,
        )
        self.details.attach_canvas(self.canvas)

        self._current_state: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render graph state from an execution event's metadata."""
        state = event.metadata.get("graph") if event.metadata else None
        self.render_state(state)

    def render_state(self, state: Optional[dict[str, Any]]) -> None:
        """Render a graph state dictionary."""
        self.clear()
        self._current_state = state

        if not state:
            self.viewport.update_scrollregion()
            return

        nodes: list[dict[str, Any]] = state.get("nodes", [])
        edges: list[dict[str, Any]] = state.get("edges", [])
        pointers: dict[str, Any] = state.get("pointers", {})
        directed = bool(state.get("directed", False))
        radius = self.NODE_RADIUS

        if not nodes:
            start_x, start_y = 60, 90
            self.canvas.create_rectangle(
                start_x,
                start_y,
                start_x + 130,
                start_y + 40,
                fill=PALETTE.editor_bg,
                outline=self.NULL_COLOR,
                width=1,
                dash=(3, 3),
                tags=("graph_node", "empty"),
            )
            self.canvas.create_text(
                start_x + 65,
                start_y + 20,
                text="None (Empty Graph)",
                fill=self.NULL_COLOR,
                font=("Segoe UI", 9, "italic"),
                tags=("graph_node_label", "empty"),
            )
            self.viewport.update_scrollregion()
            return

        # Give each vertex room on the ring; large graphs scroll instead of
        # collapsing into an unreadable cluster.
        side = max(420.0, 2.0 * (len(nodes) * 24.0 + 80.0))
        width = side
        height = side

        coords = compute_graph_layout(
            [node.get("id") for node in nodes],
            canvas_width=width,
            canvas_height=height,
        )

        # Invert pointers: vertex label -> variable names referencing it.
        node_pointers: dict[Any, list[str]] = {}
        for var_name, target in pointers.items():
            if target is not None:
                node_pointers.setdefault(target, []).append(var_name)

        directed_edges = {
            (edge.get("source"), edge.get("target"))
            for edge in edges
        }

        # 1. Draw edges first so nodes sit on top.
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source not in coords or target not in coords:
                continue

            is_active = bool(edge.get("active"))
            color = self.ACTIVE_EDGE_COLOR if is_active else self.EDGE_COLOR
            edge_width = 3 if is_active else 1.5
            edge_tags = (
                "graph_edge",
                "active_edge" if is_active else "inactive_edge",
            )

            if source == target:
                self._draw_self_loop(coords[source], radius, directed, color, edge_width, edge_tags)
                continue

            sx, sy = coords[source]
            tx, ty = coords[target]
            self._draw_edge(
                sx,
                sy,
                tx,
                ty,
                radius,
                directed,
                (target, source) in directed_edges if directed else False,
                color,
                edge_width,
                edge_tags,
            )

        # 2. Draw vertices.
        for node in nodes:
            node_id = node.get("id")
            if node_id not in coords:
                continue

            x, y = coords[node_id]
            state_name = str(node.get("state", "unvisited"))
            is_active = bool(node.get("active")) or state_name == "active"
            outline = self.STATE_OUTLINE.get(state_name, self.UNVISITED_OUTLINE)
            fill = self.STATE_FILL.get(state_name, self.NODE_BG)
            outline_width = 3 if is_active else 1.5

            # Soft drop shadow behind the vertex.
            self.canvas.create_oval(
                x - radius + 2,
                y - radius + 2,
                x + radius + 2,
                y + radius + 2,
                fill=self.SHADOW_COLOR,
                outline="",
                tags=("graph_node_shadow",),
            )

            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=fill,
                outline=outline,
                width=outline_width,
                tags=("graph_node",),
            )
            value_text = str(node.get("val", node_id))
            display_value, value_truncated = truncate_text(value_text, 10)
            value_item = self.canvas.create_text(
                x,
                y,
                text=display_value,
                fill=self.TEXT_COLOR,
                font=("Consolas", 10, "bold"),
                tags=("graph_node_label",),
            )
            if value_truncated:
                self.details.register_item(value_item, value_text)

            var_list = node_pointers.get(node_id, [])
            if var_list:
                label_text = ", ".join(sorted(var_list))
                display_label, label_truncated = truncate_text(label_text, 22)
                label_item = self.canvas.create_text(
                    x,
                    y - radius - 12,
                    text=f"{display_label} ↓",
                    fill=self.POINTER_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )
                if label_truncated:
                    self.details.register_item(label_item, label_text)

        self.viewport.update_scrollregion()

    def _draw_edge(
        self,
        sx: float,
        sy: float,
        tx: float,
        ty: float,
        radius: float,
        directed: bool,
        reciprocal: bool,
        color: str,
        width: float,
        tags: tuple[str, ...],
    ) -> None:
        """Draw a straight (or slightly curved) edge between two vertex centers."""
        dx = tx - sx
        dy = ty - sy
        distance = math.hypot(dx, dy)
        if distance == 0:
            return

        ux = dx / distance
        uy = dy / distance
        start = (sx + ux * (radius + 2), sy + uy * (radius + 2))
        end = (tx - ux * (radius + 4), ty - uy * (radius + 4))
        arrow = tk.LAST if directed else tk.NONE

        if directed and reciprocal:
            # Bow reciprocal edges in opposite directions so arrows stay visible.
            mid_x = (sx + tx) / 2.0
            mid_y = (sy + ty) / 2.0
            control = (mid_x - uy * 16.0, mid_y + ux * 16.0)
            self.canvas.create_line(
                start[0],
                start[1],
                control[0],
                control[1],
                end[0],
                end[1],
                smooth=True,
                arrow=arrow,
                fill=color,
                width=width,
                tags=tags,
            )
            return

        self.canvas.create_line(
            start[0],
            start[1],
            end[0],
            end[1],
            arrow=arrow,
            fill=color,
            width=width,
            tags=tags,
        )

    def _draw_self_loop(
        self,
        position: tuple[float, float],
        radius: float,
        directed: bool,
        color: str,
        width: float,
        tags: tuple[str, ...],
    ) -> None:
        """Draw a self-loop arc above a vertex."""
        x, y = position
        top = y - radius
        self.canvas.create_line(
            x,
            top,
            x - radius * 0.9,
            top - radius * 1.4,
            x + radius * 0.9,
            top - radius * 1.4,
            x,
            top,
            smooth=True,
            arrow=tk.LAST if directed else tk.NONE,
            fill=color,
            width=width,
            tags=tags + ("self_loop",),
        )
