from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


OUTPUT_SIZE = 800
CANVAS_MARGIN = 48


def poly_mask(shape: tuple[int, int], polygons: list[list[tuple[float, float]]]) -> np.ndarray:
    height, width = shape
    mask = np.zeros((height, width), np.uint8)
    for polygon in polygons:
        points = np.array(
            [(round(x * width), round(y * height)) for x, y in polygon],
            dtype=np.int32,
        )
        cv2.fillPoly(mask, [points], 255)
    return mask


def guide_for(name: str, shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    if name == "1":
        polygons = [
            [(0.21, 0.04), (0.79, 0.04), (0.82, 0.24), (0.80, 0.96),
             (0.73, 0.985), (0.63, 0.985), (0.54, 0.99), (0.46, 0.99),
             (0.37, 0.985), (0.27, 0.985), (0.22, 0.96)],
        ]
    elif name == "2":
        polygons = [
            [(0.25, 0.04), (0.76, 0.04), (0.79, 0.24), (0.77, 0.96),
             (0.67, 0.985), (0.57, 0.985), (0.50, 0.99), (0.43, 0.985),
             (0.33, 0.985), (0.26, 0.96)],
        ]
    elif name == "3":
        polygons = [
            [(0.11, 0.02), (0.79, 0.02), (0.81, 0.28), (0.78, 0.96),
             (0.68, 0.985), (0.58, 0.985), (0.50, 0.99), (0.42, 0.985),
             (0.31, 0.98), (0.22, 0.96), (0.12, 0.34)],
        ]
    elif name == "4":
        polygons = [
            [(0.23, 0.03), (0.77, 0.03), (0.79, 0.25), (0.78, 0.96),
             (0.67, 0.985), (0.57, 0.985), (0.50, 0.99), (0.43, 0.985),
             (0.33, 0.98), (0.25, 0.95)],
        ]
    elif name == "5":
        polygons = [
            [(0.20, 0.03), (0.82, 0.03), (0.85, 0.24), (0.83, 0.48),
             (0.78, 0.98), (0.65, 0.995), (0.50, 0.99), (0.34, 0.995),
             (0.21, 0.98), (0.17, 0.48)],
        ]
    elif name == "6":
        polygons = [
            [(0.18, 0.15), (0.34, 0.14), (0.66, 0.14), (0.82, 0.16),
             (0.88, 0.27), (0.87, 0.87), (0.82, 0.97), (0.73, 0.93),
             (0.68, 0.42), (0.32, 0.42), (0.28, 0.93), (0.20, 0.98),
             (0.13, 0.87), (0.12, 0.27)],
            [(0.23, 0.15), (0.77, 0.15), (0.80, 0.44), (0.20, 0.44)],
        ]
    elif name == "7":
        polygons = [
            [(0.16, 0.15), (0.34, 0.15), (0.66, 0.15), (0.84, 0.16),
             (0.88, 0.29), (0.87, 0.84), (0.84, 0.94), (0.74, 0.93),
             (0.69, 0.47), (0.31, 0.47), (0.27, 0.93), (0.17, 0.92),
             (0.13, 0.82), (0.12, 0.29)],
            [(0.21, 0.16), (0.79, 0.16), (0.82, 0.44), (0.18, 0.44)],
        ]
    elif name == "8":
        polygons = [
            [(0.21, 0.04), (0.80, 0.04), (0.82, 0.22), (0.80, 0.96),
             (0.70, 0.985), (0.60, 0.985), (0.53, 0.99), (0.46, 0.99),
             (0.37, 0.985), (0.26, 0.985), (0.21, 0.95)],
        ]
    else:
        polygons = [[(0.08, 0.05), (0.92, 0.05), (0.92, 0.96), (0.08, 0.96)]]
    return poly_mask((height, width), polygons)


def color_core(name: str, image: np.ndarray, guide: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    h, s, v = cv2.split(hsv)
    l, a, b = cv2.split(lab)

    if name in {"1", "2", "4", "8"}:
        core = (v < 205) | (s > 28)
    elif name in {"3", "5"}:
        core = ((v < 220) & (s > 18)) | (s > 35)
    else:
        # Light garments need texture/contrast cues in addition to color.
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        local = cv2.GaussianBlur(gray, (0, 0), 15)
        texture = cv2.absdiff(gray, local)
        core = (texture > 4) | (v < 235) | (s > 12)

    core = (core.astype(np.uint8) * 255) & guide
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return core


def clean_components(mask: np.ndarray, guide: np.ndarray, name: str) -> np.ndarray:
    mask = ((mask > 0) & (guide > 0)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return mask * 255

    keep = np.zeros_like(mask)
    image_area = mask.shape[0] * mask.shape[1]
    min_area = max(80, int(image_area * 0.00008))
    for idx in range(1, count):
        area = stats[idx, cv2.CC_STAT_AREA]
        x, y, w, h = stats[idx, :4]
        if area < min_area:
            continue
        if name in {"6", "7"}:
            # Keep the body and both sleeves, which can be disconnected after matting.
            if area >= image_area * 0.00012 or (h > image_area ** 0.5 * 0.22):
                keep[labels == idx] = 1
        elif area >= image_area * 0.00025 or h > image_area ** 0.45:
            keep[labels == idx] = 1
    return keep * 255


def segment(name: str, image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    guide = guide_for(name, (height, width))
    core = color_core(name, image, guide)

    gc_mask = np.full((height, width), cv2.GC_BGD, dtype=np.uint8)
    gc_mask[guide > 0] = cv2.GC_PR_FGD
    gc_mask[core > 0] = cv2.GC_FGD

    # Force a little background outside the clothing guide and protect the top hanger area.
    gc_mask[: max(1, int(height * 0.012)), :] = cv2.GC_BGD
    gc_mask[:, : max(1, int(width * 0.018))] = cv2.GC_BGD
    gc_mask[:, -max(1, int(width * 0.018)) :] = cv2.GC_BGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, gc_mask, None, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_MASK)
    foreground = np.where(
        (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0
    ).astype(np.uint8)

    foreground = clean_components(foreground, guide, name)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    foreground = cv2.GaussianBlur(foreground.astype(np.float32), (0, 0), 1.1)
    return np.clip(foreground, 0, 255).astype(np.uint8)


def resize_for_processing(image: np.ndarray) -> tuple[np.ndarray, float]:
    height, width = image.shape[:2]
    scale = min(1.0, 1200.0 / max(height, width))
    if scale == 1.0:
        return image, scale
    resized = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale


def compose(image: np.ndarray, alpha: np.ndarray) -> Image.Image:
    alpha_u8 = alpha.astype(np.uint8)
    ys, xs = np.where(alpha_u8 > 12)
    if len(xs) == 0:
        raise RuntimeError("No foreground found")

    x0, x1 = max(0, xs.min() - 3), min(image.shape[1], xs.max() + 4)
    y0, y1 = max(0, ys.min() - 3), min(image.shape[0], ys.max() + 4)
    crop = image[y0:y1, x0:x1]
    crop_alpha = alpha_u8[y0:y1, x0:x1]

    max_content = OUTPUT_SIZE - CANVAS_MARGIN * 2
    scale = min(max_content / crop.shape[1], max_content / crop.shape[0])
    out_w = max(1, round(crop.shape[1] * scale))
    out_h = max(1, round(crop.shape[0] * scale))
    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    crop_alpha = cv2.resize(crop_alpha, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)

    canvas = np.full((OUTPUT_SIZE, OUTPUT_SIZE, 3), 255, np.uint8)
    alpha_canvas = np.zeros((OUTPUT_SIZE, OUTPUT_SIZE), np.uint8)
    x = (OUTPUT_SIZE - out_w) // 2
    y = (OUTPUT_SIZE - out_h) // 2
    canvas[y:y + out_h, x:x + out_w] = rgb
    alpha_canvas[y:y + out_h, x:x + out_w] = crop_alpha

    # Composite onto white and keep a clean opaque catalog image.
    a = (alpha_canvas.astype(np.float32) / 255.0)[..., None]
    result = (canvas.astype(np.float32) * a + 255.0 * (1.0 - a)).clip(0, 255).astype(np.uint8)
    return Image.fromarray(result, mode="RGB")


def process_one(path: Path, output_dir: Path, debug_dir: Path | None) -> Path:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Cannot read {path}")
    small, scale = resize_for_processing(image)
    alpha = segment(path.stem, small)
    if debug_dir is not None:
        debug = small.copy()
        overlay = np.zeros_like(debug)
        overlay[:, :, 1] = 220
        mask = alpha > 12
        debug[mask] = (
            debug[mask].astype(np.float32) * 0.45
            + overlay[mask].astype(np.float32) * 0.55
        ).clip(0, 255).astype(np.uint8)
        cv2.imwrite(str(debug_dir / f"{path.stem}_mask.jpg"), debug)
    if scale != 1.0:
        alpha = cv2.resize(alpha, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR)
    result = compose(image, alpha)
    out_path = output_dir / f"{path.stem}.png"
    result.save(out_path, format="PNG", optimize=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("flat_800"))
    parser.add_argument("--debug-dir", type=Path, default=None)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.debug_dir:
        args.debug_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(args.input_dir.glob("*.jpg"), key=lambda item: int(item.stem) if item.stem.isdigit() else item.stem)
    if not paths:
        raise SystemExit("No JPG images found")
    for path in paths:
        out = process_one(path, args.output_dir, args.debug_dir)
        print(out)


if __name__ == "__main__":
    main()
