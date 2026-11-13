"""Visualization layer for Trace."""

from src.visualization.array_state import (
    HIGHLIGHT_COLORS,
    ArrayElementState,
    ArrayViewState,
    ElementHighlight,
)
from src.visualization.event_processor import EventProcessor

__all__ = [
    "ElementHighlight",
    "HIGHLIGHT_COLORS",
    "ArrayElementState",
    "ArrayViewState",
    "EventProcessor",
]
