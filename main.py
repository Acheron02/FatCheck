# main.py
import tkinter as tk
from pages.welcomepage import WelcomePage
from backend.util.config_loader import load_config

def main():
    config = load_config()

    root = tk.Tk()
    root.title(config["app"]["title"])

    if config["app"].get("fullscreen", False):
        root.update()  # ensure window is fully initialized
        root.attributes("-fullscreen", True)
        root.lift()
        root.focus_force()
    else:
        width = config["app"]["window_width"]
        height = config["app"]["window_height"]
        root.geometry(f"{width}x{height}")

    
    # Bind Esc key to close the app
    root.bind("<Escape>", lambda event: root.destroy())
    
    # Initialize the welcome page
    theme = config["theme"]
    text_sizes = config["text-size"]
    camera_config = config["camera"]
    welcome_page = WelcomePage(root, theme=theme, text_sizes=text_sizes, camera_config=camera_config)
    
    root.mainloop()

if __name__ == "__main__":
    main()
