"""Main application window integrating execution and visualization."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from src.execution.events import EventType, ExecutionEvent, ExecutionHistory
from src.execution.result import ExecutionResult, ExecutionStatus
from src.execution.runner import CodeRunner
from src.ui.array_view import ArrayView
from src.ui.code_editor import CodeEditor
from src.ui.execution_controls import ExecutionControls
from src.ui.input_panel import InputPanel
from src.ui.presets import get_preset
from src.visualization.auxiliary_canvas import AuxiliaryLinearCanvas
from src.visualization.dashboard import MultiViewDashboard
from src.visualization.event_processor import EventProcessor
from src.visualization.graph_canvas import GraphCanvas
from src.visualization.hash_canvas import AuxiliaryHashCanvas
from src.visualization.linked_list_canvas import LinkedListCanvas
from src.visualization.recursion_canvas import RecursionCanvas
from src.visualization.tree_canvas import BinaryTreeCanvas


class MainWindow:
    """Root desktop application window integrating editor, canvas, runner, and controls."""

    DEFAULT_TITLE = "Trace — Algorithm Execution Visualizer"
    DEFAULT_WIDTH = 1100
    DEFAULT_HEIGHT = 760
    MIN_WIDTH = 880
    MIN_HEIGHT = 620

    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        if root is None:
            self.root = tk.Tk()
            self._owns_root = True
        else:
            self.root = root
            self._owns_root = False

        self.runner = CodeRunner()
        self.history: Optional[ExecutionHistory] = None
        self.current_step_index: int = -1
        self._playback_job: Optional[str] = None

        self._configure_window()
        self._create_layout()

    def _configure_window(self) -> None:
        self.root.title(self.DEFAULT_TITLE)
        self.root.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.configure(bg="#11111B")

    def _create_layout(self) -> None:
        # 1. Top Panel: Array Input & Run
        self.input_panel = InputPanel(
            self.root,
            on_run=self.handle_run,
            on_preset_selected=self.handle_preset_selected,
        )
        self.input_panel.pack(fill=tk.X, side=tk.TOP)

        # 2. Error Banner (hidden by default)
        self.error_banner = tk.Label(
            self.root,
            text="",
            bg="#F38BA8",
            fg="#11111B",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=6,
            anchor="w",
        )

        # 3. Bottom Panel: Execution Controls
        self.controls = ExecutionControls(
            self.root,
            on_step_forward=self.step_forward,
            on_step_backward=self.step_backward,
            on_reset=self.reset_execution,
            on_play_toggle=self.handle_play_toggle,
        )
        self.controls.pack(fill=tk.X, side=tk.BOTTOM)

        # 4. Center Area: Split Pane (Code Editor Left | Array View Right)
        center_frame = tk.PanedWindow(
            self.root,
            orient=tk.HORIZONTAL,
            bg="#181825",
            sashwidth=6,
            bd=0,
        )
        center_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # Left: Code Editor
        editor_container = tk.Frame(center_frame, bg="#1E1E2E")
        lbl_editor = tk.Label(
            editor_container,
            text="Algorithm Source Code (Python)",
            bg="#181825",
            fg="#CDD6F4",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            anchor="w",
        )
        lbl_editor.pack(fill=tk.X)
        self.editor = CodeEditor(editor_container)
        self.editor.pack(fill=tk.BOTH, expand=True)
        center_frame.add(editor_container, minsize=380, width=480)

        # Right: Visualization View
        viz_container = tk.Frame(center_frame, bg="#0F172A")
        self.lbl_viz = tk.Label(
            viz_container,
            text="Execution Visualization",
            bg="#181825",
            fg="#CDD6F4",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            anchor="w",
        )
        self.lbl_viz.pack(fill=tk.X)
        self.dashboard = MultiViewDashboard(viz_container)
        self.dashboard.pack(fill=tk.BOTH, expand=True)

        self.array_view = ArrayView(self.dashboard.primary)
        self.array_view.pack(fill=tk.BOTH, expand=True)

        self.linked_list_view = LinkedListCanvas(self.dashboard.primary)
        self.tree_view = BinaryTreeCanvas(self.dashboard.primary)
        self.graph_view = GraphCanvas(self.dashboard.primary)
        self.auxiliary_view = AuxiliaryLinearCanvas(self.dashboard.auxiliary)
        self.hash_view = AuxiliaryHashCanvas(self.dashboard.auxiliary)
        self.recursion_view = RecursionCanvas(self.dashboard.subwork)

        center_frame.add(viz_container, minsize=400)

        # Initialize array view with initial input panel data
        try:
            initial_arr = self.input_panel.parse_array()
            self.array_view.set_array(initial_arr)
        except Exception:
            pass

    def handle_preset_selected(self, preset_name: str) -> None:
        """Load the selected preset's default algorithm code."""
        preset = get_preset(preset_name)
        if preset is not None:
            self.editor.set_code(preset.code)

    def handle_run(self) -> None:
        """Execute user code and initialize execution history for playback."""
        self._stop_playback()
        self._clear_error()

        # Parse inputs (supports LeetCode syntax or plain arrays)
        try:
            inputs = self.input_panel.parse_inputs()
            initial_array = self.input_panel.parse_array()
        except ValueError as exc:
            self._show_error(f"Invalid input: {exc}. Please check your syntax.")
            return

        code = self.editor.get_code()
        func_name = self.input_panel.get_function_name()

        # Run user code through isolated subprocess runner
        payload = inputs if inputs else initial_array
        result: ExecutionResult = self.runner.run(
            code=code,
            initial_array=payload,
            function_name=func_name,
        )

        if result.has_error:
            err = result.error
            err_type = f": {err.error_type}" if err and err.error_type else ""
            err_msg = f"[{result.status.value}{err_type}] {err.message if err else 'Execution failed'}"
            if err and err.line_number:
                err_msg += f" (line {err.line_number})"
                self.editor.highlight_line(err.line_number)
            self._show_error(err_msg)
            return

        # Prepare ExecutionHistory
        self.history = ExecutionHistory.from_dict({
            "initial_array": initial_array,
            "events": result.events,
        })

        self.current_step_index = -1
        kind, initial_event = self._initial_view()
        self._render_view(kind, initial_event)
        self.editor.clear_highlight()

        total = len(self.history)
        self.controls.set_state(
            total_steps=total,
            current_step=-1,
            details_text=f"Execution recorded successfully ({total} steps in {result.execution_time_ms:.1f}ms). Ready to step.",
        )

    def step_forward(self) -> None:
        """Advance one step in the recorded execution history."""
        if not self.history or len(self.history) == 0:
            return

        if self.current_step_index < len(self.history) - 1:
            self.current_step_index += 1
            self._apply_current_step()

    def step_backward(self) -> None:
        """Move back one step in the recorded execution history."""
        if not self.history:
            return

        if self.current_step_index > -1:
            self.current_step_index -= 1
            self._apply_current_step()

    def reset_execution(self) -> None:
        """Reset execution visualization to the initial array state."""
        if not self.history:
            return
        self._stop_playback()
        self.current_step_index = -1
        self._apply_current_step()

    def _apply_current_step(self) -> None:
        """Update editor, visualization canvas, and controls to match current_step_index."""
        if not self.history:
            return

        total = len(self.history)

        if self.current_step_index == -1:
            # Initial state before algorithm begins
            self.editor.clear_highlight()
            kind, initial_event = self._initial_view()
            self._render_view(kind, initial_event)

            self.controls.set_state(
                total_steps=total,
                current_step=-1,
                details_text="Initial state before algorithm start.",
            )
            return

        event: ExecutionEvent = self.history.get_step(self.current_step_index)

        # 1. Update Visualization View
        kind, view_event = self._event_view(event)
        self._render_view(kind, view_event)

        # 2. Update Code Editor Line Highlight
        if event.line_number:
            self.editor.highlight_line(event.line_number)

        # 3. Format Operation Details Text
        details = self._format_event_description(event)

        # 4. Update Controls
        self.controls.set_state(
            total_steps=total,
            current_step=self.current_step_index,
            details_text=details,
        )

    def _initial_view(self) -> tuple[str, Optional[ExecutionEvent]]:
        """Select the visualization kind for the pre-execution state."""
        if not self.history or not self.history.events:
            return "array", None

        first_event = self.history.events[0]
        for kind in ("graph", "linked_list", "tree"):
            if first_event.metadata.get(kind):
                return kind, first_event
        return "array", None

    def _event_view(self, event: ExecutionEvent) -> tuple[str, ExecutionEvent]:
        """Select the visualization kind for a recorded execution event.

        Graph state takes precedence because graph algorithms commonly use
        pointer-like locals (``node``, ``curr``) that node-structure heuristics
        may also recognize.
        """
        for kind in ("graph", "linked_list", "tree"):
            if event.metadata.get(kind):
                return kind, event
        return "array", event

    def _render_view(self, kind: str, event: Optional[ExecutionEvent]) -> None:
        """Show the visualization for kind and render the supplied event/state."""
        views = {
            "array": self.array_view,
            "linked_list": self.linked_list_view,
            "tree": self.tree_view,
            "graph": self.graph_view,
        }
        labels = {
            "array": "Array Execution Visualization",
            "linked_list": "Linked List Execution Visualization",
            "tree": "Binary Tree Execution Visualization",
            "graph": "Graph Execution Visualization",
        }

        for view in views.values():
            view.pack_forget()
        self.auxiliary_view.pack_forget()
        self.hash_view.pack_forget()
        self.recursion_view.pack_forget()

        auxiliary_state = event.metadata.get("auxiliary") if event is not None else None
        show_linear = bool(
            auxiliary_state
            and (auxiliary_state.get("stacks") or auxiliary_state.get("queues"))
        )
        if show_linear:
            self.auxiliary_view.render_event(event)
            self.auxiliary_view.pack(fill=tk.BOTH, expand=True)

        show_hash = bool(
            auxiliary_state
            and (auxiliary_state.get("maps") or auxiliary_state.get("sets"))
        )
        if show_hash:
            self.hash_view.render_event(event)
            self.hash_view.pack(fill=tk.BOTH, expand=True)

        recursion_state = (
            event.metadata.get("recursion") if event is not None else None
        )
        show_subwork = self._has_recursion_activity(recursion_state)
        if show_subwork:
            self.recursion_view.render_event(event)
            self.recursion_view.pack(fill=tk.BOTH, expand=True)

        self.dashboard.set_workspace_visible(
            auxiliary=show_linear or show_hash,
            subwork=show_subwork,
        )

        views[kind].pack(fill=tk.BOTH, expand=True)
        self.lbl_viz.config(text=labels.get(kind, labels["array"]))

        if kind == "array":
            if event is None:
                self.array_view.set_array(self.history.initial_array if self.history else [])
            else:
                self.array_view.set_array_state(EventProcessor.process_event(event))
        elif event is not None:
            views[kind].render_event(event)

    @staticmethod
    def _has_recursion_activity(state: Optional[dict]) -> bool:
        """Return True when call-stack, sub-work, or return data is worth showing."""
        if not state:
            return False
        frames = state.get("frames") or []
        return bool(
            len(frames) > 1
            or state.get("subarrays")
            or state.get("last_return") is not None
            or state.get("return_structure") is not None
        )

    def _format_event_description(self, event: ExecutionEvent) -> str:
        """Generate human-readable description for an execution event."""
        line_prefix = f"Line {event.line_number}: " if event.line_number else ""
        if event.event_type == EventType.COMPARISON:
            op = event.metadata.get("op", "?")
            res = event.metadata.get("result", "")
            vals = event.values
            indices = event.indices
            container_op = event.metadata.get("container_op")
            if container_op and container_op.get("action") == "lookup":
                name = container_op.get("name", "container")
                key = container_op.get("key")
                present = container_op.get("present", res)
                return f"{line_prefix}{key} {op} {name} -> {present}"
            if len(indices) >= 2 and len(vals) >= 2:
                return f"{line_prefix}Compared arr[{indices[0]}] ({vals[0]}) {op} arr[{indices[1]}] ({vals[1]}) -> {res}"
            return f"{line_prefix}Comparison {vals} with '{op}' -> {res}"

        elif event.event_type == EventType.SWAP:
            idx = event.indices
            vals = event.values
            if len(idx) >= 2 and len(vals) >= 2:
                return f"{line_prefix}Swapped arr[{idx[0]}] and arr[{idx[1]}]"
            return f"{line_prefix}Swapped elements"

        elif event.event_type == EventType.WRITE:
            idx = event.indices[0] if event.indices else "?"
            val = event.values[0] if event.values else "?"
            prev = event.metadata.get("previous_value")
            prev_str = f" (was {prev})" if prev is not None else ""
            return f"{line_prefix}Set arr[{idx}] = {val}{prev_str}"

        elif event.event_type == EventType.READ:
            idx = event.indices[0] if event.indices else "?"
            val = event.values[0] if event.values else "?"
            return f"{line_prefix}Read arr[{idx}] = {val}"

        elif event.event_type == EventType.CONTAINER:
            op = event.metadata.get("container_op", {})
            name = op.get("name", "container")
            action = op.get("action", "operation")
            kind = op.get("kind")
            key = op.get("key")
            value = op.get("value")

            if kind == "map":
                if action in ("insert", "update"):
                    prev = op.get("previous_value")
                    prev_str = (
                        f" (was {prev})"
                        if action == "update" and prev is not None
                        else ""
                    )
                    return f"{line_prefix}{name}[{key}] = {value}{prev_str}"
                if action == "lookup":
                    return f"{line_prefix}Read {name}[{key}] = {value}"
                if action == "remove":
                    return f"{line_prefix}{name} removed {key} = {value}"
            elif kind == "set":
                if action == "add":
                    return f"{line_prefix}{name} added {key}"
                if action in ("remove", "discard"):
                    return f"{line_prefix}{name} removed {key}"

            value_str = "" if value is None else f" {value}"
            return f"{line_prefix}{name} {action}{value_str}"

        elif event.event_type == EventType.CALL:
            call = event.metadata.get("call", {})
            function = call.get("function", "?")
            depth = call.get("depth", 0)
            args_text = ", ".join(
                f"{key}={value}" for key, value in call.get("args", {}).items()
            )
            signature = f"({args_text})" if args_text else "()"
            return f"{line_prefix}Called {function}{signature} at depth {depth}"

        elif event.event_type == EventType.RETURN:
            returned = event.metadata.get("return", {})
            function = returned.get("function", "?")
            depth = returned.get("depth", 0)
            value = returned.get("value")
            value_text = "None" if value is None else str(value)
            return f"{line_prefix}Returned {function} -> {value_text} (depth {depth})"

        elif event.event_type == EventType.LINE:
            return f"{line_prefix}Executed line {event.line_number}"

        return f"{line_prefix}{event.event_type.value}"

    def handle_play_toggle(self, play: bool) -> None:
        """Handle Play/Pause toggle from controls."""
        if play:
            self._schedule_next_play_step()
        else:
            self._stop_playback()

    def _schedule_next_play_step(self) -> None:
        """Schedule the next automatic step if playing."""
        if not self.controls.is_playing:
            return
        if not self.history or self.current_step_index >= len(self.history) - 1:
            self._stop_playback()
            return

        self._playback_job = self.root.after(
            self.controls.playback_speed_ms,
            self._run_play_step,
        )

    def _run_play_step(self) -> None:
        """Advance one step during automatic playback."""
        if self.controls.is_playing:
            self.step_forward()
            self._schedule_next_play_step()

    def _stop_playback(self) -> None:
        """Cancel scheduled playback job and update controls."""
        if self._playback_job is not None:
            try:
                self.root.after_cancel(self._playback_job)
            except Exception:
                pass
            self._playback_job = None
        self.controls.pause()

    def _show_error(self, message: str) -> None:
        self.error_banner.config(text=f"⚠ {message}")
        self.error_banner.pack(fill=tk.X, after=self.input_panel)

    def _clear_error(self) -> None:
        self.error_banner.pack_forget()

    @property
    def is_alive(self) -> bool:
        """Return True if the underlying window exists and has not been destroyed."""
        try:
            return bool(self.root and self.root.winfo_exists())
        except (tk.TclError, AttributeError):
            return False

    def close(self) -> None:
        """Close the application window cleanly."""
        self._stop_playback()
        if self.root:
            try:
                self.root.destroy()
            except tk.TclError:
                pass

    def run(self) -> None:
        """Start the Tkinter event loop."""
        self.root.mainloop()
