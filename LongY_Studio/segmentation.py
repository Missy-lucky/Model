from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


MODEL_DIRECTORIES = [
    Path(__file__).resolve().parent / "assets" / "models",
    Path.home() / ".rembg" / "models" / "u2netp",
    Path.home() / ".rembg" / "models" / "u2net",
]

MODEL_SPECS = {
    "u2netp": (320, 320),
    "u2net": (320, 320),
    "bria-rmbg": (1024, 1024),
}


def model_path() -> Path:
    override = os.environ.get("LONGY_SEGMENTATION_MODEL", "").strip()
    if override:
        path = Path(override)
        if not path.is_file():
            raise FileNotFoundError(f"LONGY_SEGMENTATION_MODEL does not exist: {path}")
        return path

    for directory in MODEL_DIRECTORIES:
        if not directory.is_dir():
            continue
        # Prefer the higher-quality u2net when a user provides it; fall back
        # to the small model bundled for local development builds.
        for name in ("u2net.onnx", "u2netp.onnx"):
            candidate = directory / name
            if candidate.is_file():
                return candidate
    raise FileNotFoundError(
        "No segmentation model found. Put u2netp.onnx or u2net.onnx in "
        "LongY_Studio/assets/models/, or set LONGY_SEGMENTATION_MODEL."
    )


def _normalize(image: Image.Image, size: tuple[int, int]) -> dict[str, np.ndarray]:
    resized = image.convert("RGB").resize(size, Image.Resampling.LANCZOS)
    array = np.asarray(resized).astype(np.float32) / 255.0
    mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (array - mean) / std
    normalized = np.transpose(normalized, (2, 0, 1))[None, :, :, :]
    return normalized


def _model_size(path: Path) -> tuple[int, int]:
    return MODEL_SPECS.get(path.stem.lower(), (320, 320))


def remove_background(image: Image.Image) -> Image.Image:
    """Run a local ONNX salient-object model and return an RGBA cutout."""
    import onnxruntime as ort

    source = image.convert("RGB")
    path = model_path()
    session = ort.InferenceSession(
        str(path),
        providers=["CPUExecutionProvider"],
        sess_options=_session_options(),
    )
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: _normalize(source, _model_size(path))})
    prediction = np.asarray(outputs[0])[0, 0]
    minimum = float(prediction.min())
    maximum = float(prediction.max())
    if maximum - minimum > 1e-6:
        prediction = (prediction - minimum) / (maximum - minimum)
    else:
        prediction = np.zeros_like(prediction)

    mask = Image.fromarray((prediction * 255).astype(np.uint8), mode="L")
    mask = mask.resize(source.size, Image.Resampling.LANCZOS)
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    if source.mode != "RGBA":
        source = source.convert("RGBA")
    source.putalpha(mask)
    return source


def _session_options() -> ort.SessionOptions:
    import onnxruntime as runtime

    options = runtime.SessionOptions()
    options.intra_op_num_threads = max(1, min(4, os.cpu_count() or 1))
    options.inter_op_num_threads = 1
    options.graph_optimization_level = runtime.GraphOptimizationLevel.ORT_ENABLE_ALL
    return options
