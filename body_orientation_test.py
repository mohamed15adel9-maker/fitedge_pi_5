import cv2
import numpy as np
from ultralytics import YOLO

MODEL_PATH = "yolov8n-pose.pt"
CAMERA_INDEX = 1

model = YOLO(MODEL_PATH)
cam = cv2.VideoCapture(CAMERA_INDEX)

if not cam.isOpened():
    raise RuntimeError("Could not open webcam.")


def get_body_angle(kps):
    shoulder_center = np.mean(
        [kps[5][:2], kps[6][:2]],
        axis=0
    )

    ankle_center = np.mean(
        [kps[15][:2], kps[16][:2]],
        axis=0
    )

    dx = ankle_center[0] - shoulder_center[0]
    dy = ankle_center[1] - shoulder_center[1]

    angle = abs(np.degrees(np.arctan2(dy, dx)))

    if angle > 90:
        angle = 180 - angle

    return angle


while True:
    ret, frame = cam.read()

    if not ret:
        break

    results = model(frame, verbose=False)
    result = results[0]

    if result.keypoints is not None and len(result.keypoints) > 0:
        kp = result.keypoints.data.cpu().numpy()[0]

        angle = get_body_angle(kp)

        print(f"Body angle: {angle:.1f}°")

        cv2.putText(
            frame,
            f"Body angle: {angle:.1f} deg",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

    cv2.imshow("Body Orientation Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cam.release()
cv2.destroyAllWindows()