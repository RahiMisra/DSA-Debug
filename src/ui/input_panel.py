"""Input panel component for specifying algorithm input data and LeetCode parameters."""

from __future__ import annotations

import random
import tkinter as tk
from typing import Any, Callable, Optional

from src.execution.parsers import parse_leetcode_inputs


class InputPanel(tk.Frame):
    """Panel allowing users to enter custom inputs in LeetCode format, pick presets, and configure execution."""

    BG_COLOR = "#181825"
    TEXT_COLOR = "#CDD6F4"
    ENTRY_BG = "#313244"
    ENTRY_FG = "#FFFFFF"
    BTN_BG = "#45475A"
    BTN_PRIMARY = "#89B4FA"
    BTN_PRIMARY_FG = "#11111B"

    DEFAULT_INPUT = "nums = [64, 34, 25, 12, 22, 11, 90]"

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

        presets = [
            ("Array", "nums = [2, 7, 11, 15], target = 9"),
            ("String", 's = "anagram", t = "nagaram"'),
            ("Linked List", "head = [1, 2, 3, 4, 5]"),
            ("Binary Tree", "root = [10, 5, 20, null, null, 15, 30], target = 15"),
            ("Graph", "isConnected = [[1, 1, 0], [1, 1, 0], [0, 0, 1]]"),
            ("Stack / Queue", "nums = [3, 1, 4, 1, 5]"),
            ("Hash Map / Set", "nums = [2, 7, 2, 7, 3]"),
        ]

        for label, default_txt in presets:
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
                command=lambda lbl=label, txt=default_txt: self._handle_preset(lbl, txt),
            )
            btn.pack(side=tk.LEFT, padx=2)

        btn_rand = tk.Button(
            bot_frame,
            text="Random Array",
            bg=self.BTN_BG,
            fg=self.TEXT_COLOR,
            font=("Segoe UI", 8),
            relief="flat",
            padx=6,
            pady=1,
            cursor="hand2",
            command=self._preset_random,
        )
        btn_rand.pack(side=tk.LEFT, padx=2)

    def _handle_preset(self, label: str, text: str) -> None:
        """Apply preset text and invoke optional preset callback."""
        self.set_array_text(text)
        if self.on_preset_selected:
            self.on_preset_selected(label)

    def _preset_random(self) -> None:
        """Generate a random 8-element integer list."""
        vals = [random.randint(5, 99) for _ in range(8)]
        self.set_array_text(f"nums = {vals}")
        if self.on_preset_selected:
            self.on_preset_selected("Random Array")

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
        return []
