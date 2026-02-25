import tkinter as tk
from PIL import Image, ImageTk
import cv2
from frontend.roundedButton import RoundedButton
from backend.util.calibration_manager import CalibrationManager
from pages.camerapage import CameraPage

class CalibrationCameraPage:
    def __init__(self, root, theme, camera_config):
        self.root = root
        self.theme = theme
        self.camera_config = camera_config

        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg=self.theme["zinc-950"])

        # -------------------------
        # State
        # -------------------------
        self.top_click = None
        self.bottom_click = None
        self.last_frame_full_res = None
        self.update_loop_id = None
        self.calibration_cycles = 0

        # -------------------------
        # Layout
        # -------------------------
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.left_frame = tk.Frame(self.root, width=screen_width, height=screen_height, bg="black")
        self.left_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.left_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas_image = self.canvas.create_image(0, 0, anchor="center")
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # -------------------------
        # Capture Button
        # -------------------------
        self.capture_btn = RoundedButton(
            self.root,
            text="Capture Calibration Image",
            width=280,
            height=60,
            command=self.capture_image
        )
        self.capture_btn.place(relx=0.5, rely=0.93, anchor="center")

        # -------------------------
        # Video Capture
        # -------------------------
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.get("resolution_width", 1920))
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.get("resolution_height", 1080))
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"[Calibration] Resolution: {actual_width}x{actual_height}, FPS: {actual_fps:.2f}")

        self.cam_fps = actual_fps or 30
        self.frame_delay = max(1, int(1000 / self.cam_fps))

        # Start camera loop
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
                img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
                self.imgtk = img
                self.canvas.itemconfig(self.canvas_image, image=self.imgtk)
        self.update_loop_id = self.root.after(self.frame_delay, self.update_frame)

    # ------------------------------
    def capture_image(self):
        if self.last_frame_full_res is None:
            return

        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None
        if self.cap.isOpened():
            self.cap.release()

        self.canvas.delete("instruction")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        self.canvas.create_text(
            canvas_width // 2,
            50,
            text="Click the TOP of the ruler, then the BOTTOM",
            fill="yellow",
            font=("Arial", 24, "bold"),
            tag="instruction"
        )

        self.canvas.bind("<Button-1>", self.on_click)

    # ------------------------------
    def on_click(self, event):
        img_y = event.y
        if self.top_click is None:
            self.top_click = img_y
            self.canvas.create_line(0, img_y, self.canvas.winfo_width(), img_y, fill="red", width=2, tag="click_marker")
            self.canvas.itemconfig("instruction", text="Click the BOTTOM of the ruler")
        else:
            self.bottom_click = img_y
            self.canvas.create_line(0, img_y, self.canvas.winfo_width(), img_y, fill="red", width=2, tag="click_marker")
            self.canvas.delete("instruction")
            self.calculate_scaling()

    # ------------------------------
    def calculate_scaling(self):
        pixel_height = abs(self.bottom_click - self.top_click)
        if pixel_height <= 0:
            print("Invalid selection, skipping calibration")
            self.proceed_to_camera()
            return

        ruler_cm = self.camera_config.get("ruler_cm_height", 30.0)
        cm_per_pixel = ruler_cm / pixel_height
        print("CM PER PIXEL:", cm_per_pixel)
        CalibrationManager.save_calibration(cm_per_pixel)
        print("Calibration saved!")

        # Clear markers
        self.canvas.delete("click_marker")
        self.canvas.delete("instruction")

        # Show animated message
        self.calibration_dots = 0
        self.calibration_cycles = 0
        self.calibration_text_id = self.canvas.create_text(
            self.canvas.winfo_width()//2,
            self.canvas.winfo_height()//2,
            text="Camera calibrating",
            fill="yellow",
            font=("Arial", 32, "bold")
        )
        self.animate_calibration_message()

    # ------------------------------
    def animate_calibration_message(self):
        self.calibration_dots = (self.calibration_dots + 1) % 4
        dots = "." * self.calibration_dots
        self.canvas.itemconfig(self.calibration_text_id, text=f"Camera calibrating{dots}")

        # Repeat animation for ~2 seconds (4 cycles)
        self.calibration_cycles += 1
        if self.calibration_cycles < 8:
            self.root.after(250, self.animate_calibration_message)
        else:
            self.proceed_to_camera()

    # ------------------------------
    def proceed_to_camera(self):
        # Unbind clicks and stop any running loops
        self.canvas.unbind("<Button-1>")
        if self.update_loop_id:
            self.root.after_cancel(self.update_loop_id)
            self.update_loop_id = None
        if self.cap.isOpened():
            self.cap.release()

        # Destroy all widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Start CameraPage
        CameraPage(self.root, self.theme, self.camera_config)