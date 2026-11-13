"""Execution navigation controls UI component."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional


class ExecutionControls(tk.Frame):
    """Controls for stepping forward, backward, playing, and resetting execution history."""

    BG_COLOR = "#181825"
    TEXT_COLOR = "#CDD6F4"
    BTN_BG = "#313244"
    BTN_FG = "#FFFFFF"
    BTN_DISABLED_BG = "#232433"
    BTN_DISABLED_FG = "#585B70"
    ACCENT_COLOR = "#A6E3A1"

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        on_step_forward: Optional[Callable[[], None]] = None,
        on_step_backward: Optional[Callable[[], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
        on_play_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=self.BG_COLOR, padx=10, pady=8, **kwargs)

        self.on_step_forward = on_step_forward
        self.on_step_backward = on_step_backward
        self.on_reset = on_reset
        self.on_play_toggle = on_play_toggle

        self.is_playing = False
        self._playback_speed_ms = 400

        self._create_widgets()
        self.set_state(total_steps=0, current_step=-1)

    def _create_widgets(self) -> None:
        # Left: Navigation buttons
        btn_frame = tk.Frame(self, bg=self.BG_COLOR)
        btn_frame.pack(side=tk.LEFT)

        self.btn_reset = tk.Button(
            btn_frame,
            text="⏮ Reset",
            bg=self.BTN_BG,
            fg=self.BTN_FG,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            pady=4,
            command=self._on_reset_click,
        )
        self.btn_reset.pack(side=tk.LEFT, padx=3)

        self.btn_backward = tk.Button(
            btn_frame,
            text="◀ Step Back",
            bg=self.BTN_BG,
            fg=self.BTN_FG,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            pady=4,
            command=self._on_backward_click,
        )
        self.btn_backward.pack(side=tk.LEFT, padx=3)

        self.btn_play = tk.Button(
            btn_frame,
            text="▶ Play",
            bg=self.BTN_BG,
            fg=self.ACCENT_COLOR,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=4,
            command=self._on_play_click,
        )
        self.btn_play.pack(side=tk.LEFT, padx=3)

        self.btn_forward = tk.Button(
            btn_frame,
            text="Step Forward ▶",
            bg=self.BTN_BG,
            fg=self.BTN_FG,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=8,
            pady=4,
            command=self._on_forward_click,
        )
        self.btn_forward.pack(side=tk.LEFT, padx=3)

        # Center: Step counter & Status details
        center_frame = tk.Frame(self, bg=self.BG_COLOR)
        center_frame.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)

        self.lbl_step = tk.Label(
            center_frame,
            text="Step: 0 / 0",
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )
        self.lbl_step.pack(anchor="w")

        self.lbl_details = tk.Label(
            center_frame,
            text="Ready to run.",
            bg=self.BG_COLOR,
            fg="#BAC2DE",
            font=("Consolas", 9),
            anchor="w",
        )
        self.lbl_details.pack(anchor="w")

        # Right: Speed control slider
        speed_frame = tk.Frame(self, bg=self.BG_COLOR)
        speed_frame.pack(side=tk.RIGHT)

        lbl_speed = tk.Label(
            speed_frame,
            text="Speed:",
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 8),
        )
        lbl_speed.pack(side=tk.LEFT, padx=(0, 4))

        self.speed_scale = tk.Scale(
            speed_frame,
            from_=100,
            to=1200,
            orient=tk.HORIZONTAL,
            showvalue=0,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            troughcolor="#313244",
            highlightthickness=0,
            length=100,
            command=self._on_speed_change,
        )
        self.speed_scale.set(400)
        self.speed_scale.pack(side=tk.LEFT)

    def _on_speed_change(self, val: str) -> None:
        self._playback_speed_ms = int(val)

    @property
    def playback_speed_ms(self) -> int:
        return self._playback_speed_ms

    def _on_reset_click(self) -> None:
        self.pause()
        if self.on_reset:
            self.on_reset()

    def _on_backward_click(self) -> None:
        self.pause()
        if self.on_step_backward:
            self.on_step_backward()

    def _on_forward_click(self) -> None:
        self.pause()
        if self.on_step_forward:
            self.on_step_forward()

    def _on_play_click(self) -> None:
        if self.is_playing:
            self.pause()
        else:
            self.play()

    def play(self) -> None:
        """Start auto-stepping playback."""
        self.is_playing = True
        self.btn_play.config(text="⏸ Pause", fg="#F38BA8")
        if self.on_play_toggle:
            self.on_play_toggle(True)

    def pause(self) -> None:
        """Pause auto-stepping playback."""
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="▶ Play", fg=self.ACCENT_COLOR)
            if self.on_play_toggle:
                self.on_play_toggle(False)

    def set_state(
        self,
        total_steps: int,
        current_step: int,
        details_text: str = "",
    ) -> None:
        """Update step counter, detail text, and button active states.

        Args:
            total_steps: Total number of recorded execution events.
            current_step: Current event index (-1 means initial state).
            details_text: Description of the current action.
        """
        display_curr = max(0, current_step + 1)
        self.lbl_step.config(text=f"Step: {display_curr} / {total_steps}")
        if details_text:
            self.lbl_details.config(text=details_text)

        has_steps = total_steps > 0
        at_start = current_step <= -1
        at_end = current_step >= total_steps - 1

        self._set_btn_enabled(self.btn_reset, has_steps and not at_start)
        self._set_btn_enabled(self.btn_backward, has_steps and not at_start)
        self._set_btn_enabled(self.btn_forward, has_steps and not at_end)
        self._set_btn_enabled(self.btn_play, has_steps and not at_end)

        if at_end and self.is_playing:
            self.pause()

    def _set_btn_enabled(self, btn: tk.Button, enabled: bool) -> None:
        if enabled:
            btn.config(state="normal", cursor="hand2")
        else:
            btn.config(state="disabled", cursor="arrow")
