"""Array and string visualization view component using Tkinter Canvas."""

from __future__ import annotations

import tkinter as tk
from typing import Optional, Sequence

from src.visualization.array_state import (
    BOX_BORDER_COLORS,
    BOX_FILL_COLORS,
    ArrayViewState,
    ElementHighlight,
)
from src.visualization.viewport import ScrollableCanvas


class ArrayView(tk.Frame):
    """Visual canvas representing array/string elements as boxed cells or vertical bars."""

    BG_COLOR = "#0F172A"       # Slate 900
    TEXT_COLOR = "#F8FAFC"     # Slate 50
    MUTED_TEXT = "#94A3B8"     # Slate 400
    BASELINE_COLOR = "#334155" # Slate 700

    STYLE_BOX = "box"
    STYLE_BAR = "bar"

    MIN_BOX_SIZE = 24.0
    MAX_BOX_SIZE = 56.0
    MIN_BAR_SLOT = 18.0

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        view_style: str = STYLE_BOX,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self._view_style = view_style

        # Top toolbar for style switching
        self.toolbar = tk.Frame(self, bg=self.BG_COLOR)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(4, 0))

        self.btn_toggle_style = tk.Button(
            self.toolbar,
            text="Switch to Bar View" if self._view_style == self.STYLE_BOX else "Switch to Box View",
            bg="#1E293B",
            fg=self.MUTED_TEXT,
            font=("Segoe UI", 8),
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2",
            command=self.toggle_view_style,
        )
        self.btn_toggle_style.pack(side=tk.RIGHT)

        self.viewport = ScrollableCanvas(self, bg=self.BG_COLOR)
        self.viewport.pack(fill=tk.BOTH, expand=True)
        self.canvas = self.viewport.canvas

        self._current_state: ArrayViewState = ArrayViewState.from_array([])
        self.canvas.bind("<Configure>", self._on_resize)

    @property
    def view_style(self) -> str:
        """Return the current visual style ('box' or 'bar')."""
        return self._view_style

    def set_view_style(self, style: str) -> None:
        """Set visual style ('box' or 'bar') and re-render."""
        if style in (self.STYLE_BOX, self.STYLE_BAR):
            self._view_style = style
            btn_text = "Switch to Bar View" if self._view_style == self.STYLE_BOX else "Switch to Box View"
            self.btn_toggle_style.config(text=btn_text)
            self.render()

    def toggle_view_style(self) -> None:
        """Toggle between box and bar visual styles."""
        new_style = self.STYLE_BAR if self._view_style == self.STYLE_BOX else self.STYLE_BOX
        self.set_view_style(new_style)

    @property
    def current_state(self) -> ArrayViewState:
        """Return the current ArrayViewState."""
        return self._current_state

    def set_array_state(self, state: ArrayViewState) -> None:
        """Update and re-render the view with a new ArrayViewState."""
        self._current_state = state
        self.render()

    def set_array(
        self,
        array: Sequence,
        highlights: Optional[dict[int, ElementHighlight]] = None,
    ) -> None:
        """Convenience method to set array/string values and optional highlights."""
        self.set_array_state(ArrayViewState.from_array(array, highlights=highlights))

    def _on_resize(self, event: tk.Event) -> None:
        """Redraw canvas content upon resizing."""
        self.render()

    def render(self) -> None:
        """Render elements on canvas according to active view style."""
        self.canvas.delete("all")

        elements = self._current_state.elements
        n = len(elements)

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Canvas might not be mapped yet during initial layout
        if width <= 1:
            width = 600
        if height <= 1:
            height = 300

        # Handle empty array
        if n == 0:
            self.canvas.create_text(
                width / 2,
                height / 2,
                text="(Empty array)",
                fill=self.MUTED_TEXT,
                font=("Consolas", 14, "italic"),
            )
            self.viewport.update_scrollregion()
            return

        if self._view_style == self.STYLE_BAR:
            self._render_bars(width, height, elements)
        else:
            self._render_boxes(width, height, elements)
        self.viewport.update_scrollregion()

    def _render_boxes(self, width: int, height: int, elements: list) -> None:
        """Render array/string elements as horizontal boxed cells with centered values."""
        n = len(elements)
        pad_x = 24.0
        avail_w = max(20.0, width - 2 * pad_x)

        # Keep cells readable and let the viewport scroll when the array is wide.
        ideal_spacing = 8.0
        computed_size = (avail_w - (n - 1) * ideal_spacing) / n

        if computed_size >= self.MIN_BOX_SIZE:
            box_size = min(self.MAX_BOX_SIZE, computed_size)
            spacing = ideal_spacing
        else:
            box_size = self.MIN_BOX_SIZE
            spacing = ideal_spacing

        total_w = n * box_size + (n - 1) * spacing
        start_x = pad_x if total_w >= avail_w else (width - total_w) / 2
        center_y = height / 2 - 8.0

        y0 = center_y - box_size / 2
        y1 = center_y + box_size / 2

        font_size = max(8, min(14, int(box_size * 0.36)))

        for i, elem in enumerate(elements):
            x0 = start_x + i * (box_size + spacing)
            x1 = x0 + box_size

            is_highlighted = elem.highlight != ElementHighlight.DEFAULT
            border_w = 3 if is_highlighted else 2

            # Draw box rectangle
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=elem.box_fill_color,
                outline=elem.box_border_color,
                width=border_w,
                tags=(f"box_{i}", "box"),
            )

            # Draw centered value / character
            self.canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=str(elem.value),
                fill=self.TEXT_COLOR,
                font=("Consolas", font_size, "bold"),
                tags=(f"val_{i}", "value_text"),
            )

            # Draw index below box
            if box_size >= 20:
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    y1 + 14,
                    text=str(elem.index),
                    fill=self.MUTED_TEXT,
                    font=("Consolas", 9),
                    tags=(f"idx_{i}", "index_text"),
                )

    def _render_bars(self, width: int, height: int, elements: list) -> None:
        """Render array elements as vertical bars."""
        n = len(elements)
        pad_x = 20
        pad_top = 35
        pad_bottom = 35
        available_w = max(10, width - 2 * pad_x)
        available_h = max(20, height - pad_top - pad_bottom)
        baseline_y = height - pad_bottom
        # Draw baseline
        self.canvas.create_line(
            pad_x,
            baseline_y,
            width - pad_x,
            baseline_y,
            fill=self.BASELINE_COLOR,
            width=2,
        )

        try:
            num_values = [float(elem.value) for elem in elements]
            min_val = min(num_values)
            max_val = max(num_values)
            val_range = max_val - min_val
        except (ValueError, TypeError):
            min_val = 0.0
            max_val = 1.0
            val_range = 1.0

        slot_w = max(self.MIN_BAR_SLOT, available_w / n)
        spacing = max(1.0, min(8.0, slot_w * 0.15))
        bar_w = max(1.0, slot_w - spacing)
        min_bar_h = 16.0

        for i, elem in enumerate(elements):
            x0 = pad_x + i * slot_w + spacing / 2
            x1 = x0 + bar_w

            try:
                num_v = float(elem.value)
                if val_range == 0:
                    bar_h = min_bar_h + available_h * 0.4
                else:
                    bar_h = min_bar_h + ((num_v - min_val) / val_range) * (available_h - min_bar_h - 10)
            except (ValueError, TypeError):
                bar_h = min_bar_h + available_h * 0.4

            y0 = baseline_y - bar_h
            y1 = baseline_y

            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=elem.color,
                outline="",
                tags=f"bar_{i}",
            )

            if slot_w >= 22:
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    max(12, y0 - 10),
                    text=str(elem.value),
                    fill=self.TEXT_COLOR,
                    font=("Consolas", 10, "bold"),
                )
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    baseline_y + 14,
                    text=str(elem.index),
                    fill=self.MUTED_TEXT,
                    font=("Consolas", 9),
                )
            elif elem.highlight != ElementHighlight.DEFAULT:
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    max(12, y0 - 10),
                    text=str(elem.value),
                    fill=self.TEXT_COLOR,
                    font=("Consolas", 9, "bold"),
                )
