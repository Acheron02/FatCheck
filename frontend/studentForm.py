import tkinter as tk
from frontend.roundedButton import RoundedButton
from frontend.roundedInput import RoundedInput


class StudentForm:
    def __init__(self, root, theme, text_sizes, student_data=None, submit_callback=None):
        self.root = root  # this will be the parent frame (right_frame)
        self.theme = theme
        self.text_sizes = text_sizes
        self.submit_callback = submit_callback

        self.student_data = student_data or {
            "name": "Juan Dela Cruz",
            "student_id": "",
            "lrn": "123456789012",
            "email": "juan.delacruz@example.com"
        }

        # --- Fonts ---
        self.label_font = (theme["description"], int(text_sizes["xsm"]))
        self.button_font = (theme["description"], int(text_sizes["xsm"]), "bold")
        self.title_font = (theme["description"], int(text_sizes["sm"]))

        # --- Card sizing ---
        card_width = 420
        card_height = 340
        radius = 16
        padding = 18

        # --- Main container (frame only, use grid in CameraPage) ---
        self.container = tk.Frame(root, bg=self.theme["zinc-950"])
        # Don't pack; CameraPage will grid it

        # --- Canvas card ---
        self.card_canvas = tk.Canvas(
            self.container,
            width=card_width,
            height=card_height,
            bg=self.theme["zinc-950"],
            highlightthickness=0
        )
        self.card_canvas.grid(row=0, column=0, sticky="nsew")  # use grid

        # --- Rounded card ---
        self._draw_rounded_rect(
            self.card_canvas,
            0, 0, card_width, card_height,
            radius,
            fill=self.theme["zinc-950"],
            outline=self.theme["neutral-600"],
            width=2
        )

        # --- Content frame inside canvas ---
        self.frame = tk.Frame(self.card_canvas, bg=self.theme["zinc-950"])
        self.card_canvas.create_window(padding, padding, window=self.frame, anchor="nw")

        # ==================================================
        # HEADER
        # ==================================================
        header = tk.Frame(self.frame, bg=self.theme["zinc-950"])
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        tk.Label(
            header,
            text="Search Student",
            font=self.title_font,
            fg=self.theme["zinc-100"],
            bg=self.theme["zinc-950"],
            anchor="w"
        ).grid(row=0, column=0, sticky="w")  # use grid here too

        # ==================================================
        # FORM
        # ==================================================
        self.fields = {}
        self.create_field("Name:", self.student_data["name"], editable=False, row=1)
        self.create_field("Student ID:", self.student_data["student_id"], editable=True, row=2)
        self.create_field("LRN:", self.student_data["lrn"], editable=False, row=3)
        self.create_field("Email:", self.student_data["email"], editable=False, row=4)

        # ==================================================
        # SUBMIT BUTTON (CENTERED)
        # ==================================================
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)

        self.submit_btn = RoundedButton(
            self.frame,
            text="Submit",
            command=self.on_submit,
            width=160,
            height=40,
            radius=12,
            bg=self.theme["blue-700"],
            fg=self.theme["zinc-100"],
            font=self.button_font
        )
        # span two columns and center
        self.submit_btn.grid(row=5, column=0, columnspan=2, pady=(16, 6), sticky="n")  

    # --------------------------------------------------
    def create_field(self, label_text, value, editable=False, row=0):
        label = tk.Label(
            self.frame,
            text=label_text,
            font=self.label_font,
            fg=self.theme["neutral-600"],
            bg=self.theme["zinc-950"],
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", pady=6, padx=(0, 10))

        rounded_input = RoundedInput(
            self.frame,
            theme=self.theme,
            text_sizes=self.text_sizes,
            placeholder=value,
            width=280,
            height=36,
            font_size_key="xsm"
        )
        rounded_input.grid(row=row, column=1, sticky="w", pady=6)

        if not editable:
            rounded_input.entry.config(state="disabled")
        else:
            self.student_id_entry = rounded_input

        self.fields[label_text] = rounded_input

    # --------------------------------------------------
    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1,
            x2, y1, x2, y1+r,
            x2, y2-r,
            x2, y2, x2-r, y2,
            x1+r, y2,
            x1, y2, x1, y2-r,
            x1, y1+r,
            x1, y1
        ]
        canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    # --------------------------------------------------
    def on_submit(self):
        student_id = self.student_id_entry.get()
        if self.submit_callback:
            self.submit_callback(student_id)
        print("Submitted Student ID:", student_id)
