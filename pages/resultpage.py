# resultpage.py
import tkinter as tk
from PIL import Image, ImageTk
import os

# ✅ Import your custom rounded button
from frontend.roundedButton import RoundedButton


class ResultPage:
    def __init__(
        self,
        root,
        theme,
        student_info: dict,
        analysis_result: dict,
        raw_image_path: str,
        annotated_image_path: str,
        back_callback
    ):
        self.root = root
        self.theme = theme
        self.student_info = student_info
        self.analysis_result = analysis_result
        self.raw_image_path = raw_image_path
        self.annotated_image_path = annotated_image_path
        self.back_callback = back_callback

        self.root.configure(bg=self.theme["zinc-950"])

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # --- Frames ---
        left_width = screen_width // 2
        right_width = screen_width - left_width

        self.left_frame = tk.Frame(
            self.root,
            width=left_width,
            height=screen_height,
            bg=self.theme["zinc-950"]
        )
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(
            self.root,
            width=right_width,
            height=screen_height,
            bg=self.theme["zinc-950"]
        )
        self.right_frame.pack(side="left", fill="both", expand=True)

        # ==============================
        # LEFT SIDE — IMAGES
        # ==============================

        self.raw_canvas = tk.Canvas(
            self.left_frame,
            bg="black",
            highlightthickness=0
        )
        self.raw_canvas.pack(fill="both", expand=True, padx=10, pady=(20, 5))

        # Caption 1
        tk.Label(
            self.left_frame,
            text="Figure 1. Raw Image",
            font=(self.theme["description"], 14, "italic"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        ).pack(pady=(0, 10))

        self.annotated_canvas = tk.Canvas(
            self.left_frame,
            bg="black",
            highlightthickness=0
        )
        self.annotated_canvas.pack(fill="both", expand=True, padx=10, pady=(10, 5))

        # Caption 2
        tk.Label(
            self.left_frame,
            text="Figure 2. Processed Image",
            font=(self.theme["description"], 14, "italic"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        ).pack(pady=(0, 20))

        # Load images after layout stabilizes
        self.root.after(100, self.load_images)

        # ==============================
        # RIGHT SIDE — RESULTS
        # ==============================

        self.right_frame.grid_rowconfigure(0, weight=0)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Title
        title = tk.Label(
            self.right_frame,
            text="Body Fat Analysis Result",
            font=(self.theme["description"], 28, "bold"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        )
        title.grid(row=0, column=0, pady=(30, 10), padx=40, sticky="w")

        # Info container
        info_frame = tk.Frame(self.right_frame, bg=self.theme["zinc-950"])
        info_frame.grid(row=1, column=0, sticky="nsew", padx=40)

        info_frame.grid_columnconfigure(0, weight=0)
        info_frame.grid_columnconfigure(1, weight=1)

        # ------------------------------
        # Student Info
        # ------------------------------
        student_labels = [
            ("Name", student_info.get("name", "N/A")),
            ("Age", student_info.get("age", "N/A")),
            ("Gender", student_info.get("gender", "N/A")),
            ("Student ID", student_info.get("student_id", "N/A")),
            ("Grade", student_info.get("grade_name", "N/A")),
            ("Section", student_info.get("section_name", "N/A")),
        ]

        for i, (label, value) in enumerate(student_labels):
            tk.Label(
                info_frame,
                text=f"{label}:",
                font=(self.theme["description"], 15, "bold"),
                fg=self.theme["zinc-100"],
                bg=self.theme["zinc-950"]
            ).grid(row=i, column=0, sticky="w", pady=6)

            tk.Label(
                info_frame,
                text=value,
                font=(self.theme["description"], 15),
                fg=self.theme["zinc-100"],
                bg=self.theme["zinc-950"]
            ).grid(row=i, column=1, sticky="w", pady=6)

        # ------------------------------
        # Body Fat Info
        # ------------------------------
        bfp = analysis_result.get("body_fat_percent", "N/A")
        category = analysis_result.get("category", "N/A")

        try:
            bfp_text = f"{round(float(bfp), 2)}%"
        except:
            bfp_text = "N/A"

        tk.Label(
            info_frame,
            text="Estimated Body Fat %:",
            font=(self.theme["description"], 16, "bold"),
            fg=self.theme["zinc-100"],
            bg=self.theme["zinc-950"]
        ).grid(row=6, column=0, sticky="w", pady=(20, 6))

        tk.Label(
            info_frame,
            text=bfp_text,
            font=(self.theme["description"], 16, "bold"),
            fg=self.theme["emerald-600"],
            bg=self.theme["zinc-950"]
        ).grid(row=6, column=1, sticky="w", pady=(20, 6))

        tk.Label(
            info_frame,
            text="Category:",
            font=(self.theme["description"], 16, "bold"),
            fg=self.theme["zinc-100"],
            bg=self.theme["zinc-950"]
        ).grid(row=7, column=0, sticky="w", pady=6)

        tk.Label(
            info_frame,
            text=category,
            font=(self.theme["description"], 16, "bold"),
            fg=self.theme["yellow-400"],
            bg=self.theme["zinc-950"]
        ).grid(row=7, column=1, sticky="w", pady=6)

        # ==============================
        # PRETTY BACK BUTTON
        # ==============================

        button_container = tk.Frame(self.right_frame, bg=self.theme["zinc-950"])
        button_container.grid(row=2, column=0, pady=50)

        self.back_btn = RoundedButton(
            button_container,
            text="← Back to Camera",
            command=self.on_back,
            width=260,
            height=60,
            radius=22,
            bg=self.theme["blue-700"],
            fg=self.theme["zinc-100"],
            font=(self.theme["description"], 16, "bold")
        )
        self.back_btn.pack()

    # ==============================
    # IMAGE LOADING
    # ==============================

    def load_images(self):
        self.raw_imgtk = self._load_image_on_canvas(
            self.raw_image_path,
            self.raw_canvas
        )
        self.annotated_imgtk = self._load_image_on_canvas(
            self.annotated_image_path,
            self.annotated_canvas
        )

    def _load_image_on_canvas(self, path, canvas):
        if not os.path.exists(path):
            return None

        canvas.update_idletasks()
        canvas_width = canvas.winfo_width() or 400
        canvas_height = canvas.winfo_height() or 400

        img = Image.open(path)
        img.thumbnail((canvas_width, canvas_height))
        imgtk = ImageTk.PhotoImage(img)

        if not hasattr(canvas, "image_refs"):
            canvas.image_refs = []
        canvas.image_refs.append(imgtk)

        canvas.create_image(
            canvas_width // 2,
            canvas_height // 2,
            image=imgtk,
            anchor="center"
        )

        return imgtk

    # ==============================
    # BACK ACTION
    # ==============================

    def on_back(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        if callable(self.back_callback):
            self.back_callback()
