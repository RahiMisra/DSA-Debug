"""Segmented multi-view dashboard container (T037/T041)."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from src.visualization.panel import CollapsiblePanel


class MultiViewDashboard(tk.Frame):
    """Primary viewport above a resizable secondary workspace.

    The dashboard uses a vertical ``PanedWindow`` so the divider between the
    primary view and the workspace can be dragged. The workspace itself uses a
    two-column grid for the auxiliary and subwork segments.
    """

    BG_COLOR = "#0F172A"
    MIN_PRIMARY_HEIGHT = 180
    MIN_WORKSPACE_HEIGHT = 120
    MIN_SEGMENT_WIDTH = 180

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)

        self.panes = tk.PanedWindow(
            self,
            orient=tk.VERTICAL,
            bg=self.BG_COLOR,
            sashwidth=7,
            sashrelief=tk.FLAT,
            bd=0,
            opaqueresize=True,
        )
        self.panes.pack(fill=tk.BOTH, expand=True)

        self.primary_panel = CollapsiblePanel(
            self.panes,
            title="Execution Visualization",
        )
        self.primary = self.primary_panel.body
        self.primary.pack(fill=tk.BOTH, expand=True)
        self.panes.add(
            self.primary_panel,
            minsize=self.MIN_PRIMARY_HEIGHT,
            stretch="always",
        )

        self.workspace_host = tk.Frame(self.panes, bg=self.BG_COLOR)
        self.workspace = tk.Frame(self.workspace_host, bg=self.BG_COLOR)
        self.workspace.pack(fill=tk.BOTH, expand=True)
        self.workspace.grid_rowconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(1, weight=1)

        self.auxiliary_segment = tk.Frame(self.workspace, bg=self.BG_COLOR)
        self.auxiliary_panel = CollapsiblePanel(
            self.auxiliary_segment,
            title="Stack / Queue",
        )
        self.auxiliary = self.auxiliary_panel.body
        self.auxiliary_panel.pack(fill=tk.BOTH, expand=True)

        self.hash_panel = CollapsiblePanel(
            self.auxiliary_segment,
            title="Hash Map / Set",
        )
        self.hash = self.hash_panel.body
        self.hash_panel.pack(fill=tk.BOTH, expand=True)

        self.subwork_segment = tk.Frame(self.workspace, bg=self.BG_COLOR)
        self.subwork_panel = CollapsiblePanel(
            self.subwork_segment,
            title="Recursion & Subwork",
        )
        self.subwork = self.subwork_panel.body
        self.subwork_panel.pack(fill=tk.BOTH, expand=True)

        self._auxiliary_visible = False
        self._subwork_visible = False

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def set_auxiliary_panels(self, linear: bool, hashes: bool) -> None:
        """Show/hide the stack-queue and hash panels independently."""
        self.auxiliary_panel.set_visible(linear)
        self.hash_panel.set_visible(hashes)

    def set_workspace_visible(self, auxiliary: bool, subwork: bool) -> None:
        """Show or hide the secondary workspace and its two segments."""
        self._auxiliary_visible = auxiliary
        self._subwork_visible = subwork

        if not (auxiliary or subwork):
            if self.workspace.winfo_manager() == "pack":
                self.workspace.pack_forget()
            self._remove_workspace_pane()
            return

        if self.workspace.winfo_manager() != "pack":
            self.workspace.pack(fill=tk.BOTH, expand=True)
        self._add_workspace_pane()

        if auxiliary:
            self.auxiliary_segment.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=(0, 4),
            )
        else:
            self.auxiliary_segment.grid_remove()

        if subwork:
            self.subwork_segment.grid(
                row=0,
                column=1,
                sticky="nsew",
                padx=(4, 0),
            )
        else:
            self.subwork_segment.grid_remove()

        self.workspace.grid_columnconfigure(
            0,
            weight=1 if auxiliary else 0,
            minsize=self.MIN_SEGMENT_WIDTH if auxiliary else 0,
        )
        self.workspace.grid_columnconfigure(
            1,
            weight=1 if subwork else 0,
            minsize=self.MIN_SEGMENT_WIDTH if subwork else 0,
        )

    def _add_workspace_pane(self) -> None:
        if str(self.workspace_host) in self.panes.panes():
            return
        self.panes.add(
            self.workspace_host,
            minsize=self.MIN_WORKSPACE_HEIGHT,
            stretch="always",
        )

    def _remove_workspace_pane(self) -> None:
        if str(self.workspace_host) not in self.panes.panes():
            return
        try:
            self.panes.forget(self.workspace_host)
        except tk.TclError:
            pass
