import tkinter as tk

class OnScreenKeyboard:
    def __init__(self, root, theme, height_ratio=0.35):
        self.root = root
        self.theme = theme
        self.visible = False
        self.active_entry = None  # Track focused entry

        self.screen_w = root.winfo_screenwidth()
        self.screen_h = root.winfo_screenheight()
        self.height = int(self.screen_h * height_ratio)
        self.uppercase = False  # Track if letters should be uppercase
        self.letter_buttons = []  # Keep references to letter buttons for toggling

        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=theme["neutral-800"])
        self.window.attributes("-topmost", True)

        self.window.geometry(
            f"{self.screen_w}x{self.height}+0+{self.screen_h - self.height}"
        )

        self._build_keys()
        self.root.bind_all("<Button-1>", self._handle_global_click, add="+")
        self.root.bind_all("<Button-1>", self._check_entry_click, add="+")

    # --------------------------------------------------
    def set_active_entry(self, entry):
        self.active_entry = entry

    # --------------------------------------------------
    def _build_keys(self):
        keys = [
            [*list("1234567890"), "Backspace"],
            ["@", *list("qwertyuiop"), "."],
            ["Shift", *list("asdfghjkl"), "_"],
            ["-", "?", *list("zxcv"), "Space", *list("bnm"), "!", "/"]
        ]

        for row_keys in keys:
            row_frame = tk.Frame(self.window, bg=self.theme["neutral-800"])
            row_frame.pack(pady=2)

            for key in row_keys:
                # Dynamically adjust width
                if key == "Space":
                    width = 10
                else:
                    width = max(len(key), 3)

                btn = self._create_key(row_frame, key, width)

                # Track letter buttons for case toggle
                if key.isalpha():
                    self.letter_buttons.append(btn)

    # --------------------------------------------------
    def _create_key(self, parent, text, width=4):
        btn = tk.Button(
            parent,
            text=text,
            width=width,
            height=2,
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"],
            relief="flat",
            takefocus=False,
            command=lambda t=text: self._on_key_press(t)
        )
        btn.pack(side="left", padx=2)
        return btn

    # --------------------------------------------------
    def _on_key_press(self, key):
        if not self.active_entry:
            return

        # Toggle uppercase
        if key == "Shift":
            self.uppercase = not self.uppercase
            self._update_letter_keys()
            return

        self.active_entry.focus_set()

        if key == "Backspace":
            current = self.active_entry.get()
            if len(current) > 0:
                self.active_entry.delete(len(current)-1, "end")
        elif key == "Space":
            self.active_entry.insert("end", " ")
        elif key == "Enter":
            self.active_entry.event_generate("<Return>")
        else:
            if key.isalpha():
                key_to_insert = key.upper() if self.uppercase else key.lower()
            else:
                key_to_insert = key
            self.active_entry.insert("end", key_to_insert)

    def _update_letter_keys(self):
        for btn in self.letter_buttons:
            char = btn.cget("text")
            if self.uppercase:
                btn.config(text=char.upper())
            else:
                btn.config(text=char.lower())

    # --------------------------------------------------
    def show(self):
        if not self.visible:
            self.window.deiconify()
            self.window.lift()
            self.visible = True

    # --------------------------------------------------
    def hide(self):
        if self.visible:
            self.window.withdraw()
            self.visible = False
        # **Do not remove focus from entry here!**

    # --------------------------------------------------
    def _handle_global_click(self, event):
        if not self.visible:
            return

        widget = event.widget

        # Ignore clicks inside keyboard
        parent = widget
        while parent:
            if parent == self.window:
                return
            parent = parent.master

        # Otherwise hide
        self.hide()
    
    def _check_entry_click(self, event):
        widget = event.widget

        # Only proceed if widget has 'master' (ignore strings etc.)
        if not hasattr(widget, "master"):
            return

        # Ignore clicks inside the keyboard itself
        if self._is_child_of(widget, self.window):
            return

        # If clicked on an entry, make it active and show keyboard
        if isinstance(widget, tk.Entry):
            self.set_active_entry(widget)
            self.show()

    # --------------------------------------------------
    def _is_child_of(self, widget, parent):
        """Return True if widget is a child of parent"""
        while widget:
            if widget == parent:
                return True
            widget = getattr(widget, "master", None)
        return False

    def close(self):
        if self.window is not None:
            self.window.destroy()
            self.window = None