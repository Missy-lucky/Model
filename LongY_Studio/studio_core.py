from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from apparel_studio import ROOT, build_recipes, product_path


APP_VERSION = "0.2.0"
PRODUCT_ROOT = ROOT / "workflow_products"
RUN_ROOT = ROOT / "workflow_runs"


@dataclass(frozen=True)
class ProductSummary:
    number: str
    garment_type: str
    source: str
    has_plan_view: bool
    has_attributes: bool


@dataclass(frozen=True)
class RunSummary:
    number: str
    recipe: str
    updated_at: str
    passed: int
    needs_human: int
    failed: int
    running: bool
    total: int
    path: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    """Write JSON completely or leave the previous file intact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as target:
            json.dump(value, target, ensure_ascii=False, indent=2)
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def normalize_product(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Product record must be an object")
    number = str(record.get("id", "")).strip()
    if not number.isdigit() or int(number) <= 0:
        raise ValueError("Product id must be a positive integer")

    normalized = dict(record)
    normalized["id"] = number
    normalized["garment_type"] = str(record.get("garment_type", "")).strip()
    normalized["input_class"] = record.get("input_class", "B")
    if normalized["input_class"] not in {"A", "B", "C"}:
        raise ValueError("input_class must be A, B, or C")
    try:
        normalized["piece_count"] = max(1, int(record.get("piece_count", 1)))
    except (TypeError, ValueError) as exc:
        raise ValueError("piece_count must be an integer") from exc
    normalized["capture_state"] = str(record.get("capture_state", "")).strip()
    normalized["attributes"] = record.get("attributes", {})
    normalized["must_preserve"] = record.get("must_preserve", [])
    normalized["colorways"] = record.get("colorways", [])
    normalized["model_references"] = record.get("model_references", [])
    if not normalized["garment_type"]:
        raise ValueError("garment_type is required")
    return normalized


def save_product(record: dict[str, Any]) -> Path:
    normalized = normalize_product(record)
    path = product_path(int(normalized["id"]))
    write_json_atomic(path, normalized)
    return path


def load_product(number: int | str) -> dict[str, Any]:
    path = product_path(int(number))
    if not path.exists():
        raise FileNotFoundError(f"Product record not found: {path}")
    return normalize_product(read_json(path))


def discover_products() -> list[ProductSummary]:
    summaries: list[ProductSummary] = []
    if not PRODUCT_ROOT.exists():
        return summaries
    for record_path in PRODUCT_ROOT.glob("*/product.json"):
        try:
            record = load_product(record_path.parent.name)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        summaries.append(
            ProductSummary(
                number=record["id"],
                garment_type=record.get("garment_type", "unknown"),
                source=record.get("source", ""),
                has_plan_view=bool(record.get("plan_view_source")),
                has_attributes=bool(record.get("attributes")),
            )
        )
    return sorted(summaries, key=lambda item: int(item.number))


def _run_summary(number: str, recipe: str, state: dict[str, Any]) -> RunSummary:
    nodes = list(state.get("nodes", {}).values())
    return RunSummary(
        number=number,
        recipe=recipe,
        updated_at=str(state.get("updated_at", "")),
        passed=sum(node.get("status") == "passed" for node in nodes),
        needs_human=sum(node.get("status") == "needs_human" for node in nodes),
        failed=sum(node.get("status") == "failed" for node in nodes),
        running=any(node.get("status") == "running" for node in nodes),
        total=len(nodes),
        path=str(RUN_ROOT / number / recipe),
    )


def discover_runs() -> list[RunSummary]:
    summaries: list[RunSummary] = []
    if not RUN_ROOT.exists():
        return summaries
    for product_dir in RUN_ROOT.iterdir():
        if not product_dir.is_dir() or not product_dir.name.isdigit():
            continue
        for state_path in product_dir.glob("*/state.json"):
            try:
                state = read_json(state_path)
            except (OSError, json.JSONDecodeError):
                continue
            summaries.append(_run_summary(product_dir.name, state_path.parent.name, state))
    return sorted(
        summaries,
        key=lambda item: (item.updated_at, int(item.number), item.recipe),
        reverse=True,
    )


def load_run_state(number: int | str, recipe: str) -> dict[str, Any] | None:
    path = RUN_ROOT / str(int(number)) / recipe / "state.json"
    if not path.exists():
        return None
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError):
        return None


@dataclass(frozen=True)
class BackendInfo:
    key: str
    name: str
    available: bool
    requires_key: bool
    description: str


def backend_catalog() -> list[BackendInfo]:
    return [
        BackendInfo(
            key="none",
            name="确定性处理 / 无 AI",
            available=True,
            requires_key=False,
            description="只运行抠图、合成、规格生成和 QC，不调用生图接口。",
        ),
        BackendInfo(
            key="openrouter",
            name="OpenRouter Image Edit",
            available=bool(os.environ.get("OPENROUTER_ICU_API_KEY")),
            requires_key=True,
            description="用于模特图或可选精修；调用前会在界面中再次确认。",
        ),
    ]


@dataclass(frozen=True)
class LogEntry:
    updated_at: str
    number: str
    recipe: str
    node: str
    status: str
    message: str


def collect_logs(limit: int = 500) -> list[LogEntry]:
    entries: list[LogEntry] = []
    for run in discover_runs():
        state = load_run_state(run.number, run.recipe) or {}
        for node_name, node in state.get("nodes", {}).items():
            status = str(node.get("status", ""))
            message = str(node.get("message", ""))
            if status in {"failed", "needs_human", "running"} or message:
                entries.append(
                    LogEntry(
                        updated_at=run.updated_at,
                        number=run.number,
                        recipe=run.recipe,
                        node=node_name,
                        status=status,
                        message=message,
                    )
                )
    entries.sort(key=lambda item: item.updated_at, reverse=True)
    return entries[:limit]


@dataclass(frozen=True)
class Overview:
    version: str
    product_count: int
    run_count: int
    running_count: int
    needs_human_count: int
    failed_count: int


def overview() -> Overview:
    runs = discover_runs()
    return Overview(
        version=APP_VERSION,
        product_count=len(discover_products()),
        run_count=len(runs),
        running_count=sum(run.running for run in runs),
        needs_human_count=sum(run.needs_human for run in runs),
        failed_count=sum(run.failed for run in runs),
    )


def recipe_catalog() -> dict[str, list[dict[str, Any]]]:
    return {
        name: [
            {
                "name": node.name,
                "title": node.title,
                "requires": list(node.requires),
                "branch": node.branch,
            }
            for node in nodes
        ]
        for name, nodes in build_recipes().items()
    }


def product_matches(product: ProductSummary, query: str) -> bool:
    query = query.strip().lower()
    if not query:
        return True
    values = [product.number, product.garment_type, product.source]
    return any(query in value.lower() for value in values)
