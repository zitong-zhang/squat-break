"""Squat Break - 久坐蹲起提醒工具 - 蹲起检测模块"""


class SquatDetector:
    """State machine for counting squats based on hip/knee Y coordinates.

    Coordinates are normalized (0-1, Y increases downward).
    A squat is: STANDING -> DOWN (held >= min_hold_frames) -> STANDING.
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
        self._stand_threshold = 0.12
        self._squat_threshold = 0.07
        self._pose = None

    def process(self, hip_y, knee_y):
        """Update state from hip and knee Y coordinates."""
        distance = knee_y - hip_y

        if self.state == self.STANDING:
            if distance < self._squat_threshold:
                self._hold_frames += 1
                if self._hold_frames >= self.min_hold_frames:
                    self.state = self.DOWN
                    self._was_valid_down = True
            else:
                self._hold_frames = 0

        elif self.state == self.DOWN:
            if distance > self._stand_threshold:
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
            import mediapipe as mp

            self._pose = mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        return self._pose

    def process_frame(self, frame):
        """Process a BGR OpenCV frame.

        Returns (frame, count, label, person_visible).
        """
        import cv2

        pose = self._get_pose()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        h, w = frame.shape[:2]
        label = "请站到摄像头前"
        person_visible = False

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            left_hip = lm[23]
            right_hip = lm[24]
            left_knee = lm[25]
            right_knee = lm[26]

            if (
                left_hip.visibility > 0.5
                and right_hip.visibility > 0.5
                and left_knee.visibility > 0.5
                and right_knee.visibility > 0.5
            ):
                person_visible = True
                hip_y = (left_hip.y + right_hip.y) / 2
                knee_y = (left_knee.y + right_knee.y) / 2
                self.process(hip_y, knee_y)

                if self.is_complete():
                    label = f"太棒了！ {self.count}/{self.target}"
                elif self.state == self.DOWN:
                    label = f"站起来！ ({self.count}/{self.target})"
                else:
                    label = f"蹲下去！ ({self.count}/{self.target})"

            for idx in [23, 24, 25, 26]:
                px = int(lm[idx].x * w)
                py = int(lm[idx].y * h)
                cv2.circle(frame, (px, py), 8, (0, 255, 0), -1)

        return frame, self.count, label, person_visible

    def release(self):
        if self._pose is not None:
            self._pose.close()
            self._pose = None
