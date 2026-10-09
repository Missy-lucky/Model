from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from PIL import ImageFile
from pillow_heif import register_heif_opener
from rembg import new_session, remove


register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

OUTPUT_SIZE = 800
MARGIN = 48
MAX_SOURCE_EDGE = 1200
SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
PRESERVED_STEMS = {str(i) for i in range(1, 9)}


@dataclass(frozen=True)
class SourceItem:
    path: Path
    number: int
    digest: str


def natural_key(path: Path) -> tuple:
    parts = [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]
    return tuple(parts)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assign_numbers(source_dir: Path) -> list[SourceItem]:
    files = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS
    ]

    preserved = sorted(
        (path for path in files if path.stem in PRESERVED_STEMS),
        key=lambda path: int(path.stem),
    )
    if [path.stem for path in preserved] != [str(i) for i in range(1, len(preserved) + 1)]:
        raise RuntimeError("Expected the preserved files to be named 1 through 8")

    others = sorted(
        (path for path in files if path.stem not in PRESERVED_STEMS),
        key=lambda path: (path.stat().st_mtime, natural_key(path)),
    )
    items = [
        SourceItem(path, number, sha256(path))
        for number, path in enumerate(preserved + others, start=1)
    ]

    numbers = [item.number for item in items]
    if len(numbers) != len(set(numbers)):
        raise RuntimeError("Number assignment produced duplicates")
    return items


def load_rgb(path: Path) -> Image.Image:
    image = Image.open(path)
    image.load()
    return image.convert("RGB")


def clean_alpha(alpha: np.ndarray) -> np.ndarray:
    mask = (alpha > 8).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if count <= 1:
        return mask * 255

    image_area = mask.shape[0] * mask.shape[1]
    component_ids = list(range(1, count))
    component_ids.sort(key=lambda idx: stats[idx, cv2.CC_STAT_AREA], reverse=True)
    keep = np.zeros_like(mask)

    for idx in component_ids:
        area = int(stats[idx, cv2.CC_STAT_AREA])
        if area < image_area * 0.001:
            continue
        if idx == component_ids[0] or area >= image_area * 0.01:
            keep[labels == idx] = 1

    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    alpha = cv2.GaussianBlur((keep * 255).astype(np.float32), (0, 0), 1.0)
    return np.clip(alpha, 0, 255).astype(np.uint8)


def compose_on_white(image: Image.Image, cutout: Image.Image) -> Image.Image:
    rgb = np.asarray(image, dtype=np.uint8)
    alpha = np.asarray(cutout.getchannel("A"), dtype=np.uint8)
    alpha = clean_alpha(alpha)

    ys, xs = np.where(alpha > 8)
    if len(xs) == 0:
        raise RuntimeError("No foreground found")

    x0, x1 = max(0, int(xs.min()) - 3), min(rgb.shape[1], int(xs.max()) + 4)
    y0, y1 = max(0, int(ys.min()) - 3), min(rgb.shape[0], int(ys.max()) + 4)
    crop = rgb[y0:y1, x0:x1]
    crop_alpha = alpha[y0:y1, x0:x1]

    content_size = OUTPUT_SIZE - MARGIN * 2
    scale = min(content_size / crop.shape[1], content_size / crop.shape[0])
    out_w = max(1, round(crop.shape[1] * scale))
    out_h = max(1, round(crop.shape[0] * scale))

    resized_rgb = cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    resized_alpha = cv2.resize(crop_alpha, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    opacity = (resized_alpha.astype(np.float32) / 255.0)[..., None]
    composited = (
        resized_rgb.astype(np.float32) * opacity + 255.0 * (1.0 - opacity)
    ).clip(0, 255).astype(np.uint8)

    canvas = np.full((OUTPUT_SIZE, OUTPUT_SIZE, 3), 255, np.uint8)
    left = (OUTPUT_SIZE - out_w) // 2
    top = (OUTPUT_SIZE - out_h) // 2
    canvas[top : top + out_h, left : left + out_w] = composited
    return Image.fromarray(canvas, mode="RGB")


def inspect_output(path: Path, legacy: bool = False) -> dict[str, float | int | bool]:
    image = Image.open(path)
    image.load()
    array = np.asarray(image.convert("RGB")).astype(np.int16)
    border = np.concatenate(
        [array[0, :], array[-1, :], array[:, 0], array[:, -1]], axis=0
    )
    foreground = np.max(np.abs(array - 255), axis=2) > 35
    ys, xs = np.where(foreground)
    return {
        "width": image.width,
        "height": image.height,
        "border_white": float(np.mean(np.min(border, axis=1) >= 248)),
        "coverage": float(foreground.mean()),
        "content_width": int(xs.max() - xs.min() + 1) if len(xs) else 0,
        "content_height": int(ys.max() - ys.min() + 1) if len(ys) else 0,
        "passed": bool(
            image.width == OUTPUT_SIZE
            and image.height == OUTPUT_SIZE
            and (
                legacy
                or (
                    np.mean(np.min(border, axis=1) >= 248) >= 0.995
                    and 0.05 <= foreground.mean() <= 0.88
                    and len(xs) > 0
                    and xs.min() >= 30
                    and ys.min() >= 30
                    and xs.max() <= OUTPUT_SIZE - 31
                    and ys.max() <= OUTPUT_SIZE - 31
                )
            )
        ),
    }


def write_manifest(source_dir: Path, items: list[SourceItem], output_dir: Path) -> None:
    manifest = source_dir / "renaming_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.writer(target)
        writer.writerow(["number", "original_name", "new_name", "output_name", "sha256"])
        for item in items:
            suffix = item.path.suffix.lower()
            writer.writerow(
                [
                    item.number,
                    item.path.name,
                    f"{item.number}{suffix}",
                    f"{item.number}.png",
                    item.digest,
                ]
            )

    report = {
        "source_count": len(items),
        "unique_images": len({item.digest for item in items}),
        "output_dir": str(output_dir),
        "reference_style": "example_library/plan-view.png",
        "output_size": OUTPUT_SIZE,
        "source_margin_px": MARGIN,
    }
    (source_dir / "processing_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def rename_sources(source_dir: Path, items: list[SourceItem]) -> None:
    temporary: list[tuple[Path, Path]] = []
    for index, item in enumerate(items, start=1):
        if item.path.stem == str(item.number):
            continue
        suffix = item.path.suffix.lower()
        temporary_path = source_dir / f"__renaming_tmp_{index}_{item.digest[:12]}{suffix}"
        item.path.rename(temporary_path)
        temporary.append((temporary_path, source_dir / f"{item.number}{suffix}"))

    for temporary_path, final_path in temporary:
        if final_path.exists():
            raise RuntimeError(f"Refusing to overwrite {final_path}")
        temporary_path.rename(final_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("work_library"))
    parser.add_argument("--output-dir", type=Path, default=Path("work_library_plan_view"))
    parser.add_argument("--existing-1-8", type=Path, default=Path("generated_800"))
    parser.add_argument("--rename", action="store_true")
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    items = assign_numbers(source_dir)
    write_manifest(source_dir, items, output_dir)

    by_digest: dict[str, list[SourceItem]] = defaultdict(list)
    for item in items:
        by_digest[item.digest].append(item)
    for group in by_digest.values():
        group.sort(key=lambda item: item.number)

    session = new_session("u2net")
    qc_rows: list[dict[str, str | int | float | bool]] = []
    started = time.time()

    for index, (digest, group) in enumerate(sorted(by_digest.items()), start=1):
        primary = group[0]
        primary_output = output_dir / f"{primary.number}.png"
        if not primary_output.exists():
            if primary.number <= 8 and (args.existing_1_8 / f"{primary.number}.png").exists():
                Image.open(args.existing_1_8 / f"{primary.number}.png").save(primary_output)
            else:
                source = load_rgb(primary.path)
                source.thumbnail((MAX_SOURCE_EDGE, MAX_SOURCE_EDGE), Image.Resampling.LANCZOS)
                cutout = remove(source, session=session, post_process_mask=True)
                compose_on_white(source, cutout).save(primary_output, format="PNG", optimize=True)

        for item in group[1:]:
            duplicate_output = output_dir / f"{item.number}.png"
            if not duplicate_output.exists():
                duplicate_output.write_bytes(primary_output.read_bytes())

        try:
            metrics = inspect_output(primary_output, legacy=primary.number <= 8)
        except Exception as exc:
            metrics = {
                "width": 0,
                "height": 0,
                "border_white": 0.0,
                "coverage": 0.0,
                "content_width": 0,
                "content_height": 0,
                "passed": False,
            }
            print(f"[ERROR] QC failed for {primary.path.name}: {exc}", flush=True)

        qc_rows.append(
            {
                "number": primary.number,
                "representative": primary.path.name,
                "output_count": len(group),
                **metrics,
            }
        )
        elapsed = time.time() - started
        print(
            f"[{index:03d}/{len(by_digest):03d}] {primary_output.name} "
            f"coverage={metrics['coverage']:.3f} qc={metrics['passed']} elapsed={elapsed:.1f}s",
            flush=True,
        )

    with (output_dir / "qc_report.csv").open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.DictWriter(target, fieldnames=list(qc_rows[0]))
        writer.writeheader()
        writer.writerows(qc_rows)

    missing = [
        item.number
        for item in items
        if not (output_dir / f"{item.number}.png").exists()
    ]
    if missing:
        raise RuntimeError(f"Missing outputs for numbers: {missing[:20]}")

    if args.rename:
        rename_sources(source_dir, items)

    failed = [row for row in qc_rows if not row["passed"]]
    print(
        f"DONE files={len(items)} unique={len(by_digest)} outputs={len(items)} "
        f"qc_failed={len(failed)} rename={args.rename}",
        flush=True,
    )
    if failed:
        print("QC_FAILED_NUMBERS=" + ",".join(str(row["number"]) for row in failed), flush=True)


if __name__ == "__main__":
    main()
