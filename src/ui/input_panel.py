"""Input panel component for specifying algorithm input data and LeetCode parameters."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable, Optional

from src.execution.parsers import parse_leetcode_inputs
from src.ui.presets import ARRAY_PRESET, PRESETS, Preset


class InputPanel(tk.Frame):
    """Panel allowing users to enter custom inputs in LeetCode format, pick presets, and configure execution."""

    BG_COLOR = "#181825"
    TEXT_COLOR = "#CDD6F4"
    ENTRY_BG = "#313244"
    ENTRY_FG = "#FFFFFF"
    BTN_BG = "#45475A"
    BTN_PRIMARY = "#89B4FA"
    BTN_PRIMARY_FG = "#11111B"

    DEFAULT_INPUT = ARRAY_PRESET.input_text

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        on_run: Optional[Callable[[], None]] = None,
        on_preset_selected: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=self.BG_COLOR, padx=10, pady=8, **kwargs)
        self.on_run = on_run
        self.on_preset_selected = on_preset_selected
        self.preset_buttons: dict[str, tk.Button] = {}

        self._create_widgets()

    def _create_widgets(self) -> None:
        # Row 1: Input and Run Button
        top_frame = tk.Frame(self, bg=self.BG_COLOR)
        top_frame.pack(fill=tk.X, expand=True)

        lbl_array = tk.Label(
            top_frame,
            text="Input:",
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        )
        lbl_array.pack(side=tk.LEFT, padx=(0, 6))

        self.array_entry = tk.Entry(
            top_frame,
            bg=self.ENTRY_BG,
            fg=self.ENTRY_FG,
            insertbackground="#FFFFFF",
            font=("Consolas", 11),
            relief="flat",
        )
        self.array_entry.insert(0, self.DEFAULT_INPUT)
        self.array_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=3)

        self.run_btn = tk.Button(
            top_frame,
            text="▶ Run Algorithm",
            bg=self.BTN_PRIMARY,
            fg=self.BTN_PRIMARY_FG,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=3,
            command=self._on_run_click,
        )
        self.run_btn.pack(side=tk.RIGHT)

        # Row 2: Function Name & Presets
        bot_frame = tk.Frame(self, bg=self.BG_COLOR)
        bot_frame.pack(fill=tk.X, expand=True, pady=(8, 0))

        lbl_func = tk.Label(
            bot_frame,
            text="Function Name (optional):",
            bg=self.BG_COLOR,
            fg="#A6ADC8",
            font=("Segoe UI", 9),
        )
        lbl_func.pack(side=tk.LEFT, padx=(0, 4))

        self.func_entry = tk.Entry(
            bot_frame,
            width=16,
            bg=self.ENTRY_BG,
            fg=self.ENTRY_FG,
            insertbackground="#FFFFFF",
            font=("Consolas", 10),
            relief="flat",
        )
        self.func_entry.pack(side=tk.LEFT, padx=(0, 15), ipady=2)

        lbl_presets = tk.Label(
            bot_frame,
            text="LeetCode Presets:",
            bg=self.BG_COLOR,
            fg="#A6ADC8",
            font=("Segoe UI", 9),
        )
        lbl_presets.pack(side=tk.LEFT, padx=(0, 6))

        for preset in PRESETS:
            btn = tk.Button(
                bot_frame,
                text=preset.label,
                bg=self.BTN_BG,
                fg=self.TEXT_COLOR,
                font=("Segoe UI", 8),
                relief="flat",
                padx=6,
                pady=1,
                cursor="hand2",
                command=lambda p=preset: self._handle_preset(p),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.preset_buttons[preset.label] = btn

    def _handle_preset(self, preset: Preset) -> None:
        """Apply a preset's generated input and notify the preset callback."""
        self.set_array_text(preset.build_input())
        if self.on_preset_selected:
            self.on_preset_selected(preset.label)

    def _on_run_click(self) -> None:
        if self.on_run:
            self.on_run()

    def get_array_text(self) -> str:
        """Return raw text from input entry."""
        return self.array_entry.get().strip()

    def set_array_text(self, text: str) -> None:
        """Set input entry text."""
        self.array_entry.delete(0, tk.END)
        self.array_entry.insert(0, text)

    def get_function_name(self) -> Optional[str]:
        """Return specified function name or None if empty."""
        text = self.func_entry.get().strip()
        return text if text else None

    def parse_inputs(self) -> dict[str, Any]:
        """Parse input specifications into a dictionary of parameters."""
        raw = self.get_array_text()
        return parse_leetcode_inputs(raw)

    def parse_array(self) -> list[int]:
        """Backward-compatible helper to retrieve a primary integer array."""
        parsed = self.parse_inputs()
        for v in parsed.values():
            if isinstance(v, (list, tuple)):
                return list(v)
            elif hasattr(v, "to_list") and callable(v.to_list):
                return v.to_list()

        # Fall back to string characters for String-preset visualizations.
        for v in parsed.values():
            if isinstance(v, str):
                return list(v)
        return []
