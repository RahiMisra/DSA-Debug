"""Canvas visualization for auxiliary hash maps and sets (T033)."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Optional

from src.execution.events import ExecutionEvent
from src.visualization.text_detail import TextDetailController, truncate_text
from src.visualization.theme import PALETTE
from src.visualization.viewport import ScrollableCanvas


_MISSING = object()


class AuxiliaryHashCanvas(tk.Frame):
    """Renders auxiliary maps as key/value tables and sets as badge clouds."""

    BG_COLOR = PALETTE.canvas_bg
    PANEL_BG = PALETTE.canvas_surface
    ITEM_BG = PALETTE.node_bg
    ACTIVE_BG = PALETTE.canvas_active
    TEXT_COLOR = PALETTE.canvas_text
    MUTED_COLOR = PALETTE.canvas_muted
    MAP_COLOR = PALETTE.hash_map
    SET_COLOR = PALETTE.hash_set
    OP_COLOR = PALETTE.operation
    EMPTY_COLOR = PALETTE.canvas_empty
    INSET_COLOR = PALETTE.inset_highlight

    ROW_HEIGHT = 20
    ROW_GAP = 2
    BADGE_HEIGHT = 20
    BADGE_GAP = 4
    MIN_SECTION_WIDTH = 240.0
    MIN_CONTENT_HEIGHT = 200.0

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self.details = TextDetailController(
            self,
            title="Hash Entry",
            on_activate=self.viewport.suppress_pan_for_next_press,
        )
        self.details.attach_canvas(self.canvas)

        self._current_state: Optional[dict[str, Any]] = None
        self._current_operation: Optional[dict[str, Any]] = None

    def clear(self) -> None:
        """Clear canvas content."""
        self.canvas.delete("all")

    def render_event(self, event: ExecutionEvent) -> None:
        """Render auxiliary hash state and the current operation from an event."""
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
        """Render map/set snapshots, highlighting the active key or member."""
        self.clear()
        self._current_state = state
        self._current_operation = operation

        if not state:
            self.viewport.update_scrollregion()
            return

        maps = state.get("maps", [])
        sets = state.get("sets", [])
        sections: list[tuple[str, dict[str, Any]]] = [
            ("map", mapping) for mapping in maps
        ] + [("set", values) for values in sets]

        if not sections:
            self._draw_empty()
            self.viewport.update_scrollregion()
            return

        viewport_width, viewport_height = self.viewport.viewport_size()
        section_widths: list[float] = []
        content_height = float(self.MIN_CONTENT_HEIGHT)
        for kind, container in sections:
            if kind == "map":
                entries = list(container.get("entries", []))
                section_widths.append(max(self.MIN_SECTION_WIDTH, 260.0))
                content_height = max(
                    content_height,
                    40.0 + 22.0 + len(entries) * (self.ROW_HEIGHT + self.ROW_GAP) + 30.0,
                )
            else:
                items = list(container.get("items", []))
                badge_widths = [max(30.0, len(str(item)) * 7.5 + 16.0) for item in items]
                required_width = max(
                    self.MIN_SECTION_WIDTH,
                    sum(badge_widths) + len(items) * self.BADGE_GAP + 30.0,
                )
                section_widths.append(required_width)

        total_width = sum(section_widths)
        if total_width < viewport_width:
            extra = (viewport_width - total_width) / len(sections)
            section_widths = [width + extra for width in section_widths]
        content_height = max(content_height, float(viewport_height))

        x0 = 0.0
        for (kind, container), section_width in zip(sections, section_widths):
            if kind == "map":
                self._draw_map(
                    container,
                    x0,
                    section_width,
                    content_height,
                    operation,
                )
            else:
                self._draw_set(
                    container,
                    x0,
                    section_width,
                    content_height,
                    operation,
                )
            x0 += section_width

        self.viewport.update_scrollregion()

    # ------------------------------------------------------------------
    # Hash map rendering
    # ------------------------------------------------------------------

    def _draw_map(
        self,
        container: dict[str, Any],
        x0: float,
        section_width: float,
        height: float,
        operation: Optional[dict[str, Any]],
    ) -> None:
        name = str(container.get("name", "map"))
        entries = list(container.get("entries", []))
        active = self._is_active(operation, name, "map")
        outline = self.OP_COLOR if active else self.MAP_COLOR

        center_x = x0 + section_width / 2.0
        self._draw_title(
            center_x,
            12,
            f"{name}  (map)  [{len(entries)}]",
            "map",
            outline,
            name,
        )
        self._draw_operation(center_x, 28, operation, active, "map")

        left = x0 + 10.0
        right = x0 + section_width - 10.0
        top = 40.0
        bottom = height - 10.0
        if right - left < 80.0:
            right = left + 80.0

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=self.PANEL_BG,
            outline=outline,
            width=2 if active else 1,
            tags=("hash_map", f"hash_map_{name}"),
        )
        self.canvas.create_line(
            left + 2,
            top + 2,
            right - 2,
            top + 2,
            fill=self.INSET_COLOR,
            width=1,
            tags=("hash_map_inset",),
        )

        if not entries:
            self.canvas.create_text(
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                text="empty",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("hash_map_empty",),
            )
            return

        self.canvas.create_text(
            left + 10,
            top + 10,
            text="key",
            fill=self.MUTED_COLOR,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            tags=("hash_map_header",),
        )
        self.canvas.create_text(
            right - 10,
            top + 10,
            text="value",
            fill=self.MUTED_COLOR,
            font=("Segoe UI", 8, "bold"),
            anchor="e",
            tags=("hash_map_header",),
        )

        rows_top = top + 22.0
        available = max(0.0, bottom - rows_top - 4.0)
        max_rows = int(available // (self.ROW_HEIGHT + self.ROW_GAP))
        if max_rows <= 0:
            return

        truncated = max(0, len(entries) - max_rows)
        if truncated > 0:
            # Keep space for the overflow note on the last row.
            max_rows = max(1, max_rows - 1)
            truncated = len(entries) - max_rows

        active_key = self._active_key(operation, name, "map")
        for position, entry in enumerate(entries[:max_rows]):
            key = entry.get("key")
            value = entry.get("value")
            row_top = rows_top + position * (self.ROW_HEIGHT + self.ROW_GAP)
            row_bottom = row_top + self.ROW_HEIGHT
            is_active = active_key is not _MISSING and key == active_key

            tags = ["hash_map_row", f"hash_map_row_{name}"]
            if is_active:
                tags.append("hash_map_active_row")

            self.canvas.create_rectangle(
                left + 6,
                row_top,
                right - 6,
                row_bottom,
                fill=self.ACTIVE_BG if is_active else self.ITEM_BG,
                outline=self.OP_COLOR if is_active else self.MUTED_COLOR,
                width=2 if is_active else 1,
                tags=tuple(tags),
            )
            key_text = str(key)
            value_text = str(value)
            display_key, key_truncated = truncate_text(key_text, 14)
            display_value, value_truncated = truncate_text(value_text, 20)
            key_item = self.canvas.create_text(
                left + 14,
                (row_top + row_bottom) / 2.0,
                text=display_key,
                fill=self.TEXT_COLOR,
                font=("Consolas", 9, "bold"),
                anchor="w",
                tags=("hash_map_key", f"hash_map_key_{name}"),
            )
            value_item = self.canvas.create_text(
                right - 14,
                (row_top + row_bottom) / 2.0,
                text=display_value,
                fill=self.TEXT_COLOR,
                font=("Consolas", 9),
                anchor="e",
                tags=("hash_map_value", f"hash_map_value_{name}"),
            )
            if key_truncated:
                self.details.register_item(key_item, key_text)
            if value_truncated:
                self.details.register_item(value_item, value_text)

        if truncated > 0:
            self.canvas.create_text(
                right - 10,
                bottom - 9,
                text=f"+{truncated} more",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                anchor="e",
                tags=("hash_map_overflow",),
            )

    # ------------------------------------------------------------------
    # Hash set rendering
    # ------------------------------------------------------------------

    def _draw_set(
        self,
        container: dict[str, Any],
        x0: float,
        section_width: float,
        height: float,
        operation: Optional[dict[str, Any]],
    ) -> None:
        name = str(container.get("name", "set"))
        items = list(container.get("items", []))
        active = self._is_active(operation, name, "set")
        outline = self.OP_COLOR if active else self.SET_COLOR

        center_x = x0 + section_width / 2.0
        self._draw_title(
            center_x,
            12,
            f"{name}  (set)  [{len(items)}]",
            "set",
            outline,
            name,
        )
        self._draw_operation(center_x, 28, operation, active, "set")

        left = x0 + 10.0
        right = x0 + section_width - 10.0
        top = 40.0
        bottom = height - 10.0
        if right - left < 80.0:
            right = left + 80.0

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill=self.PANEL_BG,
            outline=outline,
            width=2 if active else 1,
            tags=("hash_set", f"hash_set_{name}"),
        )
        self.canvas.create_line(
            left + 2,
            top + 2,
            right - 2,
            top + 2,
            fill=self.INSET_COLOR,
            width=1,
            tags=("hash_set_inset",),
        )

        if not items:
            self.canvas.create_text(
                (left + right) / 2.0,
                (top + bottom) / 2.0,
                text="empty",
                fill=self.EMPTY_COLOR,
                font=("Segoe UI", 8, "italic"),
                tags=("hash_set_empty",),
            )
            return

        active_key = self._active_key(operation, name, "set")
        badge_top = top + 10.0
        x_cursor = left + 10.0
        max_right = right - 10.0
        hidden = 0

        for item in items:
            text = str(item)
            badge_width = max(30.0, len(text) * 7.5 + 16.0)
            if x_cursor + badge_width > max_right:
                x_cursor = left + 10.0
                badge_top += self.BADGE_HEIGHT + self.BADGE_GAP

            if badge_top + self.BADGE_HEIGHT > bottom - 8.0:
                hidden += 1
                continue

            is_active = active_key is not _MISSING and item == active_key
            tags = ["hash_set_badge", f"hash_set_badge_{name}"]
            if is_active:
                tags.append("hash_set_active_badge")

            self.canvas.create_rectangle(
                x_cursor,
                badge_top,
                x_cursor + badge_width,
                badge_top + self.BADGE_HEIGHT,
                fill=self.ACTIVE_BG if is_active else self.ITEM_BG,
                outline=self.OP_COLOR if is_active else self.SET_COLOR,
                width=2 if is_active else 1,
                tags=tuple(tags),
            )
            display_text, text_truncated = truncate_text(text, 12)
            badge_label = self.canvas.create_text(
                x_cursor + badge_width / 2.0,
                badge_top + self.BADGE_HEIGHT / 2.0,
                text=display_text,
                fill=self.TEXT_COLOR,
                font=("Consolas", 9, "bold"),
                tags=("hash_set_badge_label", f"hash_set_badge_label_{name}"),
            )
            if text_truncated:
                self.details.register_item(badge_label, text)
            x_cursor += badge_width + self.BADGE_GAP

        if hidden > 0:
            self.canvas.create_text(
                right - 10,
                bottom - 8,
                text=f"+{hidden} more",
                fill=self.MUTED_COLOR,
                font=("Segoe UI", 8),
                anchor="e",
                tags=("hash_set_overflow",),
            )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _draw_title(
        self,
        center_x: float,
        y: float,
        text: str,
        kind: str,
        color: str,
        name: str,
    ) -> None:
        self.canvas.create_text(
            center_x,
            y,
            text=text,
            fill=color,
            font=("Segoe UI", 9, "bold"),
            tags=("hash_title", f"hash_title_{name}", f"hash_{kind}_title"),
        )

    def _draw_operation(
        self,
        center_x: float,
        y: float,
        operation: Optional[dict[str, Any]],
        active: bool,
        kind: str,
    ) -> None:
        if not operation or not active:
            return

        action = str(operation.get("action", ""))
        key = operation.get("key", _MISSING)
        value = operation.get("value", _MISSING)

        if kind == "map":
            if action in ("insert", "update"):
                text = f"{action} {key}: {value}"
            elif action == "lookup":
                text = f"lookup {key} -> {value}"
            elif action == "remove":
                text = f"remove {key}"
            else:
                text = f"{action} {key}"
        else:
            text = f"{action} {key}"

        self.canvas.create_text(
            center_x,
            y,
            text=text,
            fill=self.OP_COLOR,
            font=("Consolas", 8, "bold"),
            tags=("hash_op", f"hash_op_{kind}"),
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

    def _active_key(
        self,
        operation: Optional[dict[str, Any]],
        name: str,
        kind: str,
    ) -> Any:
        if not self._is_active(operation, name, kind):
            return _MISSING
        return operation.get("key", _MISSING)

    def _draw_empty(self) -> None:
        self.canvas.create_text(
            20,
            40,
            text="No auxiliary hash maps or sets",
            fill=self.EMPTY_COLOR,
            font=("Segoe UI", 9, "italic"),
            anchor="nw",
            tags=("hash_empty",),
        )
