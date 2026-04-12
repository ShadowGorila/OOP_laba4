import sys
import math
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolBar,
    QStatusBar, QColorDialog, QMenu, QMessageBox
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QAction, QIcon,
    QKeySequence, QPolygon
)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize


# ─────────────────────────────────────────────────────────────────
#  ЛОГИКА (независима от UI)
# ─────────────────────────────────────────────────────────────────

class CShape(ABC):
 

    DEFAULT_SIZE = 60  # начальный размер по умолчанию

    def __init__(self, x: int, y: int):
        self._x = x              # центр фигуры — X
        self._y = y              # центр фигуры — Y
        self._size = self.DEFAULT_SIZE   # «радиус» / полуразмер
        self._color = QColor(100, 149, 237)   # cornflowerblue
        self._selected = False

    # ── позиция ────────────────────────────────────────────────
    def get_x(self) -> int:
        return self._x

    def get_y(self) -> int:
        return self._y

    def get_size(self) -> int:
        return self._size

    def get_color(self) -> QColor:
        return QColor(self._color)

    def set_color(self, color: QColor):
        self._color = QColor(color)

    # ── выделение ──────────────────────────────────────────────
    def set_selected(self, value: bool):
        self._selected = value

    def is_selected(self) -> bool:
        return self._selected

    # ── перемещение с контролем границ ─────────────────────────
    def move(self, dx: int, dy: int, canvas_w: int, canvas_h: int):
        new_x = self._x + dx
        new_y = self._y + dy
        bx, by, bw, bh = self._bounding_box_params()
        # bounding_box_params возвращает смещения от центра до края
        new_x = max(bx, min(new_x, canvas_w - bw))
        new_y = max(by, min(new_y, canvas_h - bh))
        self._x = new_x
        self._y = new_y

    # ── изменение размера с контролем границ ───────────────────
    def resize(self, delta: int, canvas_w: int, canvas_h: int):
        """Изменяет размер; гарантирует, что фигура остаётся на холсте."""
        new_size = max(10, self._size + delta)
        old_size = self._size
        self._size = new_size
        bx, by, bw, bh = self._bounding_box_params()
        # если после изменения размера фигура вышла за границы — откатить
        if (self._x - bx < 0 or self._y - by < 0 or
                self._x + bw > canvas_w or self._y + bh > canvas_h):
            self._size = old_size

    # ── вспомогательный метод для контроля границ ──────────────
    @abstractmethod
    def _bounding_box_params(self) -> tuple[int, int, int, int]:
        """
        Возвращает (left_margin, top_margin, right_margin, bottom_margin) —
        расстояния от центра (_x, _y) до соответствующего края фигуры.
        Используется в move() и resize() базового класса.
        """

    # ── попадание точки ────────────────────────────────────────
    @abstractmethod
    def contains_point(self, x: int, y: int) -> bool:
        """Проверяет, попадает ли точка (x,y) внутрь фигуры."""

    # ── отрисовка ──────────────────────────────────────────────
    @abstractmethod
    def draw(self, painter: QPainter):
        """Фигура рисует себя сама на переданном QPainter."""

    # ── вспомогательная настройка кисти/пера ───────────────────
    def _apply_style(self, painter: QPainter):
        """Устанавливает стиль: выделена — красная рамка, иначе — обычная."""
        if self._selected:
            fill = QColor(self._color)
            fill.setAlpha(180)
            painter.setBrush(QBrush(fill))
            painter.setPen(QPen(QColor(220, 0, 0), 3, Qt.PenStyle.DashLine))
        else:
            painter.setBrush(QBrush(self._color))
            painter.setPen(QPen(QColor(0, 0, 0), 1))

    # ── имя для отображения в статус-баре ──────────────────────
    @abstractmethod
    def shape_name(self) -> str:
        """Название фигуры (для UI)."""


#
# ─────────────────────────────────────────────────────────────────
#  Точка входа
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())