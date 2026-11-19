"""Tests for the responsive workspace and collapsible panels (T040/T041)."""

from __future__ import annotations

import tkinter as tk

from src.ui.main_window import MainWindow
from src.visualization.dashboard import MultiViewDashboard

AUXILIARY_CODE = """
def analyze(nums):
    stack = []
    seen = set()
    for n in nums:
        stack.append(n)
        seen.add(n)
    return len(stack)
"""


def _new_window(root: tk.Tk) -> MainWindow:
    window = MainWindow(root=tk.Toplevel(root))
    window.root.geometry("1100x760")
    window.root.deiconify()
    window.root.update()
    return window


def test_dashboard_has_vertical_panes_panel_headers_and_minimums(
    session_tk_root: tk.Tk,
) -> None:
    """Verify the dashboard exposes a resizable pane layout and headers."""
    window = _new_window(session_tk_root)
    dashboard = window.dashboard

    assert isinstance(dashboard, MultiViewDashboard)
    assert str(dashboard.panes.cget("orient")) == "vertical"
    assert dashboard.primary_panel.title_label.cget("text") == "Execution Visualization"
    assert dashboard.auxiliary_panel.title_label.cget("text") == "Stack / Queue"
    assert dashboard.hash_panel.title_label.cget("text") == "Hash Map / Set"
    assert dashboard.subwork_panel.title_label.cget("text") == "Recursion & Subwork"

    assert int(dashboard.panes.panecget(dashboard.primary_panel, "minsize")) >= 180

    dashboard.set_workspace_visible(auxiliary=True, subwork=True)
    window.root.update_idletasks()
    assert int(dashboard.panes.panecget(dashboard.workspace_host, "minsize")) >= 120
    window.close()


def test_workspace_stays_within_bounds_at_default_and_minimum_sizes(
    session_tk_root: tk.Tk,
) -> None:
    """Verify both workspace segments remain visible and positive at minimum size."""
    window = _new_window(session_tk_root)
    dashboard = window.dashboard
    dashboard.set_auxiliary_panels(True, True)
    dashboard.set_workspace_visible(auxiliary=True, subwork=True)
    window.root.update_idletasks()

    assert dashboard.workspace.winfo_manager() == "pack"
    assert dashboard.auxiliary_segment.winfo_width() > 0
    assert dashboard.auxiliary_segment.winfo_height() > 0
    assert dashboard.subwork_segment.winfo_width() > 0
    assert dashboard.subwork_segment.winfo_height() > 0
    assert dashboard.primary.winfo_height() >= dashboard.MIN_PRIMARY_HEIGHT

    window.root.geometry("880x620")
    window.root.update()
    assert dashboard.primary.winfo_height() > 0
    assert dashboard.workspace.winfo_height() > 0
    assert dashboard.primary.winfo_height() >= dashboard.MIN_PRIMARY_HEIGHT

    workspace_width = dashboard.workspace.winfo_width()
    for segment in (dashboard.auxiliary_segment, dashboard.subwork_segment):
        assert segment.winfo_x() >= 0
        assert segment.winfo_x() + segment.winfo_width() <= workspace_width + 2

    window.close()


def test_only_one_visible_workspace_segment_uses_full_width(
    session_tk_root: tk.Tk,
) -> None:
    """Verify a lone auxiliary or subwork segment fills the workspace width."""
    window = _new_window(session_tk_root)
    dashboard = window.dashboard

    dashboard.set_auxiliary_panels(True, False)
    dashboard.set_workspace_visible(auxiliary=True, subwork=False)
    window.root.update_idletasks()
    assert dashboard.auxiliary_segment.winfo_width() >= dashboard.workspace.winfo_width() - 8
    assert dashboard.subwork_segment.winfo_manager() == ""

    dashboard.set_auxiliary_panels(False, False)
    dashboard.set_workspace_visible(auxiliary=False, subwork=True)
    window.root.update_idletasks()
    assert dashboard.subwork_segment.winfo_width() >= dashboard.workspace.winfo_width() - 8
    assert dashboard.auxiliary_segment.winfo_manager() == ""

    window.close()


def test_collapse_keeps_header_and_persists_across_steps(
    session_tk_root: tk.Tk,
) -> None:
    """Verify a collapsed primary panel keeps its header and stays collapsed."""
    window = _new_window(session_tk_root)
    window.input_panel.set_array_text("nums = [4, 3, 2, 1]")
    window.handle_run()
    window.step_forward()
    state_before = window.array_view.current_state

    panel = window.dashboard.primary_panel
    panel.toggle()
    window.root.update_idletasks()
    assert panel.is_collapsed is True
    assert panel.body.winfo_manager() == ""
    assert panel.header.winfo_manager() == "pack"

    for _ in range(3):
        window.step_forward()
    assert panel.is_collapsed is True
    assert panel.body.winfo_manager() == ""
    assert window.array_view.current_state is not None

    panel.toggle()
    window.root.update_idletasks()
    assert panel.is_collapsed is False
    assert panel.body.winfo_manager() == "pack"
    assert window.array_view.current_state is not None
    assert state_before is not None

    window.close()


def test_auxiliary_panels_hide_without_data_and_keep_collapse_state(
    session_tk_root: tk.Tk,
) -> None:
    """Verify data panels hide when empty but preserve their collapsed state."""
    window = _new_window(session_tk_root)
    window.editor.set_code(AUXILIARY_CODE)
    window.input_panel.set_array_text("nums = [3, 1, 2]")
    window.handle_run()

    saw_both = False
    for _ in range(len(window.history)):
        window.step_forward()
        if (
            window.dashboard.auxiliary_panel.is_visible
            and window.dashboard.hash_panel.is_visible
        ):
            saw_both = True
            break

    assert saw_both is True
    window.dashboard.hash_panel.set_collapsed(True)
    window.root.update_idletasks()
    assert window.dashboard.hash_panel.is_collapsed is True

    window.reset_execution()
    window.root.update_idletasks()
    assert window.dashboard.auxiliary_panel.is_visible is False
    assert window.dashboard.hash_panel.is_visible is False
    assert window.dashboard.workspace.winfo_manager() != "pack"

    for _ in range(len(window.history)):
        window.step_forward()
        if window.dashboard.hash_panel.is_visible:
            break

    assert window.dashboard.hash_panel.is_visible is True
    assert window.dashboard.hash_panel.is_collapsed is True
    assert window.dashboard.hash_panel.body.winfo_manager() == ""

    window.close()
