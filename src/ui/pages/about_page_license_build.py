"""Блок лицензии на вкладке «О программе»."""

from __future__ import annotations

from collections.abc import Callable

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
)
from settings.store import get_license_record


@dataclass(slots=True)
class AboutPageLicenseWidgets:
    license_card: object
    machine_id_label: object
    status_label: object
    key_edit: object
    activate_btn: object
    copy_machine_btn: object
    deactivate_btn: object


def build_about_page_license_content(
    layout,
    *,
    tr_fn: Callable[[str, str], str],
    content_parent,
    machine_id: str,
    status_text: str,
    status_valid: bool,
    on_activate,
    on_deactivate,
    on_copy_machine_id,
) -> AboutPageLicenseWidgets:
    section = StrongBodyLabel(tr_fn("page.about.license.section", "Лицензия"), content_parent)
    layout.addWidget(section)

    card = CardWidget(content_parent)
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(16, 12, 16, 12)
    card_layout.setSpacing(10)

    hint = CaptionLabel(
        tr_fn(
            "page.about.license.hint",
            "Скопируйте отпечаток устройства и передайте его для выпуска ключа. "
            "Ключ привязан к этому ПК и проверяется по подписи Ed25519.",
        ),
        card,
    )
    hint.setWordWrap(True)
    card_layout.addWidget(hint)

    machine_row = QHBoxLayout()
    machine_caption = CaptionLabel(tr_fn("page.about.license.machine_id", "Отпечаток устройства:"), card)
    machine_id_label = BodyLabel(machine_id, card)
    machine_id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    machine_id_label.setWordWrap(True)
    copy_machine_btn = PushButton(tr_fn("page.about.license.copy_fingerprint", "Копировать"), card)
    copy_machine_btn.clicked.connect(on_copy_machine_id)
    machine_row.addWidget(machine_caption)
    machine_row.addWidget(machine_id_label, 1)
    machine_row.addWidget(copy_machine_btn)
    card_layout.addLayout(machine_row)

    status_label = BodyLabel(status_text, card)
    status_label.setWordWrap(True)
    if status_valid:
        status_label.setStyleSheet("color: #2e7d32;")
    else:
        status_label.setStyleSheet("color: #c0392b;")
    card_layout.addWidget(status_label)

    key_edit = LineEdit(card)
    stored_key = str(get_license_record().get("key") or "")
    key_edit.setText(stored_key)
    key_edit.setPlaceholderText(tr_fn("page.about.license.key_placeholder", "RKNHS-L1.…"))
    key_edit.setClearButtonEnabled(True)
    card_layout.addWidget(key_edit)

    btn_row = QHBoxLayout()
    activate_btn = PrimaryPushButton(tr_fn("page.about.license.activate", "Активировать"), card)
    activate_btn.clicked.connect(on_activate)
    deactivate_btn = PushButton(tr_fn("page.about.license.deactivate", "Сбросить"), card)
    deactivate_btn.clicked.connect(on_deactivate)
    deactivate_btn.setEnabled(bool(stored_key.strip()))
    btn_row.addWidget(activate_btn)
    btn_row.addWidget(deactivate_btn)
    btn_row.addStretch()
    card_layout.addLayout(btn_row)

    layout.addWidget(card)
    layout.addSpacing(12)

    return AboutPageLicenseWidgets(
        license_card=card,
        machine_id_label=machine_id_label,
        status_label=status_label,
        key_edit=key_edit,
        activate_btn=activate_btn,
        copy_machine_btn=copy_machine_btn,
        deactivate_btn=deactivate_btn,
    )


def copy_text_to_clipboard(text: str) -> bool:
    from licensing.clipboard import copy_text_to_clipboard as _copy

    return _copy(text)


__all__ = ["AboutPageLicenseWidgets", "build_about_page_license_content", "copy_text_to_clipboard"]
