import tkinter as tk
import subprocess
import time
import json
from pages.welcomepage import WelcomePage
from backend.util.config_loader import load_config
from pyngrok import ngrok
import socket

server_process = None 

def start_server():
    global server_process
    uvicorn_path = "/home/adrian/FatCheck/venv/bin/uvicorn"
    server_process = subprocess.Popen(
        [
            uvicorn_path,
            "backend.server:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ],
        cwd="/home/adrian/FatCheck",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("[Main] FastAPI server started on port 8000", flush=True)

def wait_for_port(host, port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.5)
    return False

def start_ngrok():
    public_url = ngrok.connect(8000)
    print(f"[Main] Ngrok tunnel started: {public_url}", flush=True)
    return str(public_url)

def main():
    global server_process
    config = load_config()

    # Start server (blocking)
    start_server()

    print("[Main] Waiting for FastAPI server...")
    if not wait_for_port("127.0.0.1", 8000, timeout=20):
        print("[Main] ❌ FastAPI failed to start on port 8000")
        return
    print("[Main] ✅ FastAPI is ready on port 8000")

    start_ngrok()

    root = tk.Tk()
    root.title(config["app"]["title"])

    if config["app"].get("fullscreen", False):
        root.update()
        root.attributes("-fullscreen", True)
        root.lift()
        root.focus_force()
    else:
        width = config["app"]["window_width"]
        height = config["app"]["window_height"]
        root.geometry(f"{width}x{height}")

    def on_app_close():
        print("[Main] Closing app...")
        global server_process
        if server_process and server_process.poll() is None:
            print("[Main] Terminating FastAPI server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("[Main] FastAPI server terminated.")
            except subprocess.TimeoutExpired:
                print("[Main] FastAPI server did not terminate in time. Killing...")
                server_process.kill()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_app_close)
    root.bind("<Escape>", lambda e: on_app_close())

    theme = config["theme"]
    text_sizes = config["text-size"]
    camera_config = config["camera"]

    WelcomePage(root, theme=theme, text_sizes=text_sizes, camera_config=camera_config)

    root.mainloop()

if __name__ == "__main__":
    main()