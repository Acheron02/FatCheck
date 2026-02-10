# pages/camerapage.py
import tkinter as tk
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime
from frontend.roundedButton import RoundedButton
from frontend.studentForm import StudentForm  # import the form

class CameraPage:
    def __init__(self, root, theme, camera_config):
        self.root = root
        self.theme = theme
        self.camera_config = camera_config

        # --- Set root background ---
        self.root.configure(bg=self.theme["zinc-950"])
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # --- Frames ---
        self.left_frame = tk.Frame(self.root, width=screen_width // 2, height=screen_height, bg="black")
        self.left_frame.pack(side="left", fill="both", expand=False)

        self.right_frame = tk.Frame(self.root, width=screen_width // 2, height=screen_height, bg=self.theme["zinc-950"])
        self.right_frame.pack(side="right", fill="both", expand=True)

        # --- Canvas for camera feed ---
        self.canvas = tk.Canvas(self.left_frame, width=screen_width // 2, height=screen_height, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # --- Video capture ---
        self.cap = cv2.VideoCapture(0)
        max_width = min(self.camera_config.get("resolution_width", 1280), 1920)
        max_height = min(self.camera_config.get("resolution_height", 1080), 1080)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, max_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, max_height)
        self.cap.set(cv2.CAP_PROP_FPS, 60)

        self.cam_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cam_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        print(f"Camera opened at {self.cam_width}x{self.cam_height} @ {self.cam_fps} FPS")

        self.imgtk = None
        self.canvas_image = self.canvas.create_image(0, 0, anchor="nw")
        self.last_frame_full_res = None

        # ==================================================
        # Right frame layout (3 rows using grid)
        # ==================================================
        self.right_frame.grid_rowconfigure(0, weight=0)  # Page title row
        self.right_frame.grid_rowconfigure(1, weight=1)  # Form wrapper row (expandable)
        self.right_frame.grid_rowconfigure(2, weight=0)  # Capture button row
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- Page title ---
        self.page_title = tk.Label(
            self.right_frame,
            text="Camera Capture",
            font=(self.theme["description"], 28, "bold"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        )
        self.page_title.grid(row=0, column=0, pady=(20,10), sticky="n")

        # --- Form wrapper for centering ---
        form_wrapper = tk.Frame(self.right_frame, bg=self.theme["zinc-950"])
        form_wrapper.grid(row=1, column=0, sticky="nsew")
        form_wrapper.grid_rowconfigure(0, weight=1)
        form_wrapper.grid_columnconfigure(0, weight=1)

        # --- Student form ---
        self.student_form = StudentForm(
            form_wrapper,
            theme=self.theme,
            text_sizes={"md":28, "sm":24, "xsm":12, "l":35},
            student_data={
                "name": "Juan Dela Cruz",
                "student_id": "Enter Student ID",
                "lrn": "123456789012",
                "email": "juan.delacruz@example.com"
            },
            submit_callback=self.on_form_submit
        )
        self.student_form.container.grid(row=0, column=0, padx=20, pady=10, sticky="")

        # --- Capture button (disabled by default) ---
        self.capture_btn = RoundedButton(
            self.right_frame,
            text="Capture Image",
            command=self.capture_image,
            width=200,
            height=60
        )
        self.capture_btn.grid(row=2, column=0, pady=20, sticky="s")
        self.capture_btn.config(state="disabled")  # initially disabled

        # --- Bind student ID field to update capture button ---
        student_id_input = self.student_form.fields["Student ID:"].entry
        student_id_input.bind("<KeyRelease>", self._check_capture_state)
        # Also check immediately in case it's pre-filled
        self._check_capture_state()

        # --- Start video loop ---
        self.update_frame()

        # --- Bind Esc to close ---
        self.root.bind("<Escape>", lambda e: self.close())

    # --------------------------------------------------
    def _check_capture_state(self, event=None):
        student_input = self.student_form.fields["Student ID:"]
        student_id = student_input.get()
        if not getattr(student_input.entry, "is_placeholder", True) and student_id.strip():
            self.capture_btn.config_state("normal")
        else:
            self.capture_btn.config_state("disabled")

    # --------------------------------------------------
    def on_form_submit(self, student_id):
        print("Student ID submitted:", student_id)
        self._check_capture_state()  # re-check capture button state

    # --------------------------------------------------
    def update_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.last_frame_full_res = frame.copy()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_height, frame_width = frame_rgb.shape[:2]

                canvas_width = max(self.left_frame.winfo_width(), 1)
                canvas_height = max(self.left_frame.winfo_height(), 1)
                scale = canvas_height / frame_height
                new_width = max(int(frame_width * scale), 1)
                new_height = canvas_height

                frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
                img = ImageTk.PhotoImage(image=Image.fromarray(frame_resized))
                self.imgtk = img

                x_center = (canvas_width - new_width) // 2
                self.canvas.coords(self.canvas_image, x_center, 0)
                self.canvas.itemconfig(self.canvas_image, image=self.imgtk)
        else:
            print("Error: Camera not opened.")

        delay = max(int(1000 / self.cam_fps), 15)
        self.root.after(delay, self.update_frame)

    # --------------------------------------------------
    def capture_image(self):
        if self.last_frame_full_res is not None:
            frame_rgb = cv2.cvtColor(self.last_frame_full_res, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = "captures"
            os.makedirs(save_dir, exist_ok=True)
            file_path = os.path.join(save_dir, f"capture_{timestamp}.png")
            img.save(file_path)
            print(f"Image captured at full resolution: {file_path}")
        else:
            print("Warning: No frame available to capture.")

    # --------------------------------------------------
    def close(self):
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()
