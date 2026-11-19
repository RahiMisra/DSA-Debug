"""Canvas visualization component for linked lists (T025)."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

from src.execution.events import ExecutionEvent
from src.visualization.text_detail import TextDetailController, truncate_text
from src.visualization.viewport import ScrollableCanvas


class LinkedListCanvas(tk.Frame):
    """Visualizes singly-linked lists with nodes, directional pointer arrows, active variable labels, and cycles."""

    BG_COLOR = "#181825"
    NODE_BG = "#313244"
    NODE_OUTLINE = "#89B4FA"
    NODE_ACTIVE_OUTLINE = "#F9E2AF"
    NEXT_BOX_BG = "#45475A"
    TEXT_COLOR = "#CDD6F4"
    POINTER_COLOR = "#F9E2AF"
    ARROW_COLOR = "#89B4FA"
    CYCLE_ARROW_COLOR = "#F38BA8"
    NULL_COLOR = "#6C7086"

    NODE_VAL_WIDTH = 48
    NODE_PTR_WIDTH = 28
    NODE_HEIGHT = 40
    NODE_SPACING = 55
    START_X = 60
    START_Y = 90

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self.details = TextDetailController(
            self,
            title="Linked List Node",
            on_activate=self.viewport.suppress_pan_for_next_press,
        )
        self.details.attach_canvas(self.canvas)

        self._current_state: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render linked list state from an execution event's metadata."""
        state = event.metadata.get("linked_list") if event.metadata else None
        self.render_state(state)

    def render_state(self, state: Optional[dict[str, Any]]) -> None:
        """Render linked list state dictionary."""
        self.clear()
        self._current_state = state

        if not state:
            self.viewport.update_scrollregion()
            return

        nodes: list[dict[str, Any]] = state.get("nodes", [])
        pointers: dict[str, Any] = state.get("pointers", {})
        has_cycle: bool = state.get("has_cycle", False)
        cycle_start: Optional[int] = state.get("cycle_start")

        # Map node ID to its assigned position on canvas
        node_coords: dict[int, tuple[float, float, float, float]] = {}

        if not nodes:
            # Empty list
            self.canvas.create_rectangle(
                self.START_X,
                self.START_Y,
                self.START_X + 110,
                self.START_Y + self.NODE_HEIGHT,
                fill="#1E1E2E",
                outline=self.NULL_COLOR,
                width=1,
                dash=(3, 3),
                tags=("node_box", "empty"),
            )
            self.canvas.create_text(
                self.START_X + 55,
                self.START_Y + self.NODE_HEIGHT / 2,
                text="None (Empty)",
                fill=self.NULL_COLOR,
                font=("Segoe UI", 9, "italic"),
                tags=("node_val", "empty"),
            )
            # Render pointer labels pointing to None
            if pointers:
                labels = ", ".join(sorted(pointers.keys()))
                self.canvas.create_text(
                    self.START_X + 55,
                    self.START_Y - 18,
                    text=f"{labels} ↓",
                    fill=self.POINTER_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )
            self.viewport.update_scrollregion()
            return

        # Invert pointers: node_id -> list of variable names
        node_pointers: dict[Any, list[str]] = {}
        for var_name, target_id in pointers.items():
            if target_id is not None:
                node_pointers.setdefault(target_id, []).append(var_name)
            else:
                node_pointers.setdefault("None", []).append(var_name)

        curr_x = self.START_X
        y = self.START_Y

        # 1. Render each node
        for node in nodes:
            node_id = node.get("id")
            val = node.get("val")

            # Check if active pointer points here
            var_list = node_pointers.get(node_id, [])
            is_active = any(v in ("curr", "slow", "fast") for v in var_list)
            outline_color = self.NODE_ACTIVE_OUTLINE if is_active else self.NODE_OUTLINE
            outline_width = 2 if is_active else 1

            total_node_width = self.NODE_VAL_WIDTH + self.NODE_PTR_WIDTH
            x1, y1 = curr_x, y
            x2, y2 = curr_x + total_node_width, y + self.NODE_HEIGHT
            node_coords[node_id] = (x1, y1, x2, y2)

            # Node value compartment
            self.canvas.create_rectangle(
                x1,
                y1,
                x1 + self.NODE_VAL_WIDTH,
                y2,
                fill=self.NODE_BG,
                outline=outline_color,
                width=outline_width,
                tags=("node_box",),
            )
            value_text = str(val)
            display_value, value_truncated = truncate_text(value_text, 12)
            value_item = self.canvas.create_text(
                x1 + self.NODE_VAL_WIDTH / 2,
                y1 + self.NODE_HEIGHT / 2,
                text=display_value,
                fill=self.TEXT_COLOR,
                font=("Consolas", 11, "bold"),
                tags=("node_val",),
            )
            if value_truncated:
                self.details.register_item(value_item, value_text)

            # Next pointer compartment
            ptr_x1 = x1 + self.NODE_VAL_WIDTH
            self.canvas.create_rectangle(
                ptr_x1,
                y1,
                x2,
                y2,
                fill=self.NEXT_BOX_BG,
                outline=outline_color,
                width=outline_width,
                tags=("node_box", "ptr_box"),
            )
            self.canvas.create_oval(
                ptr_x1 + 10,
                y1 + self.NODE_HEIGHT / 2 - 3,
                ptr_x1 + 16,
                y1 + self.NODE_HEIGHT / 2 + 3,
                fill=self.ARROW_COLOR,
                outline="",
                tags=("node_bullet",),
            )

            # Variable pointer labels above node
            if var_list:
                label_text = ", ".join(sorted(var_list))
                center_x = (x1 + x2) / 2
                display, truncated = truncate_text(label_text, 24)
                item_id = self.canvas.create_text(
                    center_x,
                    y1 - 18,
                    text=f"{display} ↓",
                    fill=self.POINTER_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )
                if truncated:
                    self.details.register_item(item_id, label_text)

            curr_x += total_node_width + self.NODE_SPACING

        # 2. Render arrows connecting nodes
        for idx, node in enumerate(nodes):
            node_id = node.get("id")
            next_id = node.get("next")
            if node_id not in node_coords:
                continue

            x1, y1, x2, y2 = node_coords[node_id]
            ptr_center_x = x2 - self.NODE_PTR_WIDTH / 2
            ptr_center_y = y1 + self.NODE_HEIGHT / 2

            if next_id is not None and next_id in node_coords:
                # Normal forward arrow or cycle forward
                dest_x1, dest_y1, dest_x2, dest_y2 = node_coords[next_id]
                if dest_x1 > x2:
                    # Forward link
                    self.canvas.create_line(
                        ptr_center_x,
                        ptr_center_y,
                        dest_x1,
                        ptr_center_y,
                        arrow=tk.LAST,
                        fill=self.ARROW_COLOR,
                        width=2,
                        tags=("arrow", "forward_arrow"),
                    )
            elif next_id is None:
                # Terminal null pointer
                self.canvas.create_line(
                    ptr_center_x,
                    ptr_center_y,
                    x2 + 25,
                    ptr_center_y,
                    arrow=tk.LAST,
                    fill=self.NULL_COLOR,
                    width=2,
                    tags=("arrow", "null_arrow"),
                )
                self.canvas.create_text(
                    x2 + 45,
                    ptr_center_y,
                    text="None",
                    fill=self.NULL_COLOR,
                    font=("Consolas", 10, "italic"),
                    tags=("node_val", "null_text"),
                )

        # 3. Render cycle arrow if present
        if has_cycle and cycle_start is not None and cycle_start in node_coords:
            # Find the node that links back to cycle_start
            cycle_end_node = None
            for n in reversed(nodes):
                if n.get("next") == cycle_start:
                    cycle_end_node = n
                    break
            if not cycle_end_node and nodes:
                cycle_end_node = nodes[-1]

            if cycle_end_node and cycle_end_node.get("id") in node_coords:
                end_x1, end_y1, end_x2, end_y2 = node_coords[cycle_end_node["id"]]
                start_x1, start_y1, start_x2, start_y2 = node_coords[cycle_start]

                # Draw curved path beneath nodes
                src_x = (end_x1 + end_x2) / 2
                src_y = end_y2
                dst_x = (start_x1 + start_x2) / 2
                dst_y = start_y2

                curve_y = max(src_y, dst_y) + 30
                self.canvas.create_line(
                    src_x,
                    src_y,
                    src_x,
                    curve_y,
                    dst_x,
                    curve_y,
                    dst_x,
                    dst_y,
                    smooth=True,
                    arrow=tk.LAST,
                    fill=self.CYCLE_ARROW_COLOR,
                    width=2,
                    tags=("cycle_arrow", "arrow"),
                )

        # Render None pointers if any variable points to None
        null_vars = node_pointers.get("None", [])
        if null_vars and nodes:
            last_id = nodes[-1]["id"]
            if last_id in node_coords:
                lx1, ly1, lx2, ly2 = node_coords[last_id]
                self.canvas.create_text(
                    lx2 + 45,
                    ly1 - 18,
                    text=f"{', '.join(sorted(null_vars))} ↓",
                    fill=self.NULL_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    tags=("pointer_label",),
                )

        self.viewport.update_scrollregion()
