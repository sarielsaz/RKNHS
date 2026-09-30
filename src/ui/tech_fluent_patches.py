"""Monkey-patches for qfluentwidgets — hacker/operator console surfaces (DESIGN.md).

Fluent paints cards, settings rows, nav items, and switches with QPainter.
This module forces void/panel fills, sharp radii, cyan rails, and corner brackets.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen

_PATCHED = False

_VOID = QColor(0x0A, 0x0C, 0x10)
_PANEL = QColor(0x12, 0x15, 0x1C)
_PANEL_HOVER = QColor(0x18, 0x1C, 0x26)
_PANEL_PRESSED = QColor(0x0E, 0x11, 0x17)
_HAIRLINE = QColor(255, 255, 255, 28)
_HAIRLINE_HOVER = QColor(92, 214, 255, 110)
_ACCENT = QColor(0x5C, 0xD6, 0xFF)
_ACCENT_DIM = QColor(92, 214, 255, 36)
_BRACKET = QColor(92, 214, 255, 160)


def draw_corner_brackets(
    painter: QPainter,
    rect: QRect,
    *,
    color: QColor | None = None,
    length: int = 7,
    inset: int = 2,
) -> None:
    """Draw CRT/operator corner ticks — signature of the console shell."""
    pen = QPen(color or _BRACKET)
    pen.setWidth(1)
    pen.setCosmetic(True)
    painter.setPen(pen)
    x = rect.x() + inset
    y = rect.y() + inset
    w = rect.width() - 2 * inset
    h = rect.height() - 2 * inset
    if w < length * 2 + 4 or h < length * 2 + 4:
        return
    # top-left
    painter.drawLine(x, y, x + length, y)
    painter.drawLine(x, y, x, y + length)
    # top-right
    painter.drawLine(x + w, y, x + w - length, y)
    painter.drawLine(x + w, y, x + w, y + length)
    # bottom-left
    painter.drawLine(x, y + h, x + length, y + h)
    painter.drawLine(x, y + h, x, y + h - length)
    # bottom-right
    painter.drawLine(x + w, y + h, x + w - length, y + h)
    painter.drawLine(x + w, y + h, x + w, y + h - length)


def install_tech_fluent_patches() -> None:
    """Install once. Safe to call repeatedly."""
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    from qfluentwidgets.common.style_sheet import isDarkTheme
    from qfluentwidgets.common.icon import drawIcon
    from qfluentwidgets.components.navigation.navigation_widget import NavigationPushButton
    from qfluentwidgets.components.settings.setting_card import SettingCard
    from qfluentwidgets.components.widgets.card_widget import (
        CardWidget,
        ElevatedCardWidget,
        SimpleCardWidget,
    )
    from qfluentwidgets.components.widgets.switch_button import Indicator
    from PyQt6.QtCore import QPoint
    from PyQt6.QtGui import QCursor

    def _card_normal(self):
        if isDarkTheme():
            return QColor(_PANEL)
        return QColor(255, 255, 255, 170)

    def _card_hover(self):
        if isDarkTheme():
            return QColor(_PANEL_HOVER)
        return QColor(255, 255, 255, 64)

    def _card_pressed(self):
        if isDarkTheme():
            return QColor(_PANEL_PRESSED)
        return QColor(255, 255, 255, 64)

    CardWidget._normalBackgroundColor = _card_normal
    CardWidget._hoverBackgroundColor = _card_hover
    CardWidget._pressedBackgroundColor = _card_pressed
    SimpleCardWidget._normalBackgroundColor = _card_normal
    SimpleCardWidget._hoverBackgroundColor = _card_normal
    SimpleCardWidget._pressedBackgroundColor = _card_normal
    ElevatedCardWidget._normalBackgroundColor = _card_normal
    ElevatedCardWidget._hoverBackgroundColor = _card_hover
    ElevatedCardWidget._pressedBackgroundColor = _card_pressed

    _orig_card_paint = CardWidget.paintEvent
    _orig_simple_paint = SimpleCardWidget.paintEvent

    def _tech_card_paint(self, e):
        if not isDarkTheme():
            return _orig_card_paint(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        r = 2
        try:
            if int(getattr(self, "borderRadius", 2) or 2) != 2:
                self.setBorderRadius(2)
        except Exception:
            pass
        hover = bool(getattr(self, "isHover", False))
        pen = QPen(_HAIRLINE_HOVER if hover else _HAIRLINE)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)
        draw_corner_brackets(painter, self.rect(), color=_BRACKET if hover else QColor(92, 214, 255, 120))

    def _tech_simple_paint(self, e):
        if not isDarkTheme():
            return _orig_simple_paint(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(_HAIRLINE))
        painter.setBrush(self.backgroundColor)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 2, 2)
        draw_corner_brackets(painter, self.rect())

    CardWidget.paintEvent = _tech_card_paint
    SimpleCardWidget.paintEvent = _tech_simple_paint
    ElevatedCardWidget.paintEvent = _tech_simple_paint

    _orig_setting_paint = SettingCard.paintEvent

    def _tech_setting_paint(self, e):
        if not isDarkTheme():
            return _orig_setting_paint(self, e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing)
        painter.setBrush(_PANEL)
        painter.setPen(QPen(_HAIRLINE))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 2, 2)
        draw_corner_brackets(painter, self.rect(), length=6)

    SettingCard.paintEvent = _tech_setting_paint

    _orig_nav_paint = NavigationPushButton.paintEvent

    def _tech_nav_paint(self, e):
        if not isDarkTheme():
            return _orig_nav_paint(self, e)

        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        painter.setPen(Qt.PenStyle.NoPen)

        if self.isPressed:
            painter.setOpacity(0.75)
        if not self.isEnabled():
            painter.setOpacity(0.4)

        m = self._margins()
        pl, pr = m.left(), m.right()
        global_rect = QRect(self.mapToGlobal(QPoint()), self.size())
        selected = bool(self._canDrawIndicator())
        hovering = (
            (self.isEnter and global_rect.contains(QCursor.pos())) or self.isAboutSelected
        ) and self.isEnabled()

        if selected:
            painter.setBrush(_ACCENT_DIM)
            painter.drawRoundedRect(self.rect().adjusted(4, 2, -4, -2), 2, 2)
            painter.setBrush(_ACCENT)
            painter.drawRoundedRect(self.indicatorRect(), 1, 1)
        elif hovering:
            painter.setBrush(QColor(255, 255, 255, 14))
            painter.drawRoundedRect(self.rect().adjusted(4, 2, -4, -2), 2, 2)

        drawIcon(self._icon, painter, QRectF(11.5 + pl, 10, 16, 16))
        if self.isCompacted:
            return
        painter.setFont(self.font())
        painter.setPen(self.textColor())
        left = 44 + pl if not self.icon().isNull() else pl + 16
        painter.drawText(
            QRectF(left, 0, self.width() - 13 - left - pr, self.height()),
            Qt.AlignmentFlag.AlignVCenter,
            self.text(),
        )

    NavigationPushButton.paintEvent = _tech_nav_paint

    def _tech_switch_bg(self, painter: QPainter):
        painter.setPen(self._borderColor())
        painter.setBrush(self._backgroundColor())
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 2, 2)

    def _tech_switch_thumb(self, painter: QPainter):
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._sliderColor())
        painter.drawRoundedRect(int(self.sliderX), 5, 12, 12, 2, 2)

    Indicator._drawBackground = _tech_switch_bg
    Indicator._drawCircle = _tech_switch_thumb


def apply_tech_nav_indicators(window, accent: QColor | None = None) -> None:
    if window is None:
        return
    try:
        from qfluentwidgets.components.navigation.navigation_widget import NavigationWidget
    except Exception:
        return

    color = accent or QColor(_ACCENT)
    light = QColor(color)
    dark = QColor(color)
    try:
        for widget in window.findChildren(NavigationWidget):
            try:
                widget.setIndicatorColor(light, dark)
                widget.update()
            except Exception:
                continue
    except Exception:
        pass


def apply_tech_card_radii(window) -> None:
    if window is None:
        return
    try:
        from qfluentwidgets.components.widgets.card_widget import CardWidget
    except Exception:
        return
    try:
        for card in window.findChildren(CardWidget):
            try:
                card.setBorderRadius(2)
                if hasattr(card, "_updateBackgroundColor"):
                    card._updateBackgroundColor()
            except Exception:
                continue
    except Exception:
        pass


def force_void_window_background(window, void_hex: str = "#0A0C10") -> None:
    if window is None:
        return
    color = QColor(void_hex)
    if not color.isValid():
        color = _VOID
    try:
        if hasattr(window, "windowEffect"):
            try:
                window.windowEffect.removeBackgroundEffect(window.winId())
            except Exception:
                pass
    except Exception:
        pass
    try:
        if hasattr(window, "setMicaEffectEnabled"):
            window.setMicaEffectEnabled(False)
    except Exception:
        pass
    try:
        if hasattr(window, "setCustomBackgroundColor"):
            window.setCustomBackgroundColor(color, color)
    except Exception:
        pass
    try:
        window._darkBackgroundColor = color
        window._lightBackgroundColor = color
    except Exception:
        pass
    try:
        if hasattr(window, "clear_tint_overlay"):
            window.clear_tint_overlay()
    except Exception:
        pass
    try:
        window.setWindowOpacity(1.0)
    except Exception:
        pass


__all__ = [
    "apply_tech_card_radii",
    "apply_tech_nav_indicators",
    "draw_corner_brackets",
    "force_void_window_background",
    "install_tech_fluent_patches",
]
