from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFile, ImageOps
from pillow_heif import register_heif_opener


register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_DIR = ROOT / "workflow_products"
RUN_DIR = ROOT / "workflow_runs"
MAPPING_PATH = ROOT / "work_library" / "final_plan_view_mapping.csv"
OPENROUTER_CLI = Path(
    r"C:\Users\ZORN\.codex\skills\openrouter-icu-image\scripts\openrouter_icu_image.py"
)

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_NEEDS_HUMAN = "needs_human"
STATUS_BLOCKED = "blocked"
STATUS_SKIPPED = "skipped"


@dataclass(frozen=True)
class HandlerResult:
    status: str
    message: str = ""
    artifacts: tuple[str, ...] = ()
    data: dict | None = None


@dataclass(frozen=True)
class Node:
    name: str
    title: str
    handler: Callable[[dict, dict, str], HandlerResult]
    requires: tuple[str, ...] = ()
    branch: str = "common"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_image(path: Path) -> Image.Image:
    image = Image.open(path)
    image = ImageOps.exif_transpose(image)
    return image


def product_path(number: int) -> Path:
    return PRODUCT_DIR / str(number) / "product.json"


def run_paths(number: int, recipe: str) -> tuple[Path, Path]:
    base = RUN_DIR / str(number) / recipe
    return base, base / "state.json"


def initialize_state(product: dict, recipe: str, nodes: list[Node]) -> dict:
    return {
        "product_id": product["id"],
        "recipe": recipe,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "nodes": {
            node.name: {
                "title": node.title,
                "branch": node.branch,
                "requires": list(node.requires),
                "status": STATUS_PENDING,
                "message": "",
                "artifacts": [],
                "data": {},
            }
            for node in nodes
        },
    }


def artifact_path(context: dict, name: str) -> Path:
    return context["run_dir"] / name


def image_qc(path: Path, expected_size: int | None = None) -> dict:
    image = Image.open(path)
    image.load()
    array = np.asarray(image.convert("RGB")).astype(np.int16)
    border = np.concatenate(
        [array[0, :], array[-1, :], array[:, 0], array[:, -1]], axis=0
    )
    foreground = np.max(np.abs(array - 255), axis=2) > 25
    ys, xs = np.where(foreground)
    return {
        "width": image.width,
        "height": image.height,
        "border_white": round(float(np.mean(np.min(border, axis=1) >= 242)), 4),
        "foreground_coverage": round(float(foreground.mean()), 4),
        "foreground_bbox": (
            [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            if len(xs)
            else []
        ),
        "size_passed": expected_size is None or image.size == (expected_size, expected_size),
    }


def handle_normalize(context: dict, node: dict, backend: str) -> HandlerResult:
    source = resolve_path(context["product"]["source"])
    if not source.exists():
        return HandlerResult(STATUS_FAILED, f"Source not found: {source}")
    image = load_image(source).convert("RGB")
    image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
    output = artifact_path(context, "01-normalized.jpg")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="JPEG", quality=96, optimize=True)
    return HandlerResult(
        STATUS_PASSED,
        "Normalized source image.",
        (str(output.relative_to(ROOT)),),
        {"source": str(source), "size": image.size},
    )


def handle_classify(context: dict, node: dict, backend: str) -> HandlerResult:
    product = context["product"]
    classification = {
        "input_class": product.get("input_class", "B"),
        "garment_type": product.get("garment_type", "unknown"),
        "piece_count": product.get("piece_count", 1),
        "capture_state": product.get("capture_state", "hanging_or_worn"),
        "occlusion": product.get("occlusion", "unknown"),
        "source_of_truth": "product_record",
    }
    output = artifact_path(context, "02-classification.json")
    write_json(output, classification)
    return HandlerResult(
        STATUS_PASSED,
        "Classification copied from the product record.",
        (str(output.relative_to(ROOT)),),
        classification,
    )


def handle_attributes(context: dict, node: dict, backend: str) -> HandlerResult:
    attributes = context["product"].get("attributes", {})
    if not attributes:
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            "Product attributes are empty; fill buttons, pockets, seams, lining, and pattern.",
        )
    output = artifact_path(context, "03-garment.json")
    write_json(output, attributes)
    return HandlerResult(
        STATUS_PASSED,
        "Structured garment attributes are ready.",
        (str(output.relative_to(ROOT)),),
        {"attribute_count": len(attributes)},
    )


def handle_segment(context: dict, node: dict, backend: str) -> HandlerResult:
    source = context["state"]["nodes"]["normalize"]["artifacts"]
    if not source:
        return HandlerResult(STATUS_FAILED, "Normalized image is missing.")
    image = load_image(resolve_path(source[0])).convert("RGB")
    try:
        from segmentation import remove_background

        cutout = remove_background(image)
    except Exception as exc:
        return HandlerResult(STATUS_FAILED, f"Segmentation failed: {exc}")

    alpha = np.asarray(cutout.getchannel("A"))
    coverage = float((alpha > 12).mean())
    if coverage < 0.05 or coverage > 0.98:
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            f"Segmentation coverage is suspicious: {coverage:.3f}. Review the mask.",
            data={"coverage": round(coverage, 4)},
        )
    output = artifact_path(context, "04-segmentation.png")
    cutout.save(output, format="PNG", optimize=True)
    return HandlerResult(
        STATUS_PASSED,
        "Garment cutout created.",
        (str(output.relative_to(ROOT)),),
        {"alpha_coverage": round(coverage, 4)},
    )


def compose_white(cutout: Image.Image, size: int, margin: int) -> Image.Image:
    alpha = np.asarray(cutout.getchannel("A"))
    ys, xs = np.where(alpha > 12)
    if not len(xs):
        raise RuntimeError("No foreground pixels found")
    x0, x1 = max(0, int(xs.min()) - 4), min(cutout.width, int(xs.max()) + 5)
    y0, y1 = max(0, int(ys.min()) - 4), min(cutout.height, int(ys.max()) + 5)
    crop = cutout.crop((x0, y0, x1, y1))
    content = size - margin * 2
    scale = min(content / crop.width, content / crop.height)
    new_size = (max(1, round(crop.width * scale)), max(1, round(crop.height * scale)))
    crop = crop.resize(new_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    canvas.alpha_composite(crop, ((size - new_size[0]) // 2, (size - new_size[1]) // 2))
    return canvas.convert("RGB")


def handle_white_main(context: dict, node: dict, backend: str) -> HandlerResult:
    segmentation = context["state"]["nodes"]["segment"]["artifacts"]
    if not segmentation:
        return HandlerResult(STATUS_FAILED, "Segmentation artifact is missing.")
    cutout = load_image(resolve_path(segmentation[0])).convert("RGBA")
    output = artifact_path(context, "05-white-main.png")
    compose_white(cutout, 1536, 96).save(output, format="PNG", optimize=True)
    return HandlerResult(
        STATUS_PASSED,
        "White-background main image created.",
        (str(output.relative_to(ROOT)),),
        image_qc(output, 1536),
    )


def handle_detail_grid(context: dict, node: dict, backend: str) -> HandlerResult:
    normalized = context["state"]["nodes"]["normalize"]["artifacts"]
    if not normalized:
        return HandlerResult(STATUS_FAILED, "Normalized image is missing.")
    image = load_image(resolve_path(normalized[0])).convert("RGB")
    width, height = image.size
    crops = [
        ("top", image.crop((0, 0, width, height // 3))),
        ("middle", image.crop((0, height // 3, width, height * 2 // 3))),
        ("bottom", image.crop((0, height * 2 // 3, width, height))),
        (
            "center",
            image.crop(
                (
                    width // 4,
                    height // 4,
                    width * 3 // 4,
                    height * 3 // 4,
                )
            ),
        ),
    ]
    cell_width = 1000
    cells = []
    for label, crop in crops:
        scale = cell_width / crop.width
        cells.append(
            (
                label,
                crop.resize(
                    (cell_width, max(1, round(crop.height * scale))),
                    Image.Resampling.LANCZOS,
                ),
            )
        )
    cell_height = max(cell.height for _, cell in cells)
    sheet = Image.new("RGB", (cell_width * 2 + 60, cell_height * 2 + 90), "white")
    drawer = ImageDraw.Draw(sheet)
    for index, (label, cell) in enumerate(cells):
        x = 20 + (index % 2) * (cell_width + 20)
        y = 35 + (index // 2) * (cell_height + 25)
        sheet.paste(cell, (x, y))
        drawer.text((x, y - 22), label.upper(), fill=(0, 0, 0))
    output = artifact_path(context, "06-detail-grid.jpg")
    sheet.save(output, format="JPEG", quality=95, optimize=True)
    return HandlerResult(
        STATUS_PASSED,
        "Detail inspection sheet created.",
        (str(output.relative_to(ROOT)),),
        {"cells": [label for label, _ in cells]},
    )


def handle_plan_view(context: dict, node: dict, backend: str) -> HandlerResult:
    supplied = context["product"].get("plan_view_source")
    if supplied:
        source = resolve_path(supplied)
        if source.exists():
            output = artifact_path(context, "07-plan-view.png")
            shutil.copyfile(source, output)
            return HandlerResult(
                STATUS_PASSED,
                f"Using approved plan view: {source.name}",
                (str(output.relative_to(ROOT)),),
                image_qc(output),
            )
    request = {
        "template": context["product"].get("garment_type", "unknown"),
        "required_landmarks": (
            context["product"]
            .get("workflow", {})
            .get("plan_view_landmarks", [])
        ),
        "reason": "No deterministic template and landmark result exists yet.",
    }
    output = artifact_path(context, "07-plan-view-request.json")
    write_json(output, request)
    return HandlerResult(
        STATUS_NEEDS_HUMAN,
        "Select a garment template and annotate landmarks.",
        (str(output.relative_to(ROOT)),),
        request,
    )


def selected_model(product: dict) -> tuple[str, Path] | None:
    references = product.get("model_references", [])
    if not references:
        return None
    selected = references[0]
    return selected.get("key", "model"), resolve_path(selected["path"])


def handle_model_brief(context: dict, node: dict, backend: str) -> HandlerResult:
    product = context["product"]
    attributes = product.get("attributes", {})
    model = selected_model(product)
    model_name = model[0] if model else "unselected"
    brief = {
        "product_id": product["id"],
        "garment_type": product.get("garment_type", "unknown"),
        "selected_model": model_name,
        "pose": product.get("model_pose", "natural standing front three-quarter"),
        "required_garment_details": attributes.get("must_preserve", []),
        "background": "pure white studio",
        "aspect": "3:4",
        "output_resolution": "1200x1600",
        "policy": "AI generation is optional; casting card and request brief are deterministic.",
    }
    output = artifact_path(context, "08-model-brief.json")
    write_json(output, brief)
    markdown = artifact_path(context, "08-model-brief.md")
    lines = [
        f"# Model Image Brief - {product['id']}",
        "",
        f"- Garment: {product.get('garment_type', 'unknown')}",
        f"- Model: {model_name}",
        f"- Pose: {brief['pose']}",
        f"- Output: {brief['output_resolution']}",
        "",
        "## Must preserve",
    ]
    lines.extend(f"- {item}" for item in brief["required_garment_details"])
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return HandlerResult(
        STATUS_PASSED,
        "Model production brief created.",
        (str(output.relative_to(ROOT)), str(markdown.relative_to(ROOT))),
        brief,
    )


def handle_model_reference_sheet(
    context: dict, node: dict, backend: str
) -> HandlerResult:
    normalized = context["state"]["nodes"]["normalize"]["artifacts"]
    model = selected_model(context["product"])
    if not normalized or not model or not model[1].exists():
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            "A normalized garment image and a valid model reference are required.",
        )
    garment = load_image(resolve_path(normalized[0])).convert("RGB")
    reference = load_image(model[1]).convert("RGB")
    target_h = 1200

    def fit_height(image: Image.Image) -> Image.Image:
        scale = target_h / image.height
        return image.resize(
            (max(1, round(image.width * scale)), target_h), Image.Resampling.LANCZOS
        )

    garment, reference = fit_height(garment), fit_height(reference)
    canvas = Image.new(
        "RGB",
        (garment.width + reference.width + 60, target_h + 70),
        "white",
    )
    drawer = ImageDraw.Draw(canvas)
    drawer.text((20, 18), "GARMENT", fill=(0, 0, 0))
    drawer.text((garment.width + 40, 18), f"MODEL: {model[0].upper()}", fill=(0, 0, 0))
    canvas.paste(garment, (20, 48))
    canvas.paste(reference, (garment.width + 40, 48))
    output = artifact_path(context, "09-model-reference-sheet.jpg")
    canvas.save(output, format="JPEG", quality=95, optimize=True)
    return HandlerResult(
        STATUS_PASSED,
        "Garment/model casting sheet created.",
        (str(output.relative_to(ROOT)),),
        {"model": model[0]},
    )


MODEL_PROMPT = (
    "Image 1 is the authoritative garment. Image 2 is the selected model reference. "
    "Create a clean ecommerce model display photo of the model wearing the exact garment "
    "from Image 1. Preserve garment type, color, pattern, proportions, closures, pockets, "
    "seams, cuffs, hems and fabric texture. Use a natural standing pose, pure white studio "
    "background, soft even lighting, realistic body proportions, no text, watermark, collage, "
    "or reference panel. The complete garment and model must remain uncropped."
)


def handle_model_generate(context: dict, node: dict, backend: str) -> HandlerResult:
    references = context["state"]["nodes"]["model_reference_sheet"]["artifacts"]
    if not references:
        return HandlerResult(STATUS_FAILED, "Model reference sheet is missing.")
    request = {
        "backend": backend,
        "prompt": MODEL_PROMPT,
        "images": [context["product"].get("source", "")],
        "selected_model": selected_model(context["product"])[0]
        if selected_model(context["product"])
        else None,
        "size": "1200x1600",
    }
    request_path = artifact_path(context, "10-model-request.json")
    write_json(request_path, request)
    prompt_path = artifact_path(context, "10-model-prompt.txt")
    prompt_path.write_text(MODEL_PROMPT, encoding="utf-8")
    artifacts = [str(request_path.relative_to(ROOT)), str(prompt_path.relative_to(ROOT))]

    if backend == "none":
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            "Model request prepared. Re-run with --backend openrouter to generate.",
            tuple(artifacts),
            request,
        )
    if backend != "openrouter":
        return HandlerResult(STATUS_FAILED, f"Unknown backend: {backend}", tuple(artifacts))
    if not OPENROUTER_CLI.exists():
        return HandlerResult(
            STATUS_FAILED,
            f"OpenRouter CLI not found: {OPENROUTER_CLI}",
            tuple(artifacts),
        )

    model = selected_model(context["product"])
    if not model or not model[1].exists():
        return HandlerResult(STATUS_FAILED, "Model reference image is missing.", tuple(artifacts))
    normalized = context["state"]["nodes"]["normalize"]["artifacts"][0]
    output = artifact_path(context, "11-model-generated.png")
    command = [
        sys.executable,
        str(OPENROUTER_CLI),
        "edit",
        "--image",
        str(resolve_path(normalized)),
        "--image",
        str(model[1]),
        "--prompt",
        MODEL_PROMPT,
        "--size",
        "1200x1600",
        "--quality",
        "high",
        "--output-format",
        "png",
        "--output",
        str(output),
    ]
    result = subprocess.run(command, cwd=str(ROOT), capture_output=True, text=True, timeout=480)
    if result.returncode != 0 or not output.exists():
        return HandlerResult(
            STATUS_FAILED,
            (result.stderr or result.stdout or "unknown error")[-1600:],
            tuple(artifacts),
        )
    artifacts += [str(output.relative_to(ROOT))]
    return HandlerResult(
        STATUS_PASSED,
        "Model image generated.",
        tuple(artifacts),
        image_qc(output),
    )


def handle_colorway(context: dict, node: dict, backend: str) -> HandlerResult:
    colors = context["product"].get("colorways", [])
    if not colors:
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            "No colorway list in the product record.",
        )
    spec = {
        "source_asset": context["product"].get("plan_view_source"),
        "colorways": colors,
        "rule": "Each colorway requires either an approved source photo or a controlled recolor request.",
    }
    output = artifact_path(context, "12-colorway-spec.json")
    write_json(output, spec)
    return HandlerResult(
        STATUS_PASSED,
        "Colorway production specification created.",
        (str(output.relative_to(ROOT)),),
        {"colorway_count": len(colors)},
    )


def primary_asset(context: dict) -> Path | None:
    product = context["product"]
    preferred = product.get("marketplace_source")
    if preferred and resolve_path(preferred).exists():
        return resolve_path(preferred)
    for node_name in ("plan_view", "white_main"):
        artifacts = context["state"]["nodes"].get(node_name, {}).get("artifacts", [])
        if artifacts and resolve_path(artifacts[0]).exists():
            return resolve_path(artifacts[0])
    return None


def handle_channel_exports(context: dict, node: dict, backend: str) -> HandlerResult:
    source = primary_asset(context)
    if not source:
        return HandlerResult(
            STATUS_NEEDS_HUMAN,
            "No approved primary asset for channel export.",
        )
    image = load_image(source).convert("RGB")
    outputs = []
    specs = {
        "square-800": (800, 800),
        "square-1536": (1536, 1536),
        "portrait-1200x1600": (1200, 1600),
    }
    for name, size in specs.items():
        canvas = Image.new("RGB", size, (255, 255, 255))
        scale = min(size[0] / image.width, size[1] / image.height)
        resized = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
        canvas.paste(
            resized,
            ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2),
        )
        output = artifact_path(context, f"13-{name}.jpg")
        canvas.save(output, format="JPEG", quality=95, optimize=True)
        outputs.append(str(output.relative_to(ROOT)))
    return HandlerResult(
        STATUS_PASSED,
        "Marketplace export presets created.",
        tuple(outputs),
        {"exports": list(specs)},
    )


def handle_pixel_qc(context: dict, node: dict, backend: str) -> HandlerResult:
    candidates = []
    for name in ("plan_view", "white_main", "model_generate"):
        artifacts = context["state"]["nodes"].get(name, {}).get("artifacts", [])
        if artifacts:
            candidates.extend(artifacts)
    if not candidates:
        return HandlerResult(STATUS_NEEDS_HUMAN, "No generated image to QC.")
    reports = {}
    for relative in candidates:
        path = resolve_path(relative)
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and path.exists():
            reports[relative] = image_qc(path)
    output = artifact_path(context, "14-pixel-qc.json")
    write_json(output, reports)
    return HandlerResult(
        STATUS_PASSED,
        f"QC completed for {len(reports)} images.",
        (str(output.relative_to(ROOT)),),
        {"image_count": len(reports)},
    )


def handle_final_review(context: dict, node: dict, backend: str) -> HandlerResult:
    output = artifact_path(context, "15-final-review.json")
    review = {
        "product_id": context["product"]["id"],
        "human_review_required": True,
        "review_items": [
            "garment count",
            "buttons",
            "pockets",
            "seams",
            "lining",
            "stripe direction",
            "hem and cuffs",
            "model body proportions",
            "background cleanliness",
            "marketplace cropping",
        ],
    }
    write_json(output, review)
    return HandlerResult(
        STATUS_NEEDS_HUMAN,
        "Ready for human final review.",
        (str(output.relative_to(ROOT)),),
        review,
    )


def build_recipes() -> dict[str, list[Node]]:
    normalize = Node("normalize", "Normalize source", handle_normalize)
    classify = Node("classify", "Classify input", handle_classify, ("normalize",))
    attributes = Node(
        "attributes", "Validate garment attributes", handle_attributes, ("classify",)
    )
    segment = Node("segment", "Segment garment", handle_segment, ("normalize",))

    return {
        "plan-view": [
            normalize,
            classify,
            attributes,
            segment,
            Node("plan_view", "Create plan view", handle_plan_view, ("segment", "attributes"), "plan-view"),
            Node("pixel_qc", "Pixel QC", handle_pixel_qc, ("plan_view",), "qc"),
        ],
        "white-main": [
            normalize,
            segment,
            Node("white_main", "Create white main image", handle_white_main, ("segment",), "white-main"),
            Node("pixel_qc", "Pixel QC", handle_pixel_qc, ("white_main",), "qc"),
        ],
        "detail-sheet": [
            normalize,
            classify,
            attributes,
            Node("detail_grid", "Create detail sheet", handle_detail_grid, ("normalize",), "detail"),
        ],
        "on-model": [
            normalize,
            classify,
            attributes,
            Node("model_brief", "Model brief", handle_model_brief, ("attributes",), "model"),
            Node(
                "model_reference_sheet",
                "Casting/reference sheet",
                handle_model_reference_sheet,
                ("model_brief",),
                "model",
            ),
            Node(
                "model_generate",
                "Generate model image",
                handle_model_generate,
                ("model_reference_sheet",),
                "model",
            ),
            Node("pixel_qc", "Pixel QC", handle_pixel_qc, ("model_generate",), "qc"),
        ],
        "colorway": [
            normalize,
            classify,
            attributes,
            Node("colorway", "Colorway specification", handle_colorway, ("attributes",), "colorway"),
        ],
        "marketplace-pack": [
            normalize,
            classify,
            attributes,
            Node(
                "channel_exports",
                "Channel exports",
                handle_channel_exports,
                ("attributes",),
                "channel",
            ),
        ],
        "full-studio": [
            normalize,
            classify,
            attributes,
            segment,
            Node("plan_view", "Create plan view", handle_plan_view, ("segment", "attributes"), "plan-view"),
            Node("white_main", "Create white main image", handle_white_main, ("segment",), "white-main"),
            Node("detail_grid", "Create detail sheet", handle_detail_grid, ("normalize",), "detail"),
            Node("model_brief", "Model brief", handle_model_brief, ("attributes",), "model"),
            Node(
                "model_reference_sheet",
                "Casting/reference sheet",
                handle_model_reference_sheet,
                ("model_brief",),
                "model",
            ),
            Node(
                "model_generate",
                "Generate model image",
                handle_model_generate,
                ("model_reference_sheet",),
                "model",
            ),
            Node("colorway", "Colorway specification", handle_colorway, ("attributes",), "colorway"),
            Node(
                "channel_exports",
                "Channel exports",
                handle_channel_exports,
                ("attributes", "plan_view"),
                "channel",
            ),
            Node(
                "pixel_qc",
                "Pixel QC",
                handle_pixel_qc,
                ("plan_view", "white_main", "model_generate"),
                "qc",
            ),
            Node(
                "final_review",
                "Human final review",
                handle_final_review,
                ("pixel_qc", "channel_exports"),
                "review",
            ),
        ],
    }


def html_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_report(run_dir: Path, state: dict) -> Path:
    report = run_dir / "report.html"
    nodes = state["nodes"]
    cards = []
    for name, node in nodes.items():
        status = node["status"]
        color = {
            STATUS_PASSED: "#d8f5df",
            STATUS_FAILED: "#ffd9d9",
            STATUS_NEEDS_HUMAN: "#ffeed0",
            STATUS_BLOCKED: "#e5e5e5",
            STATUS_RUNNING: "#dcecff",
        }.get(status, "#f6f6f6")
        artifacts = "".join(
            f"<li><code>{html_escape(item)}</code></li>"
            for item in node.get("artifacts", [])
        )
        message = html_escape(node.get("message", ""))
        requires = ", ".join(node.get("requires", [])) or "-"
        cards.append(
            f"<section class='card' style='border-left-color:{color}'>"
            f"<div class='head'><strong>{html_escape(name)}</strong>"
            f"<span>{html_escape(status)}</span></div>"
            f"<div class='title'>{html_escape(node.get('title', ''))}</div>"
            f"<div class='meta'>branch: {html_escape(node.get('branch', ''))} | requires: {html_escape(requires)}</div>"
            f"<p>{message}</p><ul>{artifacts}</ul></section>"
        )
    html = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>Apparel Studio {html_escape(str(state['product_id']))} - {html_escape(state['recipe'])}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f3f5f7;margin:0;padding:28px;color:#20242a}}
h1{{font-size:24px;margin:0 0 6px}} .sub{{color:#65707d;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}}
.card{{background:white;border:1px solid #d9dee5;border-left:6px solid #ccc;border-radius:6px;padding:14px}}
.head{{display:flex;justify-content:space-between;font-size:13px}} .head span{{color:#65707d}}
.title{{font-size:17px;margin:6px 0 4px}} .meta{{font-size:12px;color:#707a86}}
ul{{padding-left:18px;margin:8px 0 0}} code{{font-size:11px}} p{{margin:8px 0 0;font-size:13px}}
</style></head><body><h1>Apparel Studio Workflow</h1>
<div class='sub'>Product {html_escape(str(state['product_id']))} · Recipe {html_escape(state['recipe'])} · Updated {html_escape(state.get('updated_at', ''))}</div>
<div class='grid'>{''.join(cards)}</div></body></html>"""
    report.write_text(html, encoding="utf-8")
    return report


def update_dependencies(state: dict) -> None:
    for name, node in state["nodes"].items():
        if node["status"] in {STATUS_PASSED, STATUS_SKIPPED}:
            continue
        failed_requirements = [
            requirement
            for requirement in node.get("requires", [])
            if state["nodes"].get(requirement, {}).get("status")
            not in {STATUS_PASSED, STATUS_SKIPPED}
        ]
        if failed_requirements:
            node["status"] = STATUS_BLOCKED
            node["message"] = "Waiting for: " + ", ".join(failed_requirements)
        elif node["status"] == STATUS_BLOCKED:
            node["status"] = STATUS_PENDING
            node["message"] = ""


def run_recipe(product: dict, recipe: str, backend: str, force: bool = False) -> dict:
    recipes = build_recipes()
    if recipe not in recipes:
        raise SystemExit(f"Unknown recipe: {recipe}")
    run_dir, state_path = run_paths(int(product["id"]), recipe)
    run_dir.mkdir(parents=True, exist_ok=True)
    if state_path.exists() and not force:
        state = read_json(state_path)
    else:
        state = initialize_state(product, recipe, recipes[recipe])
        write_json(state_path, state)

    context = {"product": product, "run_dir": run_dir, "state": state}
    for node in recipes[recipe]:
        current = state["nodes"][node.name]
        update_dependencies(state)
        if current["status"] == STATUS_PASSED and not force:
            continue
        if current["status"] == STATUS_BLOCKED:
            continue
        current["status"] = STATUS_RUNNING
        current["message"] = ""
        current["artifacts"] = []
        current["data"] = {}
        write_json(state_path, state)
        try:
            result = node.handler(context, current, backend)
            current["status"] = result.status
            current["message"] = result.message
            current["artifacts"] = list(result.artifacts)
            current["data"] = result.data or {}
        except Exception as exc:
            current["status"] = STATUS_FAILED
            current["message"] = f"{type(exc).__name__}: {exc}"
        state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        update_dependencies(state)
        write_json(state_path, state)
        write_report(run_dir, state)
    return state


def find_mapping_row(number: int) -> dict:
    if not MAPPING_PATH.exists():
        raise SystemExit(f"Mapping not found: {MAPPING_PATH}")
    with MAPPING_PATH.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            if int(row["number"]) == number:
                return row
    raise SystemExit(f"Number {number} not found in mapping")


def default_model_references() -> list[dict]:
    candidates = [
        ("modern", "model_library/modern-chinese/fullbody-final.png"),
        ("korean", "model_library/korean-minimal/fullbody-final.png"),
        ("eurasian", "model_library/eurasian-editorial/fullbody-final.png"),
    ]
    return [
        {"key": key, "path": path, "style": style}
        for style, (key, path) in zip(
            ["modern-chinese", "korean-minimal", "eurasian-editorial"], candidates
        )
        if (ROOT / path).exists()
    ]


def init_product(number: int, garment_type: str | None) -> Path:
    row = find_mapping_row(number)
    source = ROOT / "work_library" / row["original_name"]
    if not source.exists():
        raise SystemExit(f"Source image not found: {source}")
    output = product_path(number)
    plan_source = ROOT / "work_library_plan_view" / f"{number}.png"
    product = {
        "id": str(number),
        "source": str(source.relative_to(ROOT)),
        "garment_type": garment_type or "unknown",
        "input_class": "B",
        "piece_count": 1,
        "capture_state": "hanging_or_worn",
        "occlusion": "unknown",
        "attributes": {},
        "must_preserve": [],
        "colorways": [],
        "model_pose": "natural standing, front three-quarter body",
        "model_references": default_model_references(),
        "workflow": {
            "plan_view_landmarks": [
                "left_neck",
                "right_neck",
                "left_shoulder",
                "right_shoulder",
                "left_armhole",
                "right_armhole",
                "left_cuff",
                "right_cuff",
                "left_side_seam",
                "right_side_seam",
                "hem_left",
                "hem_center",
                "hem_right",
            ]
        },
    }
    if plan_source.exists():
        product["plan_view_source"] = str(plan_source.relative_to(ROOT))
        product["marketplace_source"] = product["plan_view_source"]
    write_json(output, product)
    return output


def print_state(state: dict) -> None:
    print(f"Product {state['product_id']} | recipe {state['recipe']}")
    for name, node in state["nodes"].items():
        print(f"  {node['status']:<12} {name:<24} {node.get('message', '')}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-recipe apparel image production workflow runner."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    recipes_parser = subparsers.add_parser("recipes")
    recipes_parser.add_argument("--verbose", action="store_true")

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--number", type=int, required=True)
    init_parser.add_argument("--type", dest="garment_type")

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--number", type=int, required=True)
    plan_parser.add_argument("--recipe", default="full-studio")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--number", type=int, required=True)
    run_parser.add_argument("--recipe", default="white-main")
    run_parser.add_argument("--backend", default="none")
    run_parser.add_argument("--force", action="store_true")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--number", type=int, required=True)
    status_parser.add_argument("--recipe", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    recipes = build_recipes()

    if args.command == "recipes":
        for name, nodes in recipes.items():
            print(f"{name}:")
            for node in nodes:
                requires = ", ".join(node.requires) or "-"
                if args.verbose:
                    print(f"  {node.name:<24} {node.title:<28} requires={requires}")
                else:
                    print(f"  {node.name}")
        return

    if args.command == "init":
        path = init_product(args.number, args.garment_type)
        print(f"Created {path.relative_to(ROOT)}")
        return

    path = product_path(args.number)
    if not path.exists():
        path = init_product(args.number, None)
        print(f"Created default product record {path.relative_to(ROOT)}")
    product = read_json(path)

    if args.command == "plan":
        state = initialize_state(product, args.recipe, recipes[args.recipe])
        print_state(state)
        return

    if args.command == "run":
        state = run_recipe(product, args.recipe, args.backend, args.force)
        print_state(state)
        run_dir, _ = run_paths(args.number, args.recipe)
        print(f"Report: {write_report(run_dir, state).relative_to(ROOT)}")
        return

    if args.command == "status":
        _, state_path = run_paths(args.number, args.recipe)
        if not state_path.exists():
            raise SystemExit(f"No run state found: {state_path.relative_to(ROOT)}")
        state = read_json(state_path)
        print_state(state)
        return


if __name__ == "__main__":
    main()
