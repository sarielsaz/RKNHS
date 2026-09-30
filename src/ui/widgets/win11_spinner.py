"""Windows 11 style spinner - rotating arc indicator"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ui.theme import get_theme_tokens


class Win11Spinner(QWidget):
    """Спиннер в стиле Windows 11 - кольцо с бегущей дугой"""

    def __init__(self, size=20, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._size = size
        if color is None:
            try:
                color = get_theme_tokens().accent_hex
            except Exception:
                color = "#5caee8"
        self._color = QColor(color)
        self._angle = 0
        self._arc_length = 90  # Длина дуги в градусах
        self._running = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        """Запускает анимацию"""
        self._running = True
        try:
            if self._timer.isActive():
                return
        except Exception:
            pass
        # ~30 FPS is enough for a small indeterminate spinner.
        self._timer.start(33)
        self.show()

    def stop(self):
        """Останавливает анимацию"""
        self._running = False
        try:
            if not self._timer.isActive():
                return
        except Exception:
            pass
        self._timer.stop()
        self.hide()

    def hideEvent(self, event):  # noqa: N802
        try:
            self._timer.stop()
        except Exception:
            pass
        super().hideEvent(event)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if self._running and self.isVisible() and not self._timer.isActive():
            self._timer.start(33)

    def _rotate(self):
        if not self._running or not self.isVisible():
            try:
                self._timer.stop()
            except Exception:
                pass
            return
        self._angle = (self._angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Фоновое кольцо (полупрозрачное)
        try:
            tokens = get_theme_tokens()
            ring = QColor(0, 0, 0, 30) if tokens.is_light else QColor(255, 255, 255, 30)
        except Exception:
            ring = QColor(245, 245, 245, 30)
        pen = QPen(ring)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        margin = 3
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        painter.drawEllipse(rect)

        # Активная дуга
        pen.setColor(self._color)
        painter.setPen(pen)

        start_angle = int((90 - self._angle) * 16)
        span_angle = int(-self._arc_length * 16)
        painter.drawArc(rect, start_angle, span_angle)
