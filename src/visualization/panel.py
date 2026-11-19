"""Collapsible panel container with a persistent header (T041)."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from src.visualization.theme import PALETTE, style_button, surface_kwargs


class CollapsiblePanel(tk.Frame):
    """A panel whose header stays visible while its body can be collapsed."""

    BG_COLOR = PALETTE.bg_base
    HEADER_BG = PALETTE.bg_surface
    TEXT_COLOR = PALETTE.text
    MUTED_COLOR = PALETTE.text_muted
    BUTTON_BG = PALETTE.button_bg

    HEADER_HEIGHT = 26

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        title: str = "Panel",
        collapsed: bool = False,
        on_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ) -> None:
        options = surface_kwargs(self.BG_COLOR)
        options.update(kwargs)
        super().__init__(master, **options)
        self._collapsed = collapsed
        self._visible = True
        self._on_toggle = on_toggle

        self.header = tk.Frame(self, bg=self.HEADER_BG, height=self.HEADER_HEIGHT)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)

        self.header_border = tk.Frame(self, bg=PALETTE.border, height=1)
        self.header_border.pack(fill=tk.X, side=tk.TOP)

        self.toggle_button = tk.Button(
            self.header,
            text="\u25be" if not collapsed else "\u25b8",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=0,
            command=self.toggle,
        )
        style_button(self.toggle_button, "ghost")
        self.toggle_button.pack(side=tk.RIGHT, padx=(0, 4), pady=2)

        self.title_label = tk.Label(
            self.header,
            text=title,
            bg=self.HEADER_BG,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=8,
            pady=2,
        )
        self.title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.title_label.bind("<Button-1>", lambda _event: self.toggle())

        self.body = tk.Frame(self, bg=self.BG_COLOR)
        if not collapsed:
            self.body.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

    @property
    def is_collapsed(self) -> bool:
        """Return whether the body is currently hidden."""
        return self._collapsed

    @property
    def is_visible(self) -> bool:
        """Return whether the whole panel is managed by its parent."""
        return self._visible

    def set_title(self, title: str) -> None:
        """Update the header title without recreating the panel."""
        self.title_label.config(text=title)

    def toggle(self) -> None:
        """Toggle the collapsed state."""
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        """Show or hide the body while keeping the header visible."""
        self._collapsed = collapsed
        if collapsed:
            self.body.pack_forget()
            self.toggle_button.config(text="\u25b8")
        else:
            self.body.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
            self.toggle_button.config(text="\u25be")
        if self._on_toggle is not None:
            self._on_toggle(collapsed)

    def set_visible(self, visible: bool) -> None:
        """Show or hide the entire panel while preserving collapse state."""
        self._visible = visible
        if visible:
            if self.winfo_manager() != "pack":
                self.pack(fill=tk.BOTH, expand=True)
        else:
            if self.winfo_manager() == "pack":
                self.pack_forget()
