import tkinter as tk
from frontend.roundedButton import RoundedButton
from backend.util.calibration_manager import CalibrationManager
from pages.calibration_camera_page import CalibrationCameraPage
from pages.camerapage import CameraPage

class CalibrationPromptPage:
    def __init__(self, root, theme, camera_config):
        self.root = root
        self.theme = theme
        self.camera_config = camera_config

        self.root.configure(bg=self.theme["zinc-950"])

        # Clear previous widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # ---------------------
        # Centered container
        # ---------------------
        container = tk.Frame(root, bg=self.theme["zinc-950"])
        container.place(relx=0.5, rely=0.5, anchor="center")  # <-- CENTERED

        tk.Label(
            container,
            text="Would you like to calibrate the camera first?",
            font=(theme["description"], 28, "bold"),
            bg=theme["zinc-950"],
            fg=theme["zinc-100"]
        ).pack(pady=(0, 40))  # push buttons down

        btn_frame = tk.Frame(container, bg=self.theme["zinc-950"])
        btn_frame.pack()

        self.yes_btn = RoundedButton(
            btn_frame,
            text="Yes",
            width=180,
            height=60,
            command=self.go_to_calibration
        )
        self.yes_btn.pack(side="left", padx=20)

        self.no_btn = RoundedButton(
            btn_frame,
            text="No",
            width=180,
            height=60,
            command=self.go_to_camera
        )
        self.no_btn.pack(side="left", padx=20)

        # Disable NO if no calibration exists
        if not CalibrationManager.calibration_exists():
            self.no_btn.config_state("disabled")

    def go_to_calibration(self):
        # Transition immediately to calibration page
        CalibrationCameraPage(self.root, self.theme, self.camera_config)

    def go_to_camera(self):
        # Clear widgets and force redraw
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.update_idletasks()

        # Add short delay to allow full redraw
        self.root.after(250, lambda: CameraPage(self.root, self.theme, self.camera_config))