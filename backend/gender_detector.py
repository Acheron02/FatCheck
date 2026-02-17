class GenderHeuristicPredictor:
    """
    Improved rule-based gender predictor using normalized pose landmarks.
    Uses multiple body ratios with adjusted thresholds.
    """

    def __init__(self):
        # Adjusted thresholds
        self.shoulder_hip_ratio_male = 1.15    # shoulders clearly wider than hips
        self.shoulder_hip_ratio_female = 0.97 # shoulders narrower than hips -> female
        self.shoulder_torso_ratio_male = 0.90
        self.shoulder_torso_ratio_female = 0.65
        self.arm_leg_ratio_male = 0.7

    def predict(self, measurements: dict) -> str:
        shoulder_width = measurements.get("shoulder_width", 0)
        hip_width = measurements.get("hip_width", 0)
        torso_height = measurements.get("torso_height", 0)
        left_arm = measurements.get("left_arm", 0)
        right_arm = measurements.get("right_arm", 0)
        left_leg = measurements.get("left_leg", 0)
        right_leg = measurements.get("right_leg", 0)

        # Fallback
        if hip_width == 0 or torso_height == 0:
            return "Unknown"

        # Compute ratios
        shoulder_hip_ratio = shoulder_width / hip_width
        shoulder_torso_ratio = shoulder_width / torso_height
        avg_arm_length = (left_arm + right_arm) / 2
        avg_leg_length = (left_leg + right_leg) / 2
        arm_leg_ratio = avg_arm_length / avg_leg_length if avg_leg_length > 0 else 0

        # --- Decision rules ---
        male_votes = 0
        female_votes = 0

        # Shoulder-Hip ratio
        if shoulder_hip_ratio > self.shoulder_hip_ratio_male:
            male_votes += 1
        elif shoulder_hip_ratio < self.shoulder_hip_ratio_female:
            female_votes += 1

        # Shoulder-Torso ratio
        if shoulder_torso_ratio > self.shoulder_torso_ratio_male:
            male_votes += 1
        elif shoulder_torso_ratio < self.shoulder_torso_ratio_female:
            female_votes += 1

        # Arm/Leg ratio
        if arm_leg_ratio > self.arm_leg_ratio_male:
            male_votes += 0.5
        else:
            female_votes += 0.5

        # Hip/Torso ratio (women tend to have relatively wider hips)
        hip_torso_ratio = hip_width / torso_height
        if hip_torso_ratio > 0.8:  # tweak if necessary
            female_votes += 1
        else:
            male_votes += 1

        # --- Final prediction ---
        if male_votes > female_votes:
            return "Male"
        elif female_votes > male_votes:
            return "Female"
        else:
            return "Unknown"
