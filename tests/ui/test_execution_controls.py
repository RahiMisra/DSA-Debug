"""Tests for ExecutionControls component (T015)."""

import tkinter as tk
from src.ui.execution_controls import ExecutionControls


def test_execution_controls_initial_state(session_tk_root: tk.Tk) -> None:
    """Verify initial disabled/enabled button states when no execution loaded."""
    controls = ExecutionControls(master=session_tk_root)

    # When 0 steps, all step buttons should be disabled
    assert str(controls.btn_reset["state"]) == "disabled"
    assert str(controls.btn_backward["state"]) == "disabled"
    assert str(controls.btn_forward["state"]) == "disabled"
    assert str(controls.btn_play["state"]) == "disabled"
    assert "0 / 0" in controls.lbl_step["text"]

    controls.destroy()


def test_execution_controls_state_transitions(session_tk_root: tk.Tk) -> None:
    """Verify button enabling/disabling at beginning, middle, and end of history."""
    controls = ExecutionControls(master=session_tk_root)
    total_steps = 10

    # At start (step -1)
    controls.set_state(total_steps=total_steps, current_step=-1)
    assert str(controls.btn_reset["state"]) == "disabled"
    assert str(controls.btn_backward["state"]) == "disabled"
    assert str(controls.btn_forward["state"]) == "normal"
    assert str(controls.btn_play["state"]) == "normal"

    # In middle (step 4)
    controls.set_state(total_steps=total_steps, current_step=4)
    assert str(controls.btn_reset["state"]) == "normal"
    assert str(controls.btn_backward["state"]) == "normal"
    assert str(controls.btn_forward["state"]) == "normal"
    assert str(controls.btn_play["state"]) == "normal"
    assert "Step: 5 / 10" in controls.lbl_step["text"]

    # At end (step 9)
    controls.set_state(total_steps=total_steps, current_step=9)
    assert str(controls.btn_reset["state"]) == "normal"
    assert str(controls.btn_backward["state"]) == "normal"
    assert str(controls.btn_forward["state"]) == "disabled"
    assert str(controls.btn_play["state"]) == "disabled"
    assert "Step: 10 / 10" in controls.lbl_step["text"]

    controls.destroy()
