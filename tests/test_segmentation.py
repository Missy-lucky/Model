from __future__ import annotations

from PIL import Image
import pytest

import segmentation


def test_model_is_bundled_and_selected() -> None:
    try:
        path = segmentation.model_path()
    except FileNotFoundError:
        pytest.skip("Segmentation model is not committed to Git")
    assert path.is_file()
    assert path.name in {"u2netp.onnx", "u2net.onnx"}


def test_model_prefers_higher_quality_model_when_available(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    light = tmp_path / "u2netp.onnx"
    full = tmp_path / "u2net.onnx"
    light.write_bytes(b"light")
    full.write_bytes(b"full")
    monkeypatch.setattr(segmentation, "MODEL_DIRECTORIES", [tmp_path])
    assert segmentation.model_path() == full


def test_normalize_shape() -> None:
    image = Image.new("RGB", (640, 960), (220, 30, 30))
    tensor = segmentation._normalize(image, (320, 320))
    assert tensor.shape == (1, 3, 320, 320)
    assert tensor.dtype.name == "float32"


def test_remove_background_preserves_canvas_size() -> None:
    try:
        segmentation.model_path()
    except FileNotFoundError:
        pytest.skip("Segmentation model is not committed to Git")
    image = Image.new("RGB", (320, 480), (240, 240, 240))
    result = segmentation.remove_background(image)
    assert result.mode == "RGBA"
    assert result.size == image.size
    assert result.getextrema()[3][0] >= 0
    assert result.getextrema()[3][1] <= 255
