"""Processes execution events into visual array states."""

from __future__ import annotations

from typing import Any

from src.execution.events import EventType, ExecutionEvent
from src.visualization.array_state import ArrayViewState, ElementHighlight


class EventProcessor:
    """Translates execution events into visual state representations for the UI."""

    @staticmethod
    def process_event(event: ExecutionEvent | dict[str, Any]) -> ArrayViewState:
        """Process an ExecutionEvent into an ArrayViewState.

        Args:
            event: The execution event to process.

        Returns:
            ArrayViewState reflecting current values and active operation highlights.
        """
        if isinstance(event, dict):
            raw_type = event.get("event_type", EventType.LINE.value)
            event_type = EventType(raw_type) if isinstance(raw_type, str) else raw_type
            array_state = list(event.get("array_state", []))
            indices = list(event.get("indices", []))
        else:
            event_type = event.event_type
            array_state = list(event.array_state)
            indices = list(event.indices)

        highlights: dict[int, ElementHighlight] = {}

        if event_type == EventType.COMPARISON:
            for idx in indices:
                highlights[idx] = ElementHighlight.COMPARING
        elif event_type == EventType.SWAP:
            for idx in indices:
                highlights[idx] = ElementHighlight.SWAPPING
        elif event_type == EventType.WRITE:
            for idx in indices:
                highlights[idx] = ElementHighlight.WRITING
        elif event_type == EventType.READ:
            for idx in indices:
                highlights[idx] = ElementHighlight.READING

        return ArrayViewState.from_array(array_state, highlights=highlights)
