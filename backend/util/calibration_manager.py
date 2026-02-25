import os
import json

CONFIG_FILE = os.path.join("config", "config.json")
CALIBRATION_FILE = os.path.join("config", "calibration.json")

def get_reference_object_height():
    """
    Reads ruler_cm_height from config.json
    """
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError("config.json not found")

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    return config.get("camera", {}).get("ruler_cm_height", 30.0)

REFERENCE_OBJECT_HEIGHT = get_reference_object_height()

class CalibrationManager:

    @staticmethod
    def calibration_exists():
        return os.path.exists(CALIBRATION_FILE)

    @staticmethod
    def save_calibration(cm_per_pixel, ruler_cm=REFERENCE_OBJECT_HEIGHT):
        os.makedirs("config", exist_ok=True)

        data = {
            "cm_per_pixel": cm_per_pixel,
            "ruler_cm": ruler_cm
        }

        with open(CALIBRATION_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_calibration():
        if not CalibrationManager.calibration_exists():
            return None

        with open(CALIBRATION_FILE, "r") as f:
            return json.load(f)

    @staticmethod
    def get_scale_factor():
        data = CalibrationManager.load_calibration()

        if data and "cm_per_pixel" in data:
            return float(data["cm_per_pixel"])

        raise RuntimeError("Calibration not performed yet.")