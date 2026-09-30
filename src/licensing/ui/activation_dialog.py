"""Окно ввода лицензии до запуска основного GUI."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel

from app.app_icon_resources import resolve_existing_app_icon_path
from app.branding import APP_DISPLAY_NAME
from app.ui_texts import tr
from licensing.service import activate_license_key
from licensing.ui.startup_theme import apply_label_style, apply_line_edit_style, apply_window_style
from licensing.clipboard import copy_text_to_clipboard
from qfluentwidgets import BodyLabel, CaptionLabel, LineEdit, PrimaryPushButton, PushButton, SubtitleLabel


class LicenseActivationDialog(QDialog):
    """Модальное окно активации: отпечаток + ключ. Закрытие без активации = выход из программы."""

    def __init__(self, *, machine_id: str, parent=None) -> None:
        super().__init__(parent)
        self._machine_id = str(machine_id or "")
        self.setWindowTitle(tr("startup.license.dialog.title", default="Активация RKNHS"))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)

        icon_path = resolve_existing_app_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        apply_window_style(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        if icon_path:
            logo = QLabel(self)
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
            header_row.addWidget(logo)
        title = SubtitleLabel(tr("startup.license.dialog.heading", default=f"Нужна лицензия {APP_DISPLAY_NAME}"), self)
        title.setWordWrap(True)
        apply_label_style(title, role="primary")
        header_row.addWidget(title, 1)
        root.addLayout(header_row)

        intro = BodyLabel(
            tr(
                "startup.license.dialog.intro",
                default=(
                    "Программа работает только с действующим ключом на этом компьютере. "
                    "Без активации окно закроется — это нормально."
                ),
            ),
            self,
        )
        intro.setWordWrap(True)
        apply_label_style(intro, role="secondary")
        root.addWidget(intro)

        fingerprint_title = CaptionLabel(
            tr("startup.license.dialog.fingerprint_title", default="Отпечаток этого компьютера"),
            self,
        )
        apply_label_style(fingerprint_title, role="primary")
        root.addWidget(fingerprint_title)

        fingerprint_row = QHBoxLayout()
        self._machine_label = BodyLabel(self._machine_id, self)
        self._machine_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._machine_label.setWordWrap(True)
        apply_label_style(self._machine_label, role="primary")
        self._machine_label.setStyleSheet(
            self._machine_label.styleSheet() + " font-family: Consolas, 'Courier New', monospace;"
        )
        fingerprint_row.addWidget(self._machine_label, 1)

        copy_btn = PushButton(tr("page.about.license.copy_fingerprint", default="Копировать"), self)
        copy_btn.clicked.connect(self._copy_fingerprint)
        self._copy_btn = copy_btn
        fingerprint_row.addWidget(copy_btn)
        root.addLayout(fingerprint_row)

        hint = BodyLabel(
            tr(
                "startup.license.dialog.fingerprint_hint",
                default=(
                    "Отпечаток — уникальный идентификатор вашего ПК (железо + соль). "
                    "Скопируйте его и передайте автору программы — по нему выпускают ключ, "
                    "привязанный только к этому компьютеру. На другом ПК тот же ключ не подойдёт."
                ),
            ),
            self,
        )
        hint.setWordWrap(True)
        apply_label_style(hint, role="muted")
        root.addWidget(hint)

        key_caption = CaptionLabel(tr("startup.license.dialog.key_caption", default="Лицензионный ключ"), self)
        apply_label_style(key_caption, role="primary")
        root.addWidget(key_caption)

        self._key_edit = LineEdit(self)
        apply_line_edit_style(self._key_edit)
        self._key_edit.setPlaceholderText(tr("page.about.license.key_placeholder", default="RKNHS-L1.…"))
        self._key_edit.setClearButtonEnabled(True)
        root.addWidget(self._key_edit)

        self._error_label = BodyLabel("", self)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet("color: #c0392b;")
        self._error_label.hide()
        root.addWidget(self._error_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._activate_btn = PrimaryPushButton(tr("page.about.license.activate", default="Активировать"), self)
        self._activate_btn.clicked.connect(self._on_activate)
        btn_row.addWidget(self._activate_btn)
        root.addLayout(btn_row)

        self._key_edit.returnPressed.connect(self._on_activate)

    def _copy_fingerprint(self) -> None:
        if copy_text_to_clipboard(self._machine_id):
            self._copy_btn.setText(tr("page.about.license.copy_fingerprint_done", default="Скопировано"))
            from PyQt6.QtCore import QTimer

            QTimer.singleShot(
                2000,
                lambda: self._copy_btn.setText(
                    tr("page.about.license.copy_fingerprint", default="Копировать")
                ),
            )
        else:
            self._show_error("Не удалось скопировать отпечаток в буфер обмена.")

    def _show_error(self, message: str) -> None:
        self._error_label.setText(str(message or ""))
        self._error_label.setVisible(bool(message))

    def _on_activate(self) -> None:
        key = self._key_edit.text().strip()
        if not key:
            self._show_error(tr("page.about.license.key_missing", default="Вставьте лицензионный ключ."))
            return

        status = activate_license_key(key)
        if not status.valid:
            self._show_error(status.message)
            return

        self.accept()


__all__ = ["LicenseActivationDialog"]
