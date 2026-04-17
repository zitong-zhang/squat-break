"""Squat Break - 久坐蹲起提醒工具 - 蹲起检测模块"""
import math


def _angle(a, b, c):
    """Calculate angle at point b formed by points a-b-c (in degrees)."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mag_ba * mag_bc == 0:
        return 0
    cos_angle = max(-1, min(1, dot / (mag_ba * mag_bc)))
    return math.degrees(math.acos(cos_angle))


class SquatDetector:
    """State machine for counting squats based on knee angle.

    A squat is: STANDING -> DOWN (held >= min_hold_frames) -> STANDING.
    Standing: knee angle ~170-180°. Squatting: knee angle ~90-120°.
    """

    STANDING = "standing"
    DOWN = "down"

    def __init__(self, target=10, min_hold_frames=5):
        self.target = target
        self.min_hold_frames = min_hold_frames
        self.count = 0
        self.state = self.STANDING
        self._hold_frames = 0
        self._was_valid_down = False
        self._stand_threshold = 155  # above this = standing
        self._squat_threshold = 130  # below this = squatting
        self._pose = None
        self._last_angle = 0.0

    def process(self, knee_angle):
        """Update state from knee angle in degrees."""
        self._last_angle = knee_angle

        if self.state == self.STANDING:
            if knee_angle < self._squat_threshold:
                self._hold_frames += 1
                if self._hold_frames >= self.min_hold_frames:
                    self.state = self.DOWN
                    self._was_valid_down = True
            else:
                self._hold_frames = 0

        elif self.state == self.DOWN:
            if knee_angle > self._stand_threshold:
                if self._was_valid_down:
                    self.count += 1
                    self._was_valid_down = False
                self.state = self.STANDING
                self._hold_frames = 0

    def is_complete(self):
        return self.count >= self.target

    def reset(self):
        self.count = 0
        self.state = self.STANDING
        self._hold_frames = 0
        self._was_valid_down = False

    def _get_pose(self):
        if self._pose is None:
            import os
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision

            model_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "models",
                "pose_landmarker_lite.task",
            )
            options = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=vision.RunningMode.IMAGE,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
            )
            self._pose = vision.PoseLandmarker.create_from_options(options)
        return self._pose

    def process_frame(self, frame):
        """Process a BGR OpenCV frame.

        Returns (frame, count, label, person_visible, angle).
        """
        import cv2
        import numpy as np
        import mediapipe as mp

        landmarker = self._get_pose()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = landmarker.detect(mp_image)

        h, w = frame.shape[:2]
        label = "请站到摄像头前"
        person_visible = False
        angle = self._last_angle

        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            lm = results.pose_landmarks[0]
            hip = ((lm[23].x + lm[24].x) / 2, (lm[23].y + lm[24].y) / 2)
            knee = ((lm[25].x + lm[26].x) / 2, (lm[25].y + lm[26].y) / 2)
            ankle = ((lm[27].x + lm[28].x) / 2, (lm[27].y + lm[28].y) / 2)

            person_visible = True
            angle = _angle(hip, knee, ankle)
            self.process(angle)

            if self.is_complete():
                label = f"太棒了！ {self.count}/{self.target}"
            elif self.state == self.DOWN:
                label = f"站起来！ ({self.count}/{self.target})"
            else:
                label = f"蹲下去！ ({self.count}/{self.target})"

            for idx in [23, 24, 25, 26, 27, 28]:
                px = int(lm[idx].x * w)
                py = int(lm[idx].y * h)
                cv2.circle(frame, (px, py), 8, (0, 255, 0), -1)

        return frame, self.count, label, person_visible, angle

    def release(self):
        if self._pose is not None:
            self._pose.close()
            self._pose = None
