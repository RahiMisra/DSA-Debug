"""Array visualization view component using Tkinter Canvas."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from src.visualization.array_state import ArrayViewState, ElementHighlight


class ArrayView(tk.Frame):
    """Visual canvas representing array elements as dynamic vertical bars."""

    BG_COLOR = "#0F172A"       # Slate 900
    TEXT_COLOR = "#F8FAFC"     # Slate 50
    MUTED_TEXT = "#94A3B8"     # Slate 400
    BASELINE_COLOR = "#334155" # Slate 700

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)
        self.canvas = tk.Canvas(
            self,
            bg=self.BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._current_state: ArrayViewState = ArrayViewState.from_array([])
        self.canvas.bind("<Configure>", self._on_resize)

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
        array: list[int],
        highlights: Optional[dict[int, ElementHighlight]] = None,
    ) -> None:
        """Convenience method to set array values and optional highlights."""
        self.set_array_state(ArrayViewState.from_array(array, highlights=highlights))

    def _on_resize(self, event: tk.Event) -> None:
        """Redraw canvas content upon resizing."""
        self.render()

    def render(self) -> None:
        """Render array bars, values, and highlights on the canvas."""
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
            return

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

        values = [elem.value for elem in elements]
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val

        slot_w = available_w / n
        spacing = max(1.0, min(8.0, slot_w * 0.15))
        bar_w = max(1.0, slot_w - spacing)

        min_bar_h = 16.0

        for i, elem in enumerate(elements):
            x0 = pad_x + i * slot_w + spacing / 2
            x1 = x0 + bar_w

            # Compute normalized height
            if val_range == 0:
                bar_h = min_bar_h + available_h * 0.4
            else:
                bar_h = min_bar_h + ((elem.value - min_val) / val_range) * (available_h - min_bar_h - 10)

            y0 = baseline_y - bar_h
            y1 = baseline_y

            # Draw bar rectangle
            self.canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=elem.color,
                outline="",
                tags=f"bar_{i}",
            )

            # Draw text labels if there's enough horizontal room
            if slot_w >= 22:
                # Value label above bar
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    max(12, y0 - 10),
                    text=str(elem.value),
                    fill=self.TEXT_COLOR,
                    font=("Consolas", 10, "bold"),
                )
                # Index label below baseline
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    baseline_y + 14,
                    text=str(elem.index),
                    fill=self.MUTED_TEXT,
                    font=("Consolas", 9),
                )
            elif elem.highlight != ElementHighlight.DEFAULT:
                # Always show value for actively operated elements even when dense
                self.canvas.create_text(
                    (x0 + x1) / 2,
                    max(12, y0 - 10),
                    text=str(elem.value),
                    fill=self.TEXT_COLOR,
                    font=("Consolas", 9, "bold"),
                )
