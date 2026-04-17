"""Squat Break - 久坐蹲起提醒工具 - 蹲起检测模块"""


class SquatDetector:
    """Detect squats by tracking hip Y position.

    Auto-calibrates standing baseline, then detects when body drops.
    Squat = hip_y exceeds baseline by 15% for >= min_hold_frames.
    """

    CALIBRATING = "calibrating"
    STANDING = "standing"
    DOWN = "down"

    def __init__(self, target=10, min_hold_frames=5):
        self.target = target
        self.min_hold_frames = min_hold_frames
        self.count = 0
        self.state = self.CALIBRATING
        self._hold_frames = 0
        self._was_valid_down = False
        self._calibration = []
        self._calibration_need = 30
        self._baseline = 0.0
        self._squat_threshold = 0.0
        self._stand_threshold = 0.0
        self._last_hip_y = 0.0
        self._pose = None

    def process(self, hip_y):
        """Update state from hip Y coordinate."""
        self._last_hip_y = hip_y

        if self.state == self.CALIBRATING:
            self._calibration.append(hip_y)
            if len(self._calibration) >= self._calibration_need:
                self._baseline = sum(self._calibration) / len(self._calibration)
                self._squat_threshold = self._baseline * 1.15
                self._stand_threshold = self._baseline * 1.08
                self.state = self.STANDING
            return

        if self.state == self.STANDING:
            if hip_y > self._squat_threshold:
                self._hold_frames += 1
                if self._hold_frames >= self.min_hold_frames:
                    self.state = self.DOWN
                    self._was_valid_down = True
            else:
                self._hold_frames = 0

        elif self.state == self.DOWN:
            if hip_y < self._stand_threshold:
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

        Returns (frame, count, label, person_visible, hip_y).
        """
        import cv2
        import mediapipe as mp

        landmarker = self._get_pose()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = landmarker.detect(mp_image)

        h, w = frame.shape[:2]
        label = "校准中..." if self.state == self.CALIBRATING else "请站到摄像头前"
        person_visible = False
        hip_y = self._last_hip_y

        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            lm = results.pose_landmarks[0]
            left_hip = lm[23]
            right_hip = lm[24]

            person_visible = True
            hip_y = (left_hip.y + right_hip.y) / 2
            self.process(hip_y)

            if self.state == self.CALIBRATING:
                label = f"校准中... ({len(self._calibration)}/{self._calibration_need})"
            elif self.is_complete():
                label = f"太棒了！ {self.count}/{self.target}"
            elif self.state == self.DOWN:
                label = f"站起来！ ({self.count}/{self.target})"
            else:
                label = f"蹲下去！ ({self.count}/{self.target})"

            for idx in [23, 24]:
                px = int(lm[idx].x * w)
                py = int(lm[idx].y * h)
                cv2.circle(frame, (px, py), 10, (0, 255, 0), -1)

        return frame, self.count, label, person_visible, hip_y

    def release(self):
        if self._pose is not None:
            self._pose.close()
            self._pose = None
