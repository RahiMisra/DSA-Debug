"""Canvas visualization for auxiliary stacks and queues (T031)."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

from src.execution.events import ExecutionEvent


class AuxiliaryLinearCanvas(tk.Frame):
    """Renders auxiliary stacks as vertical towers and queues as horizontal pipes."""

    BG_COLOR = "#181825"
    PANEL_BG = "#1E1E2E"
    ITEM_BG = "#313244"
    TEXT_COLOR = "#CDD6F4"
    MUTED_COLOR = "#6C7086"
    STACK_COLOR = "#89B4FA"
    QUEUE_COLOR = "#A6E3A1"
    OP_COLOR = "#F9E2AF"
    EMPTY_COLOR = "#6C7086"

    ITEM_HEIGHT = 20
    ITEM_GAP = 3
    ITEM_MIN_WIDTH = 30
    ITEM_MAX_WIDTH = 44
    CANVAS_HEIGHT = 180

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.canvas = tk.Canvas(
            self,
            bg=self.BG_COLOR,
            height=self.CANVAS_HEIGHT,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._current_state: Optional[dict[str, Any]] = None
        self._current_operation: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render auxiliary state and the current operation from an event."""
        metadata = event.metadata or {}
        self.render_state(
            metadata.get("auxiliary"),
            operation=metadata.get("container_op"),
        )

    def render_state(
        self,
        state: Optional[dict[str, Any]],
        operation: Optional[dict[str, Any]] = None,
    ) -> None:
        """Render stack/queue snapshots, highlighting the active operation."""
        self.clear()
        self._current_state = state
        self._current_operation = operation

        if not state:
            return

        stacks = state.get("stacks", [])
        queues = state.get("queues", [])
        sections: list[tuple[str, dict[str, Any]]] = [
            ("stack", stack) for stack in stacks
        ] + [("queue", queue) for queue in queues]

        if not sections:
            self._draw_empty()
            return

        width = float(self.canvas.winfo_width())
        height = float(self.canvas.winfo_height())
        if width < 200:
            width = 640.0
        if height < 100:
            height = float(self.CANVAS_HEIGHT)

        section_width = width / len(sections)
        for index, (kind, container) in enumerate(sections):
            x0 = index * section_width
            if kind == "stack":
                self._draw_stack(container, x0, section_width, height, operation)
            else:
                self._draw_queue(container, x0, section_width, height, operation)

    # ------------------------------------------------------------------
    # Stack rendering
    # ------------------------------------------------------------------

    def _draw_stack(
        self,
        container: dict[str, Any],
        x0: float,
        section_width: float,
        height: float,
        operation: Optional[dict[str, Any]],
    ) -> None:
        name = str(container.get("name", "stack"))
        items = list(container.get("items", []))
        active = self._is_active(operation, name, "stack")
        outline = self.OP_COLOR if active else self.STACK_COLOR

        center_x = x0 + section_width / 2.0
        self._draw_title(center_x, 12, name, "stack", outline)
        self._draw_operation(center_x, 28, operation, active)

        box_width = min(96.0, max(56.0, section_width - 40.0))
        left = center_x - box_width / 2.0
        right = center_x + box_width / 2.0
        top = 42.0
        bottom = height - 18.0
        if bottom <= top:
            bottom = top + 40.0

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=self.PANEL_BG,
            outline=outline,
            width=2 if active else 1,
            tags=("stack_container", f"stack_container_{name}"),
        )

        item_height = self.ITEM_HEIGHT
        item_gap = self.ITEM_GAP
        max_items = max(1, int((bottom - top - 20) // (item_height + item_gap)))
        visible = items[-max_items:]
        truncated = len(items) - len(visible)

        for level, item in enumerate(visible):
            item_bottom = bottom - 8.0 - level * (item_height + item_gap)
            item_top = item_bottom - item_height
            is_top = level == len(visible) - 1
            self.canvas.create_rectangle(
                left + 8,
                item_top,
                right - 8,
                item_bottom,
                fill=self.ITEM_BG,
                outline=outline if is_top and active else self.MUTED_COLOR,
                width=2 if is_top and active else 1,
                tags=("stack_item", f"stack_item_{name}"),
            )
            self.canvas.create_text(
                center_x,
                (item_top + item_bottom) / 2.0,
                text=str(item),
                fill=self.TEXT_COLOR,
                font=("Consolas", 9, "bold"),
                tags=("stack_item_label", f"stack_item_label_{name}"),
            )

        if visible:
            self.canvas.create_text(
                right + 18,
                bottom - 8.0 - (len(visible) - 1) * (item_height + item_gap) - item_height / 2.0,
                text="top",
                fill=outline,
                font=("Segoe UI", 8, "bold"),
                tags=("stack_top_label",),
            )
        elif truncated == 0:
            self.canvas.create_text(
                center_x,
                (top + bottom) / 2.0,
                text="empty",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("stack_empty_label",),
            )

        if truncated > 0:
            self.canvas.create_text(
                center_x,
                top + 9,
                text=f"… {truncated} more",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                tags=("stack_overflow_label",),
            )

    # ------------------------------------------------------------------
    # Queue rendering
    # ------------------------------------------------------------------

    def _draw_queue(
        self,
        container: dict[str, Any],
        x0: float,
        section_width: float,
        height: float,
        operation: Optional[dict[str, Any]],
    ) -> None:
        name = str(container.get("name", "queue"))
        items = list(container.get("items", []))
        active = self._is_active(operation, name, "queue")
        outline = self.OP_COLOR if active else self.QUEUE_COLOR

        center_x = x0 + section_width / 2.0
        self._draw_title(center_x, 12, name, "queue", outline)
        self._draw_operation(center_x, 28, operation, active)

        left = x0 + 20.0
        right = x0 + section_width - 20.0
        top = height / 2.0 - 8.0
        bottom = height / 2.0 + 14.0

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=self.PANEL_BG,
            outline=outline,
            width=2 if active else 1,
            tags=("queue_container", f"queue_container_{name}"),
        )

        if not items:
            self.canvas.create_text(
                center_x,
                (top + bottom) / 2.0,
                text="empty",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("queue_empty_label",),
            )
            return

        available = max(1.0, right - left - 16.0)
        item_width = min(
            self.ITEM_MAX_WIDTH,
            max(self.ITEM_MIN_WIDTH, available / len(items) - self.ITEM_GAP),
        )
        max_items = max(1, int((available + self.ITEM_GAP) // (item_width + self.ITEM_GAP)))
        visible = items[:max_items]

        for position, item in enumerate(visible):
            item_left = left + 8.0 + position * (item_width + self.ITEM_GAP)
            self.canvas.create_rectangle(
                item_left,
                top + 5,
                item_left + item_width,
                bottom - 5,
                fill=self.ITEM_BG,
                outline=outline,
                width=1,
                tags=("queue_item", f"queue_item_{name}"),
            )
            self.canvas.create_text(
                item_left + item_width / 2.0,
                (top + bottom) / 2.0,
                text=str(item),
                fill=self.TEXT_COLOR,
                font=("Consolas", 9, "bold"),
                tags=("queue_item_label", f"queue_item_label_{name}"),
            )

        self.canvas.create_text(
            left + 8,
            bottom + 12,
            text="front",
            fill=outline,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            tags=("queue_front_label",),
        )
        self.canvas.create_text(
            right - 8,
            bottom + 12,
            text="rear",
            fill=outline,
            font=("Segoe UI", 8, "bold"),
            anchor="e",
            tags=("queue_rear_label",),
        )

        truncated = len(items) - len(visible)
        if truncated > 0:
            self.canvas.create_text(
                right - 8,
                top - 10,
                text=f"+{truncated} more",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                anchor="e",
                tags=("queue_overflow_label",),
            )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _draw_title(
        self,
        center_x: float,
        y: float,
        name: str,
        kind: str,
        color: str,
    ) -> None:
        self.canvas.create_text(
            center_x,
            y,
            text=f"{name}  ({kind})",
            fill=color,
            font=("Segoe UI", 9, "bold"),
            tags=("aux_title", f"{kind}_title"),
        )

    def _draw_operation(
        self,
        center_x: float,
        y: float,
        operation: Optional[dict[str, Any]],
        active: bool,
    ) -> None:
        if not operation or not active:
            return
        action = str(operation.get("action", ""))
        value = operation.get("value")
        text = action if value is None else f"{action} {value}"
        self.canvas.create_text(
            center_x,
            y,
            text=text,
            fill=self.OP_COLOR,
            font=("Consolas", 8, "bold"),
            tags=("aux_op",),
        )

    @staticmethod
    def _is_active(
        operation: Optional[dict[str, Any]],
        name: str,
        kind: str,
    ) -> bool:
        if not operation:
            return False
        return operation.get("name") == name and operation.get("kind") == kind

    def _draw_empty(self) -> None:
        self.canvas.create_text(
            20,
            40,
            text="No auxiliary stacks or queues",
            fill=self.EMPTY_COLOR,
            font=("Segoe UI", 9, "italic"),
            anchor="nw",
            tags=("aux_empty",),
        )
