from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import desktop_app
from desktop_app import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(desktop_app.STYLE)
    yield app


@pytest.fixture
def window(qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MainWindow:
    monkeypatch.setattr(desktop_app, "SETTINGS_PATH", tmp_path / "desktop_settings.json")
    item = MainWindow()
    yield item
    item.runtime_timer.stop()
    item.close()
    item.deleteLater()


def test_window_starts_in_chinese_and_has_core_views(window: MainWindow) -> None:
    assert window.language == "zh"
    assert window.nav_buttons["workbench"].text() == "工作台"
    assert window.backend_combo.currentText() == "无 AI / 确定性处理"
    assert window.node_tree.topLevelItemCount() > 0
    assert window.queue_table.rowCount() > 0
    assert window.product_list.count() > 0
    assert "LongY Studio" in window.windowTitle()


def test_language_switch_updates_and_persists(window: MainWindow, tmp_path: Path) -> None:
    window.toggle_language()
    assert window.language == "en"
    assert window.nav_buttons["workbench"].text() == "Workbench"
    assert window.backend_combo.currentText() == "No AI / deterministic"
    saved = json.loads((tmp_path / "desktop_settings.json").read_text(encoding="utf-8"))
    assert saved["language"] == "en"
    assert saved["backend"] in {"none", "openrouter"}

    window.select_language("zh")
    assert window.language == "zh"
    assert window.nav_buttons["queue"].text() == "队列"


def test_product_search_filters_without_losing_selection(window: MainWindow) -> None:
    first_number = window.products[0]["id"]
    window.current_number = first_number
    window.product_search.setText(first_number)
    window.render_products()
    assert window.product_list.count() >= 1
    assert first_number in window.product_list.item(0).text()

    window.product_search.setText("___no_matching_product___")
    window.render_products()
    assert window.product_list.count() == 0


def test_structured_attributes_sync_from_record_and_form(
    window: MainWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert window.attr_color_edit.text() == "white with black vertical stripes"
    assert window.attr_buttons_spin.value() == 5
    assert window.attr_collar_edit.text() == "wide pointed collar"
    assert "shoulder" in window.attr_seams_edit.text()

    captured: dict[str, object] = {}

    def fake_save(record: dict) -> None:
        captured.update(record)

    monkeypatch.setattr(desktop_app, "save_product", fake_save)
    window.attr_buttons_spin.setValue(6)
    window.attr_pockets_edit.setText("left welt, right welt")
    window.attr_must_edit.setPlainText("stripe spacing\nsix buttons")
    window.save_product()
    attributes = captured["attributes"]
    assert attributes["buttons"] == 6
    assert attributes["pockets"] == ["left welt", "right welt"]
    assert attributes["must_preserve"] == ["stripe spacing", "six buttons"]
    assert captured["must_preserve"] == attributes["must_preserve"]


def test_full_studio_nodes_are_localized(window: MainWindow) -> None:
    window.current_recipe = "full-studio"
    window.current_state = window.state_for(window.current_number, "full-studio")
    window.render_nodes()
    texts = [window.node_tree.topLevelItem(index).text(0) for index in range(window.node_tree.topLevelItemCount())]
    assert "输入规范化" in texts
    assert "平面图" in texts
    assert "模特生成" in texts
    assert "人工审核" in texts


def test_artifact_preview_loads_image_artifact(window: MainWindow) -> None:
    target_row = None
    for index in range(window.node_tree.topLevelItemCount()):
        item = window.node_tree.topLevelItem(index)
        if item.data(0, Qt.UserRole) in {"white_main", "detail_grid", "model_reference_sheet"}:
            target_row = index
            break

    if target_row is None:
        pytest.skip("No image-producing node state available")

    window.node_tree.setCurrentItem(window.node_tree.topLevelItem(target_row))
    assert window.artifact_list.count() > 0
    assert not window.artifact_preview.pixmap().isNull()


def test_menus_and_shortcuts_exist(window: MainWindow) -> None:
    assert window.menuBar().actions()[0].text() == "文件"
    assert window.menu_actions["refresh"].shortcut().toString().startswith("Ctrl+")
    assert window.menu_actions["help"].shortcut().toString() == "F1"
