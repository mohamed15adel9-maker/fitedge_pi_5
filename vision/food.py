"""
vision/food.py

Live food recognition using a webcam.

The camera stays open and frames are continuously captured.
Food classification is performed repeatedly while the session runs.

The existing Food-101/SigLIP classifier, tiling logic, confidence
thresholds, and label remapping are preserved.

Behavior:
    analyze_food_image()       -> live camera session
    analyze_food_image(path)   -> classify one image (backward compatible)

Press Q to end the live food-recognition session.
"""

import cv2
import time

from transformers import (
    AutoImageProcessor,
    SiglipForImageClassification,
)
from PIL import Image
import torch


# =========================================================
# CONFIG
# =========================================================

CAMERA_INDEX = 1

CLASSIFIER_NAME = "prithivMLmods/Food-101-93M"

GRID = 2
OVERLAP = 0.15

TILE_CONF_MIN = 0.35
WHOLE_CONF_MIN = 0.30

TOPK_PER_TILE = 1

# Run classification every N camera frames.
# This keeps the camera display responsive on weaker hardware.
PROCESS_EVERY_N_FRAMES = 5

WINDOW_NAME = "FitEdge Food Recognition"


# =========================================================
# LABEL REMAPPING
# =========================================================

REMAP = {
    "grilled salmon": "grilled chicken",
    "deviled eggs": "eggs",
    "risotto": "rice",
    "gnocchi": "fried potato",
    "french fries": "potato",
    "steak": "beef",
    "filet mignon": "beef",
}

REMAP_CONF_MIN = 0.30


def _apply_remap(label, conf):
    """Map a Food-101 dish label to a plain fitness food."""
    key = label.lower().strip()

    if key in REMAP and conf >= REMAP_CONF_MIN:
        return REMAP[key]

    return label


# =========================================================
# MODEL
# =========================================================

_processor = AutoImageProcessor.from_pretrained(
    CLASSIFIER_NAME
)

_model = SiglipForImageClassification.from_pretrained(
    CLASSIFIER_NAME
)

_model.eval()


# =========================================================
# CLASSIFICATION
# =========================================================

def _classify(bgr):
    """
    Classify one BGR OpenCV image.

    Returns:
        (label, confidence)
    """
    rgb = cv2.cvtColor(
        bgr,
        cv2.COLOR_BGR2RGB,
    )

    pil = Image.fromarray(rgb)

    inputs = _processor(
        images=pil,
        return_tensors="pt",
    )

    with torch.no_grad():
        logits = _model(**inputs).logits

    probs = torch.softmax(
        logits,
        dim=-1,
    )[0]

    conf, idx = torch.max(
        probs,
        dim=-1,
    )

    label = _model.config.id2label[
        int(idx)
    ].replace("_", " ")

    conf = float(conf)

    label = _apply_remap(
        label,
        conf,
    )

    return label, conf


# =========================================================
# IMAGE TILING
# =========================================================

def _tiles(img, grid, overlap):
    """
    Yield:
        crop, (row, column)

    Uses overlapping grid tiles so foods close to tile boundaries
    can still be classified.
    """
    h, w = img.shape[:2]

    th = h // grid
    tw = w // grid

    oh = int(th * overlap)
    ow = int(tw * overlap)

    for r in range(grid):
        for c in range(grid):

            y1 = max(
                0,
                r * th - oh,
            )

            y2 = min(
                h,
                (r + 1) * th + oh,
            )

            x1 = max(
                0,
                c * tw - ow,
            )

            x2 = min(
                w,
                (c + 1) * tw + ow,
            )

            crop = img[
                y1:y2,
                x1:x2,
            ]

            if crop.size > 0:
                yield crop, (r, c)


# =========================================================
# ONE-FRAME ANALYSIS
# =========================================================

def _analyze_frame(img):
    """
    Analyze one camera frame.

    Returns:
        dict:
            label -> best confidence
    """
    found = {}

    # -----------------------------------------------------
    # Whole image
    # -----------------------------------------------------

    try:
        whole_label, whole_conf = _classify(
            img
        )

        if whole_conf >= WHOLE_CONF_MIN:
            found[whole_label] = max(
                found.get(
                    whole_label,
                    0.0,
                ),
                whole_conf,
            )

    except Exception as e:
        print(
            f"Whole-image classification error: {e}",
            flush=True,
        )

    # -----------------------------------------------------
    # Grid tiles
    # -----------------------------------------------------

    for crop, _ in _tiles(
        img,
        GRID,
        OVERLAP,
    ):
        try:
            label, conf = _classify(
                crop
            )

        except Exception as e:
            print(
                f"Tile classification error: {e}",
                flush=True,
            )
            continue

        if conf >= TILE_CONF_MIN:
            found[label] = max(
                found.get(
                    label,
                    0.0,
                ),
                conf,
            )

    return found


# =========================================================
# FORMAT RESULT
# =========================================================

def _format_foods(found):
    """
    Convert detected-food dictionary into readable text.
    """
    if not found:
        return "No food confidently identified."

    ordered = sorted(
        found.items(),
        key=lambda item: -item[1],
    )

    parts = [
        f"{label} ({round(conf * 100)}%)"
        for label, conf in ordered
    ]

    return (
        "Detected foods: "
        + ", ".join(parts)
        + "."
    )


# =========================================================
# DRAW LIVE RESULTS
# =========================================================

def _draw_food_results(frame, found):
    """
    Draw currently detected foods onto the live frame.
    """
    cv2.putText(
        frame,
        "FitEdge Food Recognition",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2,
    )

    if not found:
        cv2.putText(
            frame,
            "No confident food detected",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 255),
            2,
        )
        return frame

    ordered = sorted(
        found.items(),
        key=lambda item: -item[1],
    )

    y = 75

    for label, conf in ordered[:5]:

        text = (
            f"{label}: "
            f"{round(conf * 100)}%"
        )

        cv2.putText(
            frame,
            text,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )

        y += 30

    return frame


# =========================================================
# LIVE CAMERA SESSION
# =========================================================

def _run_live_food_session():
    """
    Continuously capture camera frames and classify food.

    Press Q to terminate the session.

    Returns:
        Final formatted detection result.
    """
    cam = cv2.VideoCapture(
        CAMERA_INDEX
    )

    if not cam.isOpened():
        raise RuntimeError(
            "Could not open webcam."
        )

    frame_count = 0
    current_found = {}
    last_result_time = 0.0

    print(
        "Starting live food recognition.",
        flush=True,
    )

    print(
        "Show the food to the camera. "
        "Press Q to finish.",
        flush=True,
    )

    try:

        while True:

            # -------------------------------------------------
            # 1. Capture frame
            # -------------------------------------------------

            ret, frame = cam.read()

            if not ret:
                print(
                    "Could not read camera frame.",
                    flush=True,
                )
                break

            frame_count += 1

            # -------------------------------------------------
            # 2. Run classification periodically
            # -------------------------------------------------

            if (
                frame_count
                % PROCESS_EVERY_N_FRAMES
                == 0
            ):

                current_found = _analyze_frame(
                    frame
                )

                result_text = _format_foods(
                    current_found
                )

                print(
                    result_text,
                    flush=True,
                )

                last_result_time = time.time()

            # -------------------------------------------------
            # 3. Draw current result
            # -------------------------------------------------

            frame = _draw_food_results(
                frame,
                current_found,
            )

            cv2.putText(
                frame,
                "Press Q to finish",
                (20, 450),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2,
            )

            # -------------------------------------------------
            # 4. Display
            # -------------------------------------------------

            cv2.imshow(
                WINDOW_NAME,
                frame,
            )

            if (
                cv2.waitKey(1)
                & 0xFF
                == ord("q")
            ):
                break

    finally:

        cam.release()
        cv2.destroyAllWindows()

    print(
        "Food recognition session ended.",
        flush=True,
    )

    return _format_foods(
        current_found
    )


# =========================================================
# PUBLIC TOOL FUNCTION
# =========================================================

def analyze_food_image(image_source=None):
    """
    Analyze food.

    No image_source:
        Start a live camera session.

    image_source provided:
        Analyze one existing image.

    Keeping image_source preserves compatibility with the
    previous static-image testing workflow.
    """

    # -----------------------------------------------------
    # Static image mode
    # -----------------------------------------------------

    if image_source is not None:

        img = cv2.imread(
            image_source
        )

        if img is None:
            return (
                f"ERROR: could not read image "
                f"{image_source}."
            )

        found = _analyze_frame(
            img
        )

        return _format_foods(
            found
        )

    # -----------------------------------------------------
    # Live mode
    # -----------------------------------------------------

    return _run_live_food_session()


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) > 1:
        print(
            analyze_food_image(
                sys.argv[1]
            )
        )
    else:
        print(
            analyze_food_image()
        )