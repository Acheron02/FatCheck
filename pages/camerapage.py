import tkinter as tk
from PIL import Image, ImageTk
import cv2
import os
import json
from datetime import datetime
from frontend.roundedButton import RoundedButton
from frontend.studentForm import StudentForm
from backend.pose_analyzer import PoseAnalyzer
from backend.bodyfat_analyzer import BodyFatAnalyzer
from backend.util.report_generator import PDFReportGenerator
from pages.resultpage import ResultPage

with open("config/config.json", "r") as f:
    CONFIG = json.load(f)

CATEGORY_PROGRAMS = CONFIG.get("CATEGORY_PROGRAMS", {})


class CameraPage:
    def __init__(self, root, theme, camera_config):
        self.root = root
        self.theme = theme
        self.camera_config = camera_config

        self.root.configure(bg=self.theme["zinc-950"])

        self.pose_analyzer = PoseAnalyzer()

        # ---------------- DIALOG STATE ----------------
        self.error_dialog = None
        self.overlay = None

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        camera_width = screen_width // 2
        form_width = screen_width - camera_width

        self.left_frame = tk.Frame(self.root, width=camera_width, height=screen_height, bg="black")
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(self.root, width=form_width, height=screen_height, bg=self.theme["zinc-950"])
        self.right_frame.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(self.left_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # ---------------- VIDEO CAPTURE ----------------
        self.cap = cv2.VideoCapture(0)
        self._configure_camera()

        self.cam_fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.frame_delay = max(1, int(1000 / self.cam_fps))

        self.imgtk = None
        self.canvas_image = self.canvas.create_image(0, 0, anchor="center")
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        self.last_frame_full_res = None
        self.update_loop_id = None

        # ---------------- HEADER (Title + Recalibrate) ----------------
        self.header_frame = tk.Frame(
            self.right_frame,
            bg=self.theme["zinc-950"]
        )
        self.header_frame.pack(fill="x", pady=(30, 20), padx=40)

        # Inner wrapper to bring content slightly toward center
        self.header_inner = tk.Frame(
            self.header_frame,
            bg=self.theme["zinc-950"]
        )
        self.header_inner.pack(anchor="center")

        self.page_title = tk.Label(
            self.header_inner,
            text="Camera Capture",
            font=(self.theme["description"], 20, "bold"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        )
        self.page_title.pack(side="left", padx=(20, 30), pady=5)

        self.recalibrate_btn = RoundedButton(
            self.header_inner,
            text="Recalibrate",
            command=self.go_to_calibration_prompt,
            width=110,
            height=42
        )
        self.recalibrate_btn.pack(side="left", padx=(0, 20), pady=10)

        self.student_form = StudentForm(
            self.right_frame,
            theme=self.theme,
            text_sizes={"md": 28, "sm": 24, "xsm": 12, "l": 35},
            submit_callback=None,
            on_student_fetched=self.on_student_success,
            on_reset=self.on_student_reset,
            on_fetch_error=self.on_student_error
        )
        self.student_form.container.pack(pady=5)

        self.capture_btn = RoundedButton(
            self.right_frame,
            text="Capture Image",
            command=self.capture_image,
            width=200,
            height=60
        )
        self.capture_btn.pack(pady=20)
        self.capture_btn.config_state("disabled")

        self.update_frame()

    # -------------------------------------------------
    def _configure_camera(self):
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.get("resolution_width", 1920))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.get("resolution_height", 1080))
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # -------------------------------------------------
    def on_canvas_resize(self, event):
        self.canvas.coords(self.canvas_image, event.width // 2, event.height // 2)

    # -------------------------------------------------
    def update_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.last_frame_full_res = frame.copy()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.imgtk = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
                self.canvas.itemconfig(self.canvas_image, image=self.imgtk)

        self.update_loop_id = self.root.after(self.frame_delay, self.update_frame)

    def restart_camera(self):
        # Release safely
        if self.cap and self.cap.isOpened():
            self.cap.release()

        # Recreate capture object
        self.cap = cv2.VideoCapture(0)
        self._configure_camera()

        # Small warm-up delay
        self.root.after(150, self.update_frame)

    # -------------------------------------------------
    # EMBEDDED ERROR OVERLAY SYSTEM (FIXED VERSION)
    # -------------------------------------------------
    def show_error_dialog(self, message, auto_close_ms=3000, pause_camera=True):
        if self.overlay:
            return

        # Pause camera loop only if requested
        if pause_camera and self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None

        # Create overlay
        self.overlay = tk.Frame(self.left_frame, bg="black")
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.overlay.lift()
        self.overlay.tkraise()

        # Dialog
        self.error_dialog = tk.Frame(
            self.overlay,
            bg="#1f2937",
            highlightthickness=2,
            highlightbackground="#374151"
        )

        self.error_dialog.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
            width=450,
            height=240
        )

        title = tk.Label(
            self.error_dialog,
            text="ERROR",
            font=("Arial", 20, "bold"),
            bg="#1f2937",
            fg="#EF4444"
        )
        title.pack(pady=(25, 10))

        label = tk.Label(
            self.error_dialog,
            text=message,
            font=("Arial", 14),
            bg="#1f2937",
            fg="white",
            wraplength=380,
            justify="center"
        )
        label.pack(pady=(0, 20))

        close_btn = tk.Button(
            self.error_dialog,
            text="Close",
            command=self.close_error_dialog,
            font=("Arial", 12),
            bg="#EF4444",
            fg="white",
            relief="flat"
        )
        close_btn.pack(ipadx=10, ipady=5)

        self.root.update_idletasks()

        if auto_close_ms:
            self.root.after(auto_close_ms, self.close_error_dialog)
    
    # -------------------------------------------------
    def go_to_calibration_prompt(self):
        from pages.calibration_prompt_page import CalibrationPromptPage

        # Stop update loop
        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None

        # Release camera
        if self.cap and self.cap.isOpened():
            self.cap.release()

        # Destroy current widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Go back to calibration prompt page
        CalibrationPromptPage(self.root, self.theme, self.camera_config)

    def close_error_dialog(self):
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None
            self.error_dialog = None

        if not self.update_loop_id:
            self.restart_camera()

    # -------------------------------------------------
    def capture_image(self, num_frames=5):
        if self.last_frame_full_res is None:
            self.show_error_dialog("No camera frame available.")
            return

        gender = self.student_form.get_sex()
        age = self.student_form.get_age()

        if not gender:
            self.show_error_dialog("Student gender not selected.")
            return

        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None

        frames = []
        for _ in range(num_frames):
            ret, frame = self.cap.read()
            if ret:
                frames.append(frame)

        if not frames:
            self.show_error_dialog("Failed to capture frames.")
            return

        if self.cap.isOpened():
            self.cap.release()

        image_height, image_width, _ = frames[-1].shape
        bf_analyzer = BodyFatAnalyzer()

        waist_vals, hip_vals, neck_vals, chest_vals, height_vals = [], [], [], [], []

        for frame in frames:
            annotated_image, measurements, landmarks = self.pose_analyzer.analyze_image(frame)

            if not landmarks:
                continue

            result = bf_analyzer.analyze_pose(
                landmarks,
                gender=gender,
                age=age,
                image_width=image_width,
                image_height=image_height
            )

            if not result:
                continue

            m = result["measurements"]
            waist_vals.append(m["Waist Circumference (cm)"])
            hip_vals.append(m["Hip Circumference (cm)"])
            neck_vals.append(m["Neck Circumference (cm)"])
            chest_vals.append(m["Chest Circumference (cm)"])
            height_vals.append(m["Estimated Height (cm)"])

        if not waist_vals:
            self.show_error_dialog(
                "No valid pose detected.\n\nPlease stand fully visible in front of the camera and try again.",
                auto_close_ms=4000
            )
            return

        def avg(lst):
            return sum(lst) / len(lst)

        averaged_measurements = {
            "Waist Circumference (cm)": round(avg(waist_vals), 1),
            "Hip Circumference (cm)": round(avg(hip_vals), 1),
            "Neck Circumference (cm)": round(avg(neck_vals), 1),
            "Chest Circumference (cm)": round(avg(chest_vals), 1),
            "Estimated Height (cm)": round(avg(height_vals), 1)
        }

        bfp = BodyFatAnalyzer.calculate_bfp(
            gender=gender,
            waist_cm=averaged_measurements["Waist Circumference (cm)"],
            neck_cm=averaged_measurements["Neck Circumference (cm)"],
            hip_cm=averaged_measurements["Hip Circumference (cm)"],
            height_cm=averaged_measurements["Estimated Height (cm)"],
            ethnicity_factor=BodyFatAnalyzer.ETHNICITY_ADJUSTMENT
        )

        category = BodyFatAnalyzer.categorize_bfp(bfp, gender, age)

        recommended_program = CATEGORY_PROGRAMS.get(
            category,
            "Maintain Balanced Diet & Physical Activity"
        )

        bf_result_final = {
            "measurements": averaged_measurements,
            "body_fat_percent": round(bfp, 1),
            "category": category,
            "recommended_program": recommended_program
        }

        raw_image = frames[-1]
        annotated_image, _, _ = self.pose_analyzer.analyze_image(raw_image)

        student_info = {
            "name": self.student_form.get_name(),
            "age": age,
            "gender": gender,
            "student_id": self.student_form.get_student_id(),
            "lrn": self.student_form.get_lrn(),
            "email": self.student_form.get_email(),
            "grade_name": self.student_form.get_grade_name(),
            "section_name": self.student_form.get_section_name()
        }

        if hasattr(self.student_form, "custom_keyboard"):
            self.student_form.custom_keyboard.close()

        for widget in self.root.winfo_children():
            widget.destroy()

        ResultPage(
            self.root,
            theme=self.theme,
            student_info=student_info,
            analysis_result=bf_result_final,
            raw_image_path=None,
            annotated_image_path=None,
            back_callback=self.reset_page
        )

    # -------------------------------------------------
    def reset_page(self):
        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None

        if self.cap.isOpened():
            self.cap.release()

        for widget in self.root.winfo_children():
            widget.destroy()

        CameraPage(self.root, self.theme, self.camera_config)

    # -------------------------------------------------
    def close(self):
        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None

        if self.cap.isOpened():
            self.cap.release()

        self.root.destroy()
    
    def on_student_success(self, data):
        self.capture_btn.config_state("normal")


    def on_student_reset(self):
        self.capture_btn.config_state("disabled")


    def on_student_error(self, message):
        self.capture_btn.config_state("disabled")

        # IMPORTANT: do NOT pause camera for form errors
        self.show_error_dialog(message, auto_close_ms=4000, pause_camera=False)