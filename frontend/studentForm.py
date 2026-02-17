import tkinter as tk
from frontend.roundedButton import RoundedButton
from frontend.roundedInput import RoundedInput
from backend.student_service import fetch_student_by_id
from backend.util.custom_keyboard import OnScreenKeyboard
import threading
import subprocess
import os
import signal

class StudentForm:
    def __init__(self, root, theme, text_sizes, submit_callback=None, 
                 on_student_fetched=None, on_reset=None):
        self.root = root
        self.theme = theme
        self.text_sizes = text_sizes
        self.submit_callback = submit_callback
        self.on_student_fetched = on_student_fetched
        self.on_reset = on_reset
        self._grade_name = None
        self._section_name = None


        # Default placeholders
        self.placeholders = {
            "Name:": "Name",
            "Student ID:": "Enter Student ID",
            "Age:": "Age",
            "LRN:": "LRN",
            "Email:": "Email"
        }

        # Fonts
        self.label_font = (theme["description"], int(text_sizes["xsm"]))
        self.button_font = (theme["description"], int(text_sizes["xsm"]), "bold")
        self.title_font = (theme["description"], int(text_sizes["sm"]))

        # Card settings
        card_width = 420
        card_height = 400
        radius = 16
        padding = 18

        # Container
        self.container = tk.Frame(root, bg=self.theme["zinc-950"])

        self.keyboard = OnScreenKeyboard(self.root, self.theme)

        # Canvas card
        self.card_canvas = tk.Canvas(
            self.container,
            width=card_width,
            height=card_height,
            bg=self.theme["zinc-950"],
            highlightthickness=0
        )
        self.card_canvas.grid(row=0, column=0, sticky="nsew")
        self._draw_rounded_rect(self.card_canvas, 0,0,card_width,card_height,radius,
                                fill=self.theme["zinc-950"], outline=self.theme["neutral-600"], width=2)

        self.frame = tk.Frame(self.card_canvas, bg=self.theme["zinc-950"])
        self.card_canvas.create_window(padding, padding, window=self.frame, anchor="nw")

        # Header
        header = tk.Frame(self.frame, bg=self.theme["zinc-950"])
        header.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,14))
        tk.Label(header, text="Search Student", font=self.title_font,
                 fg=self.theme["zinc-100"], bg=self.theme["zinc-950"]).grid(row=0,column=0,sticky="w")

        # Fields
        self.fields = {}
        self.create_field("Name:", self.placeholders["Name:"], editable=False, row=1)
        self.create_field("Student ID:", self.placeholders["Student ID:"], editable=True, row=2,
                          reset_callback=self.clear_student_data)
        self.create_field("Age:", self.placeholders["Age:"], editable=False, row=3)
        self.create_field("LRN:", self.placeholders["LRN:"], editable=True, row=4,
                          reset_callback=self.clear_student_data)
        self.create_field("Email:", self.placeholders["Email:"], editable=False, row=5)

        # Submit button
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
        self.submit_btn.grid(row=6, column=0, columnspan=2, pady=(16,0))

    # ------------------------------
    def create_field(self, label_text, placeholder, editable=False, row=0, reset_callback=None):
        tk.Label(self.frame, text=label_text, font=self.label_font,
                 fg=self.theme["neutral-600"], bg=self.theme["zinc-950"]).grid(row=row, column=0, sticky="w", pady=6, padx=(0,10))

        rounded_input = RoundedInput(
            self.frame,
            theme=self.theme,
            text_sizes=self.text_sizes,
            placeholder=placeholder,
            width=280,
            height=36,
            font_size_key="xsm",
            editable=editable,
            reset_callback=reset_callback
        )
        rounded_input.grid(row=row, column=1, sticky="w", pady=6)

        if editable:
            rounded_input.entry.bind(
                "<FocusIn>",
                lambda e, entry=rounded_input.entry: self._activate_keyboard(entry),
                add="+"
            )
            rounded_input.entry.bind("<FocusOut>", lambda e: self.container.after(150, self._check_focus), add="+")

        if label_text == "Student ID:":
            self.student_id_entry = rounded_input
        elif label_text == "LRN:":
            self.lrn_entry = rounded_input

        self.fields[label_text] = rounded_input

    def _activate_keyboard(self, entry):
        self.keyboard.set_active_entry(entry)
        self.keyboard.show()

    # ------------------------------
    def _check_focus(self):
        focused = self.root.focus_get()

        # If focus is not inside any editable entry, hide keyboard
        for key, field in self.fields.items():
            if field.editable and str(field.entry) == str(focused):
                return

        self.keyboard.hide()

    # ------------------------------
    def update_student_data(self, data: dict):
        self.fields["Name:"].set_value(data.get("name", self.placeholders["Name:"]))
        self.fields["Age:"].set_value(str(data.get("age", self.placeholders["Age:"])))
        self.fields["Email:"].set_value(data.get("email", self.placeholders["Email:"]))
        self.fields["Student ID:"].set_value(data.get("schoolStudentId", ""))
        self.fields["LRN:"].set_value(data.get("lrn", ""))

    # ------------------------------
    def clear_student_data(self):
        for key, field in self.fields.items():
            if not field.editable:
                field._set_placeholder()

        focused_key, focused_field = self.get_focused_editable()
        for key, field in self.fields.items():
            if field.editable and field != focused_field:
                field._set_placeholder()

        if self.on_reset:
            self.on_reset()

    # ------------------------------
    def on_submit(self):
        student_id = self.student_id_entry.get().strip()
        lrn = self.lrn_entry.get().strip()

        if not student_id and not lrn:
            print("Student ID and LRN is empty")
            return

        self.clear_student_data()

        threading.Thread(
            target=self._fetch_student,
            args=(student_id, lrn),
            daemon=True
        ).start()

    # ------------------------------
    def _fetch_student(self, student_id=None, lrn=None):
        student_id = student_id or None
        lrn = lrn or None

        if not student_id and not lrn:
            return

        data = fetch_student_by_id(student_id=student_id, lrn=lrn)
        if data:
            self.update_student_data(data)
            # Store grade & section internally
            self._grade_name = data.get("grade_name")
            self._section_name = data.get("section_name")
            if self.on_student_fetched:
                self.on_student_fetched(data)
        else:
            print(f"No student found with Student ID: {student_id} or LRN: {lrn}")


    # ------------------------------
    def get_focused_editable(self):
        for key, field in self.fields.items():
            if field.editable and field.is_focused():
                return key, field
        return None, None

    # ------------------------------
    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,
                  x2,y2-r,x2,y2,x2-r,y2,
                  x1+r,y2,x1,y2,x1,y2-r,
                  x1,y1+r,x1,y1]
        canvas.create_polygon(points, smooth=True, splinesteps=36, **kwargs)

    def get_student_id(self):
        return self.fields["Student ID:"].get().strip()

    def get_name(self):
        return self.fields["Name:"].get().strip()

    def get_age(self):
        return self.fields["Age:"].get().strip()

    def get_lrn(self):
        return self.fields["LRN:"].get().strip()

    def get_email(self):
        return self.fields["Email:"].get().strip()

    def get_grade_name(self):
        return self._grade_name or "N/A"

    def get_section_name(self):
        return self._section_name or "N/A"

