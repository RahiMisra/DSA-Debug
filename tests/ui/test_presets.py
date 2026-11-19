"""Tests for the LeetCode preset library and default algorithms (T038)."""

from __future__ import annotations

import inspect
import tkinter as tk

from src.execution.parsers import parse_leetcode_inputs
from src.execution.worker import execute_code
from src.ui.input_panel import InputPanel
from src.ui.main_window import MainWindow
from src.ui.presets import PRESETS, get_preset


def _executed_namespace(code: str) -> dict:
    namespace: dict = {}
    exec(code, namespace)
    return namespace


def test_preset_catalog_is_complete() -> None:
    """Verify every preset has input, code, and a named entry function."""
    labels = [preset.label for preset in PRESETS]

    assert labels == [
        "Array",
        "String",
        "Linked List",
        "Binary Tree",
        "Graph",
        "Stack / Queue",
        "Hash Map / Set",
    ]
    assert len(labels) == len(set(labels))
    assert "Random Array" not in labels

    for preset in PRESETS:
        assert preset.input_text.strip(), preset.label
        assert preset.code.strip(), preset.label
        assert f"def {preset.function_name}(" in preset.code, preset.label


def test_preset_parameters_match_parsed_inputs() -> None:
    """Verify preset function parameters are supplied by the preset input."""
    for preset in PRESETS:
        inputs = parse_leetcode_inputs(preset.build_input())
        namespace = _executed_namespace(preset.code)
        function = namespace[preset.function_name]
        parameters = [
            parameter.name
            for parameter in inspect.signature(function).parameters.values()
            if parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]

        assert set(parameters) <= set(inputs), (
            preset.label,
            parameters,
            list(inputs),
        )


def test_every_preset_executes_successfully() -> None:
    """Verify every preset is a complete, runnable example."""
    for preset in PRESETS:
        inputs = parse_leetcode_inputs(preset.build_input())
        result = execute_code(preset.code, inputs)

        assert result.is_success is True, (preset.label, result.error)
        assert result.events, preset.label


def test_array_preset_generates_fresh_input(monkeypatch) -> None:
    """Verify the Array preset builds a new valid array on every activation."""
    values = iter([list(range(10, 18)), list(range(20, 28))])
    monkeypatch.setattr(
        "src.ui.presets.random.sample",
        lambda population, k: next(values),
    )
    monkeypatch.setattr("src.ui.presets.random.randint", lambda low, high: 8)

    preset = get_preset("Array")
    assert preset is not None

    first = preset.build_input()
    second = preset.build_input()

    assert first != second
    for text in (first, second):
        parsed = parse_leetcode_inputs(text)
        assert len(parsed["nums"]) == 8
        assert all(5 <= value <= 99 for value in parsed["nums"])


def test_input_panel_builds_buttons_from_preset_library(
    session_tk_root: tk.Tk,
) -> None:
    """Verify preset buttons come from the shared library and Random Array is gone."""
    panel = InputPanel(master=session_tk_root)

    assert set(panel.preset_buttons) == {preset.label for preset in PRESETS}
    assert "Random Array" not in panel.preset_buttons

    panel.destroy()


def test_array_button_regenerates_input(
    session_tk_root: tk.Tk,
    monkeypatch,
) -> None:
    """Verify clicking Array replaces the input with a newly generated array."""
    values = iter([list(range(10, 18)), list(range(20, 28))])
    monkeypatch.setattr(
        "src.ui.presets.random.sample",
        lambda population, k: next(values),
    )
    monkeypatch.setattr("src.ui.presets.random.randint", lambda low, high: 8)

    panel = InputPanel(master=session_tk_root)
    panel.preset_buttons["Array"].invoke()
    first = panel.get_array_text()
    panel.preset_buttons["Array"].invoke()
    second = panel.get_array_text()

    assert first != second
    assert first.startswith("nums = ")
    assert second.startswith("nums = ")

    panel.destroy()


def test_preset_selection_updates_input_and_editor(session_tk_root: tk.Tk) -> None:
    """Verify selecting a preset updates both the input field and editor code."""
    root = tk.Toplevel(session_tk_root)
    window = MainWindow(root=root)

    for label in (
        "String",
        "Linked List",
        "Binary Tree",
        "Graph",
        "Stack / Queue",
        "Hash Map / Set",
    ):
        preset = get_preset(label)
        assert preset is not None
        window.input_panel.preset_buttons[label].invoke()

        assert window.input_panel.get_array_text() == preset.input_text
        assert window.editor.get_code().strip() == preset.code.strip()

    window.input_panel.preset_buttons["Array"].invoke()
    assert window.input_panel.get_array_text().startswith("nums = ")
    assert "def bubble_sort(nums):" in window.editor.get_code()

    window.close()


def test_string_preset_produces_character_snapshots() -> None:
    """Verify string preset inputs are visualized as characters."""
    preset = get_preset("String")
    assert preset is not None

    result = execute_code(
        preset.code,
        parse_leetcode_inputs(preset.build_input()),
    )

    assert result.is_success is True, result.error
    assert any(
        event.array_state == list("anagram")
        for event in result.events
    )


def test_input_panel_parse_array_preserves_string_characters(
    session_tk_root: tk.Tk,
) -> None:
    """Verify string inputs become character arrays for the primary view."""
    panel = InputPanel(master=session_tk_root)
    panel.set_array_text('s = "anagram", t = "nagaram"')

    assert panel.parse_array() == list("anagram")

    panel.destroy()
