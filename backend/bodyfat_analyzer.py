import math
from collections import deque
from mediapipe import solutions as mp_solutions
from backend.util.calibration_manager import CalibrationManager

mp_pose = mp_solutions.pose


class BodyFatAnalyzer:

    ETHNICITY_ADJUSTMENT = 1.0

    # -------------------------------------------------------
    # INITIALIZER
    # -------------------------------------------------------
    def __init__(self, buffer_size=15):  # Increased buffer for stability
        self.waist_buffer = deque(maxlen=buffer_size)
        self.hip_buffer = deque(maxlen=buffer_size)
        self.neck_buffer = deque(maxlen=buffer_size)
        self.height_buffer = deque(maxlen=buffer_size)

        self.image_width = None
        self.image_height = None

    # -------------------------------------------------------
    # MEDIAN HELPER (More stable than average)
    # -------------------------------------------------------
    @staticmethod
    def median_value(values):
        if not values:
            return 0
        sorted_vals = sorted(values)
        mid = len(sorted_vals) // 2
        return sorted_vals[mid]

    # -------------------------------------------------------
    # BODY FAT CALCULATION (U.S. Navy Method)
    # -------------------------------------------------------
    @staticmethod
    def calculate_bfp(
        gender,
        waist_cm,
        neck_cm,
        height_cm,
        hip_cm=None,
        ethnicity_factor=1.0
    ):
        try:
            if waist_cm <= 0 or neck_cm <= 0 or height_cm <= 0:
                return 0

            gender = gender.lower()

            # ---------------- MALE ----------------
            if gender == "male":
                diff = waist_cm - neck_cm
                if diff <= 0:
                    return 0

                bfp = (
                    495 /
                    (1.0324
                     - 0.19077 * math.log10(diff)
                     + 0.15456 * math.log10(height_cm))
                ) - 450

            # ---------------- FEMALE ----------------
            elif gender == "female":
                if hip_cm is None or hip_cm <= 0:
                    return 0

                diff = waist_cm + hip_cm - neck_cm
                if diff <= 0:
                    return 0

                bfp = (
                    495 /
                    (1.29579
                     - 0.35004 * math.log10(diff)
                     + 0.22100 * math.log10(height_cm))
                ) - 450
            else:
                return 0

            bfp *= ethnicity_factor

            # Clamp final output
            bfp = max(0, min(bfp, 80))
            return round(bfp, 2)

        except Exception:
            return 0

    # -------------------------------------------------------
    # AGE GROUP HELPER
    # -------------------------------------------------------
    @staticmethod
    def get_age_group(age):
        try:
            age = int(age)
        except (ValueError, TypeError):
            return "Unknown"

        if 5 <= age <= 17:
            return "5-17"
        elif 18 <= age <= 39:
            return "18-39"
        elif 40 <= age <= 59:
            return "40-59"
        else:
            return "60+"

    # -------------------------------------------------------
    # CLASSIFICATION TABLES
    # -------------------------------------------------------
    MALE_TABLE = {
        "5-17":  {"underfat": (0, 9), "standard_minus": (9.01, 17),
                  "standard_plus": (17.01, 26), "overfat": (26.01, 31),
                  "obese": (31.01, 100)},
        "18-39": {"underfat": (0, 12), "standard_minus": (12.01, 18),
                  "standard_plus": (18.01, 23), "overfat": (23.01, 28),
                  "obese": (28.01, 100)},
        "40-59": {"underfat": (0, 13), "standard_minus": (13.01, 19),
                  "standard_plus": (19.01, 24), "overfat": (24.01, 29),
                  "obese": (29.01, 100)},
        "60+":   {"underfat": (0, 15), "standard_minus": (15.01, 21),
                  "standard_plus": (21.01, 26), "overfat": (26.01, 31),
                  "obese": (31.01, 100)},
    }

    FEMALE_TABLE = {
        "5-17":  {"underfat": (0, 12), "standard_minus": (12.01, 21),
                  "standard_plus": (21.01, 30), "overfat": (30.01, 34),
                  "obese": (34.01, 100)},
        "18-39": {"underfat": (0, 20), "standard_minus": (20.01, 27),
                  "standard_plus": (27.01, 34), "overfat": (34.01, 39),
                  "obese": (39.01, 100)},
        "40-59": {"underfat": (0, 21), "standard_minus": (21.01, 28),
                  "standard_plus": (28.01, 35), "overfat": (35.01, 40),
                  "obese": (40.01, 100)},
        "60+":   {"underfat": (0, 22), "standard_minus": (22.01, 29),
                  "standard_plus": (29.01, 36), "overfat": (36.01, 41),
                  "obese": (41.01, 100)},
    }

    # -------------------------------------------------------
    # CATEGORY LOGIC
    # -------------------------------------------------------
    @classmethod
    def categorize_bfp(cls, bfp, gender, age):
        if bfp <= 0:
            return "Invalid"

        age_group = cls.get_age_group(age)
        gender = gender.lower()

        table = cls.MALE_TABLE.get(age_group) if gender == "male" \
            else cls.FEMALE_TABLE.get(age_group)

        if not table:
            return "Unknown"

        for category, (low, high) in table.items():
            if low <= bfp <= high:
                return category.replace("_", " ").title()

        return "Unknown"

    # -------------------------------------------------------
    # CIRCUMFERENCE APPROXIMATION
    # -------------------------------------------------------
    def circumference_approx(self, point1, point2, factor=1.0):
        dx = (point1.x - point2.x) * self.image_width
        dy = (point1.y - point2.y) * self.image_height
        distance_pixels = math.sqrt(dx ** 2 + dy ** 2)

        cm_per_pixel = CalibrationManager.get_scale_factor()
        return distance_pixels * cm_per_pixel * factor

    # -------------------------------------------------------
    # HEIGHT ESTIMATION
    # -------------------------------------------------------
    def estimate_height(self, landmarks):
        nose = landmarks[mp_pose.PoseLandmark.NOSE]
        left_heel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL]
        right_heel = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL]

        heel_y = max(left_heel.y, right_heel.y)
        dy = (nose.y - heel_y) * self.image_height

        height_pixels = abs(dy)
        cm_per_pixel = CalibrationManager.get_scale_factor()
        return height_pixels * cm_per_pixel

    # -------------------------------------------------------
    # MEASUREMENT COMPUTATION (STABLE VERSION)
    # -------------------------------------------------------
    def compute_measurements(self, landmarks):

        l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]

        # Waist midpoint
        mid_left = type("Point", (), {})()
        mid_right = type("Point", (), {})()

        mid_left.x = (l_shoulder.x + l_hip.x) / 2
        mid_left.y = (l_shoulder.y + l_hip.y) / 2
        mid_right.x = (r_shoulder.x + r_hip.x) / 2
        mid_right.y = (r_shoulder.y + r_hip.y) / 2

        waist = self.circumference_approx(mid_left, mid_right, factor=3.5)
        hip = self.circumference_approx(l_hip, r_hip, factor=4.0)
        neck = self.circumference_approx(l_shoulder, r_shoulder, factor=1.3)
        chest = self.circumference_approx(l_shoulder, r_shoulder, factor=1.1)
        height = self.estimate_height(landmarks)

        # Add to buffers
        self.waist_buffer.append(waist)
        self.hip_buffer.append(hip)
        self.neck_buffer.append(neck)
        self.height_buffer.append(height)

        return {
            "Waist Circumference (cm)": round(self.median_value(self.waist_buffer), 1),
            "Hip Circumference (cm)": round(self.median_value(self.hip_buffer), 1),
            "Neck Circumference (cm)": round(self.median_value(self.neck_buffer), 1),
            "Chest Circumference (cm)": round(chest, 1),
            "Estimated Height (cm)": round(self.median_value(self.height_buffer), 1)
        }

    # -------------------------------------------------------
    # MAIN ANALYSIS FUNCTION
    # -------------------------------------------------------
    def analyze_pose(self, landmarks, gender, age, image_width, image_height):

        self.image_width = image_width
        self.image_height = image_height

        measurements = self.compute_measurements(landmarks)

        bfp = self.calculate_bfp(
            gender=gender,
            waist_cm=measurements["Waist Circumference (cm)"],
            neck_cm=measurements["Neck Circumference (cm)"],
            hip_cm=measurements["Hip Circumference (cm)"],
            height_cm=measurements["Estimated Height (cm)"],
            ethnicity_factor=self.ETHNICITY_ADJUSTMENT
        )

        category = self.categorize_bfp(bfp, gender, age)

        return {
            "measurements": measurements,
            "body_fat_percent": bfp,
            "category": category,
            "age_group": self.get_age_group(age)
        }