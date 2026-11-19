"""Array state representation for visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Sequence

from src.visualization.theme import (
    ARRAY_BOX_BORDER_COLORS,
    ARRAY_BOX_FILL_COLORS,
    ARRAY_HIGHLIGHT_COLORS,
)


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
    ElementHighlight.DEFAULT: ARRAY_HIGHLIGHT_COLORS["default"],
    ElementHighlight.COMPARING: ARRAY_HIGHLIGHT_COLORS["comparing"],
    ElementHighlight.SWAPPING: ARRAY_HIGHLIGHT_COLORS["swapping"],
    ElementHighlight.WRITING: ARRAY_HIGHLIGHT_COLORS["writing"],
    ElementHighlight.READING: ARRAY_HIGHLIGHT_COLORS["reading"],
    ElementHighlight.SORTED: ARRAY_HIGHLIGHT_COLORS["sorted"],
}

# Color mappings for UI box/cell rendering
BOX_FILL_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: ARRAY_BOX_FILL_COLORS["default"],
    ElementHighlight.COMPARING: ARRAY_BOX_FILL_COLORS["comparing"],
    ElementHighlight.SWAPPING: ARRAY_BOX_FILL_COLORS["swapping"],
    ElementHighlight.WRITING: ARRAY_BOX_FILL_COLORS["writing"],
    ElementHighlight.READING: ARRAY_BOX_FILL_COLORS["reading"],
    ElementHighlight.SORTED: ARRAY_BOX_FILL_COLORS["sorted"],
}

BOX_BORDER_COLORS: dict[ElementHighlight, str] = {
    ElementHighlight.DEFAULT: ARRAY_BOX_BORDER_COLORS["default"],
    ElementHighlight.COMPARING: ARRAY_BOX_BORDER_COLORS["comparing"],
    ElementHighlight.SWAPPING: ARRAY_BOX_BORDER_COLORS["swapping"],
    ElementHighlight.WRITING: ARRAY_BOX_BORDER_COLORS["writing"],
    ElementHighlight.READING: ARRAY_BOX_BORDER_COLORS["reading"],
    ElementHighlight.SORTED: ARRAY_BOX_BORDER_COLORS["sorted"],
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
