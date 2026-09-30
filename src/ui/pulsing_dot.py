from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

# ~7 FPS is enough for phosphor blink; 70ms was unnecessarily hot on idle Control.
_PULSE_INTERVAL_MS = 140


class PulsingDot(QWidget):
    """Animated status dot with a low-frequency timer."""

    def __init__(self, parent=None, *, size: int = 32):
        super().__init__(parent)
        self._color = QColor("#aeb5c1")
        self._pulse_phase = 0.0
        self._is_pulsing = False

        self.setFixedSize(max(12, int(size)), max(12, int(size)))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._timer = QTimer(self)
        self._timer.setInterval(_PULSE_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

    def set_color(self, color: str) -> None:
        c = QColor(color)
        if c.isValid():
            self._color = c
        self.update()

    def start_pulse(self) -> None:
        if not self._is_pulsing:
            self._is_pulsing = True
            self._pulse_phase = 0.0
        self._sync_timer()

    def stop_pulse(self) -> None:
        self._is_pulsing = False
        self._timer.stop()
        self._pulse_phase = 0.0
        self.update()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._sync_timer()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self._timer.stop()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._sync_timer()

    def _window_is_active_for_pulse(self) -> bool:
        if not self.isVisible():
            return False
        window = self.window()
        if window is None:
            return True
        try:
            if window.isMinimized():
                return False
            if hasattr(window, "isVisible") and not window.isVisible():
                return False
        except Exception:
            return True
        return True

    def _sync_timer(self) -> None:
        should_run = bool(self._is_pulsing and self._window_is_active_for_pulse())
        if should_run:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def _tick(self) -> None:
        if not self._window_is_active_for_pulse():
            self._timer.stop()
            return
        self._pulse_phase = (self._pulse_phase + 0.14) % 1.0
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        _ = event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = max(12, min(self.width(), self.height()))
        # Square phosphor LED (operator console), not soft Win11 orb.
        pad = max(2, int(side * 0.22))
        box = self.rect().adjusted(pad, pad, -pad, -pad)
        core = max(2, int(side * 0.18))

        if self._is_pulsing:
            phase = self._pulse_phase % 1.0
            glow = QColor(self._color)
            glow.setAlphaF(max(0.0, 0.45 * (1.0 - phase)))
            expand = int(2 + phase * max(2, side * 0.18))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(box.adjusted(-expand, -expand, expand, expand), 1, 1)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color)
        painter.drawRoundedRect(box, 1, 1)

        shine = QColor(255, 255, 255, 90)
        painter.setBrush(shine)
        painter.drawRect(box.x() + 1, box.y() + 1, max(1, core), max(1, int(core * 0.6)))
