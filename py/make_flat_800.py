from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


OUTPUT_SIZE = 800
MARGIN = 48


def _points(width: int, height: int, polygon: list[tuple[float, float]]) -> np.ndarray:
    return np.array(
        [(round(x * width), round(y * height)) for x, y in polygon],
        dtype=np.int32,
    )


def fill_polygons(
    shape: tuple[int, int],
    polygons: list[list[tuple[float, float]]],
    value: int = 255,
) -> np.ndarray:
    height, width = shape
    mask = np.zeros((height, width), np.uint8)
    for polygon in polygons:
        cv2.fillPoly(mask, [_points(width, height, polygon)], value)
    return mask


def flat_specs() -> dict[str, dict[str, list[list[tuple[float, float]]]]]:
    # Coordinates are normalized to the source photo. The masks are intentionally
    # product-shaped rather than rectangular so the final image reads as a clean
    # catalog flat image on white, like example.png.
    return {
        "1": {
            "keep": [
                [
                    (0.245, 0.035),
                    (0.760, 0.035),
                    (0.782, 0.220),
                    (0.778, 0.910),
                    (0.748, 0.968),
                    (0.680, 0.988),
                    (0.555, 0.990),
                    (0.505, 0.972),
                    (0.485, 0.994),
                    (0.365, 0.985),
                    (0.268, 0.950),
                    (0.225, 0.225),
                ],
            ],
            "repair": [
                [(0.377, 0.000), (0.440, 0.000), (0.440, 0.100), (0.377, 0.100)],
                [(0.655, 0.000), (0.720, 0.000), (0.720, 0.100), (0.655, 0.100)],
                [(0.760, 0.065), (0.805, 0.065), (0.805, 0.430), (0.760, 0.430)],
            ],
        },
        "2": {
            "keep": [
                [
                    (0.250, 0.035),
                    (0.762, 0.035),
                    (0.785, 0.230),
                    (0.775, 0.930),
                    (0.720, 0.975),
                    (0.602, 0.990),
                    (0.515, 0.972),
                    (0.472, 0.990),
                    (0.355, 0.976),
                    (0.260, 0.942),
                    (0.225, 0.250),
                ],
            ],
            "repair": [
                [(0.360, 0.000), (0.425, 0.000), (0.425, 0.100), (0.360, 0.100)],
                [(0.665, 0.000), (0.735, 0.000), (0.735, 0.100), (0.665, 0.100)],
            ],
        },
        "3": {
            "keep": [
                [
                    (0.118, 0.025),
                    (0.760, 0.025),
                    (0.775, 0.220),
                    (0.750, 0.932),
                    (0.694, 0.982),
                    (0.585, 0.990),
                    (0.505, 0.970),
                    (0.460, 0.993),
                    (0.330, 0.985),
                    (0.210, 0.947),
                    (0.108, 0.245),
                ],
            ],
            "repair": [
                [(0.318, 0.000), (0.395, 0.000), (0.395, 0.130), (0.318, 0.130)],
                [(0.690, 0.000), (0.763, 0.000), (0.763, 0.135), (0.690, 0.135)],
            ],
        },
        "4": {
            "keep": [
                [
                    (0.238, 0.050),
                    (0.777, 0.050),
                    (0.798, 0.245),
                    (0.775, 0.948),
                    (0.712, 0.982),
                    (0.592, 0.990),
                    (0.516, 0.972),
                    (0.470, 0.990),
                    (0.345, 0.978),
                    (0.252, 0.940),
                    (0.220, 0.245),
                ],
            ],
            "repair": [
                [(0.392, 0.000), (0.462, 0.000), (0.462, 0.120), (0.392, 0.120)],
                [(0.676, 0.000), (0.742, 0.000), (0.742, 0.120), (0.676, 0.120)],
                [(0.665, 0.190), (0.708, 0.190), (0.708, 0.328), (0.665, 0.328)],
            ],
        },
        "5": {
            "keep": [
                [
                    (0.330, 0.130),
                    (0.670, 0.130),
                    (0.715, 0.300),
                    (0.725, 0.820),
                    (0.680, 0.948),
                    (0.500, 0.970),
                    (0.320, 0.948),
                    (0.275, 0.820),
                    (0.285, 0.300),
                ],
                [
                    (0.300, 0.185),
                    (0.135, 0.260),
                    (0.112, 0.875),
                    (0.145, 0.960),
                    (0.220, 0.943),
                    (0.275, 0.458),
                    (0.345, 0.360),
                ],
                [
                    (0.700, 0.185),
                    (0.890, 0.240),
                    (0.890, 0.875),
                    (0.848, 0.952),
                    (0.770, 0.943),
                    (0.725, 0.458),
                    (0.655, 0.360),
                ],
            ],
            "repair": [
                [(0.425, 0.000), (0.580, 0.000), (0.580, 0.185), (0.425, 0.185)],
            ],
        },
        "6": {
            "keep": [
                [
                    (0.250, 0.125),
                    (0.750, 0.125),
                    (0.800, 0.300),
                    (0.765, 0.875),
                    (0.640, 0.905),
                    (0.500, 0.918),
                    (0.360, 0.905),
                    (0.235, 0.875),
                    (0.200, 0.300),
                ],
                [
                    (0.185, 0.185),
                    (0.072, 0.260),
                    (0.085, 0.908),
                    (0.150, 0.965),
                    (0.245, 0.920),
                    (0.285, 0.420),
                    (0.330, 0.260),
                ],
                [
                    (0.815, 0.185),
                    (0.928, 0.255),
                    (0.912, 0.908),
                    (0.850, 0.958),
                    (0.742, 0.914),
                    (0.715, 0.420),
                    (0.670, 0.260),
                ],
            ],
            "repair": [
                [(0.425, 0.000), (0.575, 0.000), (0.575, 0.205), (0.425, 0.205)],
                [(0.486, 0.135), (0.520, 0.135), (0.520, 0.468), (0.486, 0.468)],
                [(0.482, 0.445), (0.536, 0.445), (0.536, 0.505), (0.482, 0.505)],
                [(0.790, 0.792), (0.860, 0.792), (0.860, 0.948), (0.790, 0.948)],
            ],
        },
        "7": {
            "keep": [
                [
                    (0.176, 0.122),
                    (0.822, 0.122),
                    (0.862, 0.255),
                    (0.815, 0.510),
                    (0.500, 0.560),
                    (0.185, 0.510),
                    (0.138, 0.255),
                ],
                [
                    (0.160, 0.430),
                    (0.500, 0.430),
                    (0.500, 0.958),
                    (0.310, 0.982),
                    (0.195, 0.985),
                    (0.138, 0.905),
                ],
                [
                    (0.500, 0.430),
                    (0.840, 0.430),
                    (0.862, 0.905),
                    (0.805, 0.985),
                    (0.690, 0.960),
                    (0.500, 0.958),
                ],
            ],
            "repair": [
                [(0.305, 0.000), (0.380, 0.000), (0.380, 0.170), (0.305, 0.170)],
                [(0.725, 0.000), (0.795, 0.000), (0.795, 0.170), (0.725, 0.170)],
            ],
        },
        "8": {
            "keep": [
                [
                    (0.220, 0.035),
                    (0.770, 0.035),
                    (0.790, 0.235),
                    (0.785, 0.932),
                    (0.728, 0.975),
                    (0.608, 0.988),
                    (0.525, 0.972),
                    (0.475, 0.990),
                    (0.345, 0.980),
                    (0.245, 0.942),
                    (0.205, 0.242),
                ],
            ],
            "repair": [
                [(0.292, 0.000), (0.365, 0.000), (0.365, 0.120), (0.292, 0.120)],
                [(0.665, 0.000), (0.735, 0.000), (0.735, 0.120), (0.665, 0.120)],
            ],
        },
    }


def edge_refine(image: np.ndarray, mask: np.ndarray, name: str) -> np.ndarray:
    if name in {"3", "5", "6", "7"}:
        return mask

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    orange = (h >= 5) & (h <= 24) & (s > 35) & (v > 80)
    wall = (s < 25) & (v > 152)
    dark_or_colored = (v < 130) | ((s > 18) & (v < 215) & (~orange))
    if name in {"3", "7"}:
        dark_or_colored |= (h >= 28) & (h <= 95) & (s > 8) & (v < 220)
    if name in {"4"}:
        dark_or_colored |= (h >= 80) & (h <= 135) & (s > 16) & (v < 225)

    refined = ((mask > 0) & dark_or_colored & (~wall) & (~orange)).astype(np.uint8) * 255
    refined = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
    refined = cv2.morphologyEx(refined, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(refined, 8)
    keep = np.zeros_like(refined)
    min_area = refined.shape[0] * refined.shape[1] * 0.002
    for idx in range(1, count):
        area = stats[idx, cv2.CC_STAT_AREA]
        x, y, w, hgt = stats[idx, :4]
        if area > min_area or (hgt > refined.shape[0] * 0.25 and w > refined.shape[1] * 0.025):
            keep[labels == idx] = 255

    # Use the manual mask as a safety net for real fabric areas that are too
    # close to the wall color, but reject the obvious top orange display cloth.
    safety = ((mask > 0) & (~orange) & (~wall)).astype(np.uint8) * 255
    keep = cv2.bitwise_or(keep, cv2.erode(safety, np.ones((5, 5), np.uint8)))
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
    return keep_main_components(keep)


def keep_main_components(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return mask

    image_area = mask.shape[0] * mask.shape[1]
    component_ids = list(range(1, count))
    component_ids.sort(key=lambda idx: stats[idx, cv2.CC_STAT_AREA], reverse=True)
    largest = component_ids[0]
    lx, ly, lw, lh = stats[largest, :4]
    largest_box = (lx, ly, lx + lw, ly + lh)

    cleaned = np.zeros_like(mask)
    for idx in component_ids:
        area = stats[idx, cv2.CC_STAT_AREA]
        x, y, w, h = stats[idx, :4]
        cx, cy = centroids[idx]
        intersects_largest = not (
            x + w < largest_box[0] - 20
            or x > largest_box[2] + 20
            or y + h < largest_box[1] - 20
            or y > largest_box[3] + 20
        )
        centered = 0.18 * mask.shape[1] <= cx <= 0.82 * mask.shape[1]
        if idx == largest or (area > image_area * 0.0015 and intersects_largest and centered):
            cleaned[labels == idx] = 255
    return cleaned


def make_alpha(mask: np.ndarray) -> np.ndarray:
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.1)


def remove_overlays(image: np.ndarray, repair_mask: np.ndarray) -> np.ndarray:
    if not np.any(repair_mask):
        return image
    repair_mask = cv2.dilate(repair_mask, np.ones((9, 9), np.uint8))
    return cv2.inpaint(image, repair_mask, 5, cv2.INPAINT_TELEA)


def compose(image: np.ndarray, alpha: np.ndarray) -> Image.Image:
    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        raise RuntimeError("No foreground mask found")

    x0, x1 = max(0, xs.min() - 8), min(image.shape[1], xs.max() + 9)
    y0, y1 = max(0, ys.min() - 8), min(image.shape[0], ys.max() + 9)
    crop = image[y0:y1, x0:x1]
    crop_alpha = alpha[y0:y1, x0:x1]

    max_content = OUTPUT_SIZE - MARGIN * 2
    scale = min(max_content / crop.shape[1], max_content / crop.shape[0])
    out_w = max(1, round(crop.shape[1] * scale))
    out_h = max(1, round(crop.shape[0] * scale))

    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    crop_alpha = cv2.resize(crop_alpha, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    a = np.clip(crop_alpha / 255.0, 0.0, 1.0)[..., None]
    comp = (rgb.astype(np.float32) * a + 255.0 * (1.0 - a)).clip(0, 255).astype(np.uint8)

    canvas = np.full((OUTPUT_SIZE, OUTPUT_SIZE, 3), 255, np.uint8)
    x = (OUTPUT_SIZE - out_w) // 2
    y = (OUTPUT_SIZE - out_h) // 2
    canvas[y : y + out_h, x : x + out_w] = comp
    return Image.fromarray(canvas, mode="RGB")


def process_one(path: Path, output_dir: Path, debug_dir: Path | None) -> Path:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Cannot read {path}")

    spec = flat_specs().get(path.stem)
    if spec is None:
        raise RuntimeError(f"No flat mask spec for {path.name}")

    height, width = image.shape[:2]
    mask = fill_polygons((height, width), spec["keep"])
    repair_mask = fill_polygons((height, width), spec.get("repair", []))
    repaired = remove_overlays(image, repair_mask)
    refined = edge_refine(repaired, mask, path.stem)
    alpha = make_alpha(refined)
    result = compose(repaired, alpha)

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{path.stem}.png"
    result.save(out_path, format="PNG", optimize=True)

    if debug_dir is not None:
        debug_dir.mkdir(parents=True, exist_ok=True)
        preview = np.full_like(repaired, 255)
        preview[alpha > 8] = repaired[alpha > 8]
        Image.fromarray(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)).save(
            debug_dir / f"{path.stem}_mask_preview.jpg",
            quality=92,
        )
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("flat_800_final"))
    parser.add_argument("--debug-dir", type=Path, default=None)
    args = parser.parse_args()

    paths = sorted(
        args.input_dir.glob("*.jpg"),
        key=lambda item: int(item.stem) if item.stem.isdigit() else item.stem,
    )
    if not paths:
        raise SystemExit("No JPG images found")

    for path in paths:
        print(process_one(path, args.output_dir, args.debug_dir))


if __name__ == "__main__":
    main()
