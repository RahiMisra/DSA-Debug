"""Execution navigation controls UI component."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional

from src.visualization.theme import PALETTE, restore_button, style_button, surface_kwargs


class ExecutionControls(tk.Frame):
    """Controls for stepping forward, backward, playing, and resetting execution history."""

    BG_COLOR = PALETTE.bg_base
    TEXT_COLOR = PALETTE.text
    MUTED_COLOR = PALETTE.text_muted
    BTN_BG = PALETTE.button_bg
    BTN_FG = PALETTE.button_text
    BTN_DISABLED_BG = PALETTE.button_disabled_bg
    BTN_DISABLED_FG = PALETTE.button_disabled_text
    ACCENT_COLOR = PALETTE.success
    DANGER_COLOR = PALETTE.danger

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        on_step_forward: Optional[Callable[[], None]] = None,
        on_step_backward: Optional[Callable[[], None]] = None,
        on_reset: Optional[Callable[[], None]] = None,
        on_play_toggle: Optional[Callable[[bool], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            padx=12,
            pady=9,
            **surface_kwargs(self.BG_COLOR),
            **kwargs,
        )

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
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            command=self._on_reset_click,
        )
        style_button(self.btn_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=3)

        self.btn_backward = tk.Button(
            btn_frame,
            text="◀ Step Back",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            command=self._on_backward_click,
        )
        style_button(self.btn_backward)
        self.btn_backward.pack(side=tk.LEFT, padx=3)

        self.btn_play = tk.Button(
            btn_frame,
            text="▶ Play",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            command=self._on_play_click,
        )
        style_button(self.btn_play)
        self.btn_play._trace_normal_fg = self.ACCENT_COLOR
        self.btn_play.config(fg=self.ACCENT_COLOR)
        self.btn_play.pack(side=tk.LEFT, padx=3)

        self.btn_forward = tk.Button(
            btn_frame,
            text="Step Forward ▶",
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
            command=self._on_forward_click,
        )
        style_button(self.btn_forward)
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
            fg=self.MUTED_COLOR,
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
            troughcolor=PALETTE.bg_item,
            activebackground=PALETTE.accent,
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT,
            sliderrelief=tk.FLAT,
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
        self.btn_play.config(text="⏸ Pause")
        if str(self.btn_play.cget("state")) != "disabled":
            self.btn_play.config(fg=self.DANGER_COLOR)
        if self.on_play_toggle:
            self.on_play_toggle(True)

    def pause(self) -> None:
        """Pause auto-stepping playback."""
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="▶ Play")
            if str(self.btn_play.cget("state")) != "disabled":
                self.btn_play.config(fg=self.ACCENT_COLOR)
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
            btn.config(
                bg=getattr(btn, "_trace_normal_bg", self.BTN_BG),
            )
            if btn is self.btn_play:
                btn.config(
                    fg=self.DANGER_COLOR if self.is_playing else self.ACCENT_COLOR
                )
            else:
                restore_button(btn)
        else:
            btn.config(
                state="disabled",
                cursor="arrow",
                bg=self.BTN_DISABLED_BG,
                fg=self.BTN_DISABLED_FG,
            )
