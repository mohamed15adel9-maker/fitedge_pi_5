import cv2
import math
import numpy as np

from vision.push_up import (
    model,
    CAMERA_INDEX,
    KP_CONF_MIN,
)


# =========================================================
# CALIBRATED THRESHOLDS
# =========================================================

HIP_LOW_THRESHOLD = 0.10
HIP_HIGH_THRESHOLD = -0.08


HORIZONTAL_LIMIT = 30.0


# =========================================================
# STABILITY
# =========================================================

# Reduced from 3 to 2 so the detector reacts faster.
CONFIRM_FRAMES = 1


# =========================================================
# HELPERS
# =========================================================

def kp_ok(kp, idx):
    return kp[idx][2] >= KP_CONF_MIN


def xy(kp, idx):
    return kp[idx][:2]


def horizontal_angle(shoulder, ankle):

    dx = ankle[0] - shoulder[0]
    dy = ankle[1] - shoulder[1]

    raw = abs(
        math.degrees(
            math.atan2(dy, dx)
        )
    )

    return min(
        raw,
        180.0 - raw,
    )


def analyze_side(
    kp,
    shoulder_idx,
    hip_idx,
    ankle_idx,
):

    if not (
        kp_ok(kp, shoulder_idx)
        and kp_ok(kp, hip_idx)
        and kp_ok(kp, ankle_idx)
    ):
        return None

    shoulder = np.array(
        xy(kp, shoulder_idx),
        dtype=float,
    )

    hip = np.array(
        xy(kp, hip_idx),
        dtype=float,
    )

    ankle = np.array(
        xy(kp, ankle_idx),
        dtype=float,
    )

    line = ankle - shoulder

    body_length = np.linalg.norm(line)

    if body_length == 0:
        return None

    # Signed perpendicular distance.
    cross = (
        line[0] * (hip[1] - shoulder[1])
        -
        line[1] * (hip[0] - shoulder[0])
    )

    signed_distance = (
        cross / body_length
    )

    signed_ratio = (
        signed_distance
        / body_length
    )

    horizontal = horizontal_angle(
        shoulder,
        ankle,
    )

    return {
        "shoulder": shoulder,
        "hip": hip,
        "ankle": ankle,
        "ratio": signed_ratio,
        "horizontal": horizontal,
    }


# =========================================================
# CLASSIFICATION
# =========================================================

def classify(left, right):

    if left is None or right is None:
        return "UNCERTAIN"

    # -----------------------------------------------------
    # Must actually be horizontal.
    # -----------------------------------------------------

    avg_horizontal = (
        left["horizontal"]
        + right["horizontal"]
    ) / 2.0

    if avg_horizontal > HORIZONTAL_LIMIT:
        return "STANDING / NOT PUSH-UP"

    left_ratio = left["ratio"]
    right_ratio = right["ratio"]

    # -----------------------------------------------------
    # Use BOTH hips together.
    #
    # This reduces sensitivity to one side moving slightly
    # differently from the other.
    # -----------------------------------------------------

    avg_hip_ratio = (
        left_ratio + right_ratio
    ) / 2.0

    # -----------------------------------------------------
    # LOW
    # -----------------------------------------------------

    if avg_hip_ratio > HIP_LOW_THRESHOLD:
        return "HIPS TOO LOW"

    # -----------------------------------------------------
    # HIGH
    # -----------------------------------------------------

    if avg_hip_ratio < HIP_HIGH_THRESHOLD:
        return "HIPS TOO HIGH"

    # -----------------------------------------------------
    # GOOD
    # -----------------------------------------------------

    return "GOOD PUSH-UP"


# =========================================================
# DRAW BODY GEOMETRY
# =========================================================

def draw_side(
    frame,
    side,
    color,
):

    if side is None:
        return frame

    shoulder = tuple(
        int(v)
        for v in side["shoulder"]
    )

    hip = tuple(
        int(v)
        for v in side["hip"]
    )

    ankle = tuple(
        int(v)
        for v in side["ankle"]
    )

    # Shoulder -> ankle reference line.
    cv2.line(
        frame,
        shoulder,
        ankle,
        color,
        2,
    )

    # Shoulder.
    cv2.circle(
        frame,
        shoulder,
        5,
        color,
        -1,
    )

    # Hip.
    cv2.circle(
        frame,
        hip,
        7,
        (0, 255, 255),
        -1,
    )

    # Ankle.
    cv2.circle(
        frame,
        ankle,
        5,
        color,
        -1,
    )

    return frame


# =========================================================
# MAIN
# =========================================================

def main():

    cam = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cam.isOpened():
        print(
            "ERROR: Could not open webcam."
        )
        return

    print()
    print(
        "=============================================="
    )
    print(
        " FINAL PUSH-UP HIP FORM DEMO"
    )
    print(
        "=============================================="
    )
    print()
    print(
        "The screen will classify your position as:"
    )
    print()
    print(
        "  GOOD PUSH-UP"
    )
    print(
        "  HIPS TOO LOW"
    )
    print(
        "  HIPS TOO HIGH"
    )
    print(
        "  STANDING / NOT PUSH-UP"
    )
    print(
        "  UNCERTAIN"
    )
    print()
    print(
        "Calibrated thresholds:"
    )
    print(
        f"  Low  > +{HIP_LOW_THRESHOLD:.2f}"
    )
    print(
        f"  High < {HIP_HIGH_THRESHOLD:.2f}"
    )
    print()
    print(
        f"Stable after {CONFIRM_FRAMES} "
        f"consecutive frames."
    )
    print()
    print(
        "Test:"
    )
    print(
        "1. Stand"
    )
    print(
        "2. Good push-up + 2-3 reps"
    )
    print(
        "3. Hips LOW + 2-3 reps"
    )
    print(
        "4. Hips HIGH + 2-3 reps"
    )
    print(
        "5. Return to GOOD"
    )
    print(
        "6. Stand up"
    )
    print()
    print(
        "Press Q to quit."
    )
    print()

    # -----------------------------------------------------
    # STABLE STATE
    # -----------------------------------------------------

    stable_classification = "UNCERTAIN"

    candidate_classification = None
    candidate_count = 0

    last_raw_classification = None

    while True:

        ret, frame = cam.read()

        if not ret:
            print(
                "ERROR: Camera frame unavailable."
            )
            break

        # -------------------------------------------------
        # YOLO
        # -------------------------------------------------

        results = model(
            frame,
            verbose=False,
        )

        result = results[0]

        # -------------------------------------------------
        # NO PERSON
        # -------------------------------------------------

        if (
            result.keypoints is None
            or len(result.keypoints) == 0
        ):

            raw_classification = "UNCERTAIN"

            left = None
            right = None

        else:

            kp = (
                result.keypoints
                .data
                .cpu()
                .numpy()[0]
            )

            left = analyze_side(
                kp,
                5,
                11,
                15,
            )

            right = analyze_side(
                kp,
                6,
                12,
                16,
            )

            raw_classification = classify(
                left,
                right,
            )

        # -------------------------------------------------
        # DRAW GEOMETRY
        # -------------------------------------------------

        if left is not None:
            frame = draw_side(
                frame,
                left,
                (255, 0, 0),
            )

        if right is not None:
            frame = draw_side(
                frame,
                right,
                (0, 255, 0),
            )

        # -------------------------------------------------
        # RAW TERMINAL DEBUG
        # -------------------------------------------------

        if (
            raw_classification
            != last_raw_classification
        ):

            print(
                f"RAW -> {raw_classification}"
            )

            if left is not None:
                print(
                    f"    LEFT  ratio = "
                    f"{left['ratio']:+.4f}"
                )

            if right is not None:
                print(
                    f"    RIGHT ratio = "
                    f"{right['ratio']:+.4f}"
                )

            last_raw_classification = (
                raw_classification
            )

        # -------------------------------------------------
        # STABILITY
        #
        # UNCERTAIN does NOT immediately destroy
        # an already-established state.
        # -------------------------------------------------

        if raw_classification == "UNCERTAIN":

            candidate_classification = None
            candidate_count = 0

        else:

            if (
                raw_classification
                == stable_classification
            ):

                candidate_classification = None
                candidate_count = 0

            else:

                if (
                    raw_classification
                    == candidate_classification
                ):

                    candidate_count += 1

                else:

                    candidate_classification = (
                        raw_classification
                    )

                    candidate_count = 1

                if (
                    candidate_count
                    >= CONFIRM_FRAMES
                ):

                    stable_classification = (
                        raw_classification
                    )

                    candidate_classification = None
                    candidate_count = 0

                    print(
                        f">>> STABLE -> "
                        f"{stable_classification}"
                    )

        # -------------------------------------------------
        # STATUS COLOR
        # -------------------------------------------------

        if (
            stable_classification
            == "GOOD PUSH-UP"
        ):

            status_color = (
                0,
                255,
                0,
            )

        elif (
            stable_classification
            == "HIPS TOO LOW"
        ):

            status_color = (
                0,
                165,
                255,
            )

        elif (
            stable_classification
            == "HIPS TOO HIGH"
        ):

            status_color = (
                255,
                0,
                255,
            )

        elif (
            stable_classification
            == "STANDING / NOT PUSH-UP"
        ):

            status_color = (
                0,
                0,
                255,
            )

        else:

            status_color = (
                0,
                255,
                255,
            )

        # -------------------------------------------------
        # MAIN STATUS
        # -------------------------------------------------

        cv2.putText(
            frame,
            stable_classification,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            status_color,
            2,
        )

        # -------------------------------------------------
        # RATIOS
        # -------------------------------------------------

        if left is not None:

            cv2.putText(
                frame,
                (
                    f"Left hip: "
                    f"{left['ratio']:+.3f}"
                ),
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
            )

        if right is not None:

            cv2.putText(
                frame,
                (
                    f"Right hip: "
                    f"{right['ratio']:+.3f}"
                ),
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
            )

        # -------------------------------------------------
        # AVERAGE HIP RATIO
        # -------------------------------------------------

        if (
            left is not None
            and right is not None
        ):

            avg_hip_ratio = (
                left["ratio"]
                + right["ratio"]
            ) / 2.0

            cv2.putText(
                frame,
                (
                    f"Avg hip: "
                    f"{avg_hip_ratio:+.3f}"
                ),
                (20, 125),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
            )

            avg_horizontal = (
                left["horizontal"]
                + right["horizontal"]
            ) / 2.0

            cv2.putText(
                frame,
                (
                    f"Horizontal: "
                    f"{avg_horizontal:.1f}"
                ),
                (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1,
            )

        # -------------------------------------------------
        # STABILITY STATUS
        # -------------------------------------------------

        if candidate_classification is not None:

            cv2.putText(
                frame,
                (
                    f"Confirming: "
                    f"{candidate_classification} "
                    f"({candidate_count}/"
                    f"{CONFIRM_FRAMES})"
                ),
                (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (0, 255, 255),
                1,
            )

        else:

            cv2.putText(
                frame,
                "Stable",
                (20, 180),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (200, 200, 200),
                1,
            )

        # -------------------------------------------------
        # THRESHOLD GUIDE
        # -------------------------------------------------

        cv2.putText(
            frame,
            (
                "LOW > +0.10 | "
                "HIGH < -0.09"
            ),
            (20, 205),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1,
        )

        # -------------------------------------------------
        # SHOW
        # -------------------------------------------------

        cv2.imshow(
            "Push-Up Hip Form Demo",
            frame,
        )

        if (
            cv2.waitKey(1) & 0xFF
            == ord("q")
        ):
            break

    cam.release()
    cv2.destroyAllWindows()

    print()
    print(
        "=============================================="
    )
    print(
        " FINAL DEMO ENDED"
    )
    print(
        "==============================================")


if __name__ == "__main__":
    main()