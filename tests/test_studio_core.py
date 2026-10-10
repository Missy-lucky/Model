from __future__ import annotations

import json
from pathlib import Path

import pytest

import studio_core as core


def test_normalize_product_accepts_valid_record() -> None:
    record = {
        "id": 172,
        "garment_type": "shirt",
        "input_class": "B",
        "piece_count": 1,
        "attributes": {"buttons": 5},
    }
    normalized = core.normalize_product(record)
    assert normalized["id"] == "172"
    assert normalized["piece_count"] == 1
    assert normalized["attributes"] == {"buttons": 5}


@pytest.mark.parametrize(
    ("record", "message"),
    [
        ({"id": "x", "garment_type": "shirt"}, "Product id must be a positive integer"),
        ({"id": "1", "garment_type": ""}, "garment_type is required"),
        ({"id": "1", "garment_type": "shirt", "input_class": "D"}, "input_class must be A, B, or C"),
    ],
)
def test_normalize_product_rejects_invalid_records(record: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        core.normalize_product(record)


def test_atomic_json_write(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "record.json"
    core.write_json_atomic(target, {"id": "1"})
    assert target.read_text(encoding="utf-8") == '{\n  "id": "1"\n}\n'

    original = target.read_text(encoding="utf-8")
    with pytest.raises(TypeError):
        core.write_json_atomic(target, {"value": object()})
    assert target.read_text(encoding="utf-8") == original


def test_discovered_products_are_consistent() -> None:
    products = core.discover_products()
    assert all(item.number.isdigit() for item in products)
    assert [int(item.number) for item in products] == sorted(int(item.number) for item in products)


def test_recipe_catalog_dependencies_are_valid() -> None:
    catalog = core.recipe_catalog()
    assert set(catalog) == {
        "plan-view",
        "white-main",
        "detail-sheet",
        "on-model",
        "colorway",
        "marketplace-pack",
        "full-studio",
    }
    for recipe, nodes in catalog.items():
        names = {node["name"] for node in nodes}
        assert names, recipe
        for node in nodes:
            assert set(node["requires"]) <= names


def test_backend_catalog_never_exposes_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_ICU_API_KEY", raising=False)
    catalog = core.backend_catalog()
    assert len(catalog) == 2
    assert catalog[0].key == "none"
    assert catalog[0].available is True
    assert not any("sk-" in backend.description for backend in catalog)


def test_discover_runs_and_overview_are_consistent() -> None:
    runs = core.discover_runs()
    overview = core.overview()
    assert overview.run_count == len(runs)
    assert overview.running_count == sum(run.running for run in runs)
    assert all(run.total >= run.passed for run in runs)
