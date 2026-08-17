

import cv2
from pathlib import Path
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image
import torch

# ---------------- CONFIG ----------------
CAMERA = "webcam"
CLASSIFIER_NAME = "prithivMLmods/Food-101-93M"
GRID = 2                 # 2 -> 2x2 tiles, 3 -> 3x3 tiles
OVERLAP = 0.15           # fraction of overlap between tiles (helps border foods)
TILE_CONF_MIN = 0.35     # a tile's top label must beat this to count
WHOLE_CONF_MIN = 0.30    # whole-image label threshold
TOPK_PER_TILE = 1        # how many labels to take from each tile

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
    """Map a Food-101 dish label to a plain fitness food, if we have a rule."""
    key = label.lower().strip()
    if key in REMAP and conf >= REMAP_CONF_MIN:
        return REMAP[key]
    return label

_processor = AutoImageProcessor.from_pretrained(CLASSIFIER_NAME)
_model = SiglipForImageClassification.from_pretrained(CLASSIFIER_NAME)
_model.eval()


# ---------------- camera ----------------
def capture_photo(output_path="captured_food.jpg"):
    if CAMERA == "webcam":
        cam = cv2.VideoCapture(0)
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


def _classify(bgr):
    """Classify a BGR numpy image, return (label, confidence)."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    inputs = _processor(images=pil, return_tensors="pt")
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    conf, idx = torch.max(probs, dim=-1)
    label = _model.config.id2label[int(idx)].replace("_", " ")
    conf = float(conf)
    label = _apply_remap(label, conf)   # dish label -> plain fitness food
    return label, conf


def _tiles(img, grid, overlap):
    """Yield (crop, (row,col)) for a grid x grid split with overlap."""
    h, w = img.shape[:2]
    th, tw = h // grid, w // grid
    oh, ow = int(th * overlap), int(tw * overlap)
    for r in range(grid):
        for c in range(grid):
            y1 = max(0, r * th - oh)
            y2 = min(h, (r + 1) * th + oh)
            x1 = max(0, c * tw - ow)
            x2 = min(w, (c + 1) * tw + ow)
            crop = img[y1:y2, x1:x2]
            if crop.size > 0:
                yield crop, (r, c)


def analyze_food_image(image_source=None):
    """
    Grid-tiling food recognition. Splits the image, classifies each tile,
    and returns all confidently-found foods.
    """
    if image_source is None:
        image_source = capture_photo()
        if image_source is None:
            return "ERROR: could not capture an image from the camera."

    img = cv2.imread(image_source)
    if img is None:
        return f"ERROR: could not read image {image_source}."

    found = {}   # label -> best confidence

    try:
        wlabel, wconf = _classify(img)
        if wconf >= WHOLE_CONF_MIN:
            found[wlabel] = max(found.get(wlabel, 0), wconf)
    except Exception:
        pass

    for crop, _ in _tiles(img, GRID, OVERLAP):
        try:
            label, conf = _classify(crop)
        except Exception:
            continue
        if conf >= TILE_CONF_MIN:
            found[label] = max(found.get(label, 0), conf)

    if not found:
        return "No food confidently identified."

    parts = [f"{label} ({round(conf*100)}%)"
             for label, conf in sorted(found.items(), key=lambda x: -x[1])]
    return "Detected foods: " + ", ".join(parts) + "."


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(analyze_food_image(sys.argv[1]))
    else:
        print(analyze_food_image())