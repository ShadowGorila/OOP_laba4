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


# ─────────────────────────────────────────────────────────────────
#  Конкретные классы фигур
# ─────────────────────────────────────────────────────────────────

class CCircle(CShape):
    """Круг. _size — радиус."""

    def _bounding_box_params(self):
        r = self._size
        return r, r, r, r   # отступы от центра до краёв = радиус

    def contains_point(self, x: int, y: int) -> bool:
        dx, dy = self._x - x, self._y - y
        return dx * dx + dy * dy <= self._size ** 2

    def draw(self, painter: QPainter):
        self._apply_style(painter)
        r = self._size
        painter.drawEllipse(self._x - r, self._y - r, r * 2, r * 2)

    def shape_name(self) -> str:
        return "Круг"


class CEllipse(CShape):
    """
    Эллипс. _size — полуось по X; полуось по Y = _size * 0.6.
    Соотношение сторон фиксировано, масштабируется вместе с _size.
    """

    def _half_y(self) -> int:
        return max(10, int(self._size * 0.6))

    def _bounding_box_params(self):
        return self._size, self._half_y(), self._size, self._half_y()

    def contains_point(self, x: int, y: int) -> bool:
        a, b = self._size, self._half_y()
        dx, dy = (x - self._x) / a, (y - self._y) / b
        return dx * dx + dy * dy <= 1.0

    def draw(self, painter: QPainter):
        self._apply_style(painter)
        a, b = self._size, self._half_y()
        painter.drawEllipse(self._x - a, self._y - b, a * 2, b * 2)

    def shape_name(self) -> str:
        return "Эллипс"


class CRectangle(CShape):
    """
    Прямоугольник. _size — полуширина; высота = _size * 0.65.
    """

    def _half_h(self) -> int:
        return max(8, int(self._size * 0.65))

    def _bounding_box_params(self):
        return self._size, self._half_h(), self._size, self._half_h()

    def contains_point(self, x: int, y: int) -> bool:
        hw, hh = self._size, self._half_h()
        return (abs(x - self._x) <= hw) and (abs(y - self._y) <= hh)

    def draw(self, painter: QPainter):
        self._apply_style(painter)
        hw, hh = self._size, self._half_h()
        painter.drawRect(self._x - hw, self._y - hh, hw * 2, hh * 2)

    def shape_name(self) -> str:
        return "Прямоугольник"


class CSquare(CRectangle):
    """
    Квадрат — частный случай прямоугольника (_half_h = _size).
    Наследуется от CRectangle, переопределяет только _half_h и shape_name.
    """

    def _half_h(self) -> int:
        return self._size   # квадрат: высота = ширина

    def shape_name(self) -> str:
        return "Квадрат"


class CTriangle(CShape):
    """
    Равносторонний треугольник. _size — расстояние от центра до вершины.
    """

    def _vertices(self) -> list[QPoint]:
        """Вычисляет три вершины треугольника."""
        r = self._size
        pts = []
        for i in range(3):
            angle = math.radians(-90 + 120 * i)
            px = int(self._x + r * math.cos(angle))
            py = int(self._y + r * math.sin(angle))
            pts.append(QPoint(px, py))
        return pts

    def _bounding_box_params(self):
        r = self._size
        return r, r, r, r

    def contains_point(self, x: int, y: int) -> bool:
        """Проверка через барицентрические координаты."""
        v = self._vertices()

        def sign(px, py, ax, ay, bx, by):
            return (px - bx) * (ay - by) - (ax - bx) * (py - by)

        d1 = sign(x, y, v[0].x(), v[0].y(), v[1].x(), v[1].y())
        d2 = sign(x, y, v[1].x(), v[1].y(), v[2].x(), v[2].y())
        d3 = sign(x, y, v[2].x(), v[2].y(), v[0].x(), v[0].y())

        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def draw(self, painter: QPainter):
        self._apply_style(painter)
        pts = self._vertices()
        poly = QPolygon(pts)
        painter.drawPolygon(poly)

    def shape_name(self) -> str:
        return "Треугольник"



# ─────────────────────────────────────────────────────────────────
#  Точка входа
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())