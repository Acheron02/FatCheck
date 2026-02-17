import tkinter as tk

class RoundedInput(tk.Frame):
    def __init__(self, parent, theme, text_sizes, width=250, height=45, radius=12,
                 placeholder="", font_size_key="xsm", value=None, editable=True, reset_callback=None, **kwargs):
        super().__init__(parent, bg=parent["bg"], **kwargs)

        self.theme = theme
        self.placeholder = placeholder
        self.font_size = int(text_sizes.get(font_size_key, 12))
        self.width = width
        self.height = height
        self.editable = editable
        self.reset_callback = reset_callback
        self.is_placeholder = False

        # Theme colors
        self.bg_color = theme.get("neutral-800")
        self.fg_color = theme.get("zinc-100")         # real data white
        self.placeholder_color = theme.get("neutral-600")  # placeholder gray
        self.font = (theme.get("description"), self.font_size)

        # Canvas for rounded rectangle
        self.canvas = tk.Canvas(self, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.canvas.pack()
        self._create_rounded_rect(0, 0, width, height, radius, fill=self.bg_color)

        # Entry widget
        self.entry = tk.Entry(
            self,
            bd=0,
            bg=self.bg_color,
            font=self.font,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            highlightthickness=0,
            relief="flat",
        )
        self.entry.place(x=12, y=(height - self.font_size - 6)//2, width=width-24, height=self.font_size+8)

        # Set initial value or placeholder
        if value is None or value == placeholder:
            self._set_placeholder()
        else:
            self.set(value)

        # If not editable, prevent typing, selection, cursor, etc.
        if not editable:
            self.entry.bind("<Key>", lambda e: "break")        # block typing
            self.entry.bind("<Button-1>", lambda e: "break")   # block mouse click
            self.entry.configure(insertwidth=0)                # hide cursor

        # Bind focus and key events for editable entries
        if editable:
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)
            self.entry.bind("<KeyRelease>", self._on_key_release)

    # ------------------------------
    def _create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,
                  x2,y2-r,x2,y2,x2-r,y2,
                  x1+r,y2,x1,y2,x1,y2-r,
                  x1,y1+r,x1,y1]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    # ------------------------------
    def _set_placeholder(self):
        self.entry.config(state="normal")
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=self.placeholder_color)
        self.is_placeholder = True

    def _on_focus_in(self, event):
        if self.is_placeholder and self.editable:
            self.entry.config(fg=self.fg_color)
            self.entry.delete(0, "end")
            self.is_placeholder = False

    def _on_focus_out(self, event):
        if not self.entry.get():
            self._set_placeholder()
        # Call reset callback here instead of on key release
        if self.reset_callback:
            self.reset_callback()

    def _on_key_release(self, event):
        # Only trigger reset callback, but do NOT set placeholder yet
        if self.editable and self.reset_callback:
            self.reset_callback()

    # ------------------------------
    def get(self):
        text = self.entry.get().strip()
        if self.is_placeholder or text == "":
            return ""
        return text 

    # ------------------------------
    def set(self, text):
        self.entry.config(state="normal")
        if not text:
            self._set_placeholder()
        else:
            self.entry.delete(0, "end")
            self.entry.insert(0, text)
            self.entry.config(fg=self.fg_color)
            self.is_placeholder = False

    # ------------------------------
    def set_value(self, text):
        """Programmatically set value and mark as NOT placeholder."""
        self.entry.config(state="normal")
        self.entry.delete(0, "end")

        if not text:
            self._set_placeholder()
        else:
            self.entry.insert(0, text)
            self.entry.config(fg=self.fg_color)
            self.is_placeholder = False   # ✅ critical for LRN to behave like Student ID


    def is_focused(self):
        return str(self.entry) == str(self.entry.focus_get())
