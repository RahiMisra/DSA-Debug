"""Segmented multi-view dashboard container (T037)."""

from __future__ import annotations

import tkinter as tk
from typing import Optional


class MultiViewDashboard(tk.Frame):
    """Option A layout: primary viewport with auxiliary and subwork segments.

    The primary data structure occupies the main viewport. Secondary segments
    are packed below it as needed:

    - ``auxiliary``: stacks, queues, hash maps, and hash sets.
    - ``subwork``: recursion call stack, intermediate sub-arrays, and the
      returned structure.

    The workspace segment is removed entirely when no secondary data exists so
    the primary viewport can use the full canvas.
    """

    BG_COLOR = "#0F172A"

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)

        self.primary = tk.Frame(self, bg=self.BG_COLOR)
        self.workspace = tk.Frame(self, bg=self.BG_COLOR)
        self.auxiliary = tk.Frame(self.workspace, bg=self.BG_COLOR)
        self.subwork = tk.Frame(self.workspace, bg=self.BG_COLOR)

        self.workspace.grid_rowconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(1, weight=1)

        self.primary.pack(fill=tk.BOTH, expand=True)

    def set_workspace_visible(self, auxiliary: bool, subwork: bool) -> None:
        """Show or hide the secondary segment and its two panels."""
        if not (auxiliary or subwork):
            self.auxiliary.grid_remove()
            self.subwork.grid_remove()
            self.workspace.pack_forget()
            return

        if self.workspace.winfo_manager() != "pack":
            self.workspace.pack(
                side=tk.BOTTOM,
                fill=tk.X,
                before=self.primary,
            )

        if auxiliary:
            self.auxiliary.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(0, 4),
            )
        else:
            self.auxiliary.grid_remove()

        if subwork:
            self.subwork.grid(
                row=0,
                column=1,
                sticky="nsew",
                padx=(4, 0),
            )
        else:
            self.subwork.grid_remove()

        # Give the visible columns equal weight without reserving space for a
        # hidden partner.
        self.workspace.grid_columnconfigure(0, weight=1 if auxiliary else 0)
        self.workspace.grid_columnconfigure(1, weight=1 if subwork else 0)
