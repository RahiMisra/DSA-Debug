"""Reusable scrollable canvas wrapper with drag, wheel, and scrollbar support (T042)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from src.visualization.theme import (
    HORIZONTAL_SCROLLBAR_STYLE,
    PALETTE,
    VERTICAL_SCROLLBAR_STYLE,
)


class ScrollableCanvas(tk.Frame):
    """A canvas with optional horizontal/vertical scrollbars and pan gestures.

    The wrapper owns the canvas so views can render at their natural content
    size and let the user scroll instead of shrinking the visualization.
    """

    BG_COLOR = PALETTE.canvas_bg

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        bg: Optional[str] = None,
        canvas_width: Optional[int] = None,
        canvas_height: Optional[int] = None,
        **kwargs,
    ) -> None:
        background = bg or self.BG_COLOR
        super().__init__(master, bg=background, **kwargs)

        self.canvas = tk.Canvas(
            self,
            bg=background,
            highlightthickness=0,
            bd=0,
        )
        if canvas_width is not None:
            self.canvas.configure(width=canvas_width)
        if canvas_height is not None:
            self.canvas.configure(height=canvas_height)

        self.h_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.HORIZONTAL,
            style=HORIZONTAL_SCROLLBAR_STYLE,
            command=self.canvas.xview,
        )
        self.v_scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            style=VERTICAL_SCROLLBAR_STYLE,
            command=self.canvas.yview,
        )
        self.canvas.configure(
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
        )

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._h_visible = False
        self._v_visible = False
        self._content_bbox: Optional[tuple[int, int, int, int]] = None
        self._suppress_pan = False
        self._press_origin: Optional[tuple[int, int]] = None
        self._configure_job: Optional[str] = None

        self._bind_gestures()

    # ------------------------------------------------------------------
    # Content bounds and scrollbars
    # ------------------------------------------------------------------

    @property
    def content_bbox(self) -> Optional[tuple[int, int, int, int]]:
        """Return the last measured content bounds, if any."""
        return self._content_bbox

    @property
    def scrollregion(self) -> tuple[int, int, int, int]:
        """Return the canvas scrollregion as integers."""
        values = self.canvas.cget("scrollregion")
        if not values:
            return (0, 0, 0, 0)
        parts = [int(float(part)) for part in str(values).split()]
        return tuple(parts) if len(parts) == 4 else (0, 0, 0, 0)

    def viewport_size(self) -> tuple[int, int]:
        """Return the usable viewport size, with a small fallback for unmapped tests."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1:
            width = 600
        if height <= 1:
            height = 360
        return width, height

    def visible_region(self) -> tuple[int, int, int, int]:
        """Return the visible canvas rectangle as ``(x0, y0, width, height)``."""
        width, height = self.viewport_size()
        return (
            int(self.canvas.canvasx(0)),
            int(self.canvas.canvasy(0)),
            width,
            height,
        )

    def update_scrollregion(self) -> None:
        """Measure canvas items and update scrollbars/scrollregion."""
        bbox = self.canvas.bbox("all")
        viewport_width, viewport_height = self.viewport_size()
        if bbox is None:
            bbox = (0, 0, viewport_width, viewport_height)

        x0, y0, x1, y1 = bbox
        region = (
            min(0, int(x0)),
            min(0, int(y0)),
            max(int(x1), viewport_width),
            max(int(y1), viewport_height),
        )
        changed = self._content_bbox is None or tuple(bbox) != self._content_bbox
        self._content_bbox = tuple(bbox)

        self.canvas.configure(scrollregion=region)
        self._update_scrollbars(region)
        if changed:
            self.clamp_view()

    def _update_scrollbars(self, region: tuple[int, int, int, int]) -> None:
        viewport_width, viewport_height = self.viewport_size()
        need_h = (region[2] - region[0]) > viewport_width + 1
        need_v = (region[3] - region[1]) > viewport_height + 1

        if need_h and not self._h_visible:
            self.h_scrollbar.grid(row=1, column=0, sticky="ew")
            self._h_visible = True
        elif not need_h and self._h_visible:
            self.h_scrollbar.grid_remove()
            self._h_visible = False

        if need_v and not self._v_visible:
            self.v_scrollbar.grid(row=0, column=1, sticky="ns")
            self._v_visible = True
        elif not need_v and self._v_visible:
            self.v_scrollbar.grid_remove()
            self._v_visible = False

    def clamp_view(self) -> None:
        """Keep the current scroll offset inside the new scrollregion."""
        region = self.scrollregion
        content_width = max(1, region[2] - region[0])
        content_height = max(1, region[3] - region[1])
        viewport_width, viewport_height = self.viewport_size()

        if content_width <= viewport_width:
            self.canvas.xview_moveto(0.0)
        if content_height <= viewport_height:
            self.canvas.yview_moveto(0.0)

    def reset_view(self) -> None:
        """Scroll back to the top-left corner."""
        self.canvas.xview_moveto(0.0)
        self.canvas.yview_moveto(0.0)

    def scroll_by(self, x_units: int, y_units: int) -> None:
        """Scroll by canvas units in each direction."""
        if x_units:
            self.canvas.xview_scroll(x_units, "units")
        if y_units:
            self.canvas.yview_scroll(y_units, "units")

    # ------------------------------------------------------------------
    # Gestures
    # ------------------------------------------------------------------

    def suppress_pan_for_next_press(self) -> None:
        """Prevent the next background press from starting a pan gesture."""
        self._suppress_pan = True

    def _bind_gestures(self) -> None:
        self.canvas.bind("<Configure>", self._on_configure, add="+")
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.canvas.bind("<Button-4>", self._on_linux_wheel_up)
        self.canvas.bind("<Button-5>", self._on_linux_wheel_down)
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_pan_end)

    def _on_mousewheel(self, event: tk.Event) -> str:
        if event.state & 0x0001:
            return self._on_shift_mousewheel(event)
        self.canvas.yview_scroll(self._wheel_steps(event.delta), "units")
        return "break"

    def _on_shift_mousewheel(self, event: tk.Event) -> str:
        self.canvas.xview_scroll(self._wheel_steps(event.delta), "units")
        return "break"

    def _on_linux_wheel_up(self, _event: tk.Event) -> str:
        self.canvas.yview_scroll(-3, "units")
        return "break"

    def _on_linux_wheel_down(self, _event: tk.Event) -> str:
        self.canvas.yview_scroll(3, "units")
        return "break"

    @staticmethod
    def _wheel_steps(delta: int) -> int:
        if delta == 0:
            return 0
        steps = int(-delta / 120)
        return steps if steps != 0 else (-1 if delta > 0 else 1)

    def _on_pan_start(self, event: tk.Event) -> None:
        if self._suppress_pan:
            self._press_origin = None
            return
        self._press_origin = (event.x, event.y)
        self.canvas.scan_mark(event.x, event.y)
        try:
            self.canvas.focus_set()
        except tk.TclError:
            pass

    def _on_pan_drag(self, event: tk.Event) -> None:
        if self._press_origin is None or self._suppress_pan:
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _on_pan_end(self, _event: tk.Event) -> None:
        self._press_origin = None
        self._suppress_pan = False

    def _on_configure(self, _event: tk.Event) -> None:
        if self._configure_job is not None:
            try:
                self.after_cancel(self._configure_job)
            except tk.TclError:
                pass
        self._configure_job = self.after_idle(self._apply_configure)

    def _apply_configure(self) -> None:
        self._configure_job = None
        if self.winfo_exists():
            self.update_scrollregion()
