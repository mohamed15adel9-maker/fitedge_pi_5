

import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ultralytics import YOLO



CAMERA = "webcam"                 # "webcam" or "pi"
POSE_MODEL_PATH = "yolov8n-pose.pt"
CONF_THRESHOLD = 0.40

KEYPOINT_CONF_THRESHOLD = 0.35

MIN_VALID_KEYPOINTS = 8



KP = {
    "nose": 0,

    "left_eye": 1,
    "right_eye": 2,

    "left_ear": 3,
    "right_ear": 4,

    "left_shoulder": 5,
    "right_shoulder": 6,

    "left_elbow": 7,
    "right_elbow": 8,

    "left_wrist": 9,
    "right_wrist": 10,

    "left_hip": 11,
    "right_hip": 12,

    "left_knee": 13,
    "right_knee": 14,

    "left_ankle": 15,
    "right_ankle": 16,
}


# ============================================================
# MODEL
# ============================================================

_pose_model = YOLO(POSE_MODEL_PATH)


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Point:
    x: float
    y: float
    confidence: float = 1.0


@dataclass
class ExerciseResult:
    exercise: str
    confidence: float
    state: str
    details: str

    def __str__(self):
        return (
            f"Detected exercise: {self.exercise} "
            f"(confidence: {self.confidence:.0%}, state: {self.state}). "
            f"{self.details}"
        )


# ============================================================
# CAMERA
# ============================================================

def capture_photo(output_path="captured_exercise.jpg"):
    """
    Capture one frame from webcam or Raspberry Pi camera.
    """

    if CAMERA == "webcam":

        import cv2

        cam = cv2.VideoCapture(0)

        if not cam.isOpened():
            return None

        ret, frame = cam.read()

        if ret:
            cv2.imwrite(output_path, frame)

        cam.release()

        return output_path if ret else None

    elif CAMERA == "pi":

        from picamera2 import Picamera2
        import time

        picam2 = Picamera2()

        picam2.start()

        time.sleep(1)

        picam2.capture_file(output_path)

        picam2.stop()

        return output_path

    else:
        raise ValueError(f"Unknown CAMERA setting: {CAMERA}")


# ============================================================
# BASIC GEOMETRY
# ============================================================

def _distance(a: Point, b: Point) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _midpoint(a: Point, b: Point) -> Point:
    return Point(
        (a.x + b.x) / 2,
        (a.y + b.y) / 2,
        min(a.confidence, b.confidence),
    )


def _angle(a: Point, b: Point, c: Point) -> Optional[float]:
    """
    Angle ABC.

    Example:
        hip -> knee -> ankle

    gives knee angle.
    """

    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)

    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)

    if mag1 == 0 or mag2 == 0:
        return None

    cosang = (
        (v1[0] * v2[0]) +
        (v1[1] * v2[1])
    ) / (mag1 * mag2)

    cosang = max(-1.0, min(1.0, cosang))

    return math.degrees(math.acos(cosang))


def _angle_from_vertical(a: Point, b: Point) -> float:
    """
    Angle of line a->b relative to vertical.

    0°   = vertical
    90°  = horizontal
    """

    dx = b.x - a.x
    dy = b.y - a.y

    return math.degrees(math.atan2(abs(dx), abs(dy)))


def _horizontal_angle(a: Point, b: Point) -> float:
    """
    Angle of line relative to horizontal.
    """

    dx = b.x - a.x
    dy = b.y - a.y

    return math.degrees(math.atan2(abs(dy), abs(dx)))


def _vertical_distance(a: Point, b: Point) -> float:
    return abs(a.y - b.y)


# ============================================================
# KEYPOINT EXTRACTION
# ============================================================

def _get_points(keypoints_xy, keypoints_conf=None):
    """
    Convert YOLO keypoints into:

        {
            "left_shoulder": Point(...),
            ...
        }

    Confidence is preserved.
    """

    pts = {}

    for name, idx in KP.items():

        x, y = keypoints_xy[idx]

        if keypoints_conf is not None:
            confidence = float(keypoints_conf[idx])
        else:
            confidence = 1.0

        pts[name] = Point(
            float(x),
            float(y),
            confidence,
        )

    return pts


def _valid_points(pts) -> int:
    return sum(
        1
        for p in pts.values()
        if p.confidence >= KEYPOINT_CONF_THRESHOLD
    )


def _good(pts, *names) -> bool:
    """
    Check whether required keypoints are reliable.
    """

    return all(
        name in pts and
        pts[name].confidence >= KEYPOINT_CONF_THRESHOLD
        for name in names
    )


# ============================================================
# JOINT ANGLES
# ============================================================

def _joint_angles(pts) -> Dict[str, Optional[float]]:
    """
    Calculate all important joint angles.
    """

    angles = {}

    if _good(
        pts,
        "left_hip",
        "left_knee",
        "left_ankle",
    ):
        angles["left_knee"] = _angle(
            pts["left_hip"],
            pts["left_knee"],
            pts["left_ankle"],
        )

    if _good(
        pts,
        "right_hip",
        "right_knee",
        "right_ankle",
    ):
        angles["right_knee"] = _angle(
            pts["right_hip"],
            pts["right_knee"],
            pts["right_ankle"],
        )

    if _good(
        pts,
        "left_shoulder",
        "left_elbow",
        "left_wrist",
    ):
        angles["left_elbow"] = _angle(
            pts["left_shoulder"],
            pts["left_elbow"],
            pts["left_wrist"],
        )

    if _good(
        pts,
        "right_shoulder",
        "right_elbow",
        "right_wrist",
    ):
        angles["right_elbow"] = _angle(
            pts["right_shoulder"],
            pts["right_elbow"],
            pts["right_wrist"],
        )

    if _good(
        pts,
        "left_shoulder",
        "left_hip",
        "left_knee",
    ):
        angles["left_hip"] = _angle(
            pts["left_shoulder"],
            pts["left_hip"],
            pts["left_knee"],
        )

    if _good(
        pts,
        "right_shoulder",
        "right_hip",
        "right_knee",
    ):
        angles["right_hip"] = _angle(
            pts["right_shoulder"],
            pts["right_hip"],
            pts["right_knee"],
        )

    return angles


def _average(values):
    values = [
        v for v in values
        if v is not None
    ]

    if not values:
        return None

    return sum(values) / len(values)


# ============================================================
# BODY MEASUREMENTS
# ============================================================

def _body_measurements(pts):
    """
    Extract normalized geometric relationships.

    Normalizing against body size makes the rules less dependent
    on how close the person is to the camera.
    """

    measurements = {}

    if _good(
        pts,
        "left_shoulder",
        "right_shoulder",
    ):
        shoulder_width = _distance(
            pts["left_shoulder"],
            pts["right_shoulder"],
        )

        measurements["shoulder_width"] = shoulder_width

    else:
        shoulder_width = 1.0

    if _good(
        pts,
        "left_hip",
        "right_hip",
    ):
        hip_width = _distance(
            pts["left_hip"],
            pts["right_hip"],
        )

        measurements["hip_width"] = hip_width

    if _good(
        pts,
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
    ):
        shoulder_center = _midpoint(
            pts["left_shoulder"],
            pts["right_shoulder"],
        )

        hip_center = _midpoint(
            pts["left_hip"],
            pts["right_hip"],
        )

        torso_length = _distance(
            shoulder_center,
            hip_center,
        )

        measurements["torso_length"] = torso_length

    else:
        torso_length = 1.0

    if _good(
        pts,
        "left_hip",
        "left_knee",
    ):
        measurements["left_thigh"] = _distance(
            pts["left_hip"],
            pts["left_knee"],
        )

    if _good(
        pts,
        "right_hip",
        "right_knee",
    ):
        measurements["right_thigh"] = _distance(
            pts["right_hip"],
            pts["right_knee"],
        )

    # Wrist positions relative to shoulders
    if _good(
        pts,
        "left_wrist",
        "left_shoulder",
    ):
        measurements["left_wrist_shoulder_y"] = (
            pts["left_wrist"].y -
            pts["left_shoulder"].y
        )

    if _good(
        pts,
        "right_wrist",
        "right_shoulder",
    ):
        measurements["right_wrist_shoulder_y"] = (
            pts["right_wrist"].y -
            pts["right_shoulder"].y
        )

    return measurements


# ============================================================
# EXERCISE SCORING
# ============================================================

def _score_squat(pts, angles):
    """
    Squat characteristics:

        - both knees bending
        - both hips bending
        - feet below hips
        - torso generally upright
    """

    score = 0.0

    knee = _average([
        angles.get("left_knee"),
        angles.get("right_knee"),
    ])

    hip = _average([
        angles.get("left_hip"),
        angles.get("right_hip"),
    ])

    if knee is not None:

        if knee < 90:
            score += 0.45

        elif knee < 120:
            score += 0.35

        elif knee < 145:
            score += 0.20

    if hip is not None:

        if hip < 100:
            score += 0.25

        elif hip < 130:
            score += 0.15

    # Symmetry strongly supports squat.
    left = angles.get("left_knee")
    right = angles.get("right_knee")

    if left is not None and right is not None:

        difference = abs(left - right)

        if difference < 20:
            score += 0.20

        elif difference < 40:
            score += 0.10

    return min(score, 1.0)


def _score_lunge(pts, angles):
    """
    Lunge characteristics:

        - one knee significantly more bent
        - other leg more extended
        - asymmetry between left/right
    """

    left = angles.get("left_knee")
    right = angles.get("right_knee")

    if left is None or right is None:
        return 0.0

    difference = abs(left - right)

    score = 0.0

    if difference > 25:
        score += 0.35

    if difference > 45:
        score += 0.25

    if min(left, right) < 120:
        score += 0.20

    if max(left, right) > 140:
        score += 0.20

    return min(score, 1.0)


def _score_pushup(pts, angles):
    """
    Push-up characteristics:

        - body roughly horizontal
        - elbows bent or extended
        - shoulders/hips/ankles approximately aligned
    """

    if not _good(
        pts,
        "left_shoulder",
        "left_hip",
        "left_ankle",
    ):
        return 0.0

    score = 0.0

    shoulder = pts["left_shoulder"]
    hip = pts["left_hip"]
    ankle = pts["left_ankle"]

    body_angle = _horizontal_angle(
        shoulder,
        ankle,
    )

    # Near-horizontal body.
    if body_angle < 25:
        score += 0.45

    elif body_angle < 40:
        score += 0.25

    # Elbows.
    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    if elbow is not None:

        if elbow < 110:
            score += 0.30

        elif elbow < 145:
            score += 0.20

        else:
            score += 0.10

    # Hip shouldn't be dramatically lower/higher than body line.
    body_height = abs(shoulder.y - ankle.y)

    if body_height < 150:
        score += 0.15

    return min(score, 1.0)


def _score_plank(pts, angles):
    """
    Plank is similar to push-up but usually has:

        - straight arms
        - horizontal body
        - hips relatively straight
    """

    pushup_score = _score_pushup(pts, angles)

    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    if elbow is None:
        return 0.0

    score = pushup_score * 0.55

    if elbow > 145:
        score += 0.35

    return min(score, 1.0)


def _score_deadlift(pts, angles):
    """
    Deadlift / RDL characteristics:

        - hips strongly hinged
        - knees moderately bent
        - torso leans forward
        - hands near knees/shins
    """

    hip = _average([
        angles.get("left_hip"),
        angles.get("right_hip"),
    ])

    knee = _average([
        angles.get("left_knee"),
        angles.get("right_knee"),
    ])

    if hip is None or knee is None:
        return 0.0

    score = 0.0

    # Hip hinge.
    if hip < 90:
        score += 0.35

    elif hip < 120:
        score += 0.25

    elif hip < 145:
        score += 0.10

    # Moderate knee bend.
    if 120 <= knee <= 165:
        score += 0.30

    elif 100 <= knee < 120:
        score += 0.15

    # Torso forward.
    if _good(
        pts,
        "left_shoulder",
        "left_hip",
    ):

        torso_angle = _angle_from_vertical(
            pts["left_shoulder"],
            pts["left_hip"],
        )

        if torso_angle > 35:
            score += 0.30

        elif torso_angle > 20:
            score += 0.15

    return min(score, 1.0)


def _score_bicep_curl(pts, angles):
    """
    Bicep curl characteristics:

        - elbows relatively fixed
        - elbows bent
        - wrists move toward shoulders
    """

    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    if elbow is None:
        return 0.0

    score = 0.0

    if elbow < 70:
        score += 0.45

    elif elbow < 100:
        score += 0.35

    elif elbow < 130:
        score += 0.15

    if _good(
        pts,
        "left_wrist",
        "left_shoulder",
    ):

        distance = _distance(
            pts["left_wrist"],
            pts["left_shoulder"],
        )

        if distance < 1.5 * _distance(
            pts["left_shoulder"],
            pts["left_hip"],
        ):
            score += 0.15

    if _good(
        pts,
        "right_wrist",
        "right_shoulder",
    ):

        distance = _distance(
            pts["right_wrist"],
            pts["right_shoulder"],
        )

        if distance < 1.5 * _distance(
            pts["right_shoulder"],
            pts["right_hip"],
        ):
            score += 0.15

    return min(score, 1.0)


def _score_overhead_press(pts, angles):
    """
    Overhead press:

        - wrists above shoulders
        - elbows generally extended or partially bent
        - arms pointing upward
    """

    score = 0.0

    if not _good(
        pts,
        "left_wrist",
        "left_shoulder",
        "right_wrist",
        "right_shoulder",
    ):
        return 0.0

    left_up = (
        pts["left_wrist"].y <
        pts["left_shoulder"].y
    )

    right_up = (
        pts["right_wrist"].y <
        pts["right_shoulder"].y
    )

    if left_up and right_up:
        score += 0.55

    elif left_up or right_up:
        score += 0.25

    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    if elbow is not None:

        if elbow > 150:
            score += 0.30

        elif elbow > 110:
            score += 0.20

        else:
            score += 0.10

    return min(score, 1.0)


def _score_lateral_raise(pts, angles):
    """
    Lateral raise:

        - arms extended outward
        - wrists approximately at shoulder height
        - wrists significantly outside torso
    """

    if not _good(
        pts,
        "left_wrist",
        "right_wrist",
        "left_shoulder",
        "right_shoulder",
    ):
        return 0.0

    shoulder_center = _midpoint(
        pts["left_shoulder"],
        pts["right_shoulder"],
    )

    wrist_center = _midpoint(
        pts["left_wrist"],
        pts["right_wrist"],
    )

    score = 0.0

    wrist_height_difference = abs(
        wrist_center.y -
        shoulder_center.y
    )

    shoulder_width = _distance(
        pts["left_shoulder"],
        pts["right_shoulder"],
    )

    if wrist_height_difference < shoulder_width * 0.50:
        score += 0.35

    elif wrist_height_difference < shoulder_width:
        score += 0.20

    # Elbows relatively extended.
    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    if elbow is not None:

        if elbow > 145:
            score += 0.40

        elif elbow > 120:
            score += 0.25

    # Wrists should be wider than shoulders.
    wrist_width = _distance(
        pts["left_wrist"],
        pts["right_wrist"],
    )

    if wrist_width > shoulder_width * 1.3:
        score += 0.25

    return min(score, 1.0)


def _score_jumping_jack(pts, angles):
    """
    Approximate jumping-jack pose:

        - arms spread/up
        - legs spread
    """

    if not _good(
        pts,
        "left_wrist",
        "right_wrist",
        "left_ankle",
        "right_ankle",
        "left_shoulder",
        "right_shoulder",
    ):
        return 0.0

    score = 0.0

    shoulder_width = _distance(
        pts["left_shoulder"],
        pts["right_shoulder"],
    )

    ankle_width = _distance(
        pts["left_ankle"],
        pts["right_ankle"],
    )

    if ankle_width > shoulder_width * 1.5:
        score += 0.50

    if (
        pts["left_wrist"].y <
        pts["left_shoulder"].y
        and
        pts["right_wrist"].y <
        pts["right_shoulder"].y
    ):
        score += 0.50

    return min(score, 1.0)


# ============================================================
# STANDING / NEUTRAL
# ============================================================

def _score_standing(pts, angles):
    """
    Standing/neutral position.

    This is intentionally a broad fallback rather than
    automatically calling every unclear pose "standing".
    """

    knee = _average([
        angles.get("left_knee"),
        angles.get("right_knee"),
    ])

    if knee is None:
        return 0.0

    score = 0.0

    if knee > 155:
        score += 0.65

    elif knee > 140:
        score += 0.40

    if _good(
        pts,
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
    ):

        shoulder_center = _midpoint(
            pts["left_shoulder"],
            pts["right_shoulder"],
        )

        hip_center = _midpoint(
            pts["left_hip"],
            pts["right_hip"],
        )

        torso_angle = _angle_from_vertical(
            shoulder_center,
            hip_center,
        )

        if torso_angle < 20:
            score += 0.35

    return min(score, 1.0)


# ============================================================
# ALL EXERCISE SCORES
# ============================================================

def _get_exercise_scores(pts, angles):
    """
    Run every classifier.

    IMPORTANT:
    We do NOT stop at the first matching rule.

    Every exercise receives a score.
    """

    return {
        "squat": _score_squat(pts, angles),

        "lunge": _score_lunge(pts, angles),

        "push-up": _score_pushup(pts, angles),

        "plank": _score_plank(pts, angles),

        "deadlift / RDL": _score_deadlift(pts, angles),

        "bicep curl": _score_bicep_curl(pts, angles),

        "overhead press": _score_overhead_press(
            pts,
            angles,
        ),

        "lateral raise": _score_lateral_raise(
            pts,
            angles,
        ),

        "jumping jack": _score_jumping_jack(
            pts,
            angles,
        ),

        "standing / neutral": _score_standing(
            pts,
            angles,
        ),
    }


# ============================================================
# MOVEMENT / POSITION STATE
# ============================================================

def _classify_state(exercise, pts, angles):
    """
    Determine where the person is in the exercise.

    This works from one image by identifying a biomechanical
    position.

    It cannot determine actual movement direction without
    previous frames.
    """

    knee = _average([
        angles.get("left_knee"),
        angles.get("right_knee"),
    ])

    elbow = _average([
        angles.get("left_elbow"),
        angles.get("right_elbow"),
    ])

    hip = _average([
        angles.get("left_hip"),
        angles.get("right_hip"),
    ])

    if exercise == "squat":

        if knee is None:
            return "unknown position"

        if knee < 95:
            return "bottom / deep squat"

        if knee < 125:
            return "mid squat"

        if knee < 155:
            return "partial squat"

        return "top / standing"

    if exercise == "lunge":

        if knee is None:
            return "unknown position"

        if knee < 90:
            return "deep lunge"

        if knee < 125:
            return "mid lunge"

        return "shallow / transition"

    if exercise == "push-up":

        if elbow is None:
            return "unknown position"

        if elbow < 90:
            return "bottom"

        if elbow < 135:
            return "mid-range"

        return "top / arms extended"

    if exercise == "plank":
        return "hold"

    if exercise == "deadlift / RDL":

        if hip is None:
            return "unknown position"

        if hip < 90:
            return "deep hinge"

        if hip < 120:
            return "mid hinge"

        if hip < 150:
            return "partial hinge"

        return "standing / top"

    if exercise == "bicep curl":

        if elbow is None:
            return "unknown position"

        if elbow < 70:
            return "top / contracted"

        if elbow < 120:
            return "mid curl"

        return "bottom / extended"

    if exercise == "overhead press":

        if _good(
            pts,
            "left_wrist",
            "right_wrist",
            "left_shoulder",
            "right_shoulder",
        ):

            wrists_up = (
                pts["left_wrist"].y <
                pts["left_shoulder"].y
                and
                pts["right_wrist"].y <
                pts["right_shoulder"].y
            )

            if wrists_up:

                if elbow is not None and elbow > 150:
                    return "top / lockout"

                return "mid press"

            return "bottom / rack position"

        return "unknown position"

    if exercise == "lateral raise":

        if _good(
            pts,
            "left_wrist",
            "right_wrist",
            "left_shoulder",
            "right_shoulder",
        ):

            shoulder_center = _midpoint(
                pts["left_shoulder"],
                pts["right_shoulder"],
            )

            wrist_center = _midpoint(
                pts["left_wrist"],
                pts["right_wrist"],
            )

            difference = abs(
                wrist_center.y -
                shoulder_center.y
            )

            shoulder_width = _distance(
                pts["left_shoulder"],
                pts["right_shoulder"],
            )

            if difference < shoulder_width * 0.4:
                return "top / arms raised"

            return "mid / arms rising"

        return "unknown position"

    if exercise == "jumping jack":
        return "open / extended"

    if exercise == "standing / neutral":
        return "neutral standing"

    return "unknown"


# ============================================================
# DETAILS
# ============================================================

def _format_details(angles):
    """
    Human-readable joint-angle output.
    """

    names = [
        ("left_knee", "L knee"),
        ("right_knee", "R knee"),
        ("left_elbow", "L elbow"),
        ("right_elbow", "R elbow"),
        ("left_hip", "L hip"),
        ("right_hip", "R hip"),
    ]

    parts = []

    for key, label in names:

        value = angles.get(key)

        if value is not None:
            parts.append(
                f"{label}: {round(value)}°"
            )

    return ", ".join(parts)


# ============================================================
# MAIN IMAGE ANALYSIS
# ============================================================

def analyze_exercise_image(image_source=None):
    """
    Analyze one image.

    Returns a string such as:

        Detected exercise: squat
        (confidence: 87%, state: mid squat).
        L knee: 108°, R knee: 111°, L hip: 101°, R hip: 104°

    image_source:
        None
            → capture from configured camera

        "tests/squat.jpg"
            → analyze saved image
    """

    if image_source is None:

        image_source = capture_photo()

        if image_source is None:
            return "ERROR: could not capture image."

    try:

        results = _pose_model(
            image_source,
            conf=CONF_THRESHOLD,
            verbose=False,
        )

    except Exception as e:

        return f"ERROR running pose detection: {e}"

    for result in results:

        if result.keypoints is None:
            continue

        if len(result.keypoints) == 0:
            continue

        # ----------------------------------------------------
        # Select first detected person
        # ----------------------------------------------------

        kp_xy = result.keypoints.xy[0].tolist()

        if len(kp_xy) < 17:
            continue

        # ----------------------------------------------------
        # Keypoint confidence
        # ----------------------------------------------------

        kp_conf = None

        if result.keypoints.conf is not None:

            kp_conf = result.keypoints.conf[0].tolist()

        pts = _get_points(
            kp_xy,
            kp_conf,
        )

        valid_count = _valid_points(pts)

        if valid_count < MIN_VALID_KEYPOINTS:

            return (
                "Pose detected, but too many body "
                "keypoints are unreliable."
            )

        # ----------------------------------------------------
        # Geometry
        # ----------------------------------------------------

        angles = _joint_angles(pts)

        measurements = _body_measurements(pts)

        # measurements currently calculated intentionally
        # because later classifiers/form checking can use them.
        _ = measurements

        # ----------------------------------------------------
        # Score every exercise
        # ----------------------------------------------------

        scores = _get_exercise_scores(
            pts,
            angles,
        )

        # ----------------------------------------------------
        # Best match
        # ----------------------------------------------------

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        best_exercise, best_score = ranked[0]

        second_score = (
            ranked[1][1]
            if len(ranked) > 1
            else 0.0
        )

        # ----------------------------------------------------
        # Ambiguity handling
        # ----------------------------------------------------

        # If everything has a weak score, don't pretend
        # that we know what exercise it is.
        if best_score < 0.40:

            return (
                "Pose detected, but exercise is unclear. "
                f"Best guess: {best_exercise} "
                f"({best_score:.0%}). "
                f"Angles: {_format_details(angles)}"
            )

        # If two exercises are extremely close, report
        # ambiguity instead of making an overconfident claim.
        if (
            best_score < 0.65
            and
            (best_score - second_score) < 0.08
        ):

            return (
                f"Exercise ambiguous: "
                f"{best_exercise} ({best_score:.0%}) "
                f"vs {ranked[1][0]} "
                f"({second_score:.0%}). "
                f"Angles: {_format_details(angles)}"
            )

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        state = _classify_state(
            best_exercise,
            pts,
            angles,
        )

        details = _format_details(angles)

        return str(
            ExerciseResult(
                exercise=best_exercise,
                confidence=best_score,
                state=state,
                details=details,
            )
        )

    return "No person / pose detected."


# ============================================================
# RETURN STRUCTURED DATA
# ============================================================

def analyze_exercise(image_source=None):
    """
    Same analysis as analyze_exercise_image(), but returns
    structured information instead of a string.

    Useful later for your AI agent / UI / database.

    Example:

        {
            "exercise": "squat",
            "confidence": 0.82,
            "state": "mid squat",
            "angles": {
                "left_knee": 110,
                ...
            },
            "scores": {
                "squat": 0.82,
                ...
            }
        }
    """

    if image_source is None:

        image_source = capture_photo()

        if image_source is None:
            return {
                "error": "Could not capture image."
            }

    try:

        results = _pose_model(
            image_source,
            conf=CONF_THRESHOLD,
            verbose=False,
        )

    except Exception as e:

        return {
            "error": str(e)
        }

    for result in results:

        if result.keypoints is None:
            continue

        if len(result.keypoints) == 0:
            continue

        kp_xy = result.keypoints.xy[0].tolist()

        kp_conf = None

        if result.keypoints.conf is not None:
            kp_conf = result.keypoints.conf[0].tolist()

        pts = _get_points(
            kp_xy,
            kp_conf,
        )

        if _valid_points(pts) < MIN_VALID_KEYPOINTS:
            return {
                "error": "Insufficient keypoint confidence."
            }

        angles = _joint_angles(pts)

        scores = _get_exercise_scores(
            pts,
            angles,
        )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        exercise, confidence = ranked[0]

        state = _classify_state(
            exercise,
            pts,
            angles,
        )

        return {
            "exercise": exercise,
            "confidence": round(confidence, 3),
            "state": state,
            "angles": {
                key: (
                    round(value, 1)
                    if value is not None
                    else None
                )
                for key, value in angles.items()
            },
            "scores": {
                key: round(value, 3)
                for key, value in scores.items()
            },
        }

    return {
        "error": "No person / pose detected."
    }


# ============================================================
# MULTI-FRAME / SEQUENCE CLASSIFICATION
# ============================================================

def classify_exercise_sequence(image_sources):
    """
    Analyze multiple frames and use temporal voting.

    Example:

        frames = [
            "frame_001.jpg",
            "frame_002.jpg",
            "frame_003.jpg",
            "frame_004.jpg",
        ]

        result = classify_exercise_sequence(frames)

    This is much more reliable than trying to identify
    an exercise from one frame.

    It also allows future movement detection:

        squat:
            standing
                ↓
            descending
                ↓
            bottom
                ↓
            ascending
                ↓
            standing

    At the moment this function identifies the dominant
    exercise and the sequence of detected states.
    """

    frame_results = []

    for image_source in image_sources:

        result = analyze_exercise(
            image_source
        )

        if "error" in result:
            continue

        frame_results.append(result)

    if not frame_results:

        return {
            "error": "No valid poses detected."
        }

    exercises = [
        result["exercise"]
        for result in frame_results
    ]

    dominant_exercise = Counter(
        exercises
    ).most_common(1)[0][0]

    relevant_frames = [
        result
        for result in frame_results
        if result["exercise"] == dominant_exercise
    ]

    states = [
        result["state"]
        for result in relevant_frames
    ]

    return {
        "exercise": dominant_exercise,
        "frames_analyzed": len(frame_results),
        "states": states,
        "results": frame_results,
    }


# ============================================================
# QUICK MANUAL TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        ("Squat bottom", "tests/squat_bottom.jpg"),
        ("Squat top", "tests/squat_top.jpg"),
        ("Push-up", "tests/pushup.jpg"),
        ("Overhead press", "tests/press_overhead.jpg"),
        ("Standing", "tests/standing.jpg"),
    ]

    for name, image_path in tests:

        print()
        print("=" * 60)
        print(name)
        print("=" * 60)

        result = analyze_exercise_image(
            image_path
        )

        print(result)