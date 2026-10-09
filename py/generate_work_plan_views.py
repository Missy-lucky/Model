from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile, ImageOps
from pillow_heif import register_heif_opener


register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

OUTPUT_SIZE = 1536
PRESERVED_STEMS = {str(i) for i in range(1, 9)}
SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
CLI = Path(r"C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py")
REFERENCE = Path(r"C:\Users\ZORN\OneDrive\桌面\Model\example_library\plan-view.png")
PROMPT = (
    "Use the exact clothing item from Image 1 as the subject. Use Image 2 only as the "
        "plan-view style and composition reference. Convert the clothing into a clean catalog "
    "plan-view garment image: laid perfectly flat, centered and symmetric, straight-on top "
    "view, with its natural silhouette and sleeves or panels arranged naturally outward. "
    "If Image 1 contains a multi-piece set, include every piece separately and completely "
    "in one large composition, choosing the clearest layout for detail inspection; do not "
    "merge, redesign, omit, or simplify any piece. Preserve the exact garment count, fit, "
    "length, silhouette, color, fabric, sheen, texture, seams, topstitching, waistband, "
    "fly, belt loops, pleats, pockets, cuffs, closures, labels and trim. Trousers must "
    "exactly match the source: keep the original rise, leg width, taper, break, hem, "
    "pocket placement and all seams. Remove the person, mannequin, hanger, floor, wall, "
    "background, cast shadows, hanging wrinkles and all text. Place the complete garment "
    "or set on a pure white background in an exact square, matching the clean presentation "
    "and framing of Image 2. The complete garment must fit inside the frame with a clean "
    "white margin of at least 4 percent on all four sides and must never touch or be cut "
    "off by an edge. Do not invent a different garment and do not add labels."
)

print_lock = threading.Lock()
file_lock = threading.Lock()


@dataclass(frozen=True)
class Item:
    number: int
    path: Path
    digest: str


def natural_key(path: Path) -> tuple:
    parts: list[object] = []
    for part in __import__("re").split(r"(\d+)", path.name):
        parts.append(int(part) if part.isdigit() else part.lower())
    return tuple(parts)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_items(source_dir: Path) -> list[Item]:
    files = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS
    ]
    preserved = sorted(
        (path for path in files if path.stem in PRESERVED_STEMS),
        key=lambda path: int(path.stem),
    )
    if [path.stem for path in preserved] != [str(i) for i in range(1, 9)]:
        raise RuntimeError("Expected preserved source files named exactly 1 through 8")

    others = sorted(
        (path for path in files if path.stem not in PRESERVED_STEMS),
        key=lambda path: (path.stat().st_mtime, natural_key(path)),
    )
    return [
        Item(number, path, sha256(path))
        for number, path in enumerate(preserved + others, start=1)
        if number > 8
    ]


def write_mapping(source_dir: Path, items: list[Item], groups: dict[str, list[Item]]) -> None:
    mapping = source_dir / "plan_view_mapping.csv"
    with mapping.open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.writer(target)
        writer.writerow(["number", "original_name", "new_name", "output_name", "sha256"])
        for item in items:
            writer.writerow(
                [
                    item.number,
                    item.path.name,
                    f"{item.number}{item.path.suffix.lower()}",
                    f"{item.number}.png",
                    item.digest,
                ]
            )

    report = {
        "source_files_after_first_8": len(items),
        "unique_images_to_generate": len(
            {digest for digest, group in groups.items() if min(x.number for x in group) > 8}
        ),
        "duplicate_source_files": len(items)
        - len({digest for digest, group in groups.items() if min(x.number for x in group) > 8}),
        "output_size": OUTPUT_SIZE,
        "reference": str(REFERENCE),
        "model_requested": "gpt-image-2.5",
    }
    (source_dir / "plan_view_batch_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def prepare_upload(item: Item, cache_dir: Path) -> Path:
    upload = cache_dir / f"{item.number}.jpg"
    if upload.exists():
        return upload

    image = Image.open(item.path)
    image.load()
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
    image.save(upload, format="JPEG", quality=96, optimize=True)
    return upload


def inspect_image(path: Path) -> dict[str, float | int | bool]:
    image = Image.open(path)
    image.load()
    rgb = np.asarray(image.convert("RGB")).astype(np.int16)
    border = np.concatenate([rgb[0, :], rgb[-1, :], rgb[:, 0], rgb[:, -1]], axis=0)
    foreground = np.max(np.abs(rgb - 255), axis=2) > 25
    ys, xs = np.where(foreground)
    border_white = float(np.mean(np.min(border, axis=1) >= 242))
    coverage = float(foreground.mean())

    valid_bounds = bool(
        len(xs) > 0
        and xs.min() >= 16
        and ys.min() >= 16
        and xs.max() <= OUTPUT_SIZE - 17
        and ys.max() <= OUTPUT_SIZE - 17
    )
    return {
        "width": image.width,
        "height": image.height,
        "border_white": border_white,
        "coverage": coverage,
        "content_width": int(xs.max() - xs.min() + 1) if len(xs) else 0,
        "content_height": int(ys.max() - ys.min() + 1) if len(ys) else 0,
        "passed": bool(
            image.width == OUTPUT_SIZE
            and image.height == OUTPUT_SIZE
            and border_white >= 0.97
            and 0.08 <= coverage <= 0.88
            and valid_bounds
        ),
    }


def normalize_output(path: Path) -> None:
    image = Image.open(path)
    image.load()
    image = image.convert("RGB")
    if image.size != (OUTPUT_SIZE, OUTPUT_SIZE):
        image = image.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)
    image.save(path, format="PNG", optimize=True)


def run_generation(item: Item, output_dir: Path, cache_dir: Path, retries: int) -> Path:
    upload = prepare_upload(item, cache_dir)
    temporary = cache_dir / f"{item.number}.pending.png"
    command = [
        "python",
        str(CLI),
        "edit",
        "--image",
        str(upload),
        "--image",
        str(REFERENCE),
        "--prompt",
        PROMPT,
        "--size",
        f"{OUTPUT_SIZE}x{OUTPUT_SIZE}",
        "--quality",
        "high",
        "--output-format",
        "png",
        "--output",
        str(temporary),
    ]

    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            result = subprocess.run(
                command,
                cwd=str(Path.cwd()),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=360,
                check=False,
            )
            if result.returncode == 0 and temporary.exists():
                normalize_output(temporary)
                metrics = inspect_image(temporary)
                if metrics["passed"]:
                    final = output_dir / f"{item.number}.png"
                    with file_lock:
                        if final.exists():
                            temporary.unlink(missing_ok=True)
                        else:
                            temporary.replace(final)
                    upload.unlink(missing_ok=True)
                    return final
                last_error = f"QC failed: {metrics}"
                temporary.unlink(missing_ok=True)
            else:
                last_error = (result.stderr or result.stdout or "unknown error").strip()[-1200:]
                temporary.unlink(missing_ok=True)
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            temporary.unlink(missing_ok=True)

        if attempt < retries:
            time.sleep(min(90, 15 * attempt))

    raise RuntimeError(last_error or "generation failed")


def rename_sources(source_dir: Path, items: list[Item]) -> None:
    temporary: list[tuple[Path, Path]] = []
    for item in items:
        final_path = source_dir / f"{item.number}{item.path.suffix.lower()}"
        if item.path == final_path:
            continue
        temporary_path = source_dir / f"__planview_tmp_{item.number}_{item.digest[:12]}{item.path.suffix.lower()}"
        item.path.rename(temporary_path)
        temporary.append((temporary_path, final_path))

    for temporary_path, final_path in temporary:
        if final_path.exists():
            raise RuntimeError(f"Refusing to overwrite {final_path}")
        temporary_path.rename(final_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("work_library"))
    parser.add_argument("--output-dir", type=Path, default=Path("work_library_plan_view"))
    parser.add_argument("--cache-dir", type=Path, default=Path("plan_view_upload_cache"))
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--only", type=int, default=0)
    parser.add_argument("--rename", action="store_true")
    args = parser.parse_args()

    if not CLI.exists():
        raise SystemExit(f"Missing OpenRouter CLI: {CLI}")
    if not REFERENCE.exists():
        raise SystemExit(f"Missing reference image: {REFERENCE}")
    if not shutil.which("python"):
        raise SystemExit("Python was not found in PATH")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    items = collect_items(args.source_dir.resolve())
    all_groups: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        all_groups[item.digest].append(item)
    for group in all_groups.values():
        group.sort(key=lambda entry: entry.number)

    groups = {
        digest: group
        for digest, group in all_groups.items()
        if group[0].number > 8
    }
    write_mapping(args.source_dir.resolve(), items, all_groups)
    tasks = [group[0] for group in groups.values() if not (args.output_dir / f"{group[0].number}.png").exists()]
    tasks.sort(key=lambda item: item.number)
    if args.only:
        tasks = [item for item in tasks if item.number == args.only]

    # Seeded or previously completed primaries must propagate to exact duplicates.
    for group in groups.values():
        primary_output = args.output_dir / f"{group[0].number}.png"
        if primary_output.exists():
            for duplicate in group[1:]:
                duplicate_output = args.output_dir / f"{duplicate.number}.png"
                if not duplicate_output.exists():
                    duplicate_output.write_bytes(primary_output.read_bytes())

    if args.limit:
        tasks = tasks[: args.limit]

    print(
        f"sources={len(items)} unique={len(groups)} pending={len(tasks)} workers={args.workers}",
        flush=True,
    )
    failures: list[tuple[int, str]] = []
    started = time.time()

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(run_generation, item, args.output_dir, args.cache_dir, args.retries): item
            for item in tasks
        }
        for index, future in enumerate(as_completed(futures), start=1):
            item = futures[future]
            try:
                output = future.result()
                with file_lock:
                    duplicates = all_groups[item.digest]
                    for duplicate in duplicates[1:]:
                        target = args.output_dir / f"{duplicate.number}.png"
                        if not target.exists():
                            target.write_bytes(output.read_bytes())
                message = f"[{index:03d}/{len(tasks):03d}] {output.name} OK elapsed={time.time()-started:.1f}s"
            except Exception as exc:
                failures.append((item.number, str(exc)))
                message = f"[{index:03d}/{len(tasks):03d}] {item.number} FAILED: {exc}"
            with print_lock:
                print(message, flush=True)

    missing = [
        item.number
        for item in items
        if not (args.output_dir / f"{item.number}.png").exists()
    ]
    if failures or (missing and not args.allow_partial):
        detail = json.dumps(
            {"failures": [{"number": number, "error": error} for number, error in failures], "missing": missing},
            ensure_ascii=False,
            indent=2,
        )
        (args.output_dir / "generation_failures.json").write_text(detail, encoding="utf-8")
        raise RuntimeError(f"Batch finished with failures={len(failures)} missing={len(missing)}")

    if args.allow_partial and missing:
        print(f"PARTIAL DONE outputs={len(items)-len(missing)}/{len(items)} pending={len(missing)}", flush=True)
        return

    if args.rename:
        rename_sources(args.source_dir.resolve(), items)
    print(f"DONE outputs={len(items)} rename={args.rename}", flush=True)


if __name__ == "__main__":
    main()
