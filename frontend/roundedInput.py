import tkinter as tk

class RoundedInput(tk.Frame):
    def __init__(self, parent, theme, text_sizes, width=250, height=45, radius=12,
                 placeholder="", font_size_key="xsm", value=None, editable=True, **kwargs):
        """
        value: optional pre-filled value from database. 
               If None, placeholder is used.
        editable: if False, the input is read-only (disabled)
        """
        super().__init__(parent, bg=parent["bg"], **kwargs)

        self.theme = theme
        self.placeholder = placeholder
        self.font_size = int(text_sizes.get(font_size_key, 12))
        self.width = width
        self.height = height
        self.editable = editable

        # Theme colors
        self.bg_color = theme["neutral-800"]
        self.fg_color = theme["zinc-100"]
        self.placeholder_color = theme["neutral-600"]

        self.font = (theme["description"], self.font_size)

        # Canvas for rounded rectangle background
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=parent["bg"],
            highlightthickness=0
        )
        self.canvas.pack()

        # Rounded rectangle
        self.rect = self._create_rounded_rect(
            0, 0, width, height, radius,
            fill=self.bg_color
        )

        # Entry widget
        self.entry = tk.Entry(
            self,
            bd=0,
            bg=self.bg_color,
            font=self.font,
            insertbackground=self.fg_color,
            highlightthickness=0,
            relief="flat",
            disabledbackground=self.bg_color,  # <-- remove light gray
            disabledforeground=self.placeholder_color
        )

        self.entry.place(
            x=12,
            y=(height - self.font_size - 6) // 2,
            width=width - 24,
            height=self.font_size + 8
        )

        # Set initial value or placeholder
        if value is None or value == placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=self.placeholder_color)
            self.is_placeholder = True
        else:
            self.entry.insert(0, value)
            self.entry.config(fg=self.fg_color)
            self.is_placeholder = False

        # Disable entry if not editable
        if not editable:
            self.entry.config(state="disabled")

        # Bind focus for placeholder logic
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._add_placeholder)

    def _create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2,
            x1+r, y2, x1, y2, x1, y2-r,
            x1, y1+r, x1, y1
        ]
        return self.canvas.create_polygon(
            points, smooth=True, splinesteps=36, **kwargs
        )

    def _clear_placeholder(self, event):
        if getattr(self, "is_placeholder", False):
            self.entry.delete(0, "end")
            self.entry.config(fg=self.fg_color)
            self.is_placeholder = False

    def _add_placeholder(self, event):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
            self.is_placeholder = True

    def get(self):
        value = self.entry.get()
        if getattr(self, "is_placeholder", False):
            return ""
        return value

    def set(self, text):
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        if text is None or text == self.placeholder:
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.placeholder_color)
            self.is_placeholder = True
        else:
            self.entry.insert(0, text)
            self.entry.config(fg=self.fg_color)
            self.is_placeholder = False
        if not self.editable:
            self.entry.config(state="disabled")
