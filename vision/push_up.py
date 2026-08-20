"""
vision/push_up.py

Continuous push-up FORM CHECKER + rep counter using YOLOv8-pose.

MERGED VERSION:
    - Rep-counting logic is UNCHANGED (the working state machine).
    - Hip-form detection (from the hip test file) is added as the
      form signal: if hips sag (too low) or pike (too high) during
      the down portion, the rep still counts, but as INCORRECT.
    - Good hips + full depth = correct rep.
    - Everything else (start gate, standing auto-end, drawings) preserved.
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
BAD_FRAMES_TO_FLAG = 1
FEEDBACK_COOLDOWN = 2.0

# Standing-up frames before automatically ending
UP_FRAMES_TO_END = 15

# Push-up depth thresholds
TOP_ANGLE = 155
BOTTOM_ANGLE = 120

# ----------------------------------------------------------------------
# START-POSITION THRESHOLDS
# ----------------------------------------------------------------------

MIN_BODY_ANGLE = 135.0
MIN_ELBOW_ANGLE = 135.0
MAX_HORIZONTAL_ANGLE = 30.0
START_POSITION_FRAMES = 5

# ----------------------------------------------------------------------
# HIP-FORM THRESHOLDS  (from the hip test file, calibrated)
# ----------------------------------------------------------------------

HIP_LOW_THRESHOLD = 0.085     # avg hip ratio above this  -> hips sagging (too low)
HIP_HIGH_THRESHOLD = -0.09   # avg hip ratio below this  -> hips piking (too high)
HIP_HORIZONTAL_LIMIT = 30.0  # only judge hips when body is horizontal enough


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
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    radians = (
        np.arctan2(c[1] - b[1], c[0] - b[0])
        - np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle = abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle


def angle_3pts(a, b, c):
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mbc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    if mba == 0 or mbc == 0:
        return None
    cosine = max(-1.0, min(1.0, dot / (mba * mbc)))
    return math.degrees(math.acos(cosine))


def kp_ok(kp, idx):
    return kp[idx][2] >= KP_CONF_MIN


def xy(kp, idx):
    return kp[idx][:2]


# ======================================================================
# ELBOW ANGLE + DEPTH   (unchanged - drives rep counting)
# ======================================================================

def get_elbow_angle(kp):
    angles = []
    if kp_ok(kp, 6) and kp_ok(kp, 8) and kp_ok(kp, 10):
        angles.append(estimate_angle(xy(kp, 6), xy(kp, 8), xy(kp, 10)))
    if kp_ok(kp, 5) and kp_ok(kp, 7) and kp_ok(kp, 9):
        angles.append(estimate_angle(xy(kp, 5), xy(kp, 7), xy(kp, 9)))
    if not angles:
        return None
    return sum(angles) / len(angles)


def angle_to_percent(angle):
    pct = np.interp(angle, (BOTTOM_ANGLE, TOP_ANGLE), (0.0, 100.0))
    return float(pct)


# ======================================================================
# BODY ALIGNMENT / STARTING POSITION   (unchanged - start gate)
# ======================================================================

def check_body_alignment(kp):
    if not (kp_ok(kp, 5) and kp_ok(kp, 11) and kp_ok(kp, 15)):
        return False, None, None

    shoulder = xy(kp, 5)
    hip = xy(kp, 11)
    ankle = xy(kp, 15)

    body_angle = angle_3pts(shoulder, hip, ankle)
    if body_angle is None:
        return False, None, None
    body_straight = body_angle >= MIN_BODY_ANGLE

    dx = hip[0] - shoulder[0]
    dy = hip[1] - shoulder[1]
    orientation_angle = abs(math.degrees(math.atan2(dy, dx)))
    horizontal_angle = min(orientation_angle, 180.0 - orientation_angle)
    body_horizontal = horizontal_angle <= MAX_HORIZONTAL_ANGLE

    body_ok = body_straight and body_horizontal
    return body_ok, body_angle, horizontal_angle


# ======================================================================
# HIP-FORM ANALYSIS   (ported from the working hip test file)
# ======================================================================

def _hip_horizontal_angle(shoulder, ankle):
    dx = ankle[0] - shoulder[0]
    dy = ankle[1] - shoulder[1]
    raw = abs(math.degrees(math.atan2(dy, dx)))
    return min(raw, 180.0 - raw)


def _analyze_side(kp, shoulder_idx, hip_idx, ankle_idx):
    """
    For one side, compute the signed hip ratio (how far the hip sits
    off the shoulder->ankle line) and the horizontal angle.
    Returns None if that side isn't confidently visible.
    """
    if not (kp_ok(kp, shoulder_idx) and kp_ok(kp, hip_idx) and kp_ok(kp, ankle_idx)):
        return None

    shoulder = np.array(xy(kp, shoulder_idx), dtype=float)
    hip = np.array(xy(kp, hip_idx), dtype=float)
    ankle = np.array(xy(kp, ankle_idx), dtype=float)

    line = ankle - shoulder
    body_length = np.linalg.norm(line)
    if body_length == 0:
        return None

    # signed perpendicular distance of hip from the shoulder-ankle line
    cross = (
        line[0] * (hip[1] - shoulder[1])
        - line[1] * (hip[0] - shoulder[0])
    )
    signed_distance = cross / body_length
    signed_ratio = signed_distance / body_length

    horizontal = _hip_horizontal_angle(shoulder, ankle)

    return {"ratio": signed_ratio, "horizontal": horizontal}


def classify_hips(kp):
    """
    Returns one of:
        "GOOD"          hips aligned
        "HIPS_LOW"      sagging
        "HIPS_HIGH"     piking
        "UNCERTAIN"     can't judge (not visible / not horizontal enough)
    Uses BOTH sides averaged, exactly like the working hip demo.
    """
    left = _analyze_side(kp, 5, 11, 15)
    right = _analyze_side(kp, 6, 12, 16)

    if left is None or right is None:
        return "UNCERTAIN"

    avg_horizontal = (left["horizontal"] + right["horizontal"]) / 2.0
    if avg_horizontal > HIP_HORIZONTAL_LIMIT:
        return "UNCERTAIN"   # not in a horizontal push-up right now

    avg_ratio = (left["ratio"] + right["ratio"]) / 2.0

    if avg_ratio > HIP_LOW_THRESHOLD:
        return "HIPS_LOW"
    if avg_ratio < HIP_HIGH_THRESHOLD:
        return "HIPS_HIGH"
    return "GOOD"


# ======================================================================
# FORM CHECKS   (now driven by hip form)
# ======================================================================

def wrists_wider_than_shoulders(kp):
    if not (kp_ok(kp, 5) and kp_ok(kp, 6) and kp_ok(kp, 9) and kp_ok(kp, 10)):
        return None
    shoulders_w = np.linalg.norm(np.array(xy(kp, 6)) - np.array(xy(kp, 5)))
    wrists_w = np.linalg.norm(np.array(xy(kp, 10)) - np.array(xy(kp, 9)))
    return wrists_w >= shoulders_w * 0.9


def evaluate_form(kp):
    """
    Returns (form_good, messages).
    Form is BAD if hips sag or pike, or hands too narrow.
    HIP form is the primary check (this is what the requirement is about).
    """
    messages = []
    form_good = True

    # --- HIP FORM (primary) ---
    hips = classify_hips(kp)
    if hips == "HIPS_LOW":
        messages.append("Don't let your hips sag - engage your core!")
        form_good = False
    elif hips == "HIPS_HIGH":
        messages.append("Lower your hips - don't pike!")
        form_good = False
    # "GOOD" or "UNCERTAIN" -> no hip complaint

    # --- WRISTS (secondary) ---
    wrists_good = wrists_wider_than_shoulders(kp)
    if wrists_good is False:
        messages.append("Place your hands about shoulder width!")
        form_good = False

    return form_good, messages


# ======================================================================
# REP COUNTER   (UNCHANGED - exactly the working logic)
# ======================================================================

class RepCounter:
    def __init__(self):
        self.stage = "up"
        self.correct = 0
        self.incorrect = 0
        self.rep_had_error = False

    def update(self, percent, frame_form_bad):
        # GOING DOWN
        if self.stage == "up" and percent <= 30:
            self.stage = "down"
            self.rep_had_error = False
        # WHILE DOWN - record any form error
        if self.stage == "down" and frame_form_bad:
            self.rep_had_error = True
        # COMING BACK UP - count once
        if self.stage == "down" and percent >= 75:
            self.stage = "up"
            if self.rep_had_error:
                self.incorrect += 1
            else:
                self.correct += 1
        return self.correct, self.incorrect


# ======================================================================
# STANDING-UP DETECTION   (unchanged)
# ======================================================================

def is_user_standing(kp):
    if not (kp_ok(kp, 5) and kp_ok(kp, 6) and kp_ok(kp, 15) and kp_ok(kp, 16)):
        return False, None
    shoulder_c = np.mean([xy(kp, 5), xy(kp, 6)], axis=0)
    ankle_c = np.mean([xy(kp, 15), xy(kp, 16)], axis=0)
    dx = ankle_c[0] - shoulder_c[0]
    dy = ankle_c[1] - shoulder_c[1]
    angle = abs(np.degrees(np.arctan2(dy, dx)))
    if angle > 90:
        angle = 180 - angle
    return angle > 60, angle


# ======================================================================
# MAIN PUSH-UP SESSION
# ======================================================================

def run_pushup_session(target_reps=None):
    cam = cv2.VideoCapture(CAMERA_INDEX)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam.")

    counter = RepCounter()
    bad_frame_streak = 0
    last_spoken = None
    last_spoken_time = 0.0
    up_streak = 0
    started = False
    position_streak = 0
    previous_total = 0
    feedback_summary = set()

    while True:
        # 1. FRAME
        ret, frame = cam.read()
        if not ret:
            print("Could not read frame.")
            break

        # 2. POSE
        results = model(frame, verbose=False)
        result = results[0]

        # 3. NO PERSON
        if result.keypoints is None or len(result.keypoints) == 0:
            if not started:
                position_streak = 0
            cv2.imshow("Push Up Trainer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        kp = result.keypoints.data.cpu().numpy()[0]

        # 4. START-POSITION GATE
        if not started:
            body_good, body_angle, horizontal_angle = check_body_alignment(kp)
            elbow_angle = get_elbow_angle(kp)

            in_position = (
                body_good
                and elbow_angle is not None
                and elbow_angle >= MIN_ELBOW_ANGLE
            )

            if in_position:
                position_streak += 1
            else:
                position_streak = 0

            if position_streak >= START_POSITION_FRAMES:
                started = True
                print("\n>>> PUSH-UP POSITION CONFIRMED. Starting rep counter.")

            frame = draw_keypoints(frame, kp)
            frame = draw_connections(CONNECTIONS, frame, kp)

            if started:
                position_status = "PUSH-UP POSITION: YES"
                position_color = (0, 255, 0)
            else:
                position_status = "PUSH-UP POSITION: NO"
                position_color = (0, 0, 255)
            cv2.putText(frame, position_status, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, position_color, 2)

            frame = feedbackText(frame,
                                 f"Get ready: {position_streak}/{START_POSITION_FRAMES}")
            if body_angle is not None:
                frame = feedbackText(frame, f"Body: {body_angle:.0f}")
            if elbow_angle is not None:
                frame = feedbackText(frame, f"Elbow: {elbow_angle:.0f}")

            cv2.imshow("Push Up Trainer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            if not started:
                continue

        # 5. ELBOW ANGLE / DEPTH
        elbow_angle = get_elbow_angle(kp)
        if elbow_angle is None:
            frame = draw_keypoints(frame, kp)
            frame = draw_connections(CONNECTIONS, frame, kp)
            cv2.imshow("Push Up Trainer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        percent = angle_to_percent(elbow_angle)

        # 6. FORM  (hip form + wrists)
        frame_form_good, messages = evaluate_form(kp)

        # 7. FORM DEBOUNCE
        if not frame_form_good:
            bad_frame_streak += 1
        else:
            bad_frame_streak = 0
        form_bad_persistent = bad_frame_streak >= BAD_FRAMES_TO_FLAG

        # 8. REP COUNT  (unchanged logic; form feeds it)
        correct, incorrect = counter.update(percent, form_bad_persistent)
        total = correct + incorrect
        if total > 0:
            started = True

        # 9. SPEAK FEEDBACK
        now = time.time()
        if form_bad_persistent and messages:
            msg = messages[0]
            feedback_summary.add(msg)
            if msg != last_spoken or (now - last_spoken_time) >= FEEDBACK_COOLDOWN:
                #speak(msg)
                last_spoken = msg
                last_spoken_time = now
        elif frame_form_good:
            last_spoken = None

        # 10. TARGET REACHED
        if target_reps is not None and total >= target_reps and previous_total < target_reps:
            speak(f"You reached your target of {target_reps} reps.")
        previous_total = total

        # 11. AUTO-END WHEN USER STANDS
        standing, _ = is_user_standing(kp)
        if started and standing:
            up_streak += 1
        else:
            up_streak = 0
        if up_streak >= UP_FRAMES_TO_END:
            speak("Great work! Ending push-up session.")
            break

        # 12. DRAW
        frame = draw_keypoints(frame, kp)
        frame = draw_connections(CONNECTIONS, frame, kp)
        frame = feedbackText(frame, f"Angle: {elbow_angle:.0f}  Depth: {percent:.0f}%")
        if form_bad_persistent and messages:
            frame = feedbackText(frame, messages[0])
        frame = repcount(frame, correct)

        # --- ALWAYS-ON HIP STATUS BANNER ---
        hip_state = classify_hips(kp)
        if hip_state == "GOOD":
            banner_text = "GOOD PUSH-UP"
            banner_color = (0, 255, 0)        # green
        elif hip_state == "HIPS_LOW":
            banner_text = "HIPS TOO LOW"
            banner_color = (0, 165, 255)      # orange
        elif hip_state == "HIPS_HIGH":
            banner_text = "HIPS TOO HIGH"
            banner_color = (255, 0, 255)      # magenta
        else:  # UNCERTAIN
            banner_text = "..."
            banner_color = (0, 255, 255)      # yellow
        cv2.putText(
            frame, banner_text, (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, banner_color, 2,
        )

        # 13. DEBUG
        print(f"elbow={elbow_angle:5.1f} depth={percent:5.1f}% "
              f"stage={counter.stage:4s} hips={hip_state:9s} "
              f"form_bad={form_bad_persistent} "
              f"correct={correct} incorrect={incorrect}")

        # 14. SHOW / EXIT
        cv2.imshow("Push Up Trainer", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()
    return {
        "correct_reps": counter.correct,
        "incorrect_reps": counter.incorrect,
        "total_reps": counter.correct + counter.incorrect,
        "feedback": list(feedback_summary),
    }


if __name__ == "__main__":
    print(run_pushup_session())