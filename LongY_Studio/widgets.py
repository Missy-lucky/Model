from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


BRANCH_COLORS = {
    "common": "#8FA8C8",
    "plan-view": "#63B3ED",
    "white-main": "#63C8B8",
    "detail": "#B79CED",
    "model": "#EF8FB5",
    "colorway": "#F2A65A",
    "channel": "#DCBM5B",
    "qc": "#7DCEA0",
    "review": "#E08069",
    "legacy": "#87919B",
}

STATUS_COLORS = {
    "pending": "#7B8794",
    "running": "#4EA8DE",
    "passed": "#43B97F",
    "failed": "#E5484D",
    "needs_human": "#F5A524",
    "blocked": "#6A7480",
    "skipped": "#6A7480",
}


def branch_color(branch: str) -> QColor:
    return QColor(BRANCH_COLORS.get(branch, BRANCH_COLORS["legacy"]))


def status_color(status: str) -> QColor:
    return QColor(STATUS_COLORS.get(status, STATUS_COLORS["pending"]))


class Card(QFrame):
    def __init__(self, accent: str = "#F28B2C", parent: QWidget | None = None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.setObjectName("StudioCard")
        self.setProperty("accent", accent)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(52, 59, 70), 1))
        painter.setBrush(QColor(31, 35, 41))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QPen(self.accent, 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(1, 5), QPointF(1, rect.height() - 5))
        painter.end()


class HeroCard(Card):
    def __init__(self, background: str, accent: str = "#F28B2C", parent: QWidget | None = None):
        super().__init__(accent, parent)
        self.background = QPixmap(background)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        if not self.background.isNull():
            scaled = self.background.scaled(
                self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            overlay = QColor(18, 22, 28, 168)
            painter.fillRect(self.rect(), overlay)
        else:
            painter.fillRect(self.rect(), QColor("#1D242B"))
        painter.end()
        super().paintEvent(event)


class ClickableCard(Card):
    clicked = Signal(str)

    def __init__(self, key: str, accent: str, parent: QWidget | None = None):
        super().__init__(accent, parent)
        self.key = key
        self.setCursor(Qt.PointingHandCursor)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit(self.key)
        super().mouseReleaseEvent(event)


class StatCard(QWidget):
    def __init__(
        self,
        title: str,
        value: str,
        caption: str,
        accent: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("StatCardRoot")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("StatTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        self.caption_label = QLabel(caption)
        self.caption_label.setObjectName("StatCaption")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.caption_label)
        self.card = Card(accent, self)
        self.card.setGeometry(self.rect())
        self.card.lower()

    def set_value(self, value: str, caption: str = "") -> None:
        self.value_label.setText(value)
        if caption:
            self.caption_label.setText(caption)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.card.setGeometry(self.rect())


class WorkflowNode(QGraphicsItem):
    def __init__(
        self,
        name: str,
        title: str,
        branch: str,
        status: str,
        status_key: str,
        message: str,
        width: float = 186,
        height: float = 80,
    ):
        super().__init__()
        self.name = name
        self.title = title
        self.branch = branch
        self.status = status
        self.status_key = status_key
        self.message = message
        self.width = width
        self.height = height
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return QRectF(-3, -3, self.width + 6, self.height + 6)

    def paint(self, painter: QPainter, option, widget=None) -> None:
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, self.width, self.height)
        painter.setPen(QPen(QColor("#39404B"), 1))
        painter.setBrush(QColor("#20252C"))
        painter.drawRoundedRect(rect, 7, 7)

        painter.setPen(QPen(branch_color(self.branch), 2.2))
        path = QPainterPath()
        path.moveTo(2, 7)
        path.lineTo(2, self.height - 7)
        painter.drawPath(path)

        title_font = QFont("Segoe UI Variable Text", 9, 650)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor("#E8ECF1")))
        painter.drawText(QRectF(12, 7, self.width - 74, 20), Qt.AlignLeft, self.title)

        status_color_value = status_color(self.status_key)
        painter.setPen(QPen(status_color_value, 1))
        painter.setBrush(status_color_value)
        painter.drawRoundedRect(QRectF(self.width - 59, 9, 49, 17), 4, 4)
        painter.setPen(QPen(QColor("#151820")))
        status_font = QFont("Segoe UI Variable Text", 7, 700)
        painter.setFont(status_font)
        painter.drawText(QRectF(self.width - 59, 9, 49, 17), Qt.AlignCenter, self.status)

        painter.setPen(QPen(QColor("#79838F")))
        message_font = QFont("Segoe UI Variable Text", 8)
        painter.setFont(message_font)
        text = self.message if self.message else self.branch
        painter.drawText(
            QRectF(12, 30, self.width - 22, self.height - 37),
            Qt.TextWordWrap,
            text[:90],
        )

        if self.isSelected():
            painter.setPen(QPen(QColor("#F28B2C"), 1.4, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)

    def shape(self) -> QPainterPath:
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width, self.height), 7, 7)
        return path


@dataclass
class CanvasNodeSpec:
    name: str
    title: str
    branch: str
    status: str
    status_key: str
    message: str
    requires: list[str]


class WorkflowCanvas(QGraphicsView):
    selection_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor("#171B20"))
        self.setFrameShape(QFrame.NoFrame)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.node_items: dict[str, WorkflowNode] = {}

    def render_workflow(self, nodes: Iterable[CanvasNodeSpec]) -> None:
        self.scene.clear()
        self.node_items.clear()
        node_list = list(nodes)
        depths = self._depths(node_list)

        columns: dict[int, list[CanvasNodeSpec]] = {}
        for node in node_list:
            columns.setdefault(depths[node.name], []).append(node)

        column_x = 18
        item_width, item_height = 188, 82
        row_gap, column_gap = 18, 50
        for depth in sorted(columns):
            rows = columns[depth]
            total_height = len(rows) * item_height + (len(rows) - 1) * row_gap
            y = max(18, (760 - total_height) / 2)
            for node in rows:
                item = WorkflowNode(
                    node.name,
                    node.title,
                    node.branch,
                    node.status,
                    node.status_key,
                    node.message,
                    item_width,
                    item_height,
                )
                item.setPos(column_x, y)
                self.scene.addItem(item)
                self.node_items[node.name] = item
                y += item_height + row_gap
            column_x += item_width + column_gap

        for node in node_list:
            if node.name not in self.node_items:
                continue
            target = self.node_items[node.name]
            for requirement in node.requires:
                source = self.node_items.get(requirement)
                if not source:
                    continue
                self._connect(source, target, status_color(node.status_key))

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-12, -12, 24, 24))
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def _connect(self, source: WorkflowNode, target: WorkflowNode, color: QColor) -> None:
        start = source.mapToScene(source.boundingRect().width(), source.boundingRect().height() / 2)
        end = target.mapToScene(0, target.boundingRect().height() / 2)
        path = QPainterPath(start)
        distance = (end.x() - start.x()) * 0.48
        path.cubicTo(
            QPointF(start.x() + distance, start.y()),
            QPointF(end.x() - distance, end.y()),
            end,
        )
        item = self.scene.addPath(path, QPen(color.darker(155), 1.5))
        item.setZValue(-2)

        radius = 3.0
        dot = QGraphicsEllipseItem(end.x() - radius, end.y() - radius, radius * 2, radius * 2)
        dot.setBrush(color)
        dot.setPen(Qt.NoPen)
        self.scene.addItem(dot)

    def _depths(self, nodes: list[CanvasNodeSpec]) -> dict[str, int]:
        by_name = {node.name: node for node in nodes}
        depths: dict[str, int] = {}

        def visit(name: str, chain: set[str]) -> int:
            if name in depths:
                return depths[name]
            if name in chain:
                return 0
            node = by_name[name]
            if not node.requires:
                depths[name] = 0
            else:
                depths[name] = 1 + max(
                    visit(requirement, chain | {name})
                    for requirement in node.requires
                    if requirement in by_name
                )
            return depths[name]

        for node in nodes:
            visit(node.name, set())
        return depths

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        selected = [item for item in self.scene.selectedItems() if isinstance(item, WorkflowNode)]
        if selected:
            self.selection_changed.emit(selected[0].name)

    def mouseReleaseEvent(self, event) -> None:
        super().mouseReleaseEvent(event)
        selected = [item for item in self.scene.selectedItems() if isinstance(item, WorkflowNode)]
        if selected:
            self.selection_changed.emit(selected[0].name)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)
