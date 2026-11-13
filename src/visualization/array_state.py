"""Array state representation for visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ElementHighlight(str, Enum):
    """Highlight categories for array elements."""

    DEFAULT = "DEFAULT"
    COMPARING = "COMPARING"
    SWAPPING = "SWAPPING"
    WRITING = "WRITING"
    READING = "READING"
    SORTED = "SORTED"


# Color mapping for UI canvas rendering
HIGHLIGHT_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: "#3B82F6",    # Blue
    ElementHighlight.COMPARING: "#F59E0B",  # Amber / Yellow
    ElementHighlight.SWAPPING: "#EF4444",   # Red
    ElementHighlight.WRITING: "#8B5CF6",    # Purple
    ElementHighlight.READING: "#10B981",    # Emerald Green
    ElementHighlight.SORTED: "#059669",     # Dark Green
}


@dataclass
class ArrayElementState:
    """State of a single array element in the visualizer."""

    index: int
    value: int
    highlight: ElementHighlight = ElementHighlight.DEFAULT

    @property
    def color(self) -> str:
        """Hex color code corresponding to current highlight."""
        return HIGHLIGHT_COLORS.get(self.highlight, HIGHLIGHT_COLORS[ElementHighlight.DEFAULT])


@dataclass
class ArrayViewState:
    """Manages the visual array state and active element highlights."""

    elements: list[ArrayElementState] = field(default_factory=list)

    @classmethod
    def from_array(
        cls,
        array: list[int],
        highlights: Optional[dict[int, ElementHighlight]] = None,
    ) -> ArrayViewState:
        """Construct an ArrayViewState from a list of integers and optional highlight map."""
        hl_map = highlights or {}
        elements = [
            ArrayElementState(
                index=i,
                value=val,
                highlight=hl_map.get(i, ElementHighlight.DEFAULT),
            )
            for i, val in enumerate(array)
        ]
        return cls(elements=elements)

    def set_array(self, array: list[int]) -> None:
        """Update element values while preserving length/indices."""
        self.elements = [
            ArrayElementState(index=i, value=val, highlight=ElementHighlight.DEFAULT)
            for i, val in enumerate(array)
        ]

    def set_highlights(self, indices: list[int], highlight: ElementHighlight) -> None:
        """Apply a highlight to specified indices."""
        for idx in indices:
            if 0 <= idx < len(self.elements):
                self.elements[idx].highlight = highlight

    def clear_highlights(self) -> None:
        """Reset all element highlights to DEFAULT."""
        for elem in self.elements:
            elem.highlight = ElementHighlight.DEFAULT

    def get_values(self) -> list[int]:
        """Return list of integer values."""
        return [elem.value for elem in self.elements]

    def get_highlights(self) -> dict[int, ElementHighlight]:
        """Return a mapping of index to highlight for non-default highlights."""
        return {
            elem.index: elem.highlight
            for elem in self.elements
            if elem.highlight != ElementHighlight.DEFAULT
        }
