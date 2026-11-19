"""Canvas visualization component for binary trees (T027)."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

from src.execution.events import ExecutionEvent
from src.visualization.text_detail import TextDetailController, truncate_text
from src.visualization.viewport import ScrollableCanvas


def compute_tree_layout(
    nodes: dict[int, dict[str, Any]],
    root_id: Optional[int],
    canvas_width: float = 600.0,
    canvas_height: float = 400.0,
) -> dict[int, tuple[float, float]]:
    """Compute non-overlapping 2D coordinates for binary tree nodes using in-order rank."""
    if not nodes or root_id is None:
        return {}

    in_order_nodes: list[int] = []
    depths: dict[int, int] = {}

    def traverse(nid: Optional[int], depth: int) -> None:
        if nid is None or nid not in nodes:
            return
        node = nodes[nid]
        traverse(node.get("left"), depth + 1)
        depths[nid] = depth
        in_order_nodes.append(nid)
        traverse(node.get("right"), depth + 1)

    traverse(root_id, 0)

    # In case there are disconnected nodes in the record, add them too
    for nid in nodes:
        if nid not in in_order_nodes:
            traverse(nid, 0)

    n = len(in_order_nodes)
    if n == 0:
        return {}

    margin_x = 60.0
    margin_y = 60.0
    level_height = 65.0

    if n == 1:
        nid = in_order_nodes[0]
        return {nid: (canvas_width / 2.0, margin_y)}

    usable_width = max(canvas_width - 2 * margin_x, float(n * 55))
    x_step = usable_width / max(1, n - 1)

    coords: dict[int, tuple[float, float]] = {}
    for idx, nid in enumerate(in_order_nodes):
        x = margin_x + idx * x_step
        y = margin_y + depths.get(nid, 0) * level_height
        coords[nid] = (x, y)

    return coords


class BinaryTreeCanvas(tk.Frame):
    """Visualizes binary trees with circular nodes, branch connections, and variable pointers."""

    BG_COLOR = "#181825"
    NODE_BG = "#313244"
    NODE_OUTLINE = "#89B4FA"
    NODE_ACTIVE_OUTLINE = "#F9E2AF"
    TEXT_COLOR = "#CDD6F4"
    BRANCH_COLOR = "#6C7086"
    POINTER_COLOR = "#F9E2AF"
    NULL_COLOR = "#6C7086"

    NODE_RADIUS = 18

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self.details = TextDetailController(
            self,
            title="Tree Node",
            on_activate=self.viewport.suppress_pan_for_next_press,
        )
        self.details.attach_canvas(self.canvas)

        self._current_state: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render tree state from an execution event's metadata."""
        state = event.metadata.get("tree") if event.metadata else None
        self.render_state(state)

    def render_state(self, state: Optional[dict[str, Any]]) -> None:
        """Render binary tree state dictionary."""
        self.clear()
        self._current_state = state

        if not state:
            self.viewport.update_scrollregion()
            return

        root_id: Optional[int] = state.get("root_id")
        nodes_raw = state.get("nodes", {})
        # Ensure integer keys for node lookup
        nodes: dict[int, dict[str, Any]] = {
            int(k): v for k, v in nodes_raw.items()
        }
        pointers: dict[str, Any] = state.get("pointers", {})

        if not nodes or root_id is None:
            # Empty tree
            start_x, start_y = 60, 90
            self.canvas.create_rectangle(
                start_x,
                start_y,
                start_x + 120,
                start_y + 40,
                fill="#1E1E2E",
                outline=self.NULL_COLOR,
                width=1,
                dash=(3, 3),
                tags=("tree_node", "empty"),
            )
            self.canvas.create_text(
                start_x + 60,
                start_y + 20,
                text="None (Empty Tree)",
                fill=self.NULL_COLOR,
                font=("Segoe UI", 9, "italic"),
                tags=("tree_val", "empty"),
            )
            if pointers:
                labels = ", ".join(sorted(pointers.keys()))
                self.canvas.create_text(
                    start_x + 60,
                    start_y - 15,
                    text=f"{labels} ↓",
                    fill=self.POINTER_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )
            self.viewport.update_scrollregion()
            return

        width, height = self._required_canvas_size(nodes)
        coords = compute_tree_layout(nodes, root_id, canvas_width=width, canvas_height=height)

        # Invert pointers: node_id -> list of variable names
        node_pointers: dict[int, list[str]] = {}
        for var_name, target_id in pointers.items():
            if target_id is not None:
                node_pointers.setdefault(int(target_id), []).append(var_name)

        # 1. Draw branch lines first so they sit under nodes
        for nid, (px, py) in coords.items():
            node_data = nodes.get(nid, {})
            for child_key in ("left", "right"):
                child_id = node_data.get(child_key)
                if child_id is not None and int(child_id) in coords:
                    cx, cy = coords[int(child_id)]
                    self.canvas.create_line(
                        px,
                        py,
                        cx,
                        cy,
                        fill=self.BRANCH_COLOR,
                        width=2,
                        tags=("branch_line",),
                    )

        # 2. Draw circular nodes
        r = self.NODE_RADIUS
        for nid, (x, y) in coords.items():
            node_data = nodes.get(nid, {})
            val = node_data.get("val", "")

            var_list = node_pointers.get(nid, [])
            is_active = any(v in ("curr", "node", "p", "q") for v in var_list)
            outline_color = self.NODE_ACTIVE_OUTLINE if is_active else self.NODE_OUTLINE
            outline_width = 3 if is_active else 1.5

            self.canvas.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=self.NODE_BG,
                outline=outline_color,
                width=outline_width,
                tags=("tree_node",),
            )
            value_text = str(val)
            display_value, value_truncated = truncate_text(value_text, 10)
            value_item = self.canvas.create_text(
                x,
                y,
                text=display_value,
                fill=self.TEXT_COLOR,
                font=("Consolas", 10, "bold"),
                tags=("tree_val",),
            )
            if value_truncated:
                self.details.register_item(value_item, value_text)

            # Draw pointer labels above node circle
            if var_list:
                label_text = ", ".join(sorted(var_list))
                display_label, label_truncated = truncate_text(label_text, 22)
                label_item = self.canvas.create_text(
                    x,
                    y - r - 12,
                    text=f"{display_label} ↓",
                    fill=self.POINTER_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )
                if label_truncated:
                    self.details.register_item(label_item, label_text)

        self.viewport.update_scrollregion()

    @staticmethod
    def _required_canvas_size(
        nodes: dict[int, dict[str, Any]],
    ) -> tuple[float, float]:
        """Compute a natural canvas size from node count and tree depth."""
        depths: list[int] = []

        def visit(node_id: Optional[int], depth: int) -> None:
            if node_id is None or node_id not in nodes:
                return
            depths.append(depth)
            node = nodes[node_id]
            visit(node.get("left"), depth + 1)
            visit(node.get("right"), depth + 1)

        roots = {nid for nid in nodes if nid is not None}
        for node in nodes.values():
            for child_key in ("left", "right"):
                child = node.get(child_key)
                if child is not None:
                    roots.discard(int(child))
        for root in list(roots) or list(nodes):
            visit(root, 0)

        max_depth = max(depths, default=0)
        width = max(600.0, len(nodes) * 80.0)
        height = max(400.0, 120.0 + max_depth * 65.0 + 70.0)
        return width, height
