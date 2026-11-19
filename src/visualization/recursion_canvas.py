"""Canvas visualization for recursion frames, sub-arrays, and returns (T035)."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

from src.execution.events import ExecutionEvent
from src.visualization.text_detail import (
    TextDetailController,
    format_value,
    truncate_text,
)
from src.visualization.viewport import ScrollableCanvas


class RecursionCanvas(tk.Frame):
    """Renders the active call stack, intermediate sub-arrays, and returned structure."""

    BG_COLOR = "#181825"
    PANEL_BG = "#1E1E2E"
    ITEM_BG = "#313244"
    ACTIVE_BG = "#45475A"
    TEXT_COLOR = "#CDD6F4"
    MUTED_COLOR = "#6C7086"
    FRAME_COLOR = "#89B4FA"
    SUBARRAY_COLOR = "#A6E3A1"
    RETURN_COLOR = "#F5C2E7"
    OP_COLOR = "#F9E2AF"
    EMPTY_COLOR = "#6C7086"

    FRAME_HEIGHT = 24
    FRAME_GAP = 3
    SUBARRAY_HEIGHT = 26
    SUBARRAY_GAP = 3
    MIN_CONTENT_WIDTH = 900.0

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self.details = TextDetailController(
            self,
            title="Recursion Detail",
            on_activate=self.viewport.suppress_pan_for_next_press,
        )
        self.details.attach_canvas(self.canvas)

        self._current_state: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render recursion metadata from an execution event."""
        metadata = event.metadata or {}
        self.render_state(metadata.get("recursion"))

    def render_state(self, state: Optional[dict[str, Any]]) -> None:
        """Render call-stack, sub-array, and return snapshots."""
        self.clear()
        self._current_state = state

        if not state:
            self._draw_empty()
            self.viewport.update_scrollregion()
            return

        frames = list(state.get("frames", []))
        subarrays = list(state.get("subarrays", []))
        return_structure = state.get("return_structure")
        last_return = state.get("last_return")
        if not frames and not subarrays and return_structure is None and not last_return:
            self._draw_empty()
            self.viewport.update_scrollregion()
            return

        viewport_width, viewport_height = self.viewport.viewport_size()
        width = max(self.MIN_CONTENT_WIDTH, float(viewport_width))
        frames_height = 60.0 + len(frames) * (self.FRAME_HEIGHT + self.FRAME_GAP)
        subarrays_height = 60.0 + len(subarrays) * (
            self.SUBARRAY_HEIGHT + self.SUBARRAY_GAP
        )
        height = max(float(viewport_height), frames_height, subarrays_height, 160.0)

        frames_width = width * 0.46
        subarrays_width = width * 0.30
        return_left = frames_width + subarrays_width
        return_width = width - return_left

        self._draw_frames(frames, 0.0, frames_width, height)
        self._draw_subarrays(subarrays, frames_width, subarrays_width, height)
        self._draw_return(
            return_structure,
            last_return,
            return_left,
            return_width,
            height,
        )

        self.viewport.update_scrollregion()

    # ------------------------------------------------------------------
    # Call stack
    # ------------------------------------------------------------------

    def _draw_frames(
        self,
        frames: list[dict[str, Any]],
        x0: float,
        section_width: float,
        height: float,
    ) -> None:
        self._draw_section_title(
            x0 + 10.0,
            "Call Stack",
            "frames",
            self.FRAME_COLOR,
        )

        left = x0 + 6.0
        right = x0 + section_width - 8.0
        top = 28.0
        bottom = height - 8.0

        if not frames:
            self.canvas.create_text(
                (left + right) / 2.0,
                top + 16.0,
                text="no active calls",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("recursion_frames_empty",),
            )
            return

        max_rows = max(1, len(frames))
        visible = frames[-max_rows:]
        hidden = len(frames) - len(visible)
        active_depth = frames[-1].get("depth")

        for position, frame in enumerate(reversed(visible)):
            row_top = top + position * (self.FRAME_HEIGHT + self.FRAME_GAP)
            row_bottom = row_top + self.FRAME_HEIGHT
            depth = frame.get("depth")
            function = frame.get("function", "?")
            is_active = depth == active_depth

            tags = ["recursion_frame", f"recursion_frame_{function}"]
            if is_active:
                tags.append("recursion_active_frame")

            self.canvas.create_rectangle(
                left,
                row_top,
                right,
                row_bottom,
                fill=self.ACTIVE_BG if is_active else self.ITEM_BG,
                outline=self.OP_COLOR if is_active else self.MUTED_COLOR,
                width=2 if is_active else 1,
                tags=tuple(tags),
            )

            args_text = self._format_args(frame.get("args", {}))
            label = f"#{depth} {function}"
            if args_text:
                label += f"({args_text})"
            display_label, label_truncated = truncate_text(label, 56)
            label_item = self.canvas.create_text(
                left + 10.0,
                (row_top + row_bottom) / 2.0,
                text=display_label,
                fill=self.TEXT_COLOR,
                font=("Consolas", 8, "bold"),
                anchor="w",
                tags=("recursion_frame_label", f"recursion_frame_label_{function}"),
            )
            if label_truncated:
                self.details.register_item(label_item, label)

            if frame.get("returning") and frame.get("return_value") is not None:
                self.canvas.create_text(
                    right - 10.0,
                    (row_top + row_bottom) / 2.0,
                    text=f"→ {self._format_value(frame['return_value'])}",
                    fill=self.SUBARRAY_COLOR,
                    font=("Consolas", 8, "bold"),
                    anchor="e",
                    tags=("recursion_frame_return",),
                )

        if hidden > 0:
            self.canvas.create_text(
                right,
                top - 2.0,
                text=f"+{hidden} outer",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                anchor="e",
                tags=("recursion_frames_overflow",),
            )

    # ------------------------------------------------------------------
    # Sub-arrays
    # ------------------------------------------------------------------

    def _draw_subarrays(
        self,
        subarrays: list[dict[str, Any]],
        x0: float,
        section_width: float,
        height: float,
    ) -> None:
        self._draw_section_title(
            x0 + 10.0,
            "Sub-arrays",
            "subarrays",
            self.SUBARRAY_COLOR,
        )

        left = x0 + 6.0
        right = x0 + section_width - 8.0
        top = 28.0
        bottom = height - 8.0

        if not subarrays:
            self.canvas.create_text(
                (left + right) / 2.0,
                top + 16.0,
                text="none yet",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("recursion_subarrays_empty",),
            )
            return

        max_rows = max(1, len(subarrays))
        visible = subarrays[-max_rows:]
        hidden = len(subarrays) - len(visible)

        for position, subarray in enumerate(visible):
            row_top = top + position * (self.SUBARRAY_HEIGHT + self.SUBARRAY_GAP)
            row_bottom = row_top + self.SUBARRAY_HEIGHT
            label = str(subarray.get("label", "slice"))
            items = subarray.get("items", [])

            self.canvas.create_rectangle(
                left,
                row_top,
                right,
                row_bottom,
                fill=self.ITEM_BG,
                outline=self.SUBARRAY_COLOR,
                width=1,
                tags=("recursion_subarray", f"recursion_subarray_{label}"),
            )
            display_label, label_truncated = truncate_text(label, 18)
            label_item = self.canvas.create_text(
                left + 8.0,
                row_top + 7.0,
                text=display_label,
                fill=self.SUBARRAY_COLOR,
                font=("Consolas", 8, "bold"),
                anchor="w",
                tags=("recursion_subarray_label",),
            )
            if label_truncated:
                self.details.register_item(label_item, label)

            item_text = self._format_value(items)
            display_items, items_truncated = truncate_text(item_text, 28)
            items_item = self.canvas.create_text(
                right - 8.0,
                row_bottom - 7.0,
                text=display_items,
                fill=self.TEXT_COLOR,
                font=("Consolas", 8),
                anchor="e",
                tags=("recursion_subarray_items",),
            )
            if items_truncated:
                self.details.register_item(items_item, item_text)

        if hidden > 0:
            self.canvas.create_text(
                right,
                top - 2.0,
                text=f"+{hidden} earlier",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                anchor="e",
                tags=("recursion_subarrays_overflow",),
            )

    # ------------------------------------------------------------------
    # Returned structure
    # ------------------------------------------------------------------

    def _draw_return(
        self,
        return_structure: Any,
        last_return: Optional[dict[str, Any]],
        x0: float,
        section_width: float,
        height: float,
    ) -> None:
        self._draw_section_title(
            x0 + 10.0,
            "Returned Structure",
            "return",
            self.RETURN_COLOR,
        )

        left = x0 + 6.0
        right = x0 + section_width - 8.0
        top = 28.0
        bottom = height - 8.0

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=self.PANEL_BG,
            outline=self.RETURN_COLOR,
            width=1,
            tags=("recursion_return",),
        )
        self.canvas.create_text(
            left + 10.0,
            top + 10.0,
            text="returned structure",
            fill=self.MUTED_COLOR,
            font=("Segoe UI", 8, "bold"),
            anchor="nw",
            tags=("recursion_return_label",),
        )

        value = return_structure
        if value is None and last_return is not None:
            value = last_return.get("value")

        value_text = "—" if value is None else self._format_value(value)
        display_value, value_truncated = truncate_text(value_text, 40)
        value_item = self.canvas.create_text(
            (left + right) / 2.0,
            (top + bottom) / 2.0 + 8.0,
            text=display_value,
            fill=self.TEXT_COLOR,
            font=("Consolas", 11, "bold"),
            tags=("recursion_return_value",),
        )
        if value_truncated:
            self.details.register_item(value_item, value_text)

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _draw_section_title(
        self,
        x: float,
        text: str,
        kind: str,
        color: str,
    ) -> None:
        self.canvas.create_text(
            x,
            10.0,
            text=text,
            fill=color,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            tags=("recursion_title", f"recursion_{kind}_title"),
        )

    def _format_args(self, args: dict[str, Any]) -> str:
        return ", ".join(
            f"{name}={self._format_value(value)}"
            for name, value in args.items()
        )

    def _format_value(self, value: Any) -> str:
        return format_value(value)

    def _draw_empty(self) -> None:
        self.canvas.create_text(
            20,
            40,
            text="No recursion activity",
            fill=self.EMPTY_COLOR,
            font=("Segoe UI", 9, "italic"),
            anchor="nw",
            tags=("recursion_empty",),
        )
