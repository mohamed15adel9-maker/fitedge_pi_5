
from typing import List, Optional, Tuple

import cv2
import numpy as np


def draw_keypoints(frame,kp):
    for point in kp:
        x, y = point[:2].astype(np.int16) 
        cv2.circle(frame,(x,y),3,(255,0,0),3) 
    return frame    

def draw_connections(connections_list,frame,kp):
    for connection in connections_list:
        p1,p2 = connection
        x,y = kp[p1][:2].astype(np.int16)
        w,z = kp[p2][:2].astype(np.int16)
        cv2.line(frame,(x,y),(w,z),(0,255,0),3)
    return frame    

def feedbackText(frame,feedback):
    cv2.putText(frame,feedback,(0,900),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)
    return frame

def repcount(frame,count):
    cv2.putText(frame,f"Reps: {count}",(0,100),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)
    return frame
def draw_elbow_angle(frame, kp, angle):
    x, y = kp[8][:2].astype(np.int16)

    cv2.putText(
        frame,
        f"{angle:.0f}°",
        (x + 10, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    return frame

def draw_problem_joint(frame, kp, joint_index):
    x, y = kp[joint_index][:2].astype(np.int16)

    cv2.circle(
        frame,
        (x, y),
        10,
        (0, 0, 255),
        3
    )

    return frame    

def debug_text(frame, text, y):
    cv2.putText(
        frame,
        str(text),
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )
    return frame    