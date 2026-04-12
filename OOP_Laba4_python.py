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
#  Контейнер (расширяет идею ShapeStorage из Л.Р.3)
# ─────────────────────────────────────────────────────────────────

class ShapeStorage:
    """
    Контейнер всех фигур на холсте.
    Инкапсулирует приватный список, предоставляет API для работы с ним.
    """

    def __init__(self):
        self._items: list[CShape] = []

    def add(self, shape: CShape):
        """Добавить фигуру в контейнер."""
        self._items.append(shape)

    def remove_selected(self):
        """Удалить все выделенные фигуры."""
        self._items = [s for s in self._items if not s.is_selected()]

    def count(self) -> int:
        return len(self._items)

    def selected_count(self) -> int:
        return sum(1 for s in self._items if s.is_selected())

    def get(self, index: int) -> CShape:
        return self._items[index]

    def __iter__(self):
        return iter(list(self._items))   # копия списка, чтобы избежать сюрпризов

    def deselect_all(self):
        for s in self._items:
            s.set_selected(False)

    def select_all(self):
        for s in self._items:
            s.set_selected(True)

    def find_at(self, x: int, y: int) -> list[CShape]:
        """Найти все фигуры, в которые попала точка."""
        return [s for s in self._items if s.contains_point(x, y)]

    def selected_shapes(self) -> list[CShape]:
        return [s for s in self._items if s.is_selected()]


# ─────────────────────────────────────────────────────────────────
#  ХОЛСТ (UI ↔ логика)
# ─────────────────────────────────────────────────────────────────

class Canvas(QWidget):
    """
    Рабочая область редактора.
    Обрабатывает пользовательский ввод и делегирует логику объектам фигур
    и контейнеру. Сам холст не знает, как рисуется конкретная фигура.
    """

    # шаг перемещения и изменения размера клавишами
    MOVE_STEP = 5
    RESIZE_STEP = 5

    def __init__(self, status_bar: QStatusBar, parent=None):
        super().__init__(parent)
        self._storage = ShapeStorage()
        self._status_bar = status_bar
        self._current_shape_class: type = CCircle   # выбранный тип новой фигуры

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background-color: #f8f8f8;")

    # ── выбор инструмента (из панели/меню) ─────────────────────
    def set_shape_class(self, cls: type):
        self._current_shape_class = cls
        self._update_status()

    # ── контейнер (для доступа извне, например из MainWindow) ──
    @property
    def storage(self) -> ShapeStorage:
        return self._storage

    # ── Paint ───────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        for shape in self._storage:
            shape.draw(painter)   # каждая фигура рисует себя сама

        if self._storage.count() == 0:
            painter.setPen(QColor(180, 180, 180))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                             "ЛКМ — добавить фигуру  |  ЛКМ по фигуре — выделить")

    # ── Мышь ────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        x = int(event.position().x())
        y = int(event.position().y())
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

        if event.button() == Qt.MouseButton.LeftButton:
            hits = self._storage.find_at(x, y)
            if hits:
                # клик по фигуре(-ам) — выделяем ВСЕ, которые накрывают точку
                if not ctrl:
                    self._storage.deselect_all()
                    for s in hits:
                        s.set_selected(True)
                else:
                    # Ctrl+ЛКМ — переключить выделение у всех под курсором:
                    # если хотя бы одна не выделена — выделить все,
                    # если все уже выделены — снять выделение со всех.
                    all_selected = all(s.is_selected() for s in hits)
                    for s in hits:
                        s.set_selected(not all_selected)
            else:
                # клик по пустому месту — создать фигуру
                if not ctrl:
                    self._storage.deselect_all()
                new_shape = self._current_shape_class(x, y)
                # контроль: не создаём, если фигура выходит за границы
                bx, by, bw, bh = new_shape._bounding_box_params()
                w, h = self.width(), self.height()
                if (x - bx >= 0 and y - by >= 0 and
                        x + bw <= w and y + bh <= h):
                    self._storage.add(new_shape)

            self.update()
            self._update_status()

    # ── Клавиатура ──────────────────────────────────────────────
    def keyPressEvent(self, event):
        key = event.key()
        w, h = self.width(), self.height()

        # Del — удалить выделенные
        if key == Qt.Key.Key_Delete:
            self._storage.remove_selected()

        # Ctrl+A — выделить все
        elif key == Qt.Key.Key_A and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self._storage.select_all()

        # Стрелки — переместить выделенные (шаг MOVE_STEP пикселей)
        elif key == Qt.Key.Key_Left:
            for s in self._storage.selected_shapes():
                s.move(-self.MOVE_STEP, 0, w, h)
        elif key == Qt.Key.Key_Right:
            for s in self._storage.selected_shapes():
                s.move(self.MOVE_STEP, 0, w, h)
        elif key == Qt.Key.Key_Up:
            for s in self._storage.selected_shapes():
                s.move(0, -self.MOVE_STEP, w, h)
        elif key == Qt.Key.Key_Down:
            for s in self._storage.selected_shapes():
                s.move(0, self.MOVE_STEP, w, h)

        # + / = — увеличить размер
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            for s in self._storage.selected_shapes():
                s.resize(+self.RESIZE_STEP, w, h)

        # - — уменьшить размер
        elif key == Qt.Key.Key_Minus:
            for s in self._storage.selected_shapes():
                s.resize(-self.RESIZE_STEP, w, h)

        self.update()
        self._update_status()

    # ── Изменение размера окна ──────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()

    # ── Смена цвета выделенных (вызывается из MainWindow) ───────
    def change_color_selected(self):
        """Открывает стандартный диалог выбора цвета и применяет ко всем выделенным."""
        selected = self._storage.selected_shapes()
        if not selected:
            return
        # начальный цвет — цвет первой выделенной фигуры
        initial = selected[0].get_color()
        color = QColorDialog.getColor(initial, self, "Выберите цвет")
        if color.isValid():
            for s in selected:
                s.set_color(color)
            self.update()

    # ── Статус-бар ──────────────────────────────────────────────
    def _update_status(self):
        total = self._storage.count()
        sel = self._storage.selected_count()
        tool = self._current_shape_class.__name__.replace("C", "", 1)
        self._status_bar.showMessage(
            f"Инструмент: {tool}  |  Фигур: {total}  |  Выделено: {sel}  |  "
            "←↑↓→ — перемещение  |  +/- — размер  |  Del — удалить  |  "
            "Ctrl+A — выделить все  |  Ctrl+ЛКМ — мультивыделение"
        )


# ─────────────────────────────────────────────────────────────────
#  ГЛАВНОЕ ОКНО (только UI-обёртка, без логики фигур)
# ─────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    """
    Главное окно редактора.
    Создаёт меню, панель инструментов, холст.
    Вся логика фигур — в классах CShape и ShapeStorage.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лаб. 4 — Визуальный редактор векторных фигур")
        self.resize(900, 650)

        # создаём холст (он и есть центральный виджет)
        self._canvas = Canvas(self.statusBar(), self)
        self.setCentralWidget(self._canvas)

        self._build_menu()
        self._build_toolbar()

    # ── Меню ────────────────────────────────────────────────────
    def _build_menu(self):
        menu_bar = self.menuBar()

        # ── Файл ──
        file_menu: QMenu = menu_bar.addMenu("&Файл")
        act_clear = QAction("Очистить холст", self)
        act_clear.setShortcut(QKeySequence("Ctrl+N"))
        act_clear.triggered.connect(self._clear_canvas)
        file_menu.addAction(act_clear)

        file_menu.addSeparator()

        act_exit = QAction("Выход", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # ── Правка ──
        edit_menu: QMenu = menu_bar.addMenu("&Правка")

        act_select_all = QAction("Выделить все", self)
        act_select_all.setShortcut(QKeySequence("Ctrl+A"))
        act_select_all.triggered.connect(lambda: (
            self._canvas.storage.select_all(), self._canvas.update()
        ))
        edit_menu.addAction(act_select_all)

        act_delete = QAction("Удалить выделенные", self)
        act_delete.setShortcut(QKeySequence("Delete"))
        act_delete.triggered.connect(lambda: (
            self._canvas.storage.remove_selected(), self._canvas.update()
        ))
        edit_menu.addAction(act_delete)

        act_color = QAction("Изменить цвет…", self)
        act_color.setShortcut(QKeySequence("Ctrl+Shift+C"))
        act_color.triggered.connect(self._canvas.change_color_selected)
        edit_menu.addAction(act_color)

        # ── Фигуры ──
        shapes_menu: QMenu = menu_bar.addMenu("&Фигуры")
        shapes = [
            ("Круг",           CCircle),
            ("Эллипс",         CEllipse),
            ("Прямоугольник",  CRectangle),
            ("Квадрат",        CSquare),
            ("Треугольник",    CTriangle),
        ]
        for name, cls in shapes:
            act = QAction(name, self)
            act.triggered.connect(lambda checked, c=cls: self._canvas.set_shape_class(c))
            shapes_menu.addAction(act)

        # ── Справка ──
        help_menu: QMenu = menu_bar.addMenu("&Справка")
        act_about = QAction("О программе", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ── Панель инструментов ─────────────────────────────────────
    def _build_toolbar(self):
        toolbar = QToolBar("Инструменты", self)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Кнопки выбора типа фигуры — текстовые (иконки не требуются)
        shapes = [
            ("⬤  Круг",          CCircle),
            ("⬭  Эллипс",        CEllipse),
            ("▬  Прямоугольник", CRectangle),
            ("■  Квадрат",       CSquare),
            ("▲  Треугольник",   CTriangle),
        ]
        for label, cls in shapes:
            act = QAction(label, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, c=cls: self._canvas.set_shape_class(c))
            toolbar.addAction(act)

        toolbar.addSeparator()

        # Кнопка изменения цвета
        act_color = QAction("🎨 Цвет", self)
        act_color.setToolTip("Изменить цвет выделенных фигур")
        act_color.triggered.connect(self._canvas.change_color_selected)
        toolbar.addAction(act_color)

        # Кнопка удаления
        act_del = QAction("🗑 Удалить", self)
        act_del.setToolTip("Удалить выделенные фигуры (Del)")
        act_del.triggered.connect(lambda: (
            self._canvas.storage.remove_selected(), self._canvas.update()
        ))
        toolbar.addAction(act_del)

    # ── Действия ────────────────────────────────────────────────
    def _clear_canvas(self):
        reply = QMessageBox.question(
            self, "Очистить холст",
            "Удалить все фигуры?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            while self._canvas.storage.count() > 0:
                self._canvas.storage.select_all()
                self._canvas.storage.remove_selected()
            self._canvas.update()

    def _show_about(self):
        QMessageBox.information(
            self, "О программе",
            "Лабораторная работа 4 — «Визуальный редактор»\n\n"
            "Управление:\n"
            "  ЛКМ на пустом месте    — создать фигуру\n"
            "  ЛКМ по фигуре          — выделить\n"
            "  Ctrl+ЛКМ               — мультивыделение\n"
            "  ←↑↓→                   — переместить выделенное\n"
            "  + / -                  — изменить размер\n"
            "  Ctrl+Shift+C           — изменить цвет\n"
            "  Del                    — удалить выделенное\n"
            "  Ctrl+A                 — выделить все\n"
            "  Ctrl+N                 — очистить холст\n\n"
            "Иерархия: CShape → CCircle, CEllipse,\n"
            "  CRectangle → CSquare, CTriangle"
        )


# ─────────────────────────────────────────────────────────────────
#  Точка входа
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())