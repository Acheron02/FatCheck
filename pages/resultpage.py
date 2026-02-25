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
        # LEFT SIDE — IMAGES (fixed layout)
        # ==============================

        # Wrap both canvases in a parent frame
        self.images_frame = tk.Frame(self.left_frame, bg=self.theme["zinc-950"])
        self.images_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Split parent frame into two equal-height frames
        self.raw_frame = tk.Frame(self.images_frame, bg="black")
        self.raw_frame.pack(side="top", fill="both", expand=True, pady=(0,5))

        self.annotated_frame = tk.Frame(self.images_frame, bg="black")
        self.annotated_frame.pack(side="top", fill="both", expand=True, pady=(5,0))

        # Canvas for raw image
        self.raw_canvas = tk.Canvas(self.raw_frame, bg="black", highlightthickness=0)
        self.raw_canvas.pack(fill="both", expand=True)

        # Canvas for annotated image
        self.annotated_canvas = tk.Canvas(self.annotated_frame, bg="black", highlightthickness=0)
        self.annotated_canvas.pack(fill="both", expand=True)

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

        # Load images after layout stabilizes
        self.root.after_idle(self.load_images)

        # Optional: make images resize when window resizes
        self.left_frame.bind("<Configure>", lambda e: self.load_images())

    # ==============================
    # IMAGE LOADING
    # ==============================

    def load_images(self):
        # Strong references on self
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
            print(f"[ResultPage] Image not found: {path}")
            return None

        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # ⚠️ Guard against zero size
        if canvas_width <= 0 or canvas_height <= 0:
            # Schedule a retry after 50ms
            self.root.after(50, lambda: self._load_image_on_canvas(path, canvas))
            return None

        img = Image.open(path)
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height

        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)

        # ⚠️ Ensure dimensions are positive integers
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        img = img.resize((new_width, new_height), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(img)

        # Keep strong references
        if not hasattr(canvas, "image_refs"):
            canvas.image_refs = []
        canvas.image_refs.append(imgtk)
        if not hasattr(self, "canvas_images"):
            self.canvas_images = []
        self.canvas_images.append(imgtk)

        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=imgtk, anchor="center")
        return imgtk

    # ==============================
    # BACK ACTION
    # ==============================

    def on_back(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        if callable(self.back_callback):
            self.back_callback()
