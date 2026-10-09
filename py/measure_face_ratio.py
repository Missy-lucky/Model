from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from mediapipe import Image as MpImage, ImageFormat
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from check_proportions import imread_unicode


def load_detector():
    model = Path(__file__).resolve().parent / "qc_assets" / "face_landmarker.task"
    ascii_dir = Path(tempfile.gettempdir()) / "model_qc_assets"
    ascii_dir.mkdir(exist_ok=True)
    ascii_model = ascii_dir / model.name
    if not ascii_model.exists():
        shutil.copy2(model, ascii_model)
    return mp_vision.FaceLandmarker.create_from_options(
        mp_vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(ascii_model)),
            running_mode=mp_vision.RunningMode.IMAGE,
            num_faces=1,
        )
    )


def measure(path: str) -> tuple[float, float] | None:
    det = load_detector()
    img = imread_unicode(Path(path))
    h, w = img.shape[:2]
    crop = img[0 : int(h * 0.30), max(0, int(w * 0.25)) : min(w, int(w * 0.75))]
    crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    ch, cw = crop.shape[:2]
    result = det.detect(MpImage(image_format=ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
    if not result.face_landmarks:
        return None
    lm = result.face_landmarks[0]

    def pt(i: int) -> np.ndarray:
        return np.array([lm[i].x * cw, lm[i].y * ch])

    face_h = float(np.linalg.norm(pt(152) - pt(10)))
    cheek = float(np.linalg.norm(pt(454) - pt(234)))
    jaw = float(np.linalg.norm(pt(397) - pt(172)))
    if face_h <= 0 or cheek <= 0:
        return None
    return cheek / face_h, jaw / cheek


if __name__ == "__main__":
    ratio = measure(sys.argv[1])
    if ratio is None:
        print("no face")
        sys.exit(2)
    print(f"cheek/height={ratio[0]:.2f} jaw/cheek={ratio[1]:.2f}")
    sys.exit(0 if ratio[0] <= 0.80 else 1)
