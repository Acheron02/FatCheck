import tkinter as tk
from PIL import Image, ImageTk

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text="", command=None, width=150, height=50,
                 radius=12, bg="#1d4ed8", fg="#ffffff", font=("Arial", 14, "bold")):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.parent = parent
        self._user_command = command
        self.radius = radius
        self.bg_color = bg
        self.fg_color = fg
        self.hover_color = self._darker_color(bg)
        self.disabled_bg = "#555555"
        self.disabled_fg = "#aaaaaa"
        self.font = font
        self.state = "normal"

        self.round_rect = self.create_rounded_rect(0, 0, width, height, radius, fill=self.bg_color)
        self.text_id = self.create_text(width//2, height//2, text=text, fill=self.fg_color, font=self.font)

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def _on_click(self, event):
        if self.state == "normal" and self._user_command:
            self._user_command()

    def _on_enter(self, event):
        if self.state == "normal":
            self.itemconfig(self.round_rect, fill=self.hover_color)

    def _on_leave(self, event):
        if self.state == "normal":
            self.itemconfig(self.round_rect, fill=self.bg_color)

    def config_state(self, state):
        """Enable or disable the button."""
        self.state = state
        if state == "normal":
            self.itemconfig(self.round_rect, fill=self.bg_color)
            self.itemconfig(self.text_id, fill=self.fg_color)
        else:
            self.itemconfig(self.round_rect, fill=self.disabled_bg)
            self.itemconfig(self.text_id, fill=self.disabled_fg)

    def _darker_color(self, hex_color, factor=0.85):
        hex_color = hex_color.lstrip("#")
        r = max(0, int(int(hex_color[0:2], 16) * factor))
        g = max(0, int(int(hex_color[2:4], 16) * factor))
        b = max(0, int(int(hex_color[4:6], 16) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
