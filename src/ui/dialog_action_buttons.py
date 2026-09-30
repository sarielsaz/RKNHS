from __future__ import annotations

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon

from qfluentwidgets import FluentIcon, PushButton, TransparentPushButton
from ui.accessibility import set_control_accessibility, set_state_text
from ui.theme import get_themed_qta_icon, get_theme_tokens
from ui.tech_style import build_ghost_button_qss, build_primary_button_qss


_DANGER_BUTTON_QSS = (
    "QPushButton{background-color:#FF5C7A;color:#0A0C10;border:none;border-radius:2px;"
    "padding:8px 16px 8px 12px;min-height:36px;text-align:left;}"
    "QPushButton:hover{background-color:#ff7a92;}"
    "QPushButton:pressed{background-color:#e04562;}"
)

_ICON_BUTTON_EXTRA_QSS = "padding:8px 16px 8px 12px;min-height:36px;text-align:left;"


def _resolve_icon(icon_name: str | None, color: str | None) -> QIcon:
    if not icon_name:
        return QIcon()

    try:
        return get_themed_qta_icon(icon_name, color=color)
    except Exception:
        return QIcon()


def _apply_button_icon(
    button,
    *,
    fluent_icon: FluentIcon | None = None,
    icon_name: str | None = None,
    icon_color: str | None = None,
) -> None:
    try:
        if fluent_icon is not None:
            button.setIcon(fluent_icon)
        elif icon_name:
            button.setIcon(_resolve_icon(icon_name, icon_color))
        button.setIconSize(QSize(16, 16))
    except Exception:
        pass


def create_dialog_action_button(
    parent,
    *,
    text: str,
    icon_name: str | None = None,
    icon_color: str | None = None,
    fluent_icon: FluentIcon | None = None,
    danger: bool = False,
) -> PushButton:
    """Создаёт fluent-кнопку действия для диалога с ровным icon+text."""

    button = PushButton(parent)
    button.setText(text)
    button.setMinimumHeight(36)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    _apply_button_icon(
        button,
        fluent_icon=fluent_icon,
        icon_name=icon_name,
        icon_color=icon_color,
    )
    set_state_text(button, text)
    set_control_accessibility(
        button,
        name=text,
        description=f"Выполняет действие диалога: {text}.",
    )

    if danger:
        try:
            button.setStyleSheet(_DANGER_BUTTON_QSS)
        except Exception:
            pass
    else:
        try:
            ghost = build_ghost_button_qss(get_theme_tokens())
            # Keep icon and label on one baseline; Fluent default padding crowds qtawesome icons.
            button.setStyleSheet(ghost.replace("padding:6px 14px;min-height:32px;", _ICON_BUTTON_EXTRA_QSS))
        except Exception:
            pass

    return button


def create_dialog_cancel_button(
    parent,
    *,
    text: str,
    icon_name: str | None = None,
    icon_color: str | None = None,
    fluent_icon: FluentIcon | None = None,
) -> TransparentPushButton:
    """Создаёт прозрачную fluent-кнопку отмены."""

    button = TransparentPushButton(parent)
    button.setText(text)
    button.setMinimumHeight(36)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    _apply_button_icon(
        button,
        fluent_icon=fluent_icon,
        icon_name=icon_name,
        icon_color=icon_color,
    )
    set_state_text(button, text)
    set_control_accessibility(
        button,
        name=text,
        description="Закрывает диалог без выполнения действия.",
    )
    try:
        ghost = build_ghost_button_qss(get_theme_tokens())
        button.setStyleSheet(ghost.replace("padding:6px 14px;min-height:32px;", _ICON_BUTTON_EXTRA_QSS))
    except Exception:
        pass
    return button
