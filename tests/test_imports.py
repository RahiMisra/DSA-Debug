"""Test that all application modules import without error."""

import importlib
import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "src",
        "src.main",
        "src.ui",
        "src.ui.main_window",
        "src.ui.code_editor",
        "src.ui.input_panel",
        "src.ui.array_view",
        "src.ui.execution_controls",
        "src.execution",
        "src.execution.runner",
        "src.execution.worker",
        "src.execution.tracer",
        "src.execution.events",
        "src.execution.instrumentation",
        "src.visualization",
        "src.visualization.array_state",
        "src.visualization.event_processor",
    ],
)
def test_module_imports(module_name: str) -> None:
    """Verify that each module in the project structure can be imported."""
    module = importlib.import_module(module_name)
    assert module is not None
