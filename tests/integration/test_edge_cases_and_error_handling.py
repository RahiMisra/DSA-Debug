"""Tests validating edge cases and error handling (T018)."""

from src.execution.result import ExecutionStatus
from src.execution.runner import CodeRunner
from src.ui.input_panel import InputPanel


def test_edge_case_empty_array() -> None:
    """Verify empty arrays execute cleanly without crashing."""
    runner = CodeRunner()
    code = "def sort(arr): arr.sort()"
    result = runner.run(code, [])
    assert result.is_success is True
    assert result.final_array == []


def test_edge_case_single_element() -> None:
    """Verify single-element arrays execute cleanly."""
    runner = CodeRunner()
    code = "def sort(arr): pass"
    result = runner.run(code, [42])
    assert result.is_success is True
    assert result.final_array == [42]


def test_edge_case_duplicates_negatives_zeros() -> None:
    """Verify arrays containing duplicates, negatives, and zeros."""
    runner = CodeRunner()
    code = """def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
    initial = [0, -10, 5, -10, 0, 3, -1, 5]
    result = runner.run(code, initial)
    assert result.is_success is True
    assert result.final_array == sorted(initial)


def test_error_handling_syntax_error() -> None:
    """Verify syntax errors return clear error feedback and line number."""
    runner = CodeRunner()
    bad_code = "def bad(arr):\n    if len(arr) > 0\n        pass\n"
    result = runner.run(bad_code, [1, 2])
    assert result.is_success is False
    assert result.status == ExecutionStatus.SYNTAX_ERROR
    assert result.error is not None
    assert result.error.line_number == 2
    assert "expected ':'" in result.error.message.lower() or "syntax" in result.error.message.lower()


def test_error_handling_runtime_error() -> None:
    """Verify runtime errors return exception type, message, and line number."""
    runner = CodeRunner()
    bad_code = "def bad(arr):\n    arr[999] = 1\n"
    result = runner.run(bad_code, [1, 2])
    assert result.is_success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.error is not None
    assert result.error.error_type == "IndexError"
    assert result.error.line_number == 2


def test_error_handling_timeout_termination() -> None:
    """Verify runaway execution (infinite while loop) is safely terminated."""
    runner = CodeRunner()
    infinite_code = "def loop(arr):\n    while True:\n        pass\n"
    result = runner.run(infinite_code, [1, 2], timeout_seconds=0.4)
    assert result.is_success is False
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.error is not None
    assert "0.4 seconds" in result.error.message


def test_input_panel_array_parsing_edge_cases() -> None:
    """Verify InputPanel handles various valid and invalid text representations."""
    panel = InputPanel()

    # Valid with spaces, negatives, zeros
    panel.set_array_text(" -5,  0, 10,   -2 ")
    assert panel.parse_array() == [-5, 0, 10, -2]

    # Empty text
    panel.set_array_text("")
    assert panel.parse_array() == []

    # Invalid text raises ValueError
    panel.set_array_text("1, 2, abc, 4")
    try:
        panel.parse_array()
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    panel.destroy()
