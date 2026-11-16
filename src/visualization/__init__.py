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

__all__ = [
    "ElementHighlight",
    "HIGHLIGHT_COLORS",
    "BOX_FILL_COLORS",
    "BOX_BORDER_COLORS",
    "ArrayElementState",
    "ArrayViewState",
    "EventProcessor",
]
