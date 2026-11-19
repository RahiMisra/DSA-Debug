"""Code editor UI component with line numbering and execution line highlighting."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from typing import Optional

from src.ui.presets import ARRAY_PRESET


class CodeEditor(tk.Frame):
    """Text editor with line numbering and current execution line highlighting."""

    BG_COLOR = "#1E1E2E"        # Editor dark background
    FG_COLOR = "#CDD6F4"        # Main text color
    GUTTER_BG = "#181825"       # Line numbers gutter background
    GUTTER_FG = "#6C7086"       # Line numbers text color
    HIGHLIGHT_BG = "#45475A"    # Line highlight background
    HIGHLIGHT_FG = "#F5E0DC"    # Line highlight text color

    DEFAULT_CODE = ARRAY_PRESET.code

    def __init__(self, master: Optional[tk.Widget] = None, **kwargs) -> None:
        super().__init__(master, bg=self.BG_COLOR, **kwargs)

        self._font = tkfont.Font(family="Consolas", size=11)
        self._current_highlighted_line: Optional[int] = None

        self._create_widgets()
        self.set_code(self.DEFAULT_CODE)

    def _create_widgets(self) -> None:
        """Initialize gutter, text area, and scrollbar."""
        # Horizontal layout: Gutter | Text | Scrollbar
        self.gutter = tk.Text(
            self,
            width=4,
            padx=4,
            pady=6,
            takefocus=0,
            bd=0,
            bg=self.GUTTER_BG,
            fg=self.GUTTER_FG,
            font=self._font,
            state="disabled",
            wrap="none",
        )
        self.gutter.pack(side=tk.LEFT, fill=tk.Y)

        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text = tk.Text(
            self,
            padx=8,
            pady=6,
            bd=0,
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            insertbackground="#F5E0DC",
            font=self._font,
            wrap="none",
            undo=True,
            yscrollcommand=self._on_text_scroll,
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self._on_scrollbar_scroll)

        # Configure highlighting tag
        self.text.tag_configure(
            "current_line",
            background=self.HIGHLIGHT_BG,
            foreground=self.HIGHLIGHT_FG,
        )

        # Bindings for line number updating
        self.text.bind("<<Modified>>", self._on_text_modified)
        self.text.bind("<KeyRelease>", self._update_line_numbers)
        self.text.bind("<MouseWheel>", self._on_mousewheel)

    def _on_text_scroll(self, *args) -> None:
        """Sync gutter and scrollbar when text scrolls."""
        self.scrollbar.set(*args)
        self.gutter.yview_moveto(args[0])

    def _on_scrollbar_scroll(self, *args) -> None:
        """Sync text and gutter when scrollbar is dragged."""
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handle mouse wheel scrolling synchronously."""
        self.gutter.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_text_modified(self, event: tk.Event) -> None:
        """Handle text modifications and reset edit flag."""
        if self.text.edit_modified():
            self._update_line_numbers()
            self.text.edit_modified(False)

    def _update_line_numbers(self, event: Optional[tk.Event] = None) -> None:
        """Refresh the line numbers in the gutter."""
        line_count = int(self.text.index("end-1c").split(".")[0])
        lines_text = "\n".join(str(i) for i in range(1, line_count + 1))

        self.gutter.config(state="normal")
        self.gutter.delete("1.0", tk.END)
        self.gutter.insert("1.0", lines_text)
        self.gutter.config(state="disabled")

    def get_code(self) -> str:
        """Return the current code string from the editor."""
        return self.text.get("1.0", "end-1c")

    def set_code(self, code: str) -> None:
        """Replace the editor contents with the given code."""
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", code)
        self._update_line_numbers()
        self.clear_highlight()

    def highlight_line(self, lineno: Optional[int]) -> None:
        """Highlight a specific source code line.

        Args:
            lineno: 1-indexed line number, or None to clear highlights.
        """
        self.clear_highlight()
        if lineno is None or lineno < 1:
            return

        total_lines = int(self.text.index("end-1c").split(".")[0])
        if lineno > total_lines:
            return

        self._current_highlighted_line = lineno
        start_index = f"{lineno}.0"
        end_index = f"{lineno}.end+1c"
        self.text.tag_add("current_line", start_index, end_index)
        self.text.see(start_index)

    def clear_highlight(self) -> None:
        """Remove any active line highlight."""
        self.text.tag_remove("current_line", "1.0", tk.END)
        self._current_highlighted_line = None

    @property
    def current_highlighted_line(self) -> Optional[int]:
        """Return the currently highlighted line number, if any."""
        return self._current_highlighted_line
