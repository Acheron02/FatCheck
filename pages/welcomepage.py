# pages/welcomepage.py
import tkinter as tk
from PIL import Image, ImageTk
import os
from pages.calibration_prompt_page import CalibrationPromptPage

class WelcomePage:
    def __init__(self, root, theme, text_sizes, camera_config):
        self.root = root
        self.theme = theme
        self.text_sizes = text_sizes
        self.camera_config = camera_config

        # --- Set root background ---
        self.root.configure(bg=self.theme["zinc-950"])

        # --- Load and scale background image ---
        asset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fatcheck_bg_dark.png")
        self.bg_image = Image.open(asset_path)
        self.bg_image = self.bg_image.resize(
            (self.root.winfo_screenwidth(), self.root.winfo_screenheight()),
            Image.LANCZOS
        )
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)

        # --- Single canvas for everything ---
        self.canvas = tk.Canvas(
            root,
            width=self.root.winfo_screenwidth(),
            height=self.root.winfo_screenheight(),
            highlightthickness=0,
            bg=self.theme["zinc-950"]
        )
        self.canvas.pack(fill="both", expand=True)

        # --- Draw background image ---
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # --- Fonts ---
        heading_font = (theme["heading"], int(text_sizes["xl"]), "bold")
        desc_font = (theme["description"], int(text_sizes["sm"]))
        click_desc_font = (theme["description"], int(text_sizes.get("xsm", 24)))

        # --- Screen dimensions ---
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        row_height = screen_h // 3

        # --- Row 1: empty (for spacing) ---
        # Row 2: title + first description
        self.canvas.create_text(
            screen_w // 2,
            row_height + row_height // 2 - 40,
            text="Welcome to FatCheck",
            font=heading_font,
            fill=self.theme["zinc-100"],
            anchor="center"
        )
        self.canvas.create_text(
            screen_w // 2,
            row_height + row_height // 2 + 20,
            text="Your automated body analysis system",
            font=desc_font,
            fill=self.theme["neutral-600"],
            anchor="center"
        )

        # --- Row 3: click instruction ---
        self.canvas.create_text(
            screen_w // 2,
            row_height * 2 + row_height // 2,
            text="Click anywhere to proceed",
            font=click_desc_font,
            fill=self.theme["neutral-600"],
            anchor="center"
        )

        # --- Make whole page clickable ---
        self.canvas.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        # Clear canvas
        self.canvas.destroy()

        # Initialize calibration page
        CalibrationPromptPage(self.root, self.theme, self.camera_config)
