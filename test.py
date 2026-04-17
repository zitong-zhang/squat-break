
import mediapipe as mp
import numpy as np

# 初始化 MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# 计算角度（用于判断膝盖弯曲程度）
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle

# 深蹲计数变量
counter = 0
stage = "up"  # up / down

cap = cv2.VideoCapture(0)

with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 翻转画面 + 转RGB
        image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # 提取关节点
        try:
            landmarks = results.pose_landmarks.landmark

            # 髋、膝、踝
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            angle = calculate_angle(hip, knee, ankle)

            # 显示角度
            cv2.putText(image, f"{int(angle)}",
                        tuple(np.multiply(knee, [640,480]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

            # 深蹲逻辑
            if angle > 160:
                stage = "up"
            if angle < 90 and stage == "up":
                stage = "down"
                counter += 1

        except:
            pass

        # 显示计数
        cv2.rectangle(image, (0,0), (225,73), (0,0,0), -1)
        cv2.putText(image, f"Count: {counter}", (10,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2)
        cv2.putText(image, f"Stage: {stage}", (10,100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1)

        # 画骨骼
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        cv2.imshow('Squat Counter', image)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
