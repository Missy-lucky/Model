from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFile, ImageDraw, ImageOps
from pillow_heif import register_heif_opener


register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

SIZE = 1536
CLI = Path(r"C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py")
REFERENCE = Path(r"C:\Users\ZORN\OneDrive\桌面\Model\example_library\plan-view.png")
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif"}
BASE_PROMPT = (
    "Image 1 is the authoritative original clothing. Image 2 is only a plan-view style and "
    "composition reference; never copy the garment shown in Image 2. Convert the actual "
    "clothing from Image 1 into a realistic catalog plan-view flat-lay. If Image 1 contains "
    "a multi-piece set, lay every piece separately and completely in one balanced square "
    "composition. The garment must look physically spread flat with natural soft volume, "
    "viewed straight from above, symmetric and uncropped. Preserve garment type, silhouette, "
    "length, proportions, color, fabric, closures, pockets, seams and stitching. Remove only "
    "the person, mannequin, hanger, background, floor, wall, cast shadows and text. Pure "
    "white background with generous margins. No cartoon, vector, technical drawing, collage, "
    "comparison panel, labels or reference thumbnail."
)
RETOUCH_PROMPT = (
    "Retouch Image 1 only. Image 1 is the approved flat-lay base and must define the final "
    "composition: keep its exact garment placement, silhouette, proportions, soft flattened "
    "feel, volume, camera angle, spacing, white background and margins. Do not rearrange, "
    "resize, redraw, reframe or replace the garments. Image 2 is the original photo. Image 3 "
    "is a high-resolution detail evidence grid from the same photo; it is not a layout to "
    "copy. Use Images 2 and 3 only to correct construction details already present in Image 1. "
    "Restore every visible button, buttonhole, inner lining, collar, front opening, pocket, "
    "seam, topstitching, waistband, fly, belt loop, cuff and hem exactly. When trousers have "
    "parallel waist stitching lines, preserve both lines. Blend corrections into Image 1's "
    "existing flat-lay lighting and fabric volume. Everything else from Image 1 remains "
    "unchanged. No text, labels, collage, thumbnails, extra panels or new garments."
)

print_lock = threading.Lock()
file_lock = threading.Lock()


@dataclass(frozen=True)
class Item:
    number: int
    path: Path
    digest: str


def natural_key(path: Path) -> tuple[object, ...]:
    return tuple(int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", path.name))


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def collect(source_dir: Path) -> list[Item]:
    files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS]
    preserved = sorted((p for p in files if p.stem in {str(i) for i in range(1, 9)}), key=lambda p: int(p.stem))
    if [p.stem for p in preserved] != [str(i) for i in range(1, 9)]:
        raise RuntimeError("Expected preserved files 1 through 8")
    others = sorted(
        (p for p in files if p.stem not in {str(i) for i in range(1, 9)}),
        key=lambda p: (p.stat().st_mtime, natural_key(p)),
    )
    return [Item(n, p, digest(p)) for n, p in enumerate(preserved + others, 1) if n > 8]


def mapping_path(source_dir: Path) -> Path:
    return source_dir / "final_plan_view_mapping.csv"


def write_mapping(source_dir: Path, items: list[Item], groups: dict[str, list[Item]]) -> None:
    with mapping_path(source_dir).open("w", newline="", encoding="utf-8-sig") as target:
        writer = csv.writer(target)
        writer.writerow(["number", "original_name", "new_name", "output_name", "sha256"])
        for item in items:
            writer.writerow([item.number, item.path.name, f"{item.number}{item.path.suffix.lower()}", f"{item.number}.png", item.digest])
    report = {
        "source_files_after_first_8": len(items),
        "unique_representatives": len(groups),
        "duplicate_sources": len(items) - len(groups),
        "pipeline": ["flat-lay base", "detail-preserving retouch"],
        "output_size": SIZE,
    }
    (source_dir / "final_plan_view_batch_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def prepare_upload(item: Item, cache: Path) -> Path:
    output = cache / f"{item.number}-upload.jpg"
    if not output.exists():
        image = ImageOps.exif_transpose(Image.open(item.path)).convert("RGB")
        image.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        image.save(output, format="JPEG", quality=96, optimize=True)
    return output


def prepare_evidence(item: Item, upload: Path, cache: Path) -> Path:
    output = cache / f"{item.number}-evidence.jpg"
    if output.exists():
        return output
    image = Image.open(upload).convert("RGB")
    width, height = image.size
    cells = [image.copy()]
    thirds = [(0, height // 3), (height // 3, 2 * height // 3), (2 * height // 3, height)]
    for top, bottom in thirds:
        crop = image.crop((0, top, width, bottom))
        crop = crop.resize((1200, max(1, round(1200 * crop.height / crop.width))), Image.Resampling.LANCZOS)
        cells.append(crop)
    cell_w, cell_h = 1120, 860
    sheet = Image.new("RGB", (cell_w * 4 + 100, cell_h * 2 + 110), "white")
    drawer = ImageDraw.Draw(sheet)
    for index, cell in enumerate(cells):
        cell.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = 40 + (index % 4) * (cell_w + 20)
        y = 50 + (index // 4) * (cell_h + 30)
        sheet.paste(cell, (x, y))
        drawer.rectangle((x, y, x + cell.width, y + cell.height), outline=(205, 205, 205), width=2)
        drawer.text((x, y - 25), f"DETAIL {index}", fill=(0, 0, 0))
    sheet.save(output, format="JPEG", quality=96, optimize=True)
    return output


def normalize(path: Path) -> None:
    image = Image.open(path).convert("RGB")
    if image.size != (SIZE, SIZE):
        image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    image.save(path, format="PNG", optimize=True)


def inspect(path: Path) -> dict[str, float | int | bool]:
    image = Image.open(path)
    image.load()
    array = np.asarray(image.convert("RGB")).astype(np.int16)
    border = np.concatenate([array[0, :], array[-1, :], array[:, 0], array[:, -1]], axis=0)
    foreground = np.max(np.abs(array - 255), axis=2) > 25
    ys, xs = np.where(foreground)
    return {
        "width": image.width,
        "height": image.height,
        "border_white": float(np.mean(np.min(border, axis=1) >= 242)),
        "coverage": float(foreground.mean()),
        "passed": bool(
            image.size == (SIZE, SIZE)
            and np.mean(np.min(border, axis=1) >= 242) >= 0.97
            and 0.08 <= foreground.mean() <= 0.88
            and len(xs) > 0
            and xs.min() >= 16
            and ys.min() >= 16
            and xs.max() <= SIZE - 17
            and ys.max() <= SIZE - 17
        ),
    }


def correlation(left: Path, right: Path) -> float:
    a = np.asarray(Image.open(left).convert("L").resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    b = np.asarray(Image.open(right).convert("L").resize((256, 256), Image.Resampling.LANCZOS), dtype=np.float32)
    return float(np.corrcoef(a.ravel(), b.ravel())[0, 1])


def call_edit(images: list[Path], prompt: str, output: Path, retries: int) -> None:
    command = ["python", str(CLI), "edit"]
    for image in images:
        command += ["--image", str(image)]
    command += [
        "--prompt", prompt,
        "--size", f"{SIZE}x{SIZE}",
        "--quality", "high",
        "--output-format", "png",
        "--output", str(output),
    ]
    last_error = ""
    for attempt in range(1, retries + 1):
        result = subprocess.run(command, cwd=str(Path.cwd()), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=420, check=False)
        if result.returncode == 0 and output.exists():
            return
        last_error = (result.stderr or result.stdout or "unknown error").strip()[-1600:]
        output.unlink(missing_ok=True)
        if attempt < retries:
            time.sleep(min(90, 20 * attempt))
    raise RuntimeError(last_error or "image edit failed")


def process(item: Item, output_dir: Path, cache: Path, retries: int, min_correlation: float) -> Path:
    upload = prepare_upload(item, cache)
    evidence = prepare_evidence(item, upload, cache)
    base = cache / f"{item.number}-base.png"
    final = output_dir / f"{item.number}.png"
    last_error = ""

    for attempt in range(1, retries + 1):
        try:
            if not base.exists():
                call_edit([upload, REFERENCE], BASE_PROMPT, base, 1)
                normalize(base)
                metrics = inspect(base)
                if not metrics["passed"]:
                    base.unlink(missing_ok=True)
                    raise RuntimeError(f"base QC failed: {metrics}")

            pending = cache / f"{item.number}-final-pending.png"
            call_edit([base, upload, evidence], RETOUCH_PROMPT, pending, 1)
            normalize(pending)
            metrics = inspect(pending)
            structural = correlation(base, pending)
            if not metrics["passed"] or structural < min_correlation:
                pending.unlink(missing_ok=True)
                raise RuntimeError(f"retouch QC failed: metrics={metrics}, correlation={structural:.4f}")
            with file_lock:
                if final.exists():
                    pending.unlink(missing_ok=True)
                else:
                    pending.replace(final)
            base.unlink(missing_ok=True)
            upload.unlink(missing_ok=True)
            evidence.unlink(missing_ok=True)
            return final
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            base.unlink(missing_ok=True)
            if attempt < retries:
                time.sleep(min(90, 20 * attempt))
    raise RuntimeError(last_error)


def rename_sources(source_dir: Path, items: list[Item]) -> None:
    temporary: list[tuple[Path, Path]] = []
    for item in items:
        final_path = source_dir / f"{item.number}{item.path.suffix.lower()}"
        if item.path == final_path:
            continue
        temporary_path = source_dir / f"__final_tmp_{item.number}_{item.digest[:12]}{item.path.suffix.lower()}"
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
    parser.add_argument("--cache-dir", type=Path, default=Path("final_plan_view_cache"))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--only", type=int, default=0)
    parser.add_argument("--min-correlation", type=float, default=0.975)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--rename", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    items = collect(args.source_dir.resolve())
    groups_all: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        groups_all[item.digest].append(item)
    for group in groups_all.values():
        group.sort(key=lambda entry: entry.number)
    write_mapping(args.source_dir.resolve(), items, groups_all)

    for group in groups_all.values():
        primary = group[0]
        primary_output = args.output_dir / f"{primary.number}.png"
        if primary_output.exists():
            for duplicate in group[1:]:
                duplicate_output = args.output_dir / f"{duplicate.number}.png"
                if not duplicate_output.exists():
                    duplicate_output.write_bytes(primary_output.read_bytes())

    tasks = [group[0] for group in groups_all.values() if not (args.output_dir / f"{group[0].number}.png").exists()]
    tasks.sort(key=lambda entry: entry.number)
    if args.only:
        tasks = [entry for entry in tasks if entry.number == args.only]
    if args.limit:
        tasks = tasks[: args.limit]

    failures: list[dict[str, str | int]] = []
    started = time.time()
    print(f"sources={len(items)} unique={len(groups_all)} pending={len(tasks)} workers={args.workers}", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(process, item, args.output_dir, args.cache_dir, args.retries, args.min_correlation): item for item in tasks}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                output = future.result()
                with file_lock:
                    for duplicate in groups_all[item.digest][1:]:
                        target = args.output_dir / f"{duplicate.number}.png"
                        if not target.exists():
                            target.write_bytes(output.read_bytes())
                message = f"[{index:03d}/{len(tasks):03d}] {output.name} OK elapsed={time.time()-started:.1f}s"
            except Exception as exc:
                failures.append({"number": item.number, "source": item.path.name, "error": str(exc)})
                message = f"[{index:03d}/{len(tasks):03d}] {item.number} FAILED {exc}"
            with print_lock:
                print(message, flush=True)

    missing = [item.number for item in items if not (args.output_dir / f"{item.number}.png").exists()]
    if failures or (missing and not args.allow_partial):
        (args.output_dir / "final_generation_failures.json").write_text(
            json.dumps({"failures": failures, "missing": missing}, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        raise RuntimeError(f"failures={len(failures)} missing={len(missing)}")
    if args.allow_partial and missing:
        print(f"PARTIAL outputs={len(items)-len(missing)}/{len(items)} pending={len(missing)}", flush=True)
        return
    if args.rename:
        rename_sources(args.source_dir.resolve(), items)
    print(f"DONE outputs={len(items)} rename={args.rename}", flush=True)


if __name__ == "__main__":
    main()
