"""Shared truncation and click-to-expand text helpers (T043)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

from src.visualization.theme import (
    PALETTE,
    VERTICAL_SCROLLBAR_STYLE,
    style_button,
)


ELLIPSIS = "\u2026"


def truncate_text(text: str, limit: int) -> tuple[str, bool]:
    """Return ``(display_text, was_truncated)`` for a fixed character budget."""
    if limit <= 0:
        return "", bool(text)
    if len(text) <= limit:
        return text, False
    return text[: max(0, limit - 1)] + ELLIPSIS, True


def format_value(value: Any) -> str:
    """Render nested lists, tuples, and dictionaries without losing structure."""
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(
            f"{key}: {format_value(item)}" for key, item in value.items()
        ) + "}"
    return str(value)


class DetailPopup(tk.Toplevel):
    """Small read-only detail window for a truncated value."""

    def __init__(
        self,
        master: tk.Widget,
        text: str,
        title: str = "Details",
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master)
        self.full_text = text
        self._on_close = on_close
        self._closed = False

        self.title(title)
        self.configure(bg=PALETTE.bg_base)
        self.resizable(True, True)

        header = tk.Frame(self, bg=PALETTE.bg_surface)
        header.pack(fill=tk.X)
        self.title_label = tk.Label(
            header,
            text=title,
            bg=PALETTE.bg_surface,
            fg=PALETTE.text,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=8,
            pady=4,
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.close_button = tk.Button(
            header,
            text="\u2715",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            command=self.close,
        )
        style_button(self.close_button, "ghost")
        self.close_button.pack(side=tk.RIGHT, padx=6, pady=4)

        body = tk.Frame(self, bg=PALETTE.editor_bg)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.text_widget = tk.Text(
            body,
            bg=PALETTE.editor_bg,
            fg=PALETTE.text,
            insertbackground=PALETTE.text,
            selectbackground=PALETTE.bg_active,
            selectforeground=PALETTE.text,
            wrap="word",
            relief="flat",
            bd=0,
            height=8,
            width=52,
            padx=6,
            pady=6,
            font=("Consolas", 10),
        )
        self.scrollbar = ttk.Scrollbar(
            body,
            orient=tk.VERTICAL,
            style=VERTICAL_SCROLLBAR_STYLE,
            command=self.text_widget.yview,
        )
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.insert("1.0", text)
        self.text_widget.config(state="disabled")

        self.bind("<Escape>", lambda _event: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.focus_set()

    def close(self) -> None:
        """Close the popup exactly once and notify the owner."""
        if self._closed:
            return
        self._closed = True
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass
        if self._on_close is not None:
            self._on_close()


class TextDetailController:
    """Track truncated canvas items and open a detail popup on activation."""

    def __init__(
        self,
        anchor_widget: tk.Widget,
        title: str = "Details",
        on_activate: Optional[Callable[[], None]] = None,
    ) -> None:
        self.anchor_widget = anchor_widget
        self.title = title
        self.on_activate = on_activate
        self.canvas: Optional[tk.Canvas] = None
        self.popup: Optional[DetailPopup] = None
        self.last_opened_text: Optional[str] = None
        self.registered_items: dict[int, str] = {}
        self._root_binding: Optional[str] = None

    def attach_canvas(self, canvas: tk.Canvas) -> None:
        """Remember the canvas that owns the expandable items."""
        self.canvas = canvas

    def register_item(self, item_id: int, full_text: str) -> None:
        """Make a truncated canvas item clickable and remember its full value."""
        if self.canvas is None:
            return
        self.registered_items[item_id] = full_text
        self.canvas.addtag_withtag("expandable", item_id)
        self.canvas.tag_bind(
            item_id,
            "<Button-1>",
            lambda _event, text=full_text: self.open(text),
        )

    def open(self, text: str) -> Optional[DetailPopup]:
        """Open a popup showing the full text; closes any previous popup."""
        self.close()
        if self.on_activate is not None:
            self.on_activate()
        self.last_opened_text = text
        try:
            self.popup = DetailPopup(
                self.anchor_widget,
                text=text,
                title=self.title,
                on_close=self._handle_popup_closed,
            )
        except tk.TclError:
            self.popup = None
            return None

        root = self.anchor_widget.winfo_toplevel()
        try:
            self._root_binding = root.bind(
                "<Button-1>",
                self._handle_click_away,
                add="+",
            )
        except tk.TclError:
            self._root_binding = None
        return self.popup

    def close(self) -> None:
        """Close the current popup and return focus to the originating widget."""
        if self._root_binding is not None:
            try:
                self.anchor_widget.winfo_toplevel().unbind(
                    "<Button-1>", self._root_binding
                )
            except tk.TclError:
                pass
            self._root_binding = None
        if self.popup is not None:
            popup = self.popup
            self.popup = None
            popup.close()
        try:
            self.anchor_widget.focus_set()
        except tk.TclError:
            pass

    def _handle_click_away(self, _event: tk.Event) -> None:
        self.close()

    def _handle_popup_closed(self) -> None:
        self.popup = None
        if self._root_binding is not None:
            try:
                self.anchor_widget.winfo_toplevel().unbind(
                    "<Button-1>", self._root_binding
                )
            except tk.TclError:
                pass
            self._root_binding = None
