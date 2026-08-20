"""
vision/push_up.py

Continuous push-up FORM CHECKER + rep counter using YOLOv8-pose.

Design:
    - ONE pose inference per frame.
    - User must first enter a valid horizontal push-up
      starting position for several consecutive frames.
    - Rep counting is a clean UP/DOWN state machine.
    - A rep is counted ONCE, on the way back up.
    - A rep is either correct OR incorrect, never both.
    - Form is only flagged "bad" if it stays bad for
      several consecutive frames.
    - Low-confidence keypoints are ignored.
    - Existing camera drawings and red/green feedback
      remain active during the real session.
"""

import time
import math

import numpy as np
import cv2
from ultralytics import YOLO

from tts.speaker import speak

from vision.drawing import (
    draw_keypoints,
    draw_connections,
    feedbackText,
    repcount,
)


# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

POSE_MODEL_PATH = "yolov8n-pose.pt"
CAMERA_INDEX = 0

KP_CONF_MIN = 0.35

# Form feedback
BAD_FRAMES_TO_FLAG = 3
FEEDBACK_COOLDOWN = 2.0

# Standing-up frames before automatically ending
UP_FRAMES_TO_END = 15

# Push-up depth thresholds
TOP_ANGLE = 155
BOTTOM_ANGLE = 120

# ----------------------------------------------------------------------
# START-POSITION THRESHOLDS
# ----------------------------------------------------------------------

# Body must be reasonably straight.
MIN_BODY_ANGLE = 135.0

# Arms must be reasonably extended.
MIN_ELBOW_ANGLE = 135.0

# Body orientation:
# 0°  = horizontal
# 90° = vertical
MAX_HORIZONTAL_ANGLE = 30.0

# User must remain in the starting position
# for this many consecutive frames.
START_POSITION_FRAMES = 5


model = YOLO(POSE_MODEL_PATH)


CONNECTIONS = [
    (5, 7), (7, 9),          # left arm
    (6, 8), (8, 10),         # right arm
    (5, 6),                  # shoulders
    (5, 11), (6, 12),        # torso
    (11, 13), (13, 15),      # left leg
    (12, 14), (14, 16),      # right leg
]


# ======================================================================
# GEOMETRY HELPERS
# ======================================================================

def estimate_angle(a, b, c):
    """
    Angle in degrees at point b, formed by the segments b->a
    and b->c.

    Each of a, b, c is an (x, y) pair.
    Returns an angle from 0 to 180 degrees.
    """

    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)

    radians = (
        np.arctan2(
            c[1] - b[1],
            c[0] - b[0],
        )
        -
        np.arctan2(
            a[1] - b[1],
            a[0] - b[0],
        )
    )

    angle = abs(
        radians * 180.0 / np.pi
    )

    if angle > 180.0:
        angle = 360.0 - angle

    return angle


def angle_3pts(a, b, c):
    """
    Calculate the angle ABC formed by three 2D points.

    a = first point
    b = vertex / middle point
    c = third point

    Returns:
        Angle in degrees from 0 to 180.
    """

    ba = (
        a[0] - b[0],
        a[1] - b[1],
    )

    bc = (
        c[0] - b[0],
        c[1] - b[1],
    )

    dot_product = (
        ba[0] * bc[0]
        + ba[1] * bc[1]
    )

    magnitude_ba = math.sqrt(
        ba[0] ** 2
        + ba[1] ** 2
    )

    magnitude_bc = math.sqrt(
        bc[0] ** 2
        + bc[1] ** 2
    )

    if magnitude_ba == 0 or magnitude_bc == 0:
        return None

    cosine = (
        dot_product
        / (magnitude_ba * magnitude_bc)
    )

    cosine = max(
        -1.0,
        min(1.0, cosine),
    )

    return math.degrees(
        math.acos(cosine)
    )


def kp_ok(kp, idx):
    """
    True if keypoint idx is confident enough to trust.
    """

    return kp[idx][2] >= KP_CONF_MIN


def xy(kp, idx):
    """
    Return just the (x, y) of a keypoint.
    """

    return kp[idx][:2]


# ======================================================================
# ELBOW ANGLE + DEPTH
# ======================================================================

def get_elbow_angle(kp):
    """
    Average elbow angle across both arms
    (whichever are confident).

    Big angle (~180) = arms straight.
    Small angle (~90) = arms bent.

    Returns None if the arms cannot be trusted.
    """

    angles = []

    # Right arm
    if (
        kp_ok(kp, 6)
        and kp_ok(kp, 8)
        and kp_ok(kp, 10)
    ):
        angles.append(
            estimate_angle(
                xy(kp, 6),
                xy(kp, 8),
                xy(kp, 10),
            )
        )

    # Left arm
    if (
        kp_ok(kp, 5)
        and kp_ok(kp, 7)
        and kp_ok(kp, 9)
    ):
        angles.append(
            estimate_angle(
                xy(kp, 5),
                xy(kp, 7),
                xy(kp, 9),
            )
        )

    if not angles:
        return None

    return sum(angles) / len(angles)


def angle_to_percent(angle):
    """
    Map elbow angle -> 0..100 "extended" percent.

    BOTTOM_ANGLE -> 0
    TOP_ANGLE    -> 100
    """

    pct = np.interp(
        angle,
        (BOTTOM_ANGLE, TOP_ANGLE),
        (0.0, 100.0),
    )

    return float(pct)


# ======================================================================
# BODY ALIGNMENT / STARTING POSITION
# ======================================================================

def check_body_alignment(kp):
    """
    Check whether the user's body is sufficiently straight
    AND horizontally oriented for a push-up.

    Returns:
        body_ok:
            True only when the body is both straight
            and sufficiently horizontal.

        body_angle:
            Shoulder-hip-ankle angle.

        horizontal_angle:
            Deviation of the shoulder->hip line
            from horizontal.

            ~0°  = horizontal
            ~90° = vertical
    """

    # -----------------------------------------------------
    # Required keypoints
    # -----------------------------------------------------

    if not (
        kp_ok(kp, 5) and
        kp_ok(kp, 11) and
        kp_ok(kp, 15)
    ):
        return (
            False,
            None,
            None,
        )

    shoulder = xy(kp, 5)
    hip = xy(kp, 11)
    ankle = xy(kp, 15)

    # -----------------------------------------------------
    # 1. BODY STRAIGHTNESS
    #
    # shoulder ---- hip ---- ankle
    #
    # ~180° = straight
    # -----------------------------------------------------

    body_angle = angle_3pts(
        shoulder,
        hip,
        ankle,
    )

    if body_angle is None:
        return (
            False,
            None,
            None,
        )

    body_straight = (
        body_angle >= MIN_BODY_ANGLE
    )

    # -----------------------------------------------------
    # 2. BODY ORIENTATION
    #
    # Shoulder -> hip line
    #
    # 0°  = horizontal
    # 90° = vertical
    # -----------------------------------------------------

    dx = hip[0] - shoulder[0]
    dy = hip[1] - shoulder[1]

    orientation_angle = abs(
        math.degrees(
            math.atan2(dy, dx)
        )
    )

    horizontal_angle = min(
        orientation_angle,
        180.0 - orientation_angle,
    )

    body_horizontal = (
        horizontal_angle <= MAX_HORIZONTAL_ANGLE
    )

    # -----------------------------------------------------
    # FINAL BODY CONDITION
    # -----------------------------------------------------

    body_ok = (
        body_straight
        and body_horizontal
    )

    return (
        body_ok,
        body_angle,
        horizontal_angle,
    )


# ======================================================================
# FORM CHECKS
# ======================================================================

def wrists_wider_than_shoulders(kp):
    """
    Hands should be at least approximately shoulder-width.

    Returns:
        True / False / None
    """

    if not (
        kp_ok(kp, 5)
        and kp_ok(kp, 6)
        and kp_ok(kp, 9)
        and kp_ok(kp, 10)
    ):
        return None

    shoulders_w = np.linalg.norm(
        np.array(xy(kp, 6))
        -
        np.array(xy(kp, 5))
    )

    wrists_w = np.linalg.norm(
        np.array(xy(kp, 10))
        -
        np.array(xy(kp, 9))
    )

    return (
        wrists_w >= shoulders_w * 0.9
    )


def evaluate_form(kp):
    """
    Look at the current frame and return:

        form_good:
            True if the visible form checks pass.

        messages:
            Feedback messages for problems.

    The starting-position gate has already been passed
    before this function is used.
    """

    messages = []
    form_good = True

    # check_body_alignment now returns
    # (body_ok, body_angle, horizontal_angle)
    body_good, _, _ = check_body_alignment(kp)

    if body_good is False:
        messages.append(
            "Keep your body straight!"
        )
        form_good = False

    wrists_good = wrists_wider_than_shoulders(kp)

    if wrists_good is False:
        messages.append(
            "Place your hands about shoulder width!"
        )
        form_good = False

    return (
        form_good,
        messages,
    )


# ======================================================================
# REP COUNTER
# ======================================================================

class RepCounter:
    """
    Counts a rep ONCE per full down-up cycle.

    A rep is correct UNLESS form was bad
    during the down portion.
    """

    def __init__(self):

        self.stage = "up"

        self.correct = 0
        self.incorrect = 0

        self.rep_had_error = False

    def update(
        self,
        percent,
        frame_form_bad,
    ):
        """
        percent:
            0 = bottom
            100 = top

        frame_form_bad:
            True when persistent form error exists.

        Returns:
            (correct, incorrect)
        """

        # -------------------------------------------------
        # GOING DOWN
        # -------------------------------------------------

        if (
            self.stage == "up"
            and percent <= 30
        ):
            self.stage = "down"
            self.rep_had_error = False

        # -------------------------------------------------
        # WHILE DOWN
        # -------------------------------------------------

        if (
            self.stage == "down"
            and frame_form_bad
        ):
            self.rep_had_error = True

        # -------------------------------------------------
        # COMING BACK UP
        # -------------------------------------------------

        if (
            self.stage == "down"
            and percent >= 75
        ):

            self.stage = "up"

            if self.rep_had_error:
                self.incorrect += 1
            else:
                self.correct += 1

        return (
            self.correct,
            self.incorrect,
        )


# ======================================================================
# STANDING-UP DETECTION
# ======================================================================

def is_user_standing(kp):
    """
    True if the body is vertical.

    Uses shoulder and ankle centres.

    Returns:
        standing_bool,
        torso_angle_from_horizontal
    """

    if not (
        kp_ok(kp, 5)
        and kp_ok(kp, 6)
        and kp_ok(kp, 15)
        and kp_ok(kp, 16)
    ):
        return False, None

    shoulder_c = np.mean(
        [
            xy(kp, 5),
            xy(kp, 6),
        ],
        axis=0,
    )

    ankle_c = np.mean(
        [
            xy(kp, 15),
            xy(kp, 16),
        ],
        axis=0,
    )

    dx = ankle_c[0] - shoulder_c[0]
    dy = ankle_c[1] - shoulder_c[1]

    angle = abs(
        np.degrees(
            np.arctan2(dy, dx)
        )
    )

    if angle > 90:
        angle = 180 - angle

    return (
        angle > 60,
        angle,
    )


# ======================================================================
# MAIN PUSH-UP SESSION
# ======================================================================

def run_pushup_session(target_reps=None):

    cam = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cam.isOpened():
        raise RuntimeError(
            "Could not open webcam."
        )

    counter = RepCounter()

    bad_frame_streak = 0

    last_spoken = None
    last_spoken_time = 0.0

    up_streak = 0

    # -----------------------------------------------------
    # Session has NOT started yet.
    # This becomes True only after the user is confirmed
    # in the horizontal push-up starting position.
    # -----------------------------------------------------

    started = False

    # Number of consecutive valid start-position frames.
    position_streak = 0

    previous_total = 0

    feedback_summary = set()

    while True:

        # =================================================
        # 1. FRAME
        # =================================================

        ret, frame = cam.read()

        if not ret:

            print(
                "Could not read frame."
            )

            break

        # =================================================
        # 2. POSE
        # =================================================

        results = model(
            frame,
            verbose=False,
        )

        result = results[0]

        # =================================================
        # 3. NO PERSON
        # =================================================

        if (
            result.keypoints is None
            or len(result.keypoints) == 0
        ):

            # If session hasn't started,
            # keep the start streak at zero.
            if not started:
                position_streak = 0

            cv2.imshow(
                "Push Up Trainer",
                frame,
            )

            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):
                break

            continue

        kp = (
            result.keypoints
            .data
            .cpu()
            .numpy()[0]
        )

        # =================================================
        # 4. START-POSITION GATE
        # =================================================

        if not started:

            body_good, body_angle, horizontal_angle = (
                check_body_alignment(kp)
            )

            elbow_angle = get_elbow_angle(kp)

            in_position = (
                body_good
                and elbow_angle is not None
                and elbow_angle >= MIN_ELBOW_ANGLE
            )
            # -----------------------------------------------------
# POSITION STATUS — RED / GREEN
# -----------------------------------------------------

            if in_position:
                position_status = "PUSH-UP POSITION: YES"
                position_color = (0, 255, 0)      # GREEN
            else:
                position_status = "PUSH-UP POSITION: NO"
                position_color = (0, 0, 255)      # RED

            cv2.putText(
                frame,
                position_status,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                position_color,
                2,
                )

            # ---------------------------------------------
            # Consecutive valid frames
            # ---------------------------------------------

            if in_position:

                position_streak += 1

            else:

                position_streak = 0

            # ---------------------------------------------
            # Confirm starting position
            # ---------------------------------------------

            if (
                position_streak
                >= START_POSITION_FRAMES
            ):

                started = True

                print(
                    "\n>>> PUSH-UP POSITION "
                    "CONFIRMED."
                )

                print(
                    ">>> Starting rep counter."
                )

            # ---------------------------------------------
            # Still getting ready
            #
            # IMPORTANT:
            # Do NOT:
            #   - count reps
            #   - evaluate form
            #   - speak form feedback
            #
            # But KEEP the drawings.
            # ---------------------------------------------

            frame = draw_keypoints(
                frame,
                kp,
            )

            frame = draw_connections(
                CONNECTIONS,
                frame,
                kp,
            )
            if started:
                position_status = "PUSH-UP POSITION: YES"
                position_color = (0, 255, 0)       # GREEN
            else:
                position_status = "PUSH-UP POSITION: NO"
                position_color = (0, 0, 255)       # RED

            cv2.putText(
            frame,
            position_status,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            position_color,
            2,
            )

            # Helpful setup feedback.
            frame = feedbackText(
                frame,
                (
                    f"Get ready: "
                    f"{position_streak}/"
                    f"{START_POSITION_FRAMES}"
                ),
            )

            # Show the detected angles as well.
            if body_angle is not None:

                frame = feedbackText(
                    frame,
                    (
                        f"Body: "
                        f"{body_angle:.0f}"
                    ),
                )

            if horizontal_angle is not None:

                frame = feedbackText(
                    frame,
                    (
                        f"Horiz: "
                        f"{horizontal_angle:.0f}"
                    ),
                )

            if elbow_angle is not None:

                frame = feedbackText(
                    frame,
                    (
                        f"Elbow: "
                        f"{elbow_angle:.0f}"
                    ),
                )

            cv2.imshow(
                "Push Up Trainer",
                frame,
            )

            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):
                break

            # If the position has JUST become confirmed,
            # continue to the next frame so the actual
            # counting pipeline starts cleanly.
            if not started:
                continue

        # =================================================
        # 5. ELBOW ANGLE / DEPTH
        #
        # The session has now started.
        # =================================================

        elbow_angle = get_elbow_angle(kp)

        if elbow_angle is None:

            # Keep the existing drawings.
            frame = draw_keypoints(
                frame,
                kp,
            )

            frame = draw_connections(
                CONNECTIONS,
                frame,
                kp,
            )

            cv2.imshow(
                "Push Up Trainer",
                frame,
            )

            if (
                cv2.waitKey(1) & 0xFF
                == ord("q")
            ):
                break

            continue

        percent = angle_to_percent(
            elbow_angle
        )

        # =================================================
        # 6. FORM
        # =================================================

        frame_form_good, messages = (
            evaluate_form(kp)
        )

        # =================================================
        # 7. FORM DEBOUNCE
        # =================================================

        if not frame_form_good:

            bad_frame_streak += 1

        else:

            bad_frame_streak = 0

        form_bad_persistent = (
            bad_frame_streak
            >= BAD_FRAMES_TO_FLAG
        )

        # =================================================
        # 8. REP COUNT
        # =================================================

        correct, incorrect = counter.update(
            percent,
            form_bad_persistent,
        )

        total = (
            correct
            + incorrect
        )

        if total > 0:
            started = True

        # =================================================
        # 9. SPEAK FEEDBACK
        # =================================================

        now = time.time()

        if (
            form_bad_persistent
            and messages
        ):

            msg = messages[0]

            feedback_summary.add(
                msg
            )

            if (
                msg != last_spoken
                or (
                    now
                    - last_spoken_time
                    >= FEEDBACK_COOLDOWN
                )
            ):

                speak(msg)

                last_spoken = msg
                last_spoken_time = now

        elif frame_form_good:

            last_spoken = None

        # =================================================
        # 10. TARGET REACHED
        # =================================================

        if (
            target_reps is not None
            and total >= target_reps
            and previous_total < target_reps
        ):

            speak(
                f"You reached your target "
                f"of {target_reps} reps."
            )

        previous_total = total

        # =================================================
        # 11. AUTO-END WHEN USER STANDS
        # =================================================

        standing, _ = (
            is_user_standing(kp)
        )

        if started and standing:

            up_streak += 1

        else:

            up_streak = 0

        if (
            up_streak
            >= UP_FRAMES_TO_END
        ):

            speak(
                "Great work! Ending "
                "push-up session."
            )

            break

        # =================================================
        # 12. DRAW
        #
        # KEEPING YOUR EXISTING VISUAL FEEDBACK
        # =================================================

        frame = draw_keypoints(
            frame,
            kp,
        )

        frame = draw_connections(
            CONNECTIONS,
            frame,
            kp,
        )

        # Existing angle/depth feedback
        frame = feedbackText(
            frame,
            (
                f"Angle: "
                f"{elbow_angle:.0f}  "
                f"Depth: "
                f"{percent:.0f}%"
            ),
        )

        # Existing form feedback
        if (
            form_bad_persistent
            and messages
        ):

            frame = feedbackText(
                frame,
                messages[0],
            )

        # Existing rep count / red-green display
        frame = repcount(
            frame,
            correct,
        )

        # =================================================
        # 13. DEBUG
        # =================================================

        print(
            f"elbow={elbow_angle:5.1f} "
            f"depth={percent:5.1f}% "
            f"stage={counter.stage:4s} "
            f"form_bad={form_bad_persistent} "
            f"correct={correct} "
            f"incorrect={incorrect}"
        )

        # =================================================
        # 14. SHOW / EXIT
        # =================================================

        cv2.imshow(
            "Push Up Trainer",
            frame,
        )

        if (
            cv2.waitKey(1) & 0xFF
            == ord("q")
        ):
            break

    # =====================================================
    # CLEANUP
    # =====================================================

    cam.release()
    cv2.destroyAllWindows()

    return {
        "correct_reps": counter.correct,
        "incorrect_reps": counter.incorrect,
        "total_reps": (
            counter.correct
            + counter.incorrect
        ),
        "feedback": list(
            feedback_summary
        ),
    }


# ======================================================================
# DIRECT TEST
# ======================================================================

if __name__ == "__main__":

    print(
        run_pushup_session()
    )