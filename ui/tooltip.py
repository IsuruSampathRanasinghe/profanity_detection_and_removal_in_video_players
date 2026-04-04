"""Tooltip helper for hover-based guidance in Tkinter widgets."""

import tkinter as tk
from tkinter import ttk


class Tooltip:
    """Displays a tooltip on hover for any Tkinter widget."""

    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        bg: str = "#2a2a3e",
        fg: str = "#e0e0e0",
        wraplength: int = 250,
    ):
        self.widget = widget
        self.text = text
        self.bg = bg
        self.fg = fg
        self.wraplength = wraplength
        self.tooltip_window = None
        self.tooltip_label = None

        self.widget.bind("<Enter>", self._show_tooltip, add=True)
        self.widget.bind("<Leave>", self._hide_tooltip, add=True)
        self.widget.bind("<Motion>", self._update_tooltip_position, add=True)

    def _show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+0+0")

        self.tooltip_label = ttk.Label(
            tw,
            text=self.text,
            background=self.bg,
            foreground=self.fg,
            wraplength=self.wraplength,
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
            padding=(8, 6),
        )
        self.tooltip_label.pack(ipadx=2, ipady=2)
        self._update_tooltip_position(event)

    def _update_tooltip_position(self, event=None):
        if self.tooltip_window and event:
            x = event.x_root + 10
            y = event.y_root + 10
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

    def _hide_tooltip(self, _event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            self.tooltip_label = None
