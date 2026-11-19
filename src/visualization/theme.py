"""Central visual theme tokens and ttk styling for Trace (T045).

This module is the single source of truth for colours. UI and visualization
modules import :data:`PALETTE` (or the semantic canvas maps below) instead of
defining their own hex literals. Importing this module has no Tkinter side
effects; call :func:`apply_theme` once a root window exists.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Optional


@dataclass(frozen=True)
class Palette:
    """Named colour tokens for every surface, text role, accent, and control."""

    # Background levels, darkest to lightest.
    bg_root: str = "#0B0B12"
    bg_base: str = "#12121A"
    bg_surface: str = "#1A1A24"
    bg_raised: str = "#242432"
    bg_item: str = "#2B2B3C"
    bg_active: str = "#36364A"
    bg_hover: str = "#2F2F42"

    # Borders, separators, and depth.
    border: str = "#31314A"
    border_strong: str = "#46465F"
    divider: str = "#252536"
    inset_highlight: str = "#3A3A52"
    shadow: str = "#07070C"

    # Text roles.
    text: str = "#D6DAF0"
    text_muted: str = "#9A9FB8"
    text_faint: str = "#7E839E"
    text_inverse: str = "#0B0B12"

    # Accents and highlights.
    accent: str = "#89B4FA"
    accent_hover: str = "#A4C6FF"
    accent_pressed: str = "#6F9BE8"
    success: str = "#A6E3A1"
    danger: str = "#F38BA8"
    danger_hover: str = "#FF9DB4"
    warning: str = "#F9E2AF"
    mauve: str = "#CBA6F7"
    pink: str = "#F5C2E7"

    # Buttons.
    button_bg: str = "#262636"
    button_hover: str = "#323249"
    button_pressed: str = "#3B3B54"
    button_text: str = "#E6E9F7"
    button_disabled_bg: str = "#1D1D28"
    button_disabled_text: str = "#5B5F78"

    # Text inputs.
    entry_bg: str = "#232333"
    entry_border: str = "#35354C"
    entry_text: str = "#F2F4FF"
    focus_ring: str = "#89B4FA"

    # Code editor.
    editor_bg: str = "#14141E"
    editor_gutter_bg: str = "#101018"
    editor_highlight_bg: str = "#33334A"
    editor_highlight_text: str = "#F5E0DC"

    # Scrollbars.
    scrollbar_trough: str = "#14141E"
    scrollbar_thumb: str = "#34344A"
    scrollbar_hover: str = "#454560"
    scrollbar_active: str = "#5A5A7A"
    scrollbar_border: str = "#252536"
    scrollbar_arrow: str = "#9A9FB8"

    # Canvas surfaces.
    canvas_bg: str = "#12121A"
    canvas_surface: str = "#1A1A24"
    canvas_item: str = "#2B2B3C"
    canvas_active: str = "#36364A"
    canvas_text: str = "#D6DAF0"
    canvas_muted: str = "#8A90AA"
    canvas_baseline: str = "#2A2A3A"
    canvas_empty: str = "#7E839E"

    # Canvas semantic tokens (nodes, edges, and data-structure accents).
    node_bg: str = "#2B2B3C"
    node_border: str = "#6E93D8"
    node_active_border: str = "#F9E2AF"
    edge: str = "#5A5F7A"
    pointer: str = "#F9E2AF"
    null: str = "#7E839E"
    stack: str = "#89B4FA"
    queue: str = "#A6E3A1"
    hash_map: str = "#CBA6F7"
    hash_set: str = "#F5C2E7"
    recursion_frame: str = "#89B4FA"
    recursion_subarray: str = "#A6E3A1"
    recursion_return: str = "#F5C2E7"
    operation: str = "#F9E2AF"
    cycle: str = "#F38BA8"
    baseline: str = "#2A2A3A"


PALETTE = Palette()

VERTICAL_SCROLLBAR_STYLE = "Trace.Vertical.TScrollbar"
HORIZONTAL_SCROLLBAR_STYLE = "Trace.Horizontal.TScrollbar"

# Semantic array highlight colours. Keys are the lowercase names of
# ``ElementHighlight`` members; ``array_state`` maps them onto the enum.
ARRAY_HIGHLIGHT_COLORS: dict[str, str] = {
    "default": "#3B82F6",
    "comparing": "#F59E0B",
    "swapping": "#EF4444",
    "writing": "#8B5CF6",
    "reading": "#10B981",
    "sorted": "#059669",
}

ARRAY_BOX_FILL_COLORS: dict[str, str] = {
    "default": "#1E293B",
    "comparing": "#78350F",
    "swapping": "#7F1D1D",
    "writing": "#581C87",
    "reading": "#064E3B",
    "sorted": "#065F46",
}

ARRAY_BOX_BORDER_COLORS: dict[str, str] = {
    "default": "#475569",
    "comparing": "#F59E0B",
    "swapping": "#EF4444",
    "writing": "#A855F7",
    "reading": "#10B981",
    "sorted": "#34D399",
}

GRAPH_STATE_FILL_COLORS: dict[str, str] = {
    "frontier": "#3E3A2B",
    "explored": "#1E3A2F",
    "active": "#3A2430",
}


def apply_theme(root: tk.Misc) -> ttk.Style:
    """Apply the shared palette and ttk scrollbar styles to ``root``.

    Safe to call more than once. Returns the :class:`ttk.Style` instance so
    callers/tests can inspect the resolved style values.
    """
    style = ttk.Style(root)
    try:
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass

    palette = PALETTE
    for name in (VERTICAL_SCROLLBAR_STYLE, HORIZONTAL_SCROLLBAR_STYLE):
        style.configure(
            name,
            gripcount=0,
            background=palette.scrollbar_thumb,
            troughcolor=palette.scrollbar_trough,
            bordercolor=palette.scrollbar_border,
            darkcolor=palette.scrollbar_trough,
            lightcolor=palette.scrollbar_thumb,
            arrowcolor=palette.scrollbar_arrow,
            relief="flat",
        )
        style.map(
            name,
            background=[
                ("pressed", palette.scrollbar_active),
                ("active", palette.scrollbar_hover),
            ],
            arrowcolor=[
                ("pressed", palette.text),
                ("active", palette.text),
            ],
        )

    try:
        root.configure(bg=palette.bg_root)
    except tk.TclError:
        pass
    return style


def surface_kwargs(
    bg: Optional[str] = None,
    *,
    border: bool = True,
) -> dict:
    """Return constructor keyword arguments for a layered panel surface."""
    palette = PALETTE
    kwargs = {"bg": bg or palette.bg_base}
    if border:
        kwargs.update(
            highlightthickness=1,
            highlightbackground=palette.border,
            highlightcolor=palette.border,
        )
    return kwargs


def style_button(button: tk.Button, variant: str = "default") -> tk.Button:
    """Apply themed normal, hover, pressed, and disabled states to a button.

    ``tk.Button`` uses ``activebackground`` for hover. Press and release are
    bound explicitly so flat buttons still show a pressed state.
    """
    palette = PALETTE
    if variant == "primary":
        normal_bg, hover_bg, pressed_bg = (
            palette.accent,
            palette.accent_hover,
            palette.accent_pressed,
        )
        normal_fg = palette.text_inverse
    elif variant == "chip":
        normal_bg, hover_bg, pressed_bg = (
            palette.button_bg,
            palette.button_hover,
            palette.button_pressed,
        )
        normal_fg = palette.text
    elif variant == "ghost":
        normal_bg, hover_bg, pressed_bg = (
            palette.bg_surface,
            palette.bg_active,
            palette.bg_item,
        )
        normal_fg = palette.text_muted
    elif variant == "danger":
        normal_bg, hover_bg, pressed_bg = (
            palette.danger,
            palette.danger_hover,
            palette.danger,
        )
        normal_fg = palette.text_inverse
    else:
        normal_bg, hover_bg, pressed_bg = (
            palette.button_bg,
            palette.button_hover,
            palette.button_pressed,
        )
        normal_fg = palette.button_text

    button.configure(
        bg=normal_bg,
        fg=normal_fg,
        activebackground=hover_bg,
        activeforeground=normal_fg,
        disabledforeground=palette.button_disabled_text,
        relief=tk.FLAT,
        bd=0,
        highlightthickness=1,
        highlightbackground=palette.border,
        highlightcolor=palette.focus_ring,
        cursor="hand2",
    )
    button._trace_normal_bg = normal_bg  # type: ignore[attr-defined]
    button._trace_pressed_bg = pressed_bg  # type: ignore[attr-defined]
    button._trace_normal_fg = normal_fg  # type: ignore[attr-defined]

    button.bind(
        "<ButtonPress-1>",
        lambda _event, btn=button: _set_button_pressed(btn, True),
        add="+",
    )
    button.bind(
        "<ButtonRelease-1>",
        lambda _event, btn=button: _set_button_pressed(btn, False),
        add="+",
    )
    return button


def restore_button(button: tk.Button) -> None:
    """Restore a themed button's normal background and foreground."""
    button.configure(
        bg=getattr(button, "_trace_normal_bg", PALETTE.button_bg),
        fg=getattr(button, "_trace_normal_fg", PALETTE.button_text),
    )


def _set_button_pressed(button: tk.Button, pressed: bool) -> None:
    if str(button.cget("state")) == "disabled":
        return
    if pressed:
        button.configure(
            bg=getattr(button, "_trace_pressed_bg", PALETTE.button_pressed)
        )
    else:
        restore_button(button)
