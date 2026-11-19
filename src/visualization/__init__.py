"""Visualization layer for Trace."""

from src.visualization.array_state import (
    BOX_BORDER_COLORS,
    BOX_FILL_COLORS,
    HIGHLIGHT_COLORS,
    ArrayElementState,
    ArrayViewState,
    ElementHighlight,
)
from src.visualization.auxiliary_canvas import AuxiliaryLinearCanvas
from src.visualization.dashboard import MultiViewDashboard
from src.visualization.event_processor import EventProcessor
from src.visualization.graph_canvas import GraphCanvas, compute_graph_layout
from src.visualization.hash_canvas import AuxiliaryHashCanvas
from src.visualization.linked_list_canvas import LinkedListCanvas
from src.visualization.panel import CollapsiblePanel
from src.visualization.recursion_canvas import RecursionCanvas
from src.visualization.text_detail import (
    DetailPopup,
    TextDetailController,
    format_value,
    truncate_text,
)
from src.visualization.tree_canvas import BinaryTreeCanvas
from src.visualization.viewport import ScrollableCanvas

__all__ = [
    "ElementHighlight",
    "HIGHLIGHT_COLORS",
    "BOX_FILL_COLORS",
    "BOX_BORDER_COLORS",
    "ArrayElementState",
    "ArrayViewState",
    "EventProcessor",
    "AuxiliaryLinearCanvas",
    "AuxiliaryHashCanvas",
    "MultiViewDashboard",
    "LinkedListCanvas",
    "BinaryTreeCanvas",
    "GraphCanvas",
    "compute_graph_layout",
    "RecursionCanvas",
    "CollapsiblePanel",
    "ScrollableCanvas",
    "DetailPopup",
    "TextDetailController",
    "format_value",
    "truncate_text",
]
