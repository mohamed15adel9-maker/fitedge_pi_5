import cv2
from ultralytics import YOLO

from push_up import (
    give_feedback_push_up,
    get_angle,
    counts_calculate_push_up,
    get_debug_info,
    is_in_starting_position,
)

from drawing import (
    draw_keypoints,
    draw_connections,
    feedbackText,
    repcount,
)


# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "yolov8n-pose.pt"
CAMERA_INDEX = 1


# COCO pose connections
CONNECTIONS = [
    (5, 7),    # left shoulder -> left elbow
    (7, 9),    # left elbow -> left wrist

    (6, 8),    # right shoulder -> right elbow
    (8, 10),   # right elbow -> right wrist

    (5, 6),    # shoulders

    (5, 11),   # left shoulder -> left hip
    (6, 12),   # right shoulder -> right hip

    (11, 13),  # left hip -> left knee
    (13, 15),  # left knee -> left ankle

    (12, 14),  # right hip -> right knee
    (14, 16),  # right knee -> right ankle
]


# ============================================================
# INITIALIZE
# ============================================================

model = YOLO(MODEL_PATH)

cam = cv2.VideoCapture(CAMERA_INDEX)

if not cam.isOpened():
    raise RuntimeError("Could not open webcam.")


# ============================================================
# LIVE LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # 1. GET FRAME
    # --------------------------------------------------------

    ret, frame = cam.read()

    if not ret:
        print("Could not read frame.")
        break


    # --------------------------------------------------------
    # 2. YOLO POSE DETECTION
    # --------------------------------------------------------

    results = model(frame, verbose=False)

    result = results[0]

    # No pose detected
    if result.keypoints is None or len(result.keypoints) == 0:

        cv2.imshow("Push Up Trainer", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        continue


    # --------------------------------------------------------
    # 3. EXTRACT FIRST PERSON'S KEYPOINTS
    # --------------------------------------------------------

    kp = result.keypoints.data.cpu().numpy()[0]
    debug = get_debug_info(kp)

    print(
    f"angle={debug['angle']:.1f} | "
    f"phase={debug['phase']} | "
    f"start={debug['start']} | "
    f"hands={debug['hands']} | "
    f"body={debug['body']} | "
    f"elbow={debug['elbow']}"
    )


    # kp is approximately:
    #
    # kp[0]  -> nose
    # kp[5]  -> left shoulder
    # kp[6]  -> right shoulder
    # kp[7]  -> left elbow
    # kp[8]  -> right elbow
    # kp[9]  -> left wrist
    # kp[10] -> right wrist
    # ...
    #
    # Each keypoint contains:
    # [x, y, confidence]


    # --------------------------------------------------------
    # 4. FORM ANALYSIS
    # --------------------------------------------------------

    (
        feedback,
        possible_corrections,
        pointsofinterest,
        feedback_flag
    ) = give_feedback_push_up(kp)
    


    # --------------------------------------------------------
    # 5. DETERMINE WHETHER THIS FRAME IS CORRECT
    # --------------------------------------------------------

    if feedback_flag:
        correct = 0
    else:
        correct = 1


    # --------------------------------------------------------
    # 6. REP COUNTING
    # --------------------------------------------------------

    correct_count, incorrect_count = counts_calculate_push_up(
    kp,
    correct
    )


    # --------------------------------------------------------
    # 7. DRAW BODY KEYPOINTS
    # --------------------------------------------------------

    frame = draw_keypoints(
        frame,
        kp
    )


    # --------------------------------------------------------
    # 8. DRAW BODY CONNECTIONS
    # --------------------------------------------------------

    frame = draw_connections(
        CONNECTIONS,
        frame,
        kp
    )


    # --------------------------------------------------------
    # 9. DRAW CURRENT ANGLE / PHASE
    # --------------------------------------------------------

    angle, phase = get_angle(kp)


    print(
    f"angle={angle:.1f} | "
    f"phase={phase} | "
    f"start={is_in_starting_position(kp)} | "
    f"feedback_flag={feedback_flag}"
    )





    frame = feedbackText(
        frame,
        f"Angle: {angle:.1f}  Phase: {phase}"
    )


    # --------------------------------------------------------
    # 10. DRAW FEEDBACK
    # --------------------------------------------------------

    for correction in possible_corrections:

        if correction in feedback:

            frame = feedbackText(
                frame,
                feedback[correction]
            )


    # --------------------------------------------------------
    # 11. DRAW REP COUNT
    # --------------------------------------------------------

    frame = repcount(
        frame,
        correct_count
    )


    # --------------------------------------------------------
    # 12. DISPLAY
    # --------------------------------------------------------

    cv2.imshow(
        "Push Up Trainer",
        frame
    )


    # --------------------------------------------------------
    # 13. EXIT
    # --------------------------------------------------------

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ============================================================
# CLEANUP
# ============================================================

cam.release()
cv2.destroyAllWindows()