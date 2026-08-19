

import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import euclidean_distances as dist
import numpy as np
from ultralytics import YOLO
MIN_ELBOW_POSITION_ANGLE = 30
MAX_ELBOW_POSITION_ANGLE = 70

incorrectState =0
phase = 0
reps = 0
incorrect_reps = 0



CAMERA = "webcam"                 # "webcam" or "pi"
POSE_MODEL_PATH = "yolov8n-pose.pt"
CONF_THRESHOLD = 0.40

KEYPOINT_CONF_THRESHOLD = 0.35

MIN_VALID_KEYPOINTS = 8

def estimate_angle(a,b,c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = (
    np.arctan2(c[1] - b[1], c[0] - b[0])
    - np.arctan2(a[1] - b[1], a[0] - b[0])
    )
    angle= abs(radians*180)/np.pi
    if angle>180:
        return 360-angle

    return angle

def get_angle(kp):
    right_shoulder = kp[6]
    right_elbow = kp[8]
    right_wrist = kp[10]
    left_shoulder = kp[5]
    left_elbow = kp[7]
    left_wrist = kp[9]

    right_angle = estimate_angle(right_shoulder,right_elbow,right_wrist)
    left_angle = estimate_angle(left_shoulder,left_elbow,left_wrist)
    avg_angle = (right_angle+left_angle) /2
    phase = ""
    if avg_angle>=155:
        phase = "start"
    elif avg_angle>125:
        phase = "midrep"
    else:
        phase = "bottom"        
    return avg_angle,phase

def is_in_starting_position(kp):
    right_shoulder = kp[6]
    right_elbow = kp[8]
    right_wrist = kp[10]
    left_shoulder = kp[5]
    left_elbow = kp[7]
    left_wrist = kp[9]
    angle = get_angle(kp)

    right_angle = estimate_angle(right_shoulder,right_elbow,right_wrist)
    left_angle = estimate_angle(left_shoulder,left_elbow,left_wrist)
    
    threshold = 155
    isUpRIght = (right_angle>=threshold and left_angle>=threshold)
    return isUpRIght


def check_elbow_position(kps: np.ndarray, movement_angle: float) -> bool:
    right_shoulder = kps[6]
    right_elbow = kps[8]
    right_hip = kps[12]

    left_shoulder = kps[5]
    left_elbow = kps[7]
    left_hip = kps[11]

    right_angle = estimate_angle(
        right_elbow,
        right_shoulder,
        right_hip
    )

    left_angle = estimate_angle(
        left_elbow,
        left_shoulder,
        left_hip
    )

    average_angle = (right_angle + left_angle) / 2

    # Movement elbow angle -> acceptable elbow-position angle.
    movement_angles = np.array([
        100.0,
        110.0,
        120.0,
        130.0,
        140.0,
        150.0
    ])

    min_position_angles = np.array([
        15.0,
        20.0,
        25.0,
        35.0,
        45.0,
        55.0
    ])

    max_position_angles = np.array([
        30.0,
        35.0,
        45.0,
        50.0,
        60.0,
        65.0
    ])

    # Clamp movement angle to our reference range.
    movement_angle = np.clip(
        movement_angle,
        100.0,
        150.0
    )

    expected_min = np.interp(
        movement_angle,
        movement_angles,
        min_position_angles
    )

    expected_max = np.interp(
        movement_angle,
        movement_angles,
        max_position_angles
    )

    print(
        f"ELBOW POSITION = {average_angle:.1f} | "
        f"EXPECTED = {expected_min:.1f}-{expected_max:.1f}"
    )
    tolerence = 10

    return (
        expected_min - tolerence
        <= average_angle
        <= expected_max + tolerence
    )


def wrists_wider_than_shoulders(kps: np.ndarray) -> bool:
    right_shoulder = kps[6]
    left_shoulder = kps[5]

    right_wrist = kps[10]
    left_wrist = kps[9]

    shoulders_width = np.linalg.norm(
        right_shoulder - left_shoulder
    )

    wrists_width = np.linalg.norm(
        right_wrist - left_wrist
    )

    return wrists_width >= shoulders_width


MIN_BODY_ANGLE = 150.0

def check_body_alignment(kps):
    right_shoulder = kps[6]
    right_hip = kps[12]
    right_ankle = kps[16]

    body_angle = estimate_angle(
        right_shoulder,
        right_hip,
        right_ankle
    )
    print(f"BODY ANGLE = {body_angle:.1f}")


    return body_angle >= MIN_BODY_ANGLE


def give_feedback_push_up(kps: np.ndarray) -> Tuple[Dict, List]:
    feedback = {}
    feedback_flag = False

    possible_corrections = [
        "start_position",
        "wrist_bad",
        "body_bad",
        "elbow_bad",
    ]

    angle, phase = get_angle(kps)

    # --------------------------------
    # Starting-position checks
    # --------------------------------

    if is_in_starting_position(kps):

        feedback["is_in_position"] = True

        if not wrists_wider_than_shoulders(kps):
            feedback["wrist_bad"] = (
                "Place your hands wider than your shoulders!"
            )
            feedback_flag = True

    # --------------------------------
    # Active push-up checks
    # --------------------------------

    else:

        if is_valid_pose_geometry(kps):
            if not check_body_alignment(kps):
                feedback["body_bad"] = (
                "Keep your body straight!"
                )
                feedback_flag = True

            if not check_elbow_position(kps,angle):
                feedback["elbow_bad"] = (
                    "Keep your elbows closer to your body!"
                )
                feedback_flag = True

    pointsofinterest = []

    return (
        feedback,
        possible_corrections,
        pointsofinterest,
        feedback_flag,
    )


def is_valid_pose_geometry(kps):
    body_angle = estimate_angle(
        kps[6],
        kps[12],
        kps[16]
    )

    return 120 <= body_angle <= 190



def counts_calculate_push_up(kps,correct):
    angle,_ = get_angle(kps)
    per = np.interp(angle, (100, 150), (0, 100))
    print(
        f"COUNT | angle={angle:.1f} | "
        f"percent={per:.1f} | "
        f"correct={correct} | "
    )
    return count(per,correct == 1)







def count(percent, isCorrect=False):
    global incorrectState
    global phase
    global reps
    global incorrect_reps

    # --------------------------------------------------
    # BEFORE REP STARTS
    # --------------------------------------------------
    # Ignore form errors while the user is simply
    # getting into the starting position.
    if phase == 0:

        # We only start a rep once the top position
        # reaches 100%.
        if percent >= 100:
            phase = 1
            incorrectState = 0

            # The frame that reaches 100% is the
            # beginning of the rep, so don't mark it
            # incorrect yet.
            return reps, incorrect_reps

        return reps, incorrect_reps

    # --------------------------------------------------
    # REP IS ACTIVE
    # --------------------------------------------------

    # Now form errors matter.
    if not isCorrect:
        incorrectState = 1

    # --------------------------------------------------
    # REP COMPLETED
    # --------------------------------------------------

    if percent <= 0:

        if incorrectState == 1:
            incorrect_reps += 1
            print(
                f"REP COMPLETED | "
                f"Correct: {reps} | "
                f"Incorrect: {incorrect_reps} | "
                f"Total: {reps + incorrect_reps}"
            )
        else:
            reps += 1
            print(
                f"REP COMPLETED | "
                f"Correct: {reps} | "
                f"Incorrect: {incorrect_reps} | "
                f"Total: {reps + incorrect_reps}"
            )

        # Reset for the next repetition.
        phase = 0
        incorrectState = 0

    return reps, incorrect_reps


def get_debug_info(kps):
    angle, movement_phase = get_angle(kps)

    start = is_in_starting_position(kps)
    hand_ok = wrists_wider_than_shoulders(kps)

    if is_valid_pose_geometry(kps):
        body_ok = check_body_alignment(kps)
        elbow_ok = check_elbow_position(kps, angle)
    else:
        body_ok = True
        elbow_ok = True

    return {
        "angle": angle,
        "phase": movement_phase,
        "start": start,
        "hands": hand_ok,
        "body": body_ok,
        "elbow": elbow_ok,
    }    