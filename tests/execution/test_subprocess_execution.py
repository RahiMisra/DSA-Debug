"""Tests for isolated subprocess execution (T006)."""

import os
from src.execution.result import ExecutionStatus
from src.execution.runner import CodeRunner


def test_runner_executes_in_subprocess() -> None:
    """Verify CodeRunner executes a sorting algorithm in a separate process."""
    runner = CodeRunner()
    code = """
import os

def record_pid(arr):
    # Mutate array with current process ID to verify distinct process
    pid = os.getpid()
    arr.clear()
    arr.append(pid)
"""
    main_pid = os.getpid()
    arr = [0]
    result = runner.run(code, arr)

    assert result.is_success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.final_array is not None
    assert len(result.final_array) == 1
    # Verify the code executed in a different process ID
    assert result.final_array[0] != main_pid


def test_runner_sort_execution_success() -> None:
    """Verify standard sorting function in subprocess produces correct result."""
    runner = CodeRunner()
    code = """
def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
    initial = [5, 1, 4, 2, 8]
    result = runner.run(code, initial)

    assert result.is_success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.final_array == [1, 2, 4, 5, 8]


def test_runner_captures_runtime_error_from_subprocess() -> None:
    """Verify runtime error raised inside subprocess is safely caught."""
    runner = CodeRunner()
    code = """
def crash(arr):
    x = 1 / 0
"""
    result = runner.run(code, [1, 2, 3])

    assert result.is_success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.error is not None
    assert result.error.error_type == "ZeroDivisionError"
    assert result.error.line_number == 3


def test_runner_terminates_on_timeout() -> None:
    """Verify runaway execution (infinite loop) is terminated by timeout."""
    runner = CodeRunner()
    code = """
import time

def infinite_loop(arr):
    while True:
        time.sleep(0.05)
"""
    # Use a small timeout of 0.5s for fast test execution
    result = runner.run(code, [1, 2, 3], timeout_seconds=0.5)

    assert result.is_success is False
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.error is not None
    assert result.error.error_type == "TimeoutError"
    assert "0.5 seconds" in result.error.message


def test_runner_handles_abnormal_worker_exit() -> None:
    """Verify that a sudden process exit does not crash the runner."""
    runner = CodeRunner()
    code = """
import os

def hard_exit(arr):
    os._exit(42)
"""
    result = runner.run(code, [1, 2])

    assert result.is_success is False
    assert result.status == ExecutionStatus.INTERNAL_ERROR
    assert result.error is not None
    assert "42" in result.error.message or "produced no output" in result.error.message


def test_runner_in_process_fallback() -> None:
    """Verify run_in_process method executes correctly."""
    runner = CodeRunner()
    code = "def sort(arr): arr.sort()"
    result = runner.run_in_process(code, [3, 1, 2])
    assert result.is_success is True
    assert result.final_array == [1, 2, 3]


def test_runner_captures_syntax_error_from_subprocess() -> None:
    """Verify syntax error in subprocess returns SYNTAX_ERROR with line number."""
    runner = CodeRunner()
    bad_code = "def bad_sort(arr):\n    for i in \n        pass"
    result = runner.run(bad_code, [1, 2, 3])
    assert result.is_success is False
    assert result.status == ExecutionStatus.SYNTAX_ERROR
    assert result.error is not None
    assert result.error.line_number == 2


def test_runner_quick_sort_in_place() -> None:
    """Verify quicksort implementation in subprocess."""
    runner = CodeRunner()
    code = """
def quick_sort(arr):
    def _quick_sort(items, low, high):
        if low < high:
            pivot = items[high]
            i = low - 1
            for j in range(low, high):
                if items[j] <= pivot:
                    i += 1
                    items[i], items[j] = items[j], items[i]
            items[i + 1], items[high] = items[high], items[i + 1]
            p = i + 1
            _quick_sort(items, low, p - 1)
            _quick_sort(items, p + 1, high)
    _quick_sort(arr, 0, len(arr) - 1)
"""
    initial = [10, 7, 8, 9, 1, 5, -2, 0, 7]
    result = runner.run(code, initial)
    assert result.is_success is True
    assert result.final_array == [-2, 0, 1, 5, 7, 7, 8, 9, 10]


def test_runner_handles_large_array() -> None:
    """Verify handling of larger array input (100 elements)."""
    runner = CodeRunner()
    code = """
def sort(arr):
    arr.sort()
"""
    initial = list(range(100, 0, -1))
    result = runner.run(code, initial)
    assert result.is_success is True
    assert result.final_array == list(range(1, 101))
