"""Visualization layer for Trace."""

from src.visualization.array_state import (
    BOX_BORDER_COLORS,
    BOX_FILL_COLORS,
    HIGHLIGHT_COLORS,
    ArrayElementState,
    ArrayViewState,
    ElementHighlight,
)
from src.visualization.event_processor import EventProcessor
from src.visualization.linked_list_canvas import LinkedListCanvas
from src.visualization.tree_canvas import BinaryTreeCanvas

__all__ = [
    "ElementHighlight",
    "HIGHLIGHT_COLORS",
    "BOX_FILL_COLORS",
    "BOX_BORDER_COLORS",
    "ArrayElementState",
    "ArrayViewState",
    "EventProcessor",
    "LinkedListCanvas",
    "BinaryTreeCanvas",
]
