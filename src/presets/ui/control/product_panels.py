"""Shared Control product panels: traffic map, scenarios, offline lists pack."""

from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QFileDialog

from presets.ui.control.scenario_profiles_widget import ScenarioProfilesWidget
from presets.ui.control.traffic_map_widget import TrafficMapWidget
from settings.store import get_active_scenario_id


def attach_product_panels(page, *, after_widget_index: int | None = None) -> None:
    """Create traffic map + scenarios on a control page (idempotent)."""
    _ = after_widget_index
    if getattr(page, "traffic_map", None) is None:
        page.traffic_map = TrafficMapWidget(language=page._ui_language, parent=page.content)
        page.add_widget(page.traffic_map)
        page.add_spacing(12)
        try:
            page.traffic_map.set_dpi_running(bool(getattr(page, "_last_known_dpi_running", False)))
        except Exception:
            pass

    if getattr(page, "scenario_profiles", None) is None:
        page.scenario_profiles = ScenarioProfilesWidget(
            language=page._ui_language,
            parent=page.content,
        )
        page.scenario_profiles.scenarioRequested.connect(page._on_scenario_requested)
        page.add_widget(page.scenario_profiles)
        page.add_spacing(12)
        try:
            page.scenario_profiles.set_active_scenario(get_active_scenario_id())
        except Exception:
            pass


def schedule_deferred_control_sections(page, builder) -> None:
    """Run heavy control sections after the first paint."""
    if getattr(page, "_deferred_sections_started", False):
        return
    page._deferred_sections_started = True

    def _run() -> None:
        if getattr(page, "_cleanup_in_progress", False):
            return
        try:
            builder()
        except Exception:
            pass

    QTimer.singleShot(0, _run)


def import_offline_lists_pack(page) -> None:
    path, _ = QFileDialog.getOpenFileName(
        page.window(),
        "Выберите офлайн-пакет списков (zip)",
        "",
        "Zip (*.zip)",
    )
    if not path:
        return
    try:
        from lists.offline_pack import import_zip_pack

        result = import_zip_pack(path)
        message = result.message
    except Exception as exc:
        message = f"Ошибка импорта: {exc}"
    try:
        page._set_status_callback(message)
    except Exception:
        pass


def restore_offline_lists_pack(page) -> None:
    try:
        from lists.offline_pack import restore_from_cache

        result = restore_from_cache()
        message = result.message
    except Exception as exc:
        message = f"Ошибка отката: {exc}"
    try:
        page._set_status_callback(message)
    except Exception:
        pass


def export_offline_lists_pack(page) -> None:
    path, _ = QFileDialog.getSaveFileName(
        page.window(),
        "Сохранить офлайн-пакет списков",
        "rknhs-lists-pack.zip",
        "Zip (*.zip)",
    )
    if not path:
        return
    try:
        from lists.offline_pack import export_current_base_zip

        result = export_current_base_zip(path)
        message = result.message
    except Exception as exc:
        message = f"Ошибка экспорта: {exc}"
    try:
        page._set_status_callback(message)
    except Exception:
        pass


__all__ = [
    "attach_product_panels",
    "export_offline_lists_pack",
    "import_offline_lists_pack",
    "restore_offline_lists_pack",
    "schedule_deferred_control_sections",
]
