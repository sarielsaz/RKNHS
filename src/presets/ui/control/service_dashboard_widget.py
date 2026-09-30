"""User-configurable service status dashboard for the main control page."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FlowLayout,
    PushButton,
    StrongBodyLabel,
    TransparentToolButton,
)
from qfluentwidgets import FluentIcon

from presets.ui.control.service_probe import (
    ServiceDefinition,
    ServiceStatusKind,
    probe_service_dns,
    probe_service_https,
)
from settings.store import get_service_dashboard_ids, set_service_dashboard_ids

_REFRESH_INTERVAL_MS = 60_000


SERVICE_CATALOG: tuple[ServiceDefinition, ...] = (
    ServiceDefinition("telegram", "Telegram", "telegram.org"),
    ServiceDefinition("youtube", "YouTube", "youtube.com"),
    ServiceDefinition("discord", "Discord", "discord.com"),
    ServiceDefinition("grok", "Grok", "grok.com", requires_vpn=True),
    ServiceDefinition("twitter", "X / Twitter", "x.com"),
    ServiceDefinition("instagram", "Instagram", "instagram.com"),
    ServiceDefinition("whatsapp", "WhatsApp", "web.whatsapp.com"),
    ServiceDefinition("spotify", "Spotify", "open.spotify.com"),
    ServiceDefinition("github", "GitHub", "github.com"),
    ServiceDefinition("chatgpt", "ChatGPT", "chatgpt.com", requires_vpn=True),
)

_CATALOG_BY_ID = {item.service_id: item for item in SERVICE_CATALOG}

_STATUS_LABELS: dict[ServiceStatusKind, str] = {
    "ok": "Доступен",
    "vpn": "Нужен VPN",
    "fail": "Проблема",
}


class _ServiceProbeWorker(QThread):
    completed = pyqtSignal(dict)

    def __init__(self, service_ids: list[str], *, use_https: bool, parent=None):
        super().__init__(parent)
        self._service_ids = list(service_ids or [])
        self._use_https = bool(use_https)

    def run(self) -> None:
        probe = probe_service_https if self._use_https else probe_service_dns
        results: dict[str, tuple[ServiceStatusKind, str]] = {}
        for service_id in self._service_ids:
            definition = _CATALOG_BY_ID.get(service_id)
            if definition is None:
                continue
            results[service_id] = probe(definition)
        self.completed.emit(results)


class ServiceStatusChip(CardWidget):
    removed = pyqtSignal(str)

    def __init__(self, definition: ServiceDefinition, parent=None):
        super().__init__(parent)
        self.service_id = definition.service_id
        self._title = StrongBodyLabel(definition.title, self)
        self._status = BodyLabel("…", self)
        self._detail = CaptionLabel(definition.host, self)

        remove_btn = TransparentToolButton(FluentIcon.CLOSE, self)
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(lambda: self.removed.emit(self.service_id))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        text_col.addWidget(self._title)
        text_col.addWidget(self._status)
        text_col.addWidget(self._detail)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 8, 10)
        row.setSpacing(8)
        row.addLayout(text_col, 1)
        row.addWidget(remove_btn, 0, Qt.AlignmentFlag.AlignTop)
        self.setMinimumWidth(220)

    def set_result(self, *, kind: ServiceStatusKind, detail: str) -> None:
        self._status.setText(_STATUS_LABELS.get(kind, "Проблема"))
        self._detail.setText(str(detail or ""))


class ServiceDashboardWidget(CardWidget):
    """Dashboard of user-selected services with quick reachability checks."""

    def __init__(self, *, language: str = "ru", parent=None):
        super().__init__(parent)
        self._language = str(language or "ru")
        self._chips: dict[str, ServiceStatusChip] = {}
        self._probe_worker: _ServiceProbeWorker | None = None
        self._polling_enabled = False

        self._title = StrongBodyLabel("Мои сервисы", self)
        self._subtitle = CaptionLabel(
            "Авто — DNS (для Grok/ChatGPT: «Нужен VPN», не «Доступен»). "
            "Кнопка «Проверить» — реальный HTTPS-запрос.",
            self,
        )
        self._subtitle.setWordWrap(True)
        self._picker = ComboBox(self)
        for item in SERVICE_CATALOG:
            self._picker.addItem(item.title, userData=item.service_id)
        self._add_btn = PushButton("Добавить", self)
        self._add_btn.clicked.connect(self._add_selected_service)
        self._refresh_btn = PushButton("Проверить", self)
        self._refresh_btn.setToolTip("HTTPS GET к сервису (не только DNS)")
        self._refresh_btn.clicked.connect(lambda: self._run_probe(use_https=True))

        picker_row = QHBoxLayout()
        picker_row.setContentsMargins(0, 0, 0, 0)
        picker_row.setSpacing(8)
        picker_row.addWidget(self._picker, 1)
        picker_row.addWidget(self._add_btn, 0)
        picker_row.addWidget(self._refresh_btn, 0)

        self._flow_host = QWidget(self)
        self._flow = FlowLayout(self._flow_host, needAni=False)
        self._flow.setContentsMargins(0, 0, 0, 0)
        self._flow.setHorizontalSpacing(10)
        self._flow.setVerticalSpacing(10)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(picker_row)
        layout.addWidget(self._flow_host)

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(lambda: self._run_probe(use_https=False))

        self._load_saved_services()

    def set_polling_enabled(self, enabled: bool) -> None:
        self._polling_enabled = bool(enabled)
        if self._polling_enabled:
            if not self._timer.isActive():
                self._timer.start()
            QTimer.singleShot(500, lambda: self._run_probe(use_https=False))
        else:
            self._timer.stop()
            self._cancel_probe_worker()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.set_polling_enabled(True)

    def hideEvent(self, event):  # noqa: N802
        self.set_polling_enabled(False)
        super().hideEvent(event)

    def refresh_statuses(self) -> None:
        self._run_probe(use_https=True)

    def _load_saved_services(self) -> None:
        for service_id in get_service_dashboard_ids():
            self._ensure_chip(service_id)

    def _persist(self) -> None:
        set_service_dashboard_ids(sorted(self._chips.keys()))

    def _add_selected_service(self) -> None:
        service_id = str(self._picker.currentData() or "").strip()
        if not service_id:
            return
        self._ensure_chip(service_id)
        self._persist()
        self._run_probe(use_https=True)

    def _ensure_chip(self, service_id: str) -> None:
        service_id = str(service_id or "").strip()
        if not service_id or service_id in self._chips:
            return
        definition = _CATALOG_BY_ID.get(service_id)
        if definition is None:
            return
        chip = ServiceStatusChip(definition, self._flow_host)
        chip.removed.connect(self._remove_service)
        self._chips[service_id] = chip
        self._flow.addWidget(chip)

    def _remove_service(self, service_id: str) -> None:
        chip = self._chips.pop(str(service_id or "").strip(), None)
        if chip is None:
            return
        self._flow.removeWidget(chip)
        chip.deleteLater()
        self._persist()

    def _run_probe(self, *, use_https: bool) -> None:
        if not self._chips:
            return
        if self._probe_worker_is_running():
            return

        self._refresh_btn.setEnabled(False)
        worker = _ServiceProbeWorker(list(self._chips.keys()), use_https=use_https, parent=self)
        worker.completed.connect(self._apply_probe_results)
        worker.finished.connect(self._on_probe_finished)
        self._probe_worker = worker
        worker.start()

    def _probe_worker_is_running(self) -> bool:
        worker = self._probe_worker
        if worker is None:
            return False
        try:
            return bool(worker.isRunning())
        except RuntimeError:
            self._probe_worker = None
            return False

    def _cancel_probe_worker(self) -> None:
        worker = self._probe_worker
        self._probe_worker = None
        if worker is None:
            return
        try:
            if worker.isRunning():
                worker.requestInterruption()
                worker.wait(200)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _on_probe_finished(self) -> None:
        self._probe_worker = None
        self._refresh_btn.setEnabled(True)

    def _apply_probe_results(self, results: dict) -> None:
        for service_id, payload in dict(results or {}).items():
            chip = self._chips.get(str(service_id))
            definition = _CATALOG_BY_ID.get(str(service_id))
            if chip is None or definition is None:
                continue
            try:
                kind, detail = payload
            except Exception:
                kind, detail = "fail", "error"
            if kind == "fail" and detail and not str(detail).startswith(definition.host):
                detail = f"{definition.host}: {detail}"
            chip.set_result(kind=kind, detail=str(detail))
