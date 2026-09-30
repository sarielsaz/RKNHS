from __future__ import annotations

from PyQt6.QtCore import QSize

from ui.accessibility import set_control_accessibility, set_state_text


def _clean_text(text: object) -> str:
    return " ".join(str(text or "").strip().split())


def _object_text(obj) -> str:
    if obj is None:
        return ""
    text_fn = getattr(obj, "text", None)
    if callable(text_fn):
        try:
            return _clean_text(text_fn())
        except Exception:
            return ""
    return ""


def _message_box_title(box) -> str:
    title = _clean_text(getattr(box, "title", ""))
    if title:
        return title
    title = _object_text(getattr(box, "titleLabel", None))
    if title:
        return title
    window_title = getattr(box, "windowTitle", None)
    if callable(window_title):
        try:
            return _clean_text(window_title())
        except Exception:
            return ""
    return ""


def _message_box_body(box) -> str:
    body = _clean_text(getattr(box, "body", ""))
    if body:
        return body
    body = _object_text(getattr(box, "contentLabel", None))
    if body:
        return body
    text_fn = getattr(box, "text", None)
    if callable(text_fn):
        try:
            return _clean_text(text_fn())
        except Exception:
            return ""
    return ""


def _set_message_box_accessibility(box) -> None:
    if box is None:
        return
    title = _message_box_title(box)
    body = _message_box_body(box)
    parts = []
    if title:
        parts.append(f"Диалог: {title}")
    else:
        parts.append("Диалог")
    if body:
        parts.append(body)
    text = ". ".join(parts)
    set_state_text(box, text)
    set_control_accessibility(box, name=text, description=body or title or text)


_DESTRUCTIVE_MARKERS = (
    "удал",
    "очист",
    "сброс",
    "стоп",
    "останов",
    "delete",
    "remove",
    "clear",
    "reset",
    "stop",
)


def _looks_destructive(text: str) -> bool:
    lowered = str(text or "").casefold()
    return any(marker in lowered for marker in _DESTRUCTIVE_MARKERS)


def _apply_button_icon(button, fluent_icon) -> None:
    if button is None or fluent_icon is None:
        return
    set_icon = getattr(button, "setIcon", None)
    if not callable(set_icon):
        return
    try:
        set_icon(fluent_icon)
        set_icon_size = getattr(button, "setIconSize", None)
        if callable(set_icon_size):
            set_icon_size(QSize(16, 16))
    except Exception:
        pass


def polish_message_box_buttons(
    box,
    *,
    yes_button=None,
    cancel_button=None,
    yes_icon=None,
    cancel_icon=None,
    danger_yes: bool | None = None,
) -> None:
    """Align Fluent MessageBox action icons like CloseDialog (icon + text baseline)."""
    if box is None:
        return
    if yes_button is None:
        yes_button = getattr(box, "yesButton", None)
    if cancel_button is None:
        cancel_button = getattr(box, "cancelButton", None)

    try:
        from qfluentwidgets import FluentIcon
    except Exception:
        return

    yes_text = _object_text(yes_button)
    if yes_icon is None:
        yes_icon = FluentIcon.DELETE if _looks_destructive(yes_text) else FluentIcon.ACCEPT
    if cancel_icon is None:
        cancel_icon = FluentIcon.CANCEL
    if danger_yes is None:
        danger_yes = _looks_destructive(yes_text)

    _apply_button_icon(yes_button, yes_icon)
    _apply_button_icon(cancel_button, cancel_icon)

    if yes_button is not None and danger_yes:
        try:
            yes_button.setStyleSheet(
                "QPushButton{background-color:#FF5C7A;color:#0A0C10;border:none;"
                "border-radius:2px;padding:8px 16px 8px 12px;min-height:34px;}"
                "QPushButton:hover{background-color:#ff7a92;}"
                "QPushButton:pressed{background-color:#e04562;}"
            )
        except Exception:
            pass
    elif yes_button is not None:
        try:
            yes_button.setStyleSheet(
                "QPushButton{padding:8px 16px 8px 12px;min-height:34px;text-align:left;}"
            )
        except Exception:
            pass

    if cancel_button is not None:
        try:
            cancel_button.setStyleSheet(
                "QPushButton{padding:8px 16px 8px 12px;min-height:34px;text-align:left;}"
            )
        except Exception:
            pass


def set_message_box_button_accessibility(
    box,
    *,
    yes_name: str,
    yes_description: str,
    cancel_name: str,
    cancel_description: str,
    yes_button=None,
    cancel_button=None,
    yes_icon=None,
    cancel_icon=None,
    danger_yes: bool | None = None,
) -> None:
    _set_message_box_accessibility(box)
    if yes_button is None:
        yes_button = getattr(box, "yesButton", None)
    if yes_button is not None:
        set_state_text(yes_button, yes_name)
        set_control_accessibility(yes_button, name=yes_name, description=yes_description)
    if cancel_button is None:
        cancel_button = getattr(box, "cancelButton", None)
    if cancel_button is not None:
        set_state_text(cancel_button, cancel_name)
        set_control_accessibility(cancel_button, name=cancel_name, description=cancel_description)
    polish_message_box_buttons(
        box,
        yes_button=yes_button,
        cancel_button=cancel_button,
        yes_icon=yes_icon,
        cancel_icon=cancel_icon,
        danger_yes=danger_yes,
    )


__all__ = ["polish_message_box_buttons", "set_message_box_button_accessibility"]
