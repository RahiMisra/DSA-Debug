"""Tests for LeetCode-style input parsing and standard data models (T022)."""

import pytest
from src.execution.models import ListNode, TreeNode
from src.execution.parsers import parse_leetcode_inputs
from src.execution.runner import CodeRunner


# 1. ListNode Model Tests
def test_list_node_creation_and_conversion() -> None:
    """Verify ListNode creation, from_list, and to_list."""
    head = ListNode.from_list([1, 2, 3, 4, 5])
    assert head is not None
    assert head.val == 1
    assert head.next.val == 2
    assert head.to_list() == [1, 2, 3, 4, 5]
    assert "1 -> 2 -> 3 -> 4 -> 5" in repr(head)

    # Empty list
    empty = ListNode.from_list([])
    assert empty is None


def test_list_node_cycle_handling() -> None:
    """Verify ListNode handles cyclic lists safely without infinite loops."""
    n1 = ListNode(1)
    n2 = ListNode(2)
    n1.next = n2
    n2.next = n1  # Cycle

    # to_list stops at cycle
    assert n1.to_list() == [1, 2]
    assert "[Cycle to 1]" in repr(n1)


# 2. TreeNode Model Tests
def test_tree_node_from_level_order() -> None:
    """Verify constructing TreeNode from level-order array with nulls."""
    # [3, 9, 20, None, None, 15, 7]
    root = TreeNode.from_level_order([3, 9, 20, None, None, 15, 7])
    assert root is not None
    assert root.val == 3
    assert root.left.val == 9
    assert root.right.val == 20
    assert root.left.left is None
    assert root.left.right is None
    assert root.right.left.val == 15
    assert root.right.right.val == 7

    assert root.to_level_order() == [3, 9, 20, None, None, 15, 7]

    # Empty tree
    assert TreeNode.from_level_order([]) is None
    assert TreeNode.from_level_order([None]) is None


# 3. LeetCode Input Parser Tests
def test_parse_plain_array() -> None:
    """Verify parsing plain array input with or without variable name."""
    res1 = parse_leetcode_inputs("[10, 20, 30]")
    assert "nums" in res1
    assert res1["nums"] == [10, 20, 30]

    res2 = parse_leetcode_inputs("nums = [5, 2, 8]")
    assert res2["nums"] == [5, 2, 8]

    # Comma-separated ints
    res3 = parse_leetcode_inputs("1, 2, 3")
    assert res3["nums"] == [1, 2, 3]


def test_parse_linked_list_input() -> None:
    """Verify parsing head = [1,2,3,4,5] into ListNode."""
    res = parse_leetcode_inputs("head = [1, 2, 3, 4, 5]")
    assert "head" in res
    assert isinstance(res["head"], ListNode)
    assert res["head"].to_list() == [1, 2, 3, 4, 5]


def test_parse_binary_tree_input_with_null() -> None:
    """Verify parsing root = [3,9,20,null,null,15,7] with JS null literals."""
    res = parse_leetcode_inputs("root = [3, 9, 20, null, null, 15, 7]")
    assert "root" in res
    assert isinstance(res["root"], TreeNode)
    assert res["root"].val == 3
    assert res["root"].left.val == 9
    assert res["root"].right.val == 20
    assert res["root"].right.left.val == 15
    assert res["root"].right.right.val == 7


def test_parse_graph_inputs() -> None:
    """Verify parsing graph adjacency matrix and edge lists."""
    res_matrix = parse_leetcode_inputs("isConnected = [[1,1,0],[1,1,0],[0,0,1]]")
    assert "isConnected" in res_matrix
    assert res_matrix["isConnected"] == [[1, 1, 0], [1, 1, 0], [0, 0, 1]]

    res_edges = parse_leetcode_inputs("edges = [[0, 1], [1, 2], [2, 0]]")
    assert "edges" in res_edges
    assert res_edges["edges"] == [[0, 1], [1, 2], [2, 0]]


def test_parse_multiple_arguments() -> None:
    """Verify parsing multiple mixed arguments on single and multiple lines."""
    # Single line separated by comma
    res1 = parse_leetcode_inputs('nums = [2, 7, 11, 15], target = 9')
    assert res1["nums"] == [2, 7, 11, 15]
    assert res1["target"] == 9

    # Strings
    res2 = parse_leetcode_inputs('s = "anagram", t = "nagaram"')
    assert res2["s"] == "anagram"
    assert res2["t"] == "nagaram"

    # Multi-line
    multi_line = """
head = [1, 2, 3]
k = 2
"""
    res3 = parse_leetcode_inputs(multi_line)
    assert isinstance(res3["head"], ListNode)
    assert res3["head"].to_list() == [1, 2, 3]
    assert res3["k"] == 2


def test_parse_malformed_input_raises_error() -> None:
    """Verify malformed input raises a descriptive ValueError."""
    with pytest.raises(ValueError):
        parse_leetcode_inputs("head = [1, 2, unclosed")


# 4. User Code Execution with Auto-Injected Models
def test_execution_with_auto_injected_list_node() -> None:
    """Verify user code can use ListNode without manually defining it."""
    runner = CodeRunner()
    code = """
def reverse_list(head):
    prev = None
    curr = head
    while curr:
        next_temp = curr.next
        curr.next = prev
        prev = curr
        curr = next_temp
    return prev
"""
    parsed = parse_leetcode_inputs("head = [1, 2, 3]")
    result = runner.run(code, parsed)
    assert result.is_success is True
    # Returned structure is a reversed ListNode
    assert result.final_array == [3, 2, 1]


def test_execution_with_auto_injected_tree_node() -> None:
    """Verify user code can use TreeNode without manually defining it."""
    runner = CodeRunner()
    code = """
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
"""
    parsed = parse_leetcode_inputs("root = [3, 9, 20, null, null, 15, 7]")
    result = runner.run(code, parsed)
    assert result.is_success is True
    assert result.final_array == 3  # Depth of the tree is 3
