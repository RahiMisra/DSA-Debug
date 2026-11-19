"""LeetCode preset definitions shared by the input panel and code editor."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Optional

DEFAULT_ARRAY_INPUT = "nums = [64, 34, 25, 12, 22, 11, 90]"


def random_array_input() -> str:
    """Return a fresh random array declaration for the Array preset."""
    values = random.sample(range(5, 100), k=random.randint(8, 12))
    return f"nums = {values}"


@dataclass(frozen=True)
class Preset:
    """A complete LeetCode example: input declaration plus runnable code."""

    label: str
    input_text: str
    code: str
    function_name: str
    input_factory: Optional[Callable[[], str]] = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("Preset label must not be empty.")
        if not self.input_text.strip() and self.input_factory is None:
            raise ValueError(f"Preset '{self.label}' has no input.")
        if not self.code.strip():
            raise ValueError(f"Preset '{self.label}' has no code.")
        if not self.function_name.strip():
            raise ValueError(f"Preset '{self.label}' has no function name.")

    def build_input(self) -> str:
        """Return this preset's input, generating a new one when configured."""
        if self.input_factory is not None:
            return self.input_factory()
        return self.input_text


ARRAY_PRESET = Preset(
    label="Array",
    input_text=DEFAULT_ARRAY_INPUT,
    code="""def bubble_sort(nums):
    n = len(nums)
    for i in range(n):
        for j in range(0, n - i - 1):
            if nums[j] > nums[j + 1]:
                nums[j], nums[j + 1] = nums[j + 1], nums[j]
""",
    function_name="bubble_sort",
    input_factory=random_array_input,
    description="Bubble Sort over a newly generated array.",
)

STRING_PRESET = Preset(
    label="String",
    input_text='s = "anagram", t = "nagaram"',
    code="""def is_anagram(s, t):
    if len(s) != len(t):
        return False
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in t:
        counts[ch] = counts.get(ch, 0) - 1
        if counts[ch] < 0:
            return False
    return True
""",
    function_name="is_anagram",
    description="Valid Anagram using a frequency map.",
)

LINKED_LIST_PRESET = Preset(
    label="Linked List",
    input_text="head = [1, 2, 3, 4, 5]",
    code="""def traverse_linked_list(head):
    curr = head
    while curr is not None:
        curr = curr.next
    return head
""",
    function_name="traverse_linked_list",
    description="Traverse a singly linked list.",
)

BINARY_TREE_PRESET = Preset(
    label="Binary Tree",
    input_text="root = [10, 5, 20, null, null, 15, 30], target = 15",
    code="""def search_bst(root, target=15):
    curr = root
    while curr is not None:
        if curr.val == target:
            return curr
        elif target < curr.val:
            curr = curr.left
        else:
            curr = curr.right
    return None
""",
    function_name="search_bst",
    description="Search a binary search tree for a target value.",
)

GRAPH_PRESET = Preset(
    label="Graph",
    input_text="isConnected = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]",
    code="""def count_provinces(isConnected):
    n = len(isConnected)
    visited = [False] * n
    provinces = 0
    for start in range(n):
        if not visited[start]:
            provinces += 1
            stack = [start]
            while stack:
                node = stack.pop()
                visited[node] = True
                for neighbor in range(n):
                    if isConnected[node][neighbor] == 1 and not visited[neighbor]:
                        stack.append(neighbor)
    return provinces
""",
    function_name="count_provinces",
    description="Count connected components in an adjacency matrix.",
)

STACK_QUEUE_PRESET = Preset(
    label="Stack / Queue",
    input_text="nums = [3, 1, 4, 1, 5]",
    code="""from collections import deque

def stack_and_queue(nums):
    stack = []
    queue = deque()
    for n in nums:
        stack.append(n)
        queue.append(n)
    result = []
    while stack:
        result.append(stack.pop())
    while queue:
        result.append(queue.popleft())
    return result
""",
    function_name="stack_and_queue",
    description="Push into a stack and queue, then drain both.",
)

HASH_PRESET = Preset(
    label="Hash Map / Set",
    input_text="nums = [2, 7, 2, 7, 3]",
    code="""def hash_demo(nums):
    counts = {}
    seen = set()
    for n in nums:
        counts[n] = counts.get(n, 0) + 1
        if n not in seen:
            seen.add(n)
    return len(counts)
""",
    function_name="hash_demo",
    description="Build a frequency map and a seen set.",
)

PRESETS: tuple[Preset, ...] = (
    ARRAY_PRESET,
    STRING_PRESET,
    LINKED_LIST_PRESET,
    BINARY_TREE_PRESET,
    GRAPH_PRESET,
    STACK_QUEUE_PRESET,
    HASH_PRESET,
)

PRESETS_BY_LABEL: dict[str, Preset] = {preset.label: preset for preset in PRESETS}


def get_preset(label: str) -> Optional[Preset]:
    """Return the preset with the given label, or None when unknown."""
    return PRESETS_BY_LABEL.get(label)
