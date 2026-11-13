"""Validation tests for the five initial sorting algorithms (T017)."""

from src.execution.events import EventType, ExecutionHistory
from src.execution.runner import CodeRunner

BUBBLE_SORT = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""

SELECTION_SORT = """
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
"""

INSERTION_SORT = """
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
"""

QUICK_SORT = """
def quick_sort(arr):
    def partition(low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        return i + 1

    def sort_helper(low, high):
        if low < high:
            pi = partition(low, high)
            sort_helper(low, pi - 1)
            sort_helper(pi + 1, high)

    sort_helper(0, len(arr) - 1)
"""

MERGE_SORT = """
def merge_sort(arr):
    def merge(left, mid, right):
        L = arr[left:mid + 1]
        R = arr[mid + 1:right + 1]
        i = 0
        j = 0
        k = left
        while i < len(L) and j < len(R):
            if L[i] <= R[j]:
                arr[k] = L[i]
                i += 1
            else:
                arr[k] = R[j]
                j += 1
            k += 1
        while i < len(L):
            arr[k] = L[i]
            i += 1
            k += 1
        while j < len(R):
            arr[k] = R[j]
            j += 1
            k += 1

    def sort_helper(left, right):
        if left < right:
            mid = (left + right) // 2
            sort_helper(left, mid)
            sort_helper(mid + 1, right)
            merge(left, mid, right)

    sort_helper(0, len(arr) - 1)
"""


def _validate_algorithm(code: str, func_name: str, test_arr: list[int]) -> None:
    runner = CodeRunner()
    result = runner.run(code, test_arr, function_name=func_name)

    assert result.is_success is True, f"{func_name} failed: {result.error}"
    assert result.final_array == sorted(test_arr), f"{func_name} produced unsorted array: {result.final_array}"
    assert len(result.events) > 0, f"{func_name} produced no execution events"

    # Verify history navigability
    history = ExecutionHistory.from_dict({"initial_array": test_arr, "events": result.events})
    assert history.get_array_at_step(-1) == test_arr
    assert history.get_array_at_step(len(history) - 1) == sorted(test_arr)

    # Verify all event array snapshots have correct length
    for step_idx in range(len(history)):
        state = history.get_array_at_step(step_idx)
        assert len(state) == len(test_arr)


def test_validate_bubble_sort() -> None:
    """Validate Bubble sort execution, sorting, and history navigation."""
    _validate_algorithm(BUBBLE_SORT, "bubble_sort", [38, 27, 43, 3, 9, 82, 10])


def test_validate_selection_sort() -> None:
    """Validate Selection sort execution, sorting, and history navigation."""
    _validate_algorithm(SELECTION_SORT, "selection_sort", [64, 25, 12, 22, 11])


def test_validate_insertion_sort() -> None:
    """Validate Insertion sort execution, sorting, and history navigation."""
    _validate_algorithm(INSERTION_SORT, "insertion_sort", [12, 11, 13, 5, 6])


def test_validate_quick_sort() -> None:
    """Validate Quick sort execution, sorting, and history navigation."""
    _validate_algorithm(QUICK_SORT, "quick_sort", [10, 80, 30, 90, 40, 50, 70])


def test_validate_merge_sort() -> None:
    """Validate in-place Merge sort execution, sorting, and history navigation."""
    _validate_algorithm(MERGE_SORT, "merge_sort", [12, 11, 13, 5, 6, 7])
