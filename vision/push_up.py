"""
vision/pushup.py

Continuous push-up FORM CHECKER + rep counter using YOLOv8-pose.

Design (fixed):
  - ONE pose inference per frame.
  - Rep counting is a clean UP/DOWN state machine: a rep is counted ONCE,
    on the way back up, and is EITHER correct OR incorrect, never both.
  - Form is only flagged "bad" if it stays bad for several consecutive
    frames (kills single-frame keypoint noise).
  - Low-confidence keypoints are ignored so garbage positions don't create
    fake angles.

Keypoint indices (COCO, YOLOv8-pose):
  5 L-shoulder 6 R-shoulder 7 L-elbow 8 R-elbow 9 L-wrist 10 R-wrist
  11 L-hip 12 R-hip 13 L-knee 14 R-knee 15 L-ankle 16 R-ankle
Each keypoint is [x, y, confidence].
"""

import time
import numpy as np
import cv2
from ultralytics import YOLO
from tts.speaker import speak
from vision.drawing import draw_keypoints, draw_connections, feedbackText, repcount

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
POSE_MODEL_PATH = "yolov8n-pose.pt"
CAMERA_INDEX = 0
KP_CONF_MIN = 0.35            # ignore keypoints below this confidence
BAD_FRAMES_TO_FLAG = 3        # form must be bad this many frames in a row to count as bad
FEEDBACK_COOLDOWN = 2.0       # seconds between spoken feedbacks
UP_FRAMES_TO_END = 15         # standing-up frames before ending the session

# Push-up depth thresholds (elbow angle):
TOP_ANGLE = 155              # arms basically straight = top of push-up
BOTTOM_ANGLE = 120           # arms bent this far = bottom of push-up
# We convert the elbow angle into a 0-100 "percent extended" for the state machine.

# Form thresholds:
MIN_BODY_ANGLE = 150.0       # shoulder-hip-ankle; straighter = better plank line

model = YOLO(POSE_MODEL_PATH)

CONNECTIONS = [
    (5, 7), (7, 9),          # left arm
    (6, 8), (8, 10),         # right arm
    (5, 6),                  # shoulders
    (5, 11), (6, 12),        # torso sides
    (11, 13), (13, 15),      # left leg
    (12, 14), (14, 16),      # right leg
]


# ======================================================================
# GEOMETRY HELPERS
# ======================================================================
def estimate_angle(a, b, c):
    """
    Angle in degrees at point b, formed by the segments b->a and b->c.
    Each of a, b, c is an (x, y) pair. Returns 0-180.
    """
    a = np.array(a, dtype=float)
    b = np.array(b, dtype=float)
    c = np.array(c, dtype=float)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360.0 - angle
    return angle


def kp_ok(kp, idx):
    """True if keypoint idx is confident enough to trust."""
    return kp[idx][2] >= KP_CONF_MIN


def xy(kp, idx):
    """Return just the (x, y) of a keypoint."""
    return kp[idx][:2]


# ======================================================================
# ELBOW ANGLE + PHASE  (drives depth / rep detection)
# ======================================================================
def get_elbow_angle(kp):
    """
    Average elbow angle across both arms (whichever are confident).
    Big angle (~180) = arms straight (top). Small (~90) = arms bent (bottom).
    Returns None if we can't see the arms well enough.
    """
    angles = []
    # right arm: shoulder(6) elbow(8) wrist(10)
    if kp_ok(kp, 6) and kp_ok(kp, 8) and kp_ok(kp, 10):
        angles.append(estimate_angle(xy(kp, 6), xy(kp, 8), xy(kp, 10)))
    # left arm: shoulder(5) elbow(7) wrist(9)
    if kp_ok(kp, 5) and kp_ok(kp, 7) and kp_ok(kp, 9):
        angles.append(estimate_angle(xy(kp, 5), xy(kp, 7), xy(kp, 9)))

    if not angles:
        return None
    return sum(angles) / len(angles)


def angle_to_percent(angle):
    """
    Map elbow angle -> 0..100 'extended' percent.
    BOTTOM_ANGLE -> 0 (fully bent, bottom of push-up)
    TOP_ANGLE    -> 100 (straight, top of push-up)
    """
    pct = np.interp(angle, (BOTTOM_ANGLE, TOP_ANGLE), (0.0, 100.0))
    return float(pct)


# ======================================================================
# FORM CHECKS
# ======================================================================
def check_body_alignment(kp):
    """
    Straight-body (plank) check using right shoulder(6)-hip(12)-ankle(16).
    Returns (is_good, angle) or (None, None) if not visible.
    """
    if not (kp_ok(kp, 6) and kp_ok(kp, 12) and kp_ok(kp, 16)):
        return None, None
    body_angle = estimate_angle(xy(kp, 6), xy(kp, 12), xy(kp, 16))
    return body_angle >= MIN_BODY_ANGLE, body_angle


def wrists_wider_than_shoulders(kp):
    """
    Hands should be at least shoulder-width. Returns True/False, or None
    if keypoints aren't confident.
    """
    if not (kp_ok(kp, 5) and kp_ok(kp, 6) and kp_ok(kp, 9) and kp_ok(kp, 10)):
        return None
    shoulders_w = np.linalg.norm(np.array(xy(kp, 6)) - np.array(xy(kp, 5)))
    wrists_w = np.linalg.norm(np.array(xy(kp, 10)) - np.array(xy(kp, 9)))
    return wrists_w >= shoulders_w * 0.9   # small tolerance


def evaluate_form(kp):
    """
    Look at the current frame and return:
      form_good  : bool  (is this frame's form acceptable?)
      messages   : list of feedback strings for what's wrong
    Only checks that are confidently visible are applied.
    """
    messages = []
    form_good = True

    body_good, _ = check_body_alignment(kp)
    if body_good is False:              # explicitly bad (None = not visible, skip)
        messages.append("Keep your body straight!")
        form_good = False

    wrists_good = wrists_wider_than_shoulders(kp)
    if wrists_good is False:
        messages.append("Place your hands about shoulder width!")
        form_good = False

    return form_good, messages


# ======================================================================
# REP COUNTER  (clean up/down state machine)
# ======================================================================
class RepCounter:
    """
    Counts a rep ONCE per full down-up cycle.
    A rep is correct UNLESS form was bad during the 'down' portion.
    """
    def __init__(self):
        self.stage = "up"          # start at the top
        self.correct = 0
        self.incorrect = 0
        self.rep_had_error = False

    def update(self, percent, frame_form_bad):
        """
        percent        : 0 (bottom) .. 100 (top)
        frame_form_bad : True if this frame's form is (persistently) bad
        Returns (correct, incorrect).
        """
        # --- going DOWN: we pass below 15% while currently 'up' ---
        if self.stage == "up" and percent <= 30:
            self.stage = "down"
            self.rep_had_error = False        # fresh rep

        # --- while DOWN, remember if form ever broke ---
        if self.stage == "down" and frame_form_bad:
            self.rep_had_error = True

        # --- coming back UP: we pass above 85% while 'down' => rep done ---
        if self.stage == "down" and percent >= 75:
            self.stage = "up"
            if self.rep_had_error:
                self.incorrect += 1
            else:
                self.correct += 1

        return self.correct, self.incorrect


# ======================================================================
# STANDING-UP DETECTION  (to auto-end the session)
# ======================================================================
def is_user_standing(kp):
    """
    True if the body is vertical (user stood up). Uses shoulder & ankle
    centres; returns (standing_bool, torso_angle_from_horizontal).
    """
    if not (kp_ok(kp, 5) and kp_ok(kp, 6) and kp_ok(kp, 15) and kp_ok(kp, 16)):
        return False, None
    shoulder_c = np.mean([xy(kp, 5), xy(kp, 6)], axis=0)
    ankle_c = np.mean([xy(kp, 15), xy(kp, 16)], axis=0)
    dx = ankle_c[0] - shoulder_c[0]
    dy = ankle_c[1] - shoulder_c[1]
    angle = abs(np.degrees(np.arctan2(dy, dx)))
    if angle > 90:
        angle = 180 - angle
    return angle > 60, angle    # >60 from horizontal = fairly upright


# ======================================================================
# MAIN SESSION LOOP
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
    previous_total = 0
    feedback_summary = set()

    while True:
        # 1. FRAME
        ret, frame = cam.read()
        if not ret:
            print("Could not read frame.")
            break

        # 2. POSE (once)
        results = model(frame, verbose=False)
        result = results[0]

        # 3. NO PERSON -> just show frame
        if result.keypoints is None or len(result.keypoints) == 0:
            cv2.imshow("Push Up Trainer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        kp = result.keypoints.data.cpu().numpy()[0]   # (17, 3): x,y,conf

        # 4. ELBOW ANGLE / DEPTH
        elbow_angle = get_elbow_angle(kp)
        if elbow_angle is None:
            # arms not visible enough this frame; show and continue
            frame = draw_keypoints(frame, kp)
            frame = draw_connections(CONNECTIONS, frame, kp)
            cv2.imshow("Push Up Trainer", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        percent = angle_to_percent(elbow_angle)

        # 5. FORM (this frame)
        frame_form_good, messages = evaluate_form(kp)

        # 6. DEBOUNCE form: only "bad" after several consecutive bad frames
        if not frame_form_good:
            bad_frame_streak += 1
        else:
            bad_frame_streak = 0
        form_bad_persistent = bad_frame_streak >= BAD_FRAMES_TO_FLAG

        # 7. REP COUNT (state machine)
        correct, incorrect = counter.update(percent, form_bad_persistent)
        total = correct + incorrect
        if total > 0:
            started = True

        # 8. SPEAK FEEDBACK (persistent problems only, with cooldown)
        now = time.time()
        if form_bad_persistent and messages:
            msg = messages[0]
            feedback_summary.add(msg)
            if msg != last_spoken or (now - last_spoken_time) >= FEEDBACK_COOLDOWN:
                speak(msg)
                last_spoken = msg
                last_spoken_time = now
        elif frame_form_good:
            last_spoken = None

        # 9. TARGET REACHED
        if target_reps is not None and total >= target_reps and previous_total < target_reps:
            speak(f"You reached your target of {target_reps} reps.")
        previous_total = total

        # 10. AUTO-END when user stands up
        standing, _ = is_user_standing(kp)
        if started and standing:
            up_streak += 1
        else:
            up_streak = 0
        if up_streak >= UP_FRAMES_TO_END:
            speak("Great work! Ending push-up session.")
            break

        # 11. DRAW
        frame = draw_keypoints(frame, kp)
        frame = draw_connections(CONNECTIONS, frame, kp)
        frame = feedbackText(frame, f"Angle: {elbow_angle:.0f}  Depth: {percent:.0f}%")
        if form_bad_persistent and messages:
            frame = feedbackText(frame, messages[0])
        frame = repcount(frame, correct)

        # 12. DEBUG
        print(f"elbow={elbow_angle:5.1f} depth={percent:5.1f}% "
              f"stage={counter.stage:4s} form_bad={form_bad_persistent} "
              f"correct={correct} incorrect={incorrect}")

        # 13. SHOW / EXIT
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