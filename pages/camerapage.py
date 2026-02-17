import tkinter as tk
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime
from frontend.roundedButton import RoundedButton
from frontend.studentForm import StudentForm
from backend.gender_detector import GenderHeuristicPredictor
from backend.pose_analyzer import PoseAnalyzer
from backend.bodyfat_analyzer import BodyFatAnalyzer
from backend.util.report_generator import PDFReportGenerator
from pages.resultpage import ResultPage

class CameraPage:
    def __init__(self, root, theme, camera_config):
        self.root = root
        self.theme = theme
        self.camera_config = camera_config

        self.root.configure(bg=self.theme["zinc-950"])

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.pose_analyzer = PoseAnalyzer()

        # --- Frames ---
        camera_width = screen_width // 2
        form_width = screen_width - camera_width

        self.left_frame = tk.Frame(self.root, width=camera_width, height=screen_height, bg="black")
        self.left_frame.pack(side="left", fill="both", expand=True)

        self.right_frame = tk.Frame(self.root, width=form_width, height=screen_height, bg=self.theme["zinc-950"])
        self.right_frame.pack(side="left", fill="both", expand=True)

        # --- Camera canvas ---
        self.canvas = tk.Canvas(self.left_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # --- Video capture ---
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1280)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.cam_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if not self.cam_fps or self.cam_fps < 1:
            self.cam_fps = 30
        print(f"[CameraPage] Running at {self.cam_fps} FPS")

        self.frame_delay = int(1000 / self.cam_fps)
        self.imgtk = None
        self.canvas_image = self.canvas.create_image(0, 0, anchor="center")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.last_frame_full_res = None

        # --- Layout ---
        self.right_frame.grid_rowconfigure(0, weight=0)
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_rowconfigure(2, weight=0)
        self.right_frame.grid_columnconfigure(0, weight=1)

        # --- Title ---
        self.page_title = tk.Label(
            self.right_frame,
            text="Camera Capture",
            font=(self.theme["description"], 28, "bold"),
            bg=self.theme["zinc-950"],
            fg=self.theme["zinc-100"]
        )
        self.page_title.grid(row=0, column=0, pady=(20,0), padx=20)

        # --- Form wrapper ---
        form_wrapper = tk.Frame(self.right_frame, bg=self.theme["zinc-950"])
        form_wrapper.grid(row=1, column=0, sticky="nsew", padx=20)
        form_wrapper.grid_rowconfigure(0, weight=1)
        form_wrapper.grid_columnconfigure(0, weight=1)

        # --- Student Form ---
        self.student_form = StudentForm(
            form_wrapper,
            theme=self.theme,
            text_sizes={"md": 28, "sm": 24, "xsm": 12, "l": 35},
            submit_callback=None,
            on_student_fetched=lambda data: self.capture_btn.config_state("normal"),
            on_reset=lambda: self.capture_btn.config_state("disabled")
        )
        self.student_form.container.grid(row=0, column=0, sticky="n", pady=10)

        # --- Capture Button ---
        self.capture_btn = RoundedButton(
            self.right_frame,
            text="Capture Image",
            command=self.capture_image,
            width=200,
            height=60
        )
        self.capture_btn.grid(row=2, column=0, pady=20, padx=20)
        self.capture_btn.config_state("disabled")  # initially disabled

        # --- Start video loop ---
        self.update_loop_id = None
        self.update_frame()

    # ------------------------------
    def on_canvas_resize(self, event):
        canvas_width = event.width
        canvas_height = event.height
        self.canvas.coords(self.canvas_image, canvas_width // 2, canvas_height // 2)

    # ------------------------------
    def update_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.last_frame_full_res = frame.copy()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
                self.imgtk = img
                self.canvas.itemconfig(self.canvas_image, image=self.imgtk)
        self.update_loop_id = self.root.after(self.frame_delay, self.update_frame)

    # ------------------------------
    def capture_image(self):
        if self.last_frame_full_res is None:
            return

        # Stop camera loop
        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
        if self.cap.isOpened():
            self.cap.release()

        raw_image = self.last_frame_full_res.copy()

        # --- Pose analysis ---
        annotated_image, measurements, landmarks = self.pose_analyzer.analyze_image(raw_image)
        if not measurements:
            print("[CameraPage] No pose detected. Skipping capture.")
            return

        # --- Gender & Body Fat ---
        gender = GenderHeuristicPredictor().predict(measurements)
        bf_result = BodyFatAnalyzer(scaling_factor=200).analyze_pose(landmarks, gender=gender)

        # --- Student info ---
        student_id = self.student_form.get_student_id()
        student_info = {
            "name": self.student_form.get_name(),
            "age": self.student_form.get_age(),
            "gender": gender,
            "student_id": student_id,
            "lrn": self.student_form.get_lrn(),
            "email": self.student_form.get_email(),
            "grade_name": self.student_form.get_grade_name(),
            "section_name": self.student_form.get_section_name()
        }

        # --- Save folder & images ---
        student_folder = os.path.join("captures", student_id)
        os.makedirs(student_folder, exist_ok=True)

        raw_filename = os.path.join(student_folder, f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        cv2.imwrite(raw_filename, raw_image)

        processed_filename = os.path.join(student_folder, f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        cv2.imwrite(processed_filename, annotated_image)

        # --- Generate PDF ---
        pdf_path = PDFReportGenerator(base_output_dir="captures").generate_report(
            student_info, bf_result, raw_image_path=raw_filename, annotated_image_path=processed_filename
        )

        # --- Save CSV result ---
        results_file = os.path.join(student_folder, "bodyfat_results.csv")
        import csv
        file_exists = os.path.isfile(results_file)
        with open(results_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow([
                    "Timestamp", "Gender", "Body Fat %", "Category",
                    "Waist (cm)", "Hip (cm)", "Neck (cm)", "Chest (cm)", "Height (cm)"
                ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                gender,
                round(bf_result["body_fat_percent"], 2),
                bf_result["category"],
                round(bf_result["measurements"]["Waist Circumference (cm)"], 2),
                round(bf_result["measurements"]["Hip Circumference (cm)"], 2),
                round(bf_result["measurements"]["Neck Circumference (cm)"], 2),
                round(bf_result["measurements"]["Chest Circumference (cm)"], 2),
                round(bf_result["measurements"]["Estimated Height (cm)"], 2)
            ])

        print("[CameraPage] Saved images, PDF, and CSV in folder:", student_folder)

        # --- Navigate to ResultPage ---
        for widget in self.root.winfo_children():
            widget.destroy()
        ResultPage(
            self.root,
            theme=self.theme,
            student_info=student_info,
            analysis_result=bf_result,
            raw_image_path=raw_filename,
            annotated_image_path=processed_filename,
            back_callback=self.reset_page
        )

    def reset_page(self):
        # destroy everything
        for widget in self.root.winfo_children():
            widget.destroy()
        # re-initialize CameraPage
        CameraPage(self.root, self.theme, self.camera_config)

    # ------------------------------
    def close(self):
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()
