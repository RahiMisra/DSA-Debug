"""Integration tests for LeetCode Solution methods and the segmented dashboard (T036)."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from src.execution.events import EventType
from src.execution.worker import execute_code
from src.ui.main_window import MainWindow


REVERSE_LIST = """
class Solution:
    def reverseList(self, head):
        prev = None
        curr = head
        while curr is not None:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        return prev
"""

MERGE_TWO_LISTS = """
class Solution:
    def mergeTwoLists(self, l1, l2):
        dummy = ListNode()
        tail = dummy
        while l1 is not None and l2 is not None:
            if l1.val <= l2.val:
                tail.next = l1
                l1 = l1.next
            else:
                tail.next = l2
                l2 = l2.next
            tail = tail.next
        tail.next = l1 if l1 is not None else l2
        return dummy.next
"""

LOWEST_COMMON_ANCESTOR = """
class Solution:
    def lowestCommonAncestor(self, root, p, q):
        curr = root
        while curr is not None:
            if p < curr.val and q < curr.val:
                curr = curr.left
            elif p > curr.val and q > curr.val:
                curr = curr.right
            else:
                return curr.val
        return None
"""

MAX_DEPTH = """
class Solution:
    def maxDepth(self, root):
        if root is None:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))
"""

INVERT_TREE = """
class Solution:
    def invertTree(self, root):
        if root is None:
            return None
        root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root
"""

VALIDATE_BST = """
class Solution:
    def isValidBST(self, root):
        def validate(node, low, high):
            if node is None:
                return True
            if not (low < node.val < high):
                return False
            return validate(node.left, low, node.val) and validate(
                node.right, node.val, high
            )

        return validate(root, float("-inf"), float("inf"))
"""

NUMBER_OF_ISLANDS = """
class Solution:
    def numIslands(self, grid):
        if not grid:
            return 0
        rows = len(grid)
        cols = len(grid[0])
        count = 0

        def sink(r, c):
            if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] != "1":
                return
            grid[r][c] = "0"
            sink(r + 1, c)
            sink(r - 1, c)
            sink(r, c + 1)
            sink(r, c - 1)

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "1":
                    count += 1
                    sink(r, c)
        return count
"""

CLONE_GRAPH = """
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


class Solution:
    def cloneGraph(self, node):
        if node is None:
            return None

        clones = {}

        def dfs(curr):
            if curr in clones:
                return clones[curr]
            copy = Node(curr.val)
            clones[curr] = copy
            for neighbor in curr.neighbors:
                copy.neighbors.append(dfs(neighbor))
            return copy

        return dfs(node)
"""

VALID_PARENTHESES = """
class Solution:
    def isValid(self, s):
        stack = []
        pairs = {")": "(", "]": "[", "}": "{"}
        for ch in s:
            if ch in pairs:
                if not stack or stack[-1] != pairs[ch]:
                    return False
                stack.pop()
            else:
                stack.append(ch)
        return not stack
"""

QUEUE_WITH_STACKS = """
class Solution:
    def queueUsingStacks(self, nums):
        self.stack_in = []
        self.stack_out = []
        for n in nums:
            self.stack_in.append(n)

        result = []
        while self.stack_in or self.stack_out:
            if not self.stack_out:
                while self.stack_in:
                    self.stack_out.append(self.stack_in.pop())
            result.append(self.stack_out.pop())
        return result
"""

TWO_SUM = """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, n in enumerate(nums):
            complement = target - n
            if complement in seen:
                return [seen[complement], i]
            seen[n] = i
        return []
"""

GROUP_ANAGRAMS = """
class Solution:
    def groupAnagrams(self, strs):
        groups = {}
        for word in strs:
            key = "".join(sorted(word))
            if key in groups:
                groups[key].append(word)
            else:
                groups[key] = [word]
        return list(groups.values())
"""

DASHBOARD_CODE = """
class Solution:
    def analyze(self, nums):
        stack = []
        seen = set()
        for n in nums:
            stack.append(n)
            seen.add(n)

        def split(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left = split(arr[:mid])
            right = split(arr[mid:])
            return left + right

        ordered = split(nums)
        return ordered
"""


def _call_events(result: Any) -> list[Any]:
    """Return CALL events from an execution result."""
    return [event for event in result.events if event.event_type == EventType.CALL]


def _first_call(result: Any) -> dict[str, Any]:
    """Return the first recorded call metadata."""
    calls = _call_events(result)
    assert calls, "expected at least one CALL event"
    return calls[0].metadata["call"]


def _has_metadata(result: Any, key: str) -> bool:
    """Return True when any event carries the given structure metadata."""
    return any(event.metadata.get(key) for event in result.events)


def _canvas_tags(canvas: tk.Canvas) -> set[str]:
    """Collect all tags used on a Tk canvas."""
    tags: set[str] = set()
    for item in canvas.find_all():
        tags.update(canvas.gettags(item))
    return tags


def _canvas_texts(canvas: tk.Canvas, tag: str) -> list[str]:
    """Return the text of every canvas item matching a tag."""
    return [canvas.itemcget(item, "text") for item in canvas.find_withtag(tag)]


# ---------------------------------------------------------------------------
# 1. class Solution execution
# ---------------------------------------------------------------------------


def test_solution_class_method_runs_with_bound_self() -> None:
    """Verify a Solution instance method runs without self being passed as input."""
    result = execute_code(REVERSE_LIST, "head = [1, 2, 3, 4, 5]")

    assert result.is_success is True, result.error
    assert result.final_array == [5, 4, 3, 2, 1]

    call = _first_call(result)
    assert call["function"] == "reverseList"
    assert "self" not in call["args"]
    assert call["args"]["head"] == [1, 2, 3, 4, 5]
    assert _has_metadata(result, "linked_list") is True


def test_solution_class_supports_multiple_linked_list_parameters() -> None:
    """Verify l1/l2 parameters reach a Solution method as linked lists."""
    result = execute_code(MERGE_TWO_LISTS, "l1 = [1, 2, 4], l2 = [1, 3, 4]")

    assert result.is_success is True, result.error
    assert result.final_array == [1, 1, 2, 3, 4, 4]

    call = _first_call(result)
    assert call["function"] == "mergeTwoLists"
    assert call["args"]["l1"] == [1, 2, 4]
    assert call["args"]["l2"] == [1, 3, 4]
    assert _has_metadata(result, "linked_list") is True


def test_solution_class_supports_three_parameters() -> None:
    """Verify root/p/q are bound by name for a multi-parameter Solution method."""
    result = execute_code(
        LOWEST_COMMON_ANCESTOR,
        "root = [6, 2, 8, 0, 4, 7, 9, null, null, 3, 5], p = 2, q = 8",
    )

    assert result.is_success is True, result.error
    assert result.final_array == 6

    call = _first_call(result)
    assert call["function"] == "lowestCommonAncestor"
    assert call["args"]["p"] == 2
    assert call["args"]["q"] == 8
    assert _has_metadata(result, "tree") is True


# ---------------------------------------------------------------------------
# 2. End-to-end LeetCode problem families
# ---------------------------------------------------------------------------


def test_class_solution_tree_problems() -> None:
    """Verify depth, inversion, and BST validation Solution methods run end-to-end."""
    depth = execute_code(MAX_DEPTH, "root = [3, 9, 20, null, null, 15, 7]")
    assert depth.is_success is True, depth.error
    assert depth.final_array == 3

    inverted = execute_code(INVERT_TREE, "root = [4, 2, 7, 1, 3, 6, 9]")
    assert inverted.is_success is True, inverted.error
    assert inverted.final_array == [4, 7, 2, 9, 6, 3, 1]

    valid = execute_code(VALIDATE_BST, "root = [2, 1, 3]")
    assert valid.is_success is True, valid.error
    assert valid.final_array is True
    assert _has_metadata(valid, "tree") is True


def test_class_solution_graph_problems() -> None:
    """Verify island counting and graph cloning Solution methods run end-to-end."""
    islands = execute_code(
        NUMBER_OF_ISLANDS,
        "grid = [[\"1\",\"1\",\"0\",\"0\",\"0\"], "
        "[\"1\",\"1\",\"0\",\"0\",\"0\"], "
        "[\"0\",\"0\",\"1\",\"0\",\"0\"], "
        "[\"0\",\"0\",\"0\",\"1\",\"1\"]]",
    )
    assert islands.is_success is True, islands.error
    assert islands.final_array == 3
    assert _has_metadata(islands, "graph") is True

    cloned = execute_code(CLONE_GRAPH, "adjList = [[2, 4], [1, 3], [2, 4], [1, 3]]")
    assert cloned.is_success is True, cloned.error
    assert cloned.final_array == [[2, 4], [1, 3], [2, 4], [1, 3]]
    assert _has_metadata(cloned, "graph") is True


def test_class_solution_stack_and_hash_problems() -> None:
    """Verify parentheses, queue-with-stacks, Two Sum, and anagram grouping."""
    parentheses = execute_code(VALID_PARENTHESES, 's = "()[]{}"')
    assert parentheses.is_success is True, parentheses.error
    assert parentheses.final_array is True
    assert any(
        event.metadata.get("auxiliary", {}).get("stacks")
        for event in parentheses.events
    )

    queue = execute_code(QUEUE_WITH_STACKS, "nums = [1, 2, 3]")
    assert queue.is_success is True, queue.error
    assert queue.final_array == [1, 2, 3]
    queue_stack_names = {
        stack["name"]
        for event in queue.events
        for stack in event.metadata.get("auxiliary", {}).get("stacks", [])
    }
    assert {"stack_in", "stack_out"} <= queue_stack_names

    two_sum = execute_code(TWO_SUM, "nums = [2, 7, 11, 15], target = 9")
    assert two_sum.is_success is True, two_sum.error
    assert two_sum.final_array == [0, 1]
    assert any(
        event.metadata.get("auxiliary", {}).get("maps")
        for event in two_sum.events
    )

    anagrams = execute_code(GROUP_ANAGRAMS, 'strs = ["eat", "tea", "tan", "ate", "nat", "bat"]')
    assert anagrams.is_success is True, anagrams.error
    assert sorted(sorted(group) for group in anagrams.final_array) == [
        ["ate", "eat", "tea"],
        ["bat"],
        ["nat", "tan"],
    ]


def test_standard_node_structures_do_not_create_graph_metadata() -> None:
    """Verify ListNode/TreeNode values are not misread as object graphs."""
    linked = execute_code(REVERSE_LIST, "head = [1, 2, 3]")
    assert linked.is_success is True, linked.error
    assert _has_metadata(linked, "linked_list") is True
    assert _has_metadata(linked, "graph") is False

    tree = execute_code(MAX_DEPTH, "root = [3, 9, 20, null, null, 15, 7]")
    assert tree.is_success is True, tree.error
    assert _has_metadata(tree, "tree") is True
    assert _has_metadata(tree, "graph") is False


def test_clone_graph_accepts_node_input_and_empty_adjacency() -> None:
    """Verify object-graph coercion handles nested node input and empty graphs."""
    cloned = execute_code(CLONE_GRAPH, "node = [[2, 4], [1, 3], [2, 4], [1, 3]]")
    assert cloned.is_success is True, cloned.error
    assert cloned.final_array == [[2, 4], [1, 3], [2, 4], [1, 3]]
    assert _has_metadata(cloned, "graph") is True

    empty = execute_code(CLONE_GRAPH, "adjList = []")
    assert empty.is_success is True, empty.error
    assert empty.final_array is None


# ---------------------------------------------------------------------------
# 3. Segmented multi-view dashboard
# ---------------------------------------------------------------------------


def test_dashboard_segments_host_the_expected_views(session_tk_root: tk.Tk) -> None:
    """Verify the dashboard exposes primary, auxiliary, and subwork segments."""
    window = MainWindow(root=session_tk_root)

    assert window.dashboard.primary is window.array_view.master
    assert window.dashboard.primary is window.linked_list_view.master
    assert window.dashboard.primary is window.tree_view.master
    assert window.dashboard.primary is window.graph_view.master

    assert window.dashboard.auxiliary is window.auxiliary_view.master
    assert window.dashboard.auxiliary is window.hash_view.master
    assert window.dashboard.subwork is window.recursion_view.master


def test_dashboard_shows_primary_auxiliary_and_subwork_together(
    session_tk_root: tk.Tk,
) -> None:
    """Verify one step can show the primary view plus every secondary segment."""
    window = MainWindow(root=session_tk_root)
    window.editor.set_code(DASHBOARD_CODE)
    window.input_panel.set_array_text("nums = [3, 1, 2]")

    window.handle_run()
    assert window.history is not None
    assert window.error_banner.winfo_manager() == ""
    assert window.dashboard.workspace.winfo_manager() != "pack"

    saw_all_segments = False
    for _ in range(len(window.history)):
        window.step_forward()
        if (
            window.array_view.winfo_manager() == "pack"
            and window.auxiliary_view.winfo_manager() == "pack"
            and window.hash_view.winfo_manager() == "pack"
            and window.recursion_view.winfo_manager() == "pack"
        ):
            saw_all_segments = True
            assert window.dashboard.workspace.winfo_manager() == "pack"
            assert window.dashboard.auxiliary.winfo_manager() != ""
            assert window.dashboard.subwork.winfo_manager() != ""
            break

    assert saw_all_segments is True

    while window.current_step_index < len(window.history) - 1:
        window.step_forward()

    recursion_tags = _canvas_tags(window.recursion_view.canvas)
    assert "recursion_subarray" in recursion_tags
    assert "recursion_return" in recursion_tags
    assert _canvas_texts(window.recursion_view.canvas, "recursion_return_value") == [
        "[3, 1, 2]"
    ]

    window.reset_execution()
    assert window.dashboard.workspace.winfo_manager() != "pack"
    assert window.array_view.winfo_manager() == "pack"
