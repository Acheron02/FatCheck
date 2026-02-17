# bodyfat_analyzer.py
import math
import numpy as np
from mediapipe import solutions as mp_solutions

mp_pose = mp_solutions.pose

class BodyFatAnalyzer:
    """
    Estimate Body Fat % (BF%) from pose landmarks using heuristic circumferences.
    Based on US Navy method, adapted for 2D pose landmarks.
    """
    def __init__(self, scaling_factor=200):
        self.scaling_factor = scaling_factor

    @staticmethod
    def dist_3d(a, b):
        return np.linalg.norm(np.array([a.x, a.y, a.z]) - np.array([b.x, b.y, b.z]))

    def circumference_approx(self, a, b, factor=1.0):
        width = self.dist_3d(a, b) * self.scaling_factor
        return math.pi * width * factor

    def estimate_height(self, landmarks):
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        l_foot = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]
        r_foot = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX]

        foot_center = type('Point', (object,), {})()
        foot_center.x = (l_foot.x + r_foot.x) / 2
        foot_center.y = (l_foot.y + r_foot.y) / 2
        foot_center.z = (l_foot.z + r_foot.z) / 2

        pixel_height = self.dist_3d(nose, foot_center)
        return pixel_height * self.scaling_factor

    def compute_measurements(self, landmarks):
        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        waist_circ = self.circumference_approx(l_hip, r_hip, factor=2.0)
        hip_circ = self.circumference_approx(l_hip, r_hip, factor=1.2)
        neck_circ = self.circumference_approx(l_shoulder, r_shoulder, factor=0.3)
        chest_circ = self.circumference_approx(l_shoulder, r_shoulder, factor=1.1)

        height_cm = self.estimate_height(landmarks)

        # Round all measurements to nearest integer
        measurements = {
            "Waist Circumference (cm)": round(waist_circ),
            "Hip Circumference (cm)": round(hip_circ),
            "Neck Circumference (cm)": round(neck_circ),
            "Chest Circumference (cm)": round(chest_circ),
            "Estimated Height (cm)": round(height_cm)
        }
        return measurements

    @staticmethod
    def calculate_bfp(gender, waist_cm, neck_cm, hip_cm=None, height_cm=None):
        if gender.lower() == "male":
            if height_cm is None:
                raise ValueError("Height required for male BF% calculation")
            bfp = 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        else:
            if hip_cm is None or height_cm is None:
                raise ValueError("Hip and height required for female BF% calculation")
            bfp = 495 / (1.29579 - 0.35004 * math.log10(waist_cm + hip_cm - neck_cm) + 0.22100 * math.log10(height_cm)) - 450
        return bfp

    @staticmethod
    def categorize_bfp(bfp, gender, age=None):
        gender = gender.lower()
        if gender == "male":
            if bfp < 6:
                return "Underfat"
            elif bfp < 24:
                return "Average"
            elif bfp < 30:
                return "Overfat"
            else:
                return "Obese"
        else:
            if bfp < 16:
                return "Underfat"
            elif bfp < 30:
                return "Average"
            elif bfp < 36:
                return "Overfat"
            else:
                return "Obese"

    def analyze_pose(self, landmarks, gender="male", age=None):
        """
        Full pipeline: compute measurements, estimate BF%, and categorize
        Rounded values for PDF reporting.
        """
        measurements = self.compute_measurements(landmarks)
        bfp = self.calculate_bfp(
            gender,
            waist_cm=measurements["Waist Circumference (cm)"],
            neck_cm=measurements["Neck Circumference (cm)"],
            hip_cm=measurements.get("Hip Circumference (cm)"),
            height_cm=measurements["Estimated Height (cm)"]
        )
        category = self.categorize_bfp(bfp, gender, age)

        # Round BF% to nearest integer
        return {
            "measurements": measurements,
            "body_fat_percent": round(bfp),
            "category": category
        }
