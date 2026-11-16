"""Array state representation for visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Sequence


class ElementHighlight(str, Enum):
    """Highlight categories for array elements."""

    DEFAULT = "DEFAULT"
    COMPARING = "COMPARING"
    SWAPPING = "SWAPPING"
    WRITING = "WRITING"
    READING = "READING"
    SORTED = "SORTED"


# Color mapping for UI bar rendering
HIGHLIGHT_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: "#3B82F6",    # Blue
    ElementHighlight.COMPARING: "#F59E0B",  # Amber / Yellow
    ElementHighlight.SWAPPING: "#EF4444",   # Red
    ElementHighlight.WRITING: "#8B5CF6",    # Purple
    ElementHighlight.READING: "#10B981",    # Emerald Green
    ElementHighlight.SORTED: "#059669",     # Dark Green
}

# Color mappings for UI box/cell rendering
BOX_FILL_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: "#1E293B",    # Dark Slate 800
    ElementHighlight.COMPARING: "#78350F",  # Amber 900
    ElementHighlight.SWAPPING: "#7F1D1D",   # Red 900
    ElementHighlight.WRITING: "#581C87",    # Purple 900
    ElementHighlight.READING: "#064E3B",    # Emerald 900
    ElementHighlight.SORTED: "#065F46",     # Green 800
}

BOX_BORDER_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: "#475569",    # Slate 600
    ElementHighlight.COMPARING: "#F59E0B",  # Amber 500
    ElementHighlight.SWAPPING: "#EF4444",   # Red 500
    ElementHighlight.WRITING: "#A855F7",    # Purple 500
    ElementHighlight.READING: "#10B981",    # Emerald 500
    ElementHighlight.SORTED: "#34D399",     # Green 400
}


@dataclass
class ArrayElementState:
    """State of a single array/string element in the visualizer."""

    index: int
    value: Any
    highlight: ElementHighlight = ElementHighlight.DEFAULT

    @property
    def color(self) -> str:
        """Hex color code for bar rendering."""
        return HIGHLIGHT_COLORS.get(self.highlight, HIGHLIGHT_COLORS[ElementHighlight.DEFAULT])

    @property
    def box_fill_color(self) -> str:
        """Hex fill color for box rendering."""
        return BOX_FILL_COLORS.get(self.highlight, BOX_FILL_COLORS[ElementHighlight.DEFAULT])

    @property
    def box_border_color(self) -> str:
        """Hex border color for box rendering."""
        return BOX_BORDER_COLORS.get(self.highlight, BOX_BORDER_COLORS[ElementHighlight.DEFAULT])


@dataclass
class ArrayViewState:
    """Manages the visual array/string state and active element highlights."""

    elements: list[ArrayElementState] = field(default_factory=list)

    @classmethod
    def from_array(
        cls,
        array: Sequence[Any],
        highlights: Optional[dict[int, ElementHighlight]] = None,
    ) -> ArrayViewState:
        """Construct an ArrayViewState from a sequence (list or string) and optional highlight map."""
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

    def set_array(self, array: Sequence[Any]) -> None:
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

    def get_values(self) -> list[Any]:
        """Return list of values."""
        return [elem.value for elem in self.elements]

    def get_highlights(self) -> dict[int, ElementHighlight]:
        """Return a mapping of index to highlight for non-default highlights."""
        return {
            elem.index: elem.highlight
            for elem in self.elements
            if elem.highlight != ElementHighlight.DEFAULT
        }
