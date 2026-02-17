import cv2
import mediapipe as mp
import numpy as np

class PoseAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5
        )

    def analyze_image(self, image_bgr):
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image_rgb)

        measurements = {}
        landmarks = None

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark  # <-- return this
            # Shoulders, hips, etc.
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP]
            left_knee = landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE]
            right_knee = landmarks[self.mp_pose.PoseLandmark.RIGHT_KNEE]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST]

            torso_height = abs(left_shoulder.y - left_hip.y)
            shoulder_width = abs(left_shoulder.x - right_shoulder.x) / torso_height
            hip_width = abs(left_hip.x - right_hip.x) / torso_height
            left_arm = np.linalg.norm([left_shoulder.x-left_elbow.x, left_shoulder.y-left_elbow.y]) / torso_height
            right_arm = np.linalg.norm([right_shoulder.x-right_elbow.x, right_shoulder.y-right_elbow.y]) / torso_height
            left_leg = np.linalg.norm([left_hip.x-left_knee.x, left_hip.y-left_knee.y]) / torso_height
            right_leg = np.linalg.norm([right_hip.x-right_knee.x, right_hip.y-right_knee.y]) / torso_height

            measurements = {
                "shoulder_width": shoulder_width,
                "hip_width": hip_width,
                "torso_height": torso_height,
                "left_arm": left_arm,
                "right_arm": right_arm,
                "left_leg": left_leg,
                "right_leg": right_leg,
                "waist_width": hip_width * 0.9
            }

            annotated = image_bgr.copy()
            self.mp_drawing.draw_landmarks(
                annotated,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
            return annotated, measurements, landmarks  # <-- return 3 values

        return image_bgr, measurements, landmarks

