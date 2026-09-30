"""Экран загрузки перед основным окном RKNHS."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.app_icon_resources import resolve_existing_app_icon_path
from app.branding import APP_DISPLAY_NAME
from app.ui_texts import tr
from licensing.ui.startup_theme import apply_card_style, apply_label_style
from qfluentwidgets import BodyLabel, CardWidget, ProgressBar, SubtitleLabel


class _PulsingLogoLabel(QLabel):
    """Логотип с лёгкой пульсацией масштаба."""

    def __init__(self, pixmap: QPixmap, parent=None) -> None:
        super().__init__(parent)
        self._base_pixmap = pixmap
        self._scale = 1.0
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_scale(1.0)

    def _apply_scale(self, scale: float) -> None:
        self._scale = max(0.82, min(1.08, float(scale)))
        if self._base_pixmap.isNull():
            return
        side = int(72 * self._scale)
        self.setPixmap(
            self._base_pixmap.scaled(
                side,
                side,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def get_scale(self) -> float:
        return self._scale

    def set_scale(self, value: float) -> None:
        self._apply_scale(value)

    scale = pyqtProperty(float, get_scale, set_scale)


class StartupSplashScreen(QWidget):
    """Frameless splash с логотипом, прогрессом и сменяющимися подписями."""

    finished = pyqtSignal(object)

    _STEP_MS = 1050
    _FINAL_PAUSE_MS = 850
    _DOTS_MS = 380

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._license_status = None
        self._step_index = 0
        self._steps = self._build_steps()
        self._base_message = ""
        self._dots_phase = 0
        self._progress_anim: QPropertyAnimation | None = None
        self._status_fade_anim: QPropertyAnimation | None = None
        self._logo_scale_anim: QPropertyAnimation | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.SplashScreen
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(480, 320)

        icon_path = resolve_existing_app_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        card = CardWidget(self)
        apply_card_style(card)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 24, 28, 24)
        card_layout.setSpacing(14)

        self._logo_label = _PulsingLogoLabel(QPixmap(), card)
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self._logo_label = _PulsingLogoLabel(pixmap, card)
        card_layout.addWidget(self._logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title = SubtitleLabel(APP_DISPLAY_NAME, card)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        apply_label_style(title, role="primary")
        card_layout.addWidget(title)

        self._status_label = BodyLabel("", card)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        apply_label_style(self._status_label, role="secondary")
        self._status_effect = QGraphicsOpacityEffect(self._status_label)
        self._status_effect.setOpacity(1.0)
        self._status_label.setGraphicsEffect(self._status_effect)
        card_layout.addWidget(self._status_label)

        self._progress = ProgressBar(card)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        card_layout.addWidget(self._progress)

        dots_row = QHBoxLayout()
        dots_row.addStretch()
        self._dots_label = BodyLabel("", card)
        apply_label_style(self._dots_label, role="muted")
        self._dots_label.setStyleSheet(self._dots_label.styleSheet() + " letter-spacing: 2px;")
        self._dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dots_row.addWidget(self._dots_label)
        dots_row.addStretch()
        card_layout.addLayout(dots_row)

        outer.addWidget(card)

        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._tick_dots)

    @staticmethod
    def _build_steps() -> tuple[tuple[str, int], ...]:
        return (
            (tr("startup.splash.step.boot", default="Загружаем программу RKNHS…"), 10),
            (tr("startup.splash.step.fun", default="Проверяем приколы…"), 30),
            (tr("startup.splash.step.connect", default="Коннектимся…"), 55),
            (tr("startup.splash.step.license", default="Проверяем лицензию…"), 78),
        )

    def center_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        self.move(
            geo.center().x() - self.width() // 2,
            geo.center().y() - self.height() // 2,
        )

    def start(self, *, license_check: Callable[[], object]) -> None:
        self._license_check = license_check
        self._step_index = 0
        self._progress.setValue(0)
        self._start_logo_pulse()
        self._dots_timer.start(self._DOTS_MS)
        QTimer.singleShot(180, self._advance_step)

    def _start_logo_pulse(self) -> None:
        if self._logo_scale_anim is not None:
            self._logo_scale_anim.stop()
        self._logo_scale_anim = QPropertyAnimation(self._logo_label, b"scale", self)
        self._logo_scale_anim.setDuration(1400)
        self._logo_scale_anim.setStartValue(0.92)
        self._logo_scale_anim.setEndValue(1.06)
        self._logo_scale_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._logo_scale_anim.setLoopCount(-1)
        self._logo_scale_anim.start()

    def _tick_dots(self) -> None:
        if not self._base_message:
            self._dots_label.setText("")
            return
        self._dots_phase = (self._dots_phase + 1) % 4
        self._dots_label.setText("." * self._dots_phase)

    def _animate_progress_to(self, value: int) -> None:
        if self._progress_anim is not None:
            self._progress_anim.stop()
        self._progress_anim = QPropertyAnimation(self._progress, b"value", self)
        self._progress_anim.setDuration(720)
        self._progress_anim.setStartValue(self._progress.value())
        self._progress_anim.setEndValue(int(value))
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.start()

    def _set_status_message(self, message: str, *, animated: bool = True) -> None:
        self._base_message = str(message or "")
        self._dots_phase = 0

        def _apply_text() -> None:
            self._status_label.setText(self._base_message)

        if not animated or not self._base_message:
            _apply_text()
            self._status_effect.setOpacity(1.0)
            return

        if self._status_fade_anim is not None:
            self._status_fade_anim.stop()

        fade_out = QPropertyAnimation(self._status_effect, b"opacity", self)
        fade_out.setDuration(160)
        fade_out.setStartValue(self._status_effect.opacity())
        fade_out.setEndValue(0.15)
        fade_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        fade_in = QPropertyAnimation(self._status_effect, b"opacity", self)
        fade_in.setDuration(220)
        fade_in.setStartValue(0.15)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InQuad)

        fade_out.finished.connect(_apply_text)
        fade_out.finished.connect(fade_in.start)
        self._status_fade_anim = fade_out
        fade_out.start()

    def _advance_step(self) -> None:
        if self._step_index >= len(self._steps):
            self._animate_progress_to(100)
            QTimer.singleShot(self._FINAL_PAUSE_MS, self._complete)
            return

        message, progress_value = self._steps[self._step_index]
        self._set_status_message(message)
        self._animate_progress_to(progress_value)

        if self._step_index == len(self._steps) - 1:
            try:
                self._license_status = self._license_check()
            except Exception:
                from licensing.service import get_current_license_status

                self._license_status = get_current_license_status()

        self._step_index += 1
        QTimer.singleShot(self._STEP_MS, self._advance_step)

    def _complete(self) -> None:
        self._dots_timer.stop()
        if self._logo_scale_anim is not None:
            self._logo_scale_anim.stop()
        self.finished.emit(self._license_status)
        self.close()


__all__ = ["StartupSplashScreen"]
