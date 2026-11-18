"""Tests for basic code execution (T005)."""

from src.execution.result import ExecutionStatus
from src.execution.worker import execute_code


def test_execute_bubble_sort_success() -> None:
    """Verify executing a valid bubble sort function sorts an array in-place."""
    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
    initial = [64, 34, 25, 12, 22, 11, 90]
    result = execute_code(code, initial)

    assert result.is_success is True
    assert result.status == ExecutionStatus.SUCCESS
    assert result.final_array == [11, 12, 22, 25, 34, 64, 90]
    assert result.execution_time_ms >= 0.0


def test_execute_selection_sort_with_explicit_function_name() -> None:
    """Verify selecting a specific function name when multiple exist."""
    code = """
def helper(x):
    return x * 2

def selection_sort(arr):
    for i in range(len(arr)):
        min_idx = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
"""
    initial = [29, 10, 14, 37, 13]
    result = execute_code(code, initial, function_name="selection_sort")

    assert result.is_success is True
    assert result.final_array == [10, 13, 14, 29, 37]


def test_auto_detect_prefers_sort_over_declaration_order() -> None:
    """Verify a helper defined first does not shadow an unselected sort function."""
    code = """
def helper(x):
    return x

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
    result = execute_code(code, [3, 1, 2])

    assert result.is_success is True, result.error
    assert result.final_array == [1, 2, 3]


def test_execute_empty_and_single_element_arrays() -> None:
    """Verify executing on empty and single-element arrays."""
    code = """
def sort(arr):
    arr.sort()
"""
    empty_res = execute_code(code, [])
    assert empty_res.is_success is True
    assert empty_res.final_array == []

    single_res = execute_code(code, [42])
    assert single_res.is_success is True
    assert single_res.final_array == [42]


def test_execute_arrays_with_negatives_and_duplicates() -> None:
    """Verify executing on arrays with duplicate, negative, and zero values."""
    code = """
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
"""
    initial = [0, -5, 3, -5, 2, 0, -1]
    result = execute_code(code, initial)
    assert result.is_success is True
    assert result.final_array == [-5, -5, -1, 0, 0, 2, 3]


def test_execute_syntax_error() -> None:
    """Verify syntax errors return appropriate status and line number."""
    bad_code = """
def broken_sort(arr):
    if len(arr) > 0
        arr[0] = 1
"""
    result = execute_code(bad_code, [1, 2, 3])
    assert result.is_success is False
    assert result.status == ExecutionStatus.SYNTAX_ERROR
    assert result.error is not None
    assert result.error.error_type == "SyntaxError"
    assert result.error.line_number == 3


def test_execute_runtime_error() -> None:
    """Verify runtime errors capture line number and message."""
    bad_code = """
def faulty_sort(arr):
    # This will trigger IndexError
    return arr[100]
"""
    result = execute_code(bad_code, [1, 2, 3])
    assert result.is_success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert result.error is not None
    assert result.error.error_type == "IndexError"
    assert result.error.line_number == 4


def test_execute_nonexistent_function_name() -> None:
    """Verify requesting a nonexistent function name returns an error."""
    code = "def my_sort(arr): pass"
    result = execute_code(code, [1, 2], function_name="other_sort")
    assert result.is_success is False
    assert result.status == ExecutionStatus.RUNTIME_ERROR
    assert "not found" in result.error.message


def test_execute_with_user_print_statements() -> None:
    """Verify user code with print statements runs cleanly without errors."""
    code = """
def sort_with_print(arr):
    print("Sorting array:", arr)
    arr.sort()
    print("Done sorting")
"""
    result = execute_code(code, [3, 2, 1])
    assert result.is_success is True
    assert result.final_array == [1, 2, 3]
