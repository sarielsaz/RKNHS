"""ISP auto-preset + first-run preset guide notifications."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QTimer

from app_notifications import advisory_notification, notification_action
from log.log import log
from main.post_startup_gate import bind_startup_gate, is_startup_host_alive
from main.post_startup_threading import start_daemon_thread


@dataclass(frozen=True, slots=True)
class IspApplyOutcome:
    applied: bool
    isp_label: str = ""
    preset_file: str = ""


def install_isp_auto_preset(startup_host, *, log_startup_metric, notify=None, show_page=None) -> None:
    def _run_isp_auto_preset() -> None:
        if not is_startup_host_alive(startup_host):
            return
        outcome = IspApplyOutcome(False)
        try:
            from settings.isp_auto_preset import maybe_apply_isp_preset_detailed

            outcome = maybe_apply_isp_preset_detailed()
        except Exception as exc:
            log(f"ISP auto-preset startup failed: {exc}", "DEBUG")
            try:
                from settings.isp_auto_preset import maybe_apply_isp_preset

                maybe_apply_isp_preset()
            except Exception:
                pass

        if outcome.applied and callable(notify):
            try:
                from app.ui_texts import tr as tr_catalog

                notify(
                    advisory_notification(
                        level="success",
                        title=tr_catalog(
                            "page.control.isp_auto.toast.title",
                            default="Пресет по провайдеру",
                        ),
                        content=tr_catalog(
                            "page.control.isp_auto.toast.body",
                            default="Подобран пресет «{preset}» для {isp}",
                        ).format(preset=outcome.preset_file, isp=outcome.isp_label or "ISP"),
                        source="startup.isp_auto_preset",
                        presentation="infobar",
                        queue="startup",
                        duration=10000,
                        dedupe_key="startup.isp_auto_preset",
                    )
                )
            except Exception as exc:
                log(f"ISP auto-preset notify failed: {exc}", "DEBUG")

    def _schedule_isp_auto_preset() -> None:
        if not is_startup_host_alive(startup_host):
            return
        log_startup_metric("StartupIspAutoPresetQueued", "2500ms")
        start_daemon_thread("isp-auto-preset", _run_isp_auto_preset)
        QTimer.singleShot(3200, lambda: _maybe_show_preset_guide(startup_host, notify=notify, show_page=show_page))

    bind_startup_gate(
        startup_host.startup_post_init_ready,
        _schedule_isp_auto_preset,
        is_ready=lambda: bool(startup_host.startup_state.post_init_ready),
    )


def _maybe_show_preset_guide(startup_host, *, notify=None, show_page=None) -> None:
    if not is_startup_host_alive(startup_host):
        return
    try:
        from settings.store import get_preset_guide_seen, set_preset_guide_seen

        if get_preset_guide_seen():
            return
        set_preset_guide_seen(True)
    except Exception:
        return
    if not callable(notify):
        return
    try:
        from app.ui_texts import tr as tr_catalog

        buttons = [
            notification_action(
                "preset_guide_isp",
                tr_catalog("page.control.preset_guide.isp", default="Авто по провайдеру"),
            ),
            notification_action(
                "preset_guide_blockcheck",
                tr_catalog("page.control.preset_guide.blockcheck", default="Подобрать (Blockcheck)"),
            ),
            notification_action(
                "preset_guide_keep",
                tr_catalog("page.control.preset_guide.keep", default="Оставить текущий"),
            ),
        ]
        notify(
            advisory_notification(
                level="info",
                title=tr_catalog("page.control.preset_guide.title", default="С чего начать"),
                content=tr_catalog(
                    "page.control.preset_guide.body",
                    default="Выберите путь: авто по провайдеру, Blockcheck или оставить текущий.",
                ),
                source="startup.preset_guide",
                presentation="infobar",
                queue="startup",
                duration=18000,
                buttons=buttons,
                dedupe_key="startup.preset_guide",
            )
        )
    except Exception as exc:
        log(f"Preset guide notify failed: {exc}", "DEBUG")


__all__ = ["IspApplyOutcome", "install_isp_auto_preset"]
