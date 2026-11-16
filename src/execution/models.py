"""Standard data structure models for LeetCode-style problem execution."""

from __future__ import annotations

from collections import deque
from typing import Any, Optional


class ListNode:
    """Singly-linked list node compatible with LeetCode conventions."""

    def __init__(self, val: Any = 0, next: Optional[ListNode] = None) -> None:
        self.val = val
        self.next = next

    def to_list(self) -> list[Any]:
        """Convert linked list to Python list, handling cycles safely."""
        result: list[Any] = []
        visited = set()
        curr: Optional[ListNode] = self
        while curr is not None:
            if id(curr) in visited:
                break
            visited.add(id(curr))
            result.append(curr.val)
            curr = curr.next
        return result

    @classmethod
    def from_list(cls, values: list[Any]) -> Optional[ListNode]:
        """Construct a linked list from a Python list."""
        if not values:
            return None
        head = cls(values[0])
        curr = head
        for val in values[1:]:
            curr.next = cls(val)
            curr = curr.next
        return head

    def __repr__(self) -> str:
        items = []
        visited = set()
        curr: Optional[ListNode] = self
        while curr is not None:
            if id(curr) in visited:
                items.append(f"[Cycle to {curr.val}]")
                break
            visited.add(id(curr))
            items.append(str(curr.val))
            curr = curr.next
        return " -> ".join(items) if items else "Empty"

    def to_dict(self) -> dict[str, Any]:
        """Serialize linked list node for IPC."""
        return {"val": self.val, "values": self.to_list()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Optional[ListNode]:
        """Deserialize linked list from dict."""
        values = data.get("values", [])
        return cls.from_list(values)


class TreeNode:
    """Binary tree node compatible with LeetCode conventions."""

    def __init__(
        self,
        val: Any = 0,
        left: Optional[TreeNode] = None,
        right: Optional[TreeNode] = None,
    ) -> None:
        self.val = val
        self.left = left
        self.right = right

    @classmethod
    def from_level_order(cls, values: list[Any]) -> Optional[TreeNode]:
        """Construct binary tree from level-order array with nulls."""
        if not values or values[0] is None:
            return None

        root = cls(values[0])
        queue: deque[TreeNode] = deque([root])
        idx = 1
        n = len(values)

        while queue and idx < n:
            curr = queue.popleft()

            # Left child
            if idx < n:
                left_val = values[idx]
                idx += 1
                if left_val is not None:
                    curr.left = cls(left_val)
                    queue.append(curr.left)

            # Right child
            if idx < n:
                right_val = values[idx]
                idx += 1
                if right_val is not None:
                    curr.right = cls(right_val)
                    queue.append(curr.right)

        return root

    def to_level_order(self) -> list[Any]:
        """Convert binary tree to level-order list with None for nulls."""
        result: list[Any] = []
        queue: deque[Optional[TreeNode]] = deque([self])

        while queue:
            curr = queue.popleft()
            if curr is not None:
                result.append(curr.val)
                queue.append(curr.left)
                queue.append(curr.right)
            else:
                result.append(None)

        # Trim trailing None values
        while result and result[-1] is None:
            result.pop()
        return result

    def __repr__(self) -> str:
        return f"TreeNode({self.to_level_order()})"

    def to_dict(self) -> dict[str, Any]:
        """Serialize tree node for IPC."""
        return {"val": self.val, "values": self.to_level_order()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Optional[TreeNode]:
        """Deserialize tree from dict."""
        values = data.get("values", [])
        return cls.from_level_order(values)
