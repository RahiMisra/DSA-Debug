"""Input panel component for specifying array data and execution parameters."""

from __future__ import annotations

import random
import tkinter as tk
from typing import Callable, Optional


class InputPanel(tk.Frame):
    """Panel allowing users to enter custom arrays, pick presets, and configure execution."""

    BG_COLOR = "#181825"
    TEXT_COLOR = "#CDD6F4"
    ENTRY_BG = "#313244"
    ENTRY_FG = "#FFFFFF"
    BTN_BG = "#45475A"
    BTN_PRIMARY = "#89B4FA"
    BTN_PRIMARY_FG = "#11111B"

    DEFAULT_ARRAY = "64, 34, 25, 12, 22, 11, 90"

    def __init__(
        self,
        master: Optional[tk.Widget] = None,
        on_run: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=self.BG_COLOR, padx=10, pady=8, **kwargs)
        self.on_run = on_run

        self._create_widgets()

    def _create_widgets(self) -> None:
        # Row 1: Array Input and Run Button
        top_frame = tk.Frame(self, bg=self.BG_COLOR)
        top_frame.pack(fill=tk.X, expand=True)

        lbl_array = tk.Label(
            top_frame,
            text="Input Array:",
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
        self.array_entry.insert(0, self.DEFAULT_ARRAY)
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
            text="Presets:",
            bg=self.BG_COLOR,
            fg="#A6ADC8",
            font=("Segoe UI", 9),
        )
        lbl_presets.pack(side=tk.LEFT, padx=(0, 6))

        presets = [
            ("Random", self._preset_random),
            ("Reverse", lambda: self.set_array_text("90, 64, 34, 25, 22, 12, 11")),
            ("Sorted", lambda: self.set_array_text("11, 12, 22, 25, 34, 64, 90")),
            ("Duplicates", lambda: self.set_array_text("5, 2, 8, 5, 2, 9, 8")),
            ("Negatives", lambda: self.set_array_text("-10, 5, -2, 0, 8, -5")),
        ]

        for label, cmd in presets:
            btn = tk.Button(
                bot_frame,
                text=label,
                bg=self.BTN_BG,
                fg=self.TEXT_COLOR,
                font=("Segoe UI", 8),
                relief="flat",
                padx=6,
                pady=1,
                cursor="hand2",
                command=cmd,
            )
            btn.pack(side=tk.LEFT, padx=2)

    def _preset_random(self) -> None:
        """Generate a random 8-element integer list."""
        vals = [random.randint(5, 99) for _ in range(8)]
        self.set_array_text(", ".join(str(x) for x in vals))

    def _on_run_click(self) -> None:
        if self.on_run:
            self.on_run()

    def get_array_text(self) -> str:
        """Return raw text from array entry."""
        return self.array_entry.get().strip()

    def set_array_text(self, text: str) -> None:
        """Set array entry text."""
        self.array_entry.delete(0, tk.END)
        self.array_entry.insert(0, text)

    def get_function_name(self) -> Optional[str]:
        """Return specified function name or None if empty."""
        text = self.func_entry.get().strip()
        return text if text else None

    def parse_array(self) -> list[int]:
        """Parse comma-separated integers from entry.

        Raises:
            ValueError: If entry contains invalid integer formatting.
        """
        raw = self.get_array_text()
        if not raw:
            return []
        items = [item.strip() for item in raw.split(",") if item.strip()]
        return [int(item) for item in items]
