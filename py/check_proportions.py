from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import cv2
import numpy as np

os.environ.setdefault("GLOG_minloglevel", "2")


HEAD_TO_FACE = 1.3   # full head height vs frontal face-box height
MIN_HEADS = 6.8      # conservative machine estimate for a 7.5-8 head body
MIN_FILL = 0.75      # body height vs frame height
MIN_SHOULDER_RATIO = 1.6
MIN_LEGS = 1.25      # ankle-hip distance / hip-shoulder distance; 1.0 is a five-five split


try:
    from mediapipe import Image as MpImage, ImageFormat
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    _MODEL_PATH = Path(__file__).resolve().parent / "qc_assets" / "pose_landmarker_heavy.task"
    if _MODEL_PATH.exists():
        _LOAD_PATH = _MODEL_PATH
        try:
            str(_LOAD_PATH).encode("ascii")
        except UnicodeEncodeError:
            # The native loader cannot open non-ASCII Windows paths.
            import shutil
            import tempfile
            _ascii_dir = Path(tempfile.gettempdir()) / "model_qc_assets"
            _ascii_dir.mkdir(parents=True, exist_ok=True)
            _ascii_model = _ascii_dir / _MODEL_PATH.name
            if not _ascii_model.exists():
                shutil.copy2(_MODEL_PATH, _ascii_model)
            _LOAD_PATH = _ascii_model
        _OPTIONS = mp_vision.PoseLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(_LOAD_PATH)),
            running_mode=mp_vision.RunningMode.IMAGE,
            num_poses=1,
        )
        _POSE = mp_vision.PoseLandmarker.create_from_options(_OPTIONS)
    else:
        _POSE = None
except Exception:  # noqa: BLE001
    _POSE = None


def pose_metrics(img: np.ndarray) -> dict | None:
    """Measure torso/leg split from body landmarks; returns None when unusable."""
    if _POSE is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_img = MpImage(image_format=ImageFormat.SRGB, data=rgb)
    result = _POSE.detect(mp_img)
    if not result.pose_landmarks:
        return None
    lm = result.pose_landmarks[0]
    idx = {
        "ls": 11, "rs": 12,   # shoulders
        "lh": 23, "rh": 24,   # hips
        "lk": 25, "rk": 26,   # knees
        "la": 27, "ra": 28,   # ankles
    }
    if any(lm[i].visibility < 0.5 for i in idx.values()):
        return None

    h, w = img.shape[:2]
    def pt(i):
        return np.array([lm[i].x * w, lm[i].y * h])

    shoulder_mid = (pt(idx["ls"]) + pt(idx["rs"])) / 2
    hip_mid = (pt(idx["lh"]) + pt(idx["rh"])) / 2
    ankle_mid = (pt(idx["la"]) + pt(idx["ra"])) / 2
    torso = hip_mid[1] - shoulder_mid[1]
    legs = ankle_mid[1] - hip_mid[1]
    if torso <= 0 or legs <= 0:
        return None

    shoulder_w = float(np.linalg.norm(pt(idx["ls"]) - pt(idx["rs"])))
    hip_w = float(np.linalg.norm(pt(idx["lh"]) - pt(idx["rh"])))
    return {
        "leg_ratio": round(legs / torso, 2),
        "leg_share": round(legs / (legs + torso), 3),
        "shoulder_hip": round(shoulder_w / hip_w, 2) if hip_w else None,
        "_landmarks": {
            "ls": pt(idx["ls"]), "rs": pt(idx["rs"]),
            "lh": pt(idx["lh"]), "rh": pt(idx["rh"]),
            "lk": pt(idx["lk"]), "rk": pt(idx["rk"]),
            "la": pt(idx["la"]), "ra": pt(idx["ra"]),
        },
    }


def detect_face(gray: np.ndarray):
    cascades = [
        cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml"),
        cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"),
        cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml"),
    ]
    best = None
    for casc in cascades:
        faces = casc.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(20, 20))
        if len(faces):
            candidate = max(faces, key=lambda f: f[2] * f[3])
            if best is None or candidate[2] * candidate[3] > best[2] * best[3]:
                best = candidate
    return best


def imread_unicode(path: Path) -> np.ndarray:
    # cv2.imread cannot handle non-ASCII Windows paths.
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def person_mask(img: np.ndarray) -> np.ndarray:
    small = cv2.resize(img, (160, 160))
    border = np.concatenate([small[0, :], small[-1, :], small[:, 0], small[:, -1]])
    bg = np.median(border, axis=0)
    diff = np.abs(small.astype(int) - bg.astype(int)).sum(axis=2)
    mask = (diff > 55).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)


def analyze(
    path: Path,
    min_heads: float = MIN_HEADS,
    min_fill: float = MIN_FILL,
    min_legs: float = MIN_LEGS,
) -> dict:
    img = imread_unicode(path)
    if img is None:
        raise RuntimeError(f"cannot read {path}")

    h, w = img.shape[:2]
    scale = 1400 / max(h, w)
    work = cv2.resize(img, (round(w * scale), round(h * scale))) if scale != 1 else img
    gray = cv2.equalizeHist(cv2.cvtColor(work, cv2.COLOR_BGR2GRAY))

    face = detect_face(gray)
    mask = person_mask(img)
    rows = np.where(mask.sum(axis=1) > w * 0.02)[0]

    result = {
        "path": str(path),
        "frame": (w, h),
        "face_px": None,
        "heads": None,
        "fill": None,
        "shoulder_ratio": None,
        "leg_ratio": None,
        "leg_share": None,
        "thigh_shoulder": None,
        "calf_shoulder": None,
        "ok": False,
        "reason": [],
    }
    pose = pose_metrics(img)
    if pose:
        landmarks = pose.pop("_landmarks")
        result.update(pose)
        ls, rs = landmarks["ls"], landmarks["rs"]
        lh, rh = landmarks["lh"], landmarks["rh"]
        lk, rk = landmarks["lk"], landmarks["rk"]
        la, ra = landmarks["la"], landmarks["ra"]
        shoulder_w = float(np.linalg.norm(ls - rs))
        hip_mid = (lh + rh) / 2
        knee_mid = (lk + rk) / 2
        ankle_mid = (la + ra) / 2

        def width_at_row(y: float) -> float | None:
            yi = int(y)
            if not (0 <= yi < h):
                return None
            band = mask[max(0, yi - 3): yi + 4, :]
            cols = np.where(band.sum(axis=0) > 255 * 3)[0]
            if not len(cols):
                return None
            return float(cols[-1] - cols[0])

        thigh_w = width_at_row((hip_mid[1] + knee_mid[1]) / 2)
        calf_w = width_at_row((knee_mid[1] + ankle_mid[1]) / 2)
        if thigh_w is not None and shoulder_w:
            result["thigh_shoulder"] = round(thigh_w / shoulder_w, 2)
        if calf_w is not None and shoulder_w:
            result["calf_shoulder"] = round(calf_w / shoulder_w, 2)

    if face is None:
        result["reason"].append("face not detected")
    if len(rows) == 0:
        result["reason"].append("body not detected")

    if face is None or len(rows) == 0:
        result["ok"] = not result["reason"]
        return result

    fx, fy, fw, fh = face
    face_h = fh / scale
    face_w = fw / scale
    top, bottom = rows[0], rows[-1]
    body_h = bottom - top
    head_full = face_h * HEAD_TO_FACE

    result["face_px"] = int(face_h)
    result["heads"] = round(body_h / head_full, 2)
    result["fill"] = round(body_h / h, 3)
    # Shoulder width from the person mask at roughly 1.8 head-heights below the crown.
    crown = max(0, int(fy / scale - 0.35 * face_h))
    shoulder_y = int(crown + 1.8 * head_full)
    if 0 <= shoulder_y < h:
        band = mask[max(0, shoulder_y - 4): shoulder_y + 5, :]
        cols = np.where(band.sum(axis=0) > 255 * 3)[0]
        if len(cols):
            shoulder_w = cols[-1] - cols[0]
            result["shoulder_ratio"] = round(shoulder_w / face_w, 2)

    if result["heads"] is not None and result["heads"] < min_heads:
        result["reason"].append(f"heads {result['heads']} < {min_heads}")
    if result["fill"] < min_fill:
        result["reason"].append(f"fill {result['fill']} < {min_fill}")
    if result["shoulder_ratio"] is not None and result["shoulder_ratio"] < MIN_SHOULDER_RATIO:
        result["reason"].append(f"shoulder/head-width {result['shoulder_ratio']} < {MIN_SHOULDER_RATIO}")
    if result["leg_ratio"] is not None and result["leg_ratio"] < min_legs:
        result["reason"].append(f"legs/torso {result['leg_ratio']} < {min_legs} (five-five split)")
    result["ok"] = not result["reason"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="QC head-to-body proportion for fashion model images")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--min-heads", type=float, default=MIN_HEADS,
                        help="minimum estimated head-to-body ratio; 0 disables (use 0 for 3/4 crops)")
    parser.add_argument("--min-fill", type=float, default=MIN_FILL,
                        help="minimum body height vs frame height; 0 disables")
    parser.add_argument("--min-legs", type=float, default=MIN_LEGS,
                        help="minimum ankle-hip / hip-shoulder ratio; 0 disables (use 0 for 3/4 crops)")
    parser.add_argument("--max-thigh", type=float, default=0.0,
                        help="maximum mid-thigh width / shoulder width; 0 disables")
    parser.add_argument("--max-calf", type=float, default=0.0,
                        help="maximum mid-calf width / shoulder width; 0 disables")
    args = parser.parse_args()

    failed = False
    for path in args.images:
        try:
            r = analyze(path, args.min_heads, args.min_fill, args.min_legs)
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {path}: {exc}")
            failed = True
            continue
        reasons = list(r["reason"])
        if args.min_heads <= 0:
            reasons = [x for x in reasons if not x.startswith("heads ")]
        if args.min_fill <= 0:
            reasons = [x for x in reasons if not x.startswith("fill ")]
        if args.min_legs <= 0:
            reasons = [x for x in reasons if not x.startswith("legs/torso ")]
        if args.max_thigh > 0 and r["thigh_shoulder"] is not None and r["thigh_shoulder"] > args.max_thigh:
            reasons.append(f"thigh/shoulder {r['thigh_shoulder']} > {args.max_thigh}")
        if args.max_calf > 0 and r["calf_shoulder"] is not None and r["calf_shoulder"] > args.max_calf:
            reasons.append(f"calf/shoulder {r['calf_shoulder']} > {args.max_calf}")
        ok = not reasons
        status = "PASS" if ok else "FAIL"
        print(
            f"{status} {path} heads={r['heads']} fill={r['fill']} "
            f"legs/torso={r['leg_ratio']} leg_share={r['leg_share']} "
            f"thigh/sh={r['thigh_shoulder']} calf/sh={r['calf_shoulder']} "
            f"shoulder_ratio={r['shoulder_ratio']} face={r['face_px']}px"
            + ("" if ok else " | " + "; ".join(reasons))
        )
        failed = failed or not ok
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
