"""Tests for comparison and swap tracking (T010)."""

from src.execution.events import EventType
from src.execution.runner import CodeRunner
from src.execution.worker import execute_code


def test_comparison_tracking_distinguished_and_details() -> None:
    """Verify comparisons produce COMPARISON events with operands and indices."""
    code = """def compare_test(arr):
    if arr[0] > arr[1]:
        return True
    return False
"""
    result = execute_code(code, [50, 20])
    assert result.is_success is True

    comp_events = [e for e in result.events if e.get("event_type") == EventType.COMPARISON.value]
    assert len(comp_events) == 1

    event = comp_events[0]
    assert event["line_number"] == 2
    assert event["indices"] == [0, 1]
    assert event["values"] == [50, 20]
    assert event["metadata"]["op"] == ">"
    assert event["metadata"]["result"] is True


def test_swap_tracking_canonical_pattern() -> None:
    """Verify arr[i], arr[j] = arr[j], arr[i] produces a SWAP event."""
    code = """def swap_test(arr):
    arr[0], arr[1] = arr[1], arr[0]
"""
    initial = [100, 200]
    result = execute_code(code, initial)

    assert result.is_success is True
    assert result.final_array == [200, 100]

    swap_events = [e for e in result.events if e.get("event_type") == EventType.SWAP.value]
    assert len(swap_events) == 1

    event = swap_events[0]
    assert event["line_number"] == 2
    assert event["indices"] == [0, 1]
    assert event["metadata"]["val_before"] == [100, 200]
    assert event["metadata"]["val_after"] == [200, 100]
    assert event["array_state"] == [200, 100]


def test_bubble_sort_comparisons_and_swaps_sequence() -> None:
    """Verify bubble sort produces both comparison and swap events in correct order."""
    code = """def bubble_sort(arr):
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
"""
    initial = [3, 1, 2]
    result = execute_code(code, initial)

    assert result.is_success is True
    assert result.final_array == [1, 2, 3]

    comparisons = [e for e in result.events if e.get("event_type") == EventType.COMPARISON.value]
    swaps = [e for e in result.events if e.get("event_type") == EventType.SWAP.value]

    # For [3, 1, 2]:
    # Pass 1:
    # compare 3, 1 -> True -> swap 3, 1 (arr becomes [1, 3, 2])
    # compare 3, 2 -> True -> swap 3, 2 (arr becomes [1, 2, 3])
    # Pass 2:
    # compare 1, 2 -> False
    assert len(comparisons) == 3
    assert len(swaps) == 2

    assert swaps[0]["indices"] == [0, 1]
    assert swaps[0]["array_state"] == [1, 3, 2]

    assert swaps[1]["indices"] == [1, 2]
    assert swaps[1]["array_state"] == [1, 2, 3]


def test_comparison_with_variable_operand() -> None:
    """Verify comparisons where one operand is a variable (e.g. key < arr[j])."""
    code = """def var_compare(arr):
    key = 15
    if key < arr[0]:
        return True
    return False
"""
    result = execute_code(code, [20])
    assert result.is_success is True

    comp_events = [e for e in result.events if e.get("event_type") == EventType.COMPARISON.value]
    assert len(comp_events) == 1
    assert comp_events[0]["indices"] == [0]
    assert comp_events[0]["values"] == [15, 20]
    assert comp_events[0]["metadata"]["result"] is True


def test_all_five_algorithms_produce_traces() -> None:
    """Verify that all five initial target sorting algorithms execute with full tracing."""
    runner = CodeRunner()

    algorithms = {
        "bubble_sort": """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
""",
        "selection_sort": """
def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
""",
        "insertion_sort": """
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
""",
        "quick_sort": """
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
""",
        "merge_sort": """
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
""",
    }

    test_input = [5, 2, 9, 1, 5, 6]
    expected_sorted = sorted(test_input)

    for name, code in algorithms.items():
        result = runner.run(code, test_input, function_name=name)
        assert result.is_success is True, f"{name} failed with error: {result.error}"
        assert result.final_array == expected_sorted, f"{name} output {result.final_array} != {expected_sorted}"
        assert len(result.events) > 0, f"{name} produced 0 events"

        event_types = {e.event_type for e in result.events}
        # Every algorithm should have line executions and comparisons or writes/swaps
        assert EventType.LINE in event_types, f"{name} has no LINE events"
        assert (
            EventType.COMPARISON in event_types
            or EventType.SWAP in event_types
            or EventType.WRITE in event_types
        ), f"{name} has no operation events"
