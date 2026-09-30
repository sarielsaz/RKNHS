from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ApplicationLifecycleWindowPort:
    _window: Any

    def persist_geometry(self, *, context: str, level: str = "DEBUG") -> None:
        from main.window_lifecycle_cleanup import persist_window_geometry

        persist_window_geometry(self._window, context=context, level=level)

    def cleanup_theme(self) -> None:
        from main.window_lifecycle_cleanup import cleanup_theme_for_close

        cleanup_theme_for_close(self._window)

    def cleanup_threaded_pages(self) -> None:
        from main.window_lifecycle_cleanup import (
            cleanup_session_runtimes_for_close,
            cleanup_threaded_pages_for_close,
        )

        cleanup_threaded_pages_for_close(self._window)
        cleanup_session_runtimes_for_close(self._window)

    def cleanup_visual_and_proxy_resources(self, *, telegram_proxy_feature) -> None:
        from main.window_lifecycle_cleanup import cleanup_visual_and_proxy_resources_for_close

        cleanup_visual_and_proxy_resources_for_close(
            self._window,
            telegram_proxy_feature=telegram_proxy_feature,
        )

    def show_tray_unavailable_notice(self) -> None:
        try:
            from qfluentwidgets import InfoBar

            InfoBar.warning(
                title="Трей недоступен",
                content=(
                    "Не удалось свернуть окно в трей. "
                    "Перезапустите RKNHS или проверьте лог приложения."
                ),
                parent=self._window,
                duration=6000,
            )
        except Exception:
            pass


def build_application_lifecycle_window_port(window) -> ApplicationLifecycleWindowPort:
    return ApplicationLifecycleWindowPort(window)


__all__ = ["ApplicationLifecycleWindowPort", "build_application_lifecycle_window_port"]
