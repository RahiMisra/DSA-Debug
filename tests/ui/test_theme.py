"""Tests for the centralized palette, ttk styling, and visual depth (T044/T046)."""

from __future__ import annotations

import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path

from src.ui.array_view import ArrayView
from src.ui.main_window import MainWindow
from src.visualization.graph_canvas import GraphCanvas
from src.visualization.theme import (
    ARRAY_BOX_BORDER_COLORS,
    ARRAY_BOX_FILL_COLORS,
    ARRAY_HIGHLIGHT_COLORS,
    GRAPH_STATE_FILL_COLORS,
    HORIZONTAL_SCROLLBAR_STYLE,
    PALETTE,
    VERTICAL_SCROLLBAR_STYLE,
    apply_theme,
)

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
HEX_IN_TEXT_RE = re.compile(r"#[0-9A-Fa-f]{6}")

REQUIRED_TOKENS = (
    "bg_root",
    "bg_base",
    "bg_surface",
    "bg_raised",
    "bg_item",
    "bg_active",
    "border",
    "border_strong",
    "divider",
    "text",
    "text_muted",
    "text_faint",
    "accent",
    "success",
    "danger",
    "warning",
    "button_bg",
    "button_hover",
    "button_pressed",
    "button_disabled_bg",
    "button_disabled_text",
    "entry_bg",
    "entry_text",
    "editor_bg",
    "editor_gutter_bg",
    "editor_highlight_bg",
    "scrollbar_trough",
    "scrollbar_thumb",
    "scrollbar_hover",
    "scrollbar_active",
    "scrollbar_border",
)


def _channel(value: float) -> float:
    value = value / 255.0
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(color: str) -> float:
    red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
    return (
        0.2126 * _channel(red)
        + 0.7152 * _channel(green)
        + 0.0722 * _channel(blue)
    )


def _contrast(foreground: str, background: str) -> float:
    lighter = max(_luminance(foreground), _luminance(background))
    darker = min(_luminance(foreground), _luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _window(root: tk.Tk) -> MainWindow:
    apply_theme(root)
    window = MainWindow(root=tk.Toplevel(root))
    window.root.deiconify()
    window.root.update_idletasks()
    return window


def test_palette_exposes_named_tokens_for_every_role() -> None:
    """Verify background, surface, border, text, accent, and scrollbar tokens exist."""
    for token in REQUIRED_TOKENS:
        value = getattr(PALETTE, token)
        assert HEX_RE.match(value), f"{token}={value!r} is not a hex colour"


def test_semantic_canvas_maps_use_hex_colours() -> None:
    """Verify array and graph semantic colour maps are complete and valid."""
    expected_highlights = {
        "default",
        "comparing",
        "swapping",
        "writing",
        "reading",
        "sorted",
    }
    assert set(ARRAY_HIGHLIGHT_COLORS) == expected_highlights
    assert set(ARRAY_BOX_FILL_COLORS) == expected_highlights
    assert set(ARRAY_BOX_BORDER_COLORS) == expected_highlights
    for mapping in (
        ARRAY_HIGHLIGHT_COLORS,
        ARRAY_BOX_FILL_COLORS,
        ARRAY_BOX_BORDER_COLORS,
        GRAPH_STATE_FILL_COLORS,
    ):
        for name, value in mapping.items():
            assert HEX_RE.match(value), f"{name}={value!r} is not a hex colour"


def test_text_contrast_meets_wcag_aa_on_surfaces() -> None:
    """Verify normal text reaches 4.5:1 and muted text reaches 4.5:1 on base surfaces."""
    surfaces = (
        PALETTE.bg_root,
        PALETTE.bg_base,
        PALETTE.bg_surface,
        PALETTE.bg_raised,
        PALETTE.bg_item,
        PALETTE.bg_active,
    )
    for background in surfaces:
        assert _contrast(PALETTE.text, background) >= 4.5

    for background in (PALETTE.bg_root, PALETTE.bg_base, PALETTE.bg_surface):
        assert _contrast(PALETTE.text_muted, background) >= 4.5
        assert _contrast(PALETTE.text_faint, background) >= 4.5

    assert _contrast(PALETTE.entry_text, PALETTE.entry_bg) >= 4.5
    assert _contrast(PALETTE.text, PALETTE.editor_bg) >= 4.5
    assert _contrast(PALETTE.button_text, PALETTE.button_bg) >= 4.5
    assert _contrast(PALETTE.text_inverse, PALETTE.accent) >= 4.5
    # Disabled controls are intentionally exempt from WCAG AA contrast.


def test_importing_theme_has_no_tkinter_side_effects() -> None:
    """Verify importing the theme does not create a Tk root or touch a display."""
    root = Path(__file__).resolve().parents[2]
    code = (
        "import tkinter as tk; "
        "import src.visualization.theme as theme; "
        "print(tk._default_root is None, theme.PALETTE.bg_root)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True #0B0B12"


def test_apply_theme_styles_scrollbar_trough_thumb_and_states(
    session_tk_root: tk.Tk,
) -> None:
    """Verify ttk scrollbars resolve themed trough, thumb, hover, and pressed colours."""
    style = apply_theme(session_tk_root)

    for name in (VERTICAL_SCROLLBAR_STYLE, HORIZONTAL_SCROLLBAR_STYLE):
        assert style.lookup(name, "troughcolor") == PALETTE.scrollbar_trough
        assert style.lookup(name, "background") == PALETTE.scrollbar_thumb
        mapping = dict(style.map(name, "background"))
        assert mapping["active"] == PALETTE.scrollbar_hover
        assert mapping["pressed"] == PALETTE.scrollbar_active


def test_key_widgets_resolve_to_theme_tokens(session_tk_root: tk.Tk) -> None:
    """Verify root, panels, editor, controls, dashboard, and canvases use the palette."""
    window = _window(session_tk_root)
    try:
        assert window.root.cget("bg") == PALETTE.bg_root
        assert window.input_panel.cget("bg") == PALETTE.bg_base
        assert window.editor.cget("bg") == PALETTE.editor_bg
        assert window.editor.text.cget("bg") == PALETTE.editor_bg
        assert window.editor.gutter.cget("bg") == PALETTE.editor_gutter_bg
        assert window.controls.cget("bg") == PALETTE.bg_base
        assert window.dashboard.cget("bg") == PALETTE.bg_base
        assert window.array_view.cget("bg") == PALETTE.canvas_bg
        assert window.array_view.canvas.cget("bg") == PALETTE.canvas_bg
        assert window.error_banner.cget("bg") == PALETTE.danger
    finally:
        window.close()


def test_buttons_expose_hover_pressed_and_disabled_tokens(
    session_tk_root: tk.Tk,
) -> None:
    """Verify primary, chip, and control buttons carry themed interaction states."""
    window = _window(session_tk_root)
    try:
        run = window.input_panel.run_btn
        assert run.cget("bg") == PALETTE.accent
        assert run.cget("activebackground") == PALETTE.accent_hover
        assert run.cget("disabledforeground") == PALETTE.button_disabled_text
        assert str(run.cget("cursor")) == "hand2"

        chip = window.input_panel.preset_buttons["Array"]
        assert chip.cget("bg") == PALETTE.button_bg
        assert chip.cget("activebackground") == PALETTE.button_hover

        window.controls.set_state(total_steps=2, current_step=0)
        reset = window.controls.btn_reset
        assert reset.cget("bg") == PALETTE.button_bg
        assert reset.cget("activebackground") == PALETTE.button_hover
        assert reset.cget("activeforeground") == PALETTE.button_text

        window.controls.set_state(total_steps=0, current_step=-1)
        assert reset.cget("bg") == PALETTE.button_disabled_bg
        assert reset.cget("fg") == PALETTE.button_disabled_text
    finally:
        window.close()


def test_panels_have_layered_surfaces_and_visible_dividers(
    session_tk_root: tk.Tk,
) -> None:
    """Verify panels expose an inset border and dashboard headers read as surfaces."""
    window = _window(session_tk_root)
    try:
        assert int(window.input_panel.cget("highlightthickness")) == 1
        assert window.input_panel.cget("highlightbackground") == PALETTE.border

        panel = window.dashboard.primary_panel
        assert int(panel.cget("highlightthickness")) == 1
        assert panel.header.cget("bg") == PALETTE.bg_surface
        assert panel.header_border.cget("bg") == PALETTE.border
        assert panel.body.cget("bg") == PALETTE.bg_base
        assert window.dashboard.panes.cget("bg") == PALETTE.divider
    finally:
        window.close()


def test_canvas_cards_have_inset_or_shadow_treatment(
    session_tk_root: tk.Tk,
) -> None:
    """Verify array cells and node cards carry cheap depth cues."""
    apply_theme(session_tk_root)

    array = ArrayView(session_tk_root)
    array.pack()
    array.set_array([1, 2, 3])
    assert array.canvas.find_withtag("box_inset")

    graph = GraphCanvas(session_tk_root)
    graph.pack()
    graph.render_state(
        {
            "nodes": [
                {"id": 0, "val": 0, "state": "unvisited"},
                {"id": 1, "val": 1, "state": "unvisited"},
            ],
            "edges": [{"source": 0, "target": 1}],
            "pointers": {},
            "directed": False,
        }
    )
    assert graph.canvas.find_withtag("graph_node_shadow")

    array.destroy()
    graph.destroy()


def test_ui_and_visualization_modules_have_no_raw_hex_outside_theme() -> None:
    """Verify colour literals live only in the theme module."""
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for folder in (root / "src" / "ui", root / "src" / "visualization"):
        for path in sorted(folder.glob("*.py")):
            if path.name == "theme.py":
                continue
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if HEX_IN_TEXT_RE.search(line):
                    offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert offenders == [], "raw hex colours found:\n" + "\n".join(offenders)
