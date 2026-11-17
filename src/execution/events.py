"""Execution event and history models for Trace."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Types of execution events captured during algorithm execution."""

    LINE = "LINE"
    COMPARISON = "COMPARISON"
    SWAP = "SWAP"
    WRITE = "WRITE"
    READ = "READ"
    CONTAINER = "CONTAINER"


def _safe_json_value(val: Any) -> Any:
    """Ensure a value is safely serializable to JSON."""
    if val is None or isinstance(val, (int, float, str, bool)):
        return val
    elif isinstance(val, (list, tuple, set)):
        return [_safe_json_value(x) for x in val]
    elif isinstance(val, dict):
        return {str(k): _safe_json_value(v) for k, v in val.items()}
    elif hasattr(val, "val"):
        inner_val = getattr(val, "val")
        if isinstance(inner_val, (int, float, str, bool)):
            return inner_val
        return str(val)
    return str(val)


@dataclass
class ExecutionEvent:
    """Represents a single atomic execution step/event in the algorithm."""

    step_index: int
    event_type: EventType
    line_number: Optional[int] = None
    array_state: list[int] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)
    values: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-style key access for convenience."""
        if hasattr(self, key):
            val = getattr(self, key)
            if key == "event_type" and isinstance(val, EventType):
                return val.value
            return val
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """Allow dict-style .get access for convenience."""
        try:
            return self[key]
        except KeyError:
            return default

    def to_dict(self) -> dict[str, Any]:
        """Convert the execution event to a dictionary."""
        return {
            "step_index": self.step_index,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else str(self.event_type),
            "line_number": self.line_number,
            "array_state": list(self.array_state),
            "indices": list(self.indices),
            "values": [_safe_json_value(v) for v in self.values],
            "metadata": {str(k): _safe_json_value(v) for k, v in self.metadata.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionEvent:
        """Create an ExecutionEvent from a dictionary."""
        raw_type = data.get("event_type", EventType.LINE.value)
        event_type = EventType(raw_type) if isinstance(raw_type, str) else raw_type
        return cls(
            step_index=data.get("step_index", 0),
            event_type=event_type,
            line_number=data.get("line_number"),
            array_state=data.get("array_state", []),
            indices=data.get("indices", []),
            values=data.get("values", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ExecutionHistory:
    """Maintains the ordered sequence of events and initial application state."""

    initial_array: list[int] = field(default_factory=list)
    events: list[ExecutionEvent] = field(default_factory=list)

    def add_event(
        self,
        event_type: EventType,
        line_number: Optional[int],
        array_state: list[int],
        indices: Optional[list[int]] = None,
        values: Optional[list[Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ExecutionEvent:
        """Create, append, and return a new execution event."""
        step_index = len(self.events)
        event = ExecutionEvent(
            step_index=step_index,
            event_type=event_type,
            line_number=line_number,
            array_state=list(array_state),
            indices=list(indices) if indices is not None else [],
            values=list(values) if values is not None else [],
            metadata=dict(metadata) if metadata is not None else {},
        )
        self.events.append(event)
        return event

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, index: int) -> ExecutionEvent:
        return self.events[index]

    def get_step(self, index: int) -> ExecutionEvent:
        """Retrieve the execution event at the specified step index."""
        if not (0 <= index < len(self.events)):
            raise IndexError(f"Step index {index} out of range [0, {len(self.events) - 1}]")
        return self.events[index]

    def get_array_at_step(self, index: int) -> list[int]:
        """Retrieve the array state snapshot at the specified step index.

        If index is -1, returns the initial array state.
        """
        if index == -1:
            return list(self.initial_array)
        if not (0 <= index < len(self.events)):
            raise IndexError(f"Step index {index} out of range [-1, {len(self.events) - 1}]")
        return list(self.events[index].array_state)

    def to_dict(self) -> dict[str, Any]:
        """Convert the entire history to a dictionary."""
        return {
            "initial_array": list(self.initial_array),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionHistory:
        """Create an ExecutionHistory from a dictionary."""
        initial_array = data.get("initial_array", [])
        events = [ExecutionEvent.from_dict(e) for e in data.get("events", [])]
        return cls(initial_array=initial_array, events=events)

    def to_json(self) -> str:
        """Serialize the history to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> ExecutionHistory:
        """Deserialize an ExecutionHistory from a JSON string."""
        return cls.from_dict(json.loads(json_str))
