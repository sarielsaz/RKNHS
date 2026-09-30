from __future__ import annotations

from PyQt6.QtGui import QIcon

from qfluentwidgets import PushButton, TransparentPushButton
from ui.accessibility import set_control_accessibility, set_state_text
from ui.theme import get_themed_qta_icon, get_theme_tokens
from ui.tech_style import build_ghost_button_qss, build_primary_button_qss


_DANGER_BUTTON_QSS = (
    "QPushButton{background-color:#FF5C7A;color:#0A0C10;border:none;border-radius:2px;}"
    "QPushButton:hover{background-color:#ff7a92;}"
    "QPushButton:pressed{background-color:#e04562;}"
)


def _resolve_icon(icon_name: str | None, color: str | None) -> QIcon:
    if not icon_name:
        return QIcon()

    try:
        return get_themed_qta_icon(icon_name, color=color)
    except Exception:
        return QIcon()


def _configure_button_icon(button, icon_name: str | None, icon_color: str | None) -> None:
    try:
        button.setIcon(_resolve_icon(icon_name, icon_color))
    except Exception:
        pass


def create_dialog_action_button(
    parent,
    *,
    text: str,
    icon_name: str | None = None,
    icon_color: str | None = None,
    danger: bool = False,
) -> PushButton:
    """Создаёт обычную fluent-кнопку действия для диалога."""

    button = PushButton(parent)
    button.setText(text)
    button.setMinimumHeight(34)
    _configure_button_icon(button, icon_name, icon_color)
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
            button.setStyleSheet(build_ghost_button_qss(get_theme_tokens()))
        except Exception:
            pass

    return button


def create_dialog_cancel_button(
    parent,
    *,
    text: str,
    icon_name: str | None = None,
    icon_color: str | None = None,
) -> TransparentPushButton:
    """Создаёт прозрачную fluent-кнопку отмены."""

    button = TransparentPushButton(parent)
    button.setText(text)
    button.setMinimumHeight(34)
    _configure_button_icon(button, icon_name, icon_color)
    set_state_text(button, text)
    set_control_accessibility(
        button,
        name=text,
        description="Закрывает диалог без выполнения действия.",
    )
    try:
        button.setStyleSheet(build_ghost_button_qss(get_theme_tokens()))
    except Exception:
        pass
    return button
