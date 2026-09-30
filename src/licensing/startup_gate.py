"""Проверка лицензии при старте: splash → окно активации (если нужно)."""

from __future__ import annotations

from PyQt6.QtCore import QEventLoop
from PyQt6.QtWidgets import QApplication, QDialog

from licensing.service import get_current_license_status
from licensing.ui.activation_dialog import LicenseActivationDialog
from licensing.ui.startup_splash import StartupSplashScreen
from log.log import log


def ensure_license_before_main_window(app: QApplication) -> bool:
    """
    Показывает загрузчик, проверяет лицензию и при необходимости окно активации.

    Возвращает True, если можно запускать основное GUI.
    """
    # ВРЕМЕННО: проверка лицензии отключена для разработки/тестирования.
    log("Проверка лицензии пропущена (dev bypass)", "INFO")
    return True

    # splash = StartupSplashScreen()
    # splash.center_on_screen()
    # splash.show()
    # app.processEvents()
    #
    # loop = QEventLoop()
    # license_status_holder: list[object] = [None]
    #
    # def _on_splash_finished(status) -> None:
    #     license_status_holder[0] = status
    #     loop.quit()
    #
    # splash.finished.connect(_on_splash_finished)
    # splash.start(license_check=get_current_license_status)
    # loop.exec()
    #
    # status = license_status_holder[0]
    # if status is None:
    #     status = get_current_license_status()
    #
    # if getattr(status, "valid", False):
    #     log("Лицензия действительна, запуск основного окна", "INFO")
    #     return True
    #
    # log("Лицензия не активирована, показываем окно активации", "INFO")
    # dialog = LicenseActivationDialog(machine_id=str(getattr(status, "machine_id", "") or ""))
    # result = dialog.exec()
    # if result == QDialog.DialogCode.Accepted:
    #     log("Лицензия активирована при старте", "INFO")
    #     return True
    #
    # log("Активация отменена пользователем, выход", "INFO")
    # return False


__all__ = ["ensure_license_before_main_window"]
