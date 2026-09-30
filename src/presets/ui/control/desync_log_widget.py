"""Recent desync / block events parsed from winws2 debug logs."""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from config.config import LOGS_FOLDER
from qfluentwidgets import CaptionLabel, CardWidget, StrongBodyLabel, BodyLabel

_REFRESH_INTERVAL_MS = 20_000
_TAIL_BYTES = 128_000
_TAIL_LINES = 800

_DESYNC_SEARCH = re.compile(
    r"desync profile search for (?:tcp|udp) ip=[^\s]+ port=\d+ l7proto=(\S+).*hostname='([^']*)'",
    re.I,
)
_LOCK = re.compile(r"slm_quality:? (?:\[\w+\] )?LOCK:? (.+?) -> strat=(\d+)", re.I)
_UNLOCK = re.compile(r"slm_quality:? (?:\[\w+\] )?UNLOCK:? (\S+)", re.I)
_FAIL = re.compile(r"slm_quality: (?:\[\w+\] )?(?:udp )?(.+?) strat=(\d+) FAIL", re.I)


@dataclass(frozen=True, slots=True)
class DesyncEvent:
    timestamp: str
    domain: str
    event_type: str
    detail: str


def _latest_debug_log_path() -> str | None:
    pattern = os.path.join(LOGS_FOLDER, "zapret_winws2_debug_*.log")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def _read_tail_lines(path: str, *, max_bytes: int = _TAIL_BYTES, max_lines: int = _TAIL_LINES) -> list[str]:
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as handle:
            if size > max_bytes:
                handle.seek(size - max_bytes)
            payload = handle.read().decode("utf-8", errors="ignore")
    except OSError:
        return []
    lines = payload.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return lines


def parse_recent_desync_events(*, limit: int = 12) -> list[DesyncEvent]:
    path = _latest_debug_log_path()
    if not path or not os.path.isfile(path):
        return []

    lines = _read_tail_lines(path)
    if not lines:
        return []

    events: list[DesyncEvent] = []
    for raw_line in reversed(lines):
        line = raw_line.strip()
        if not line:
            continue

        ts = ""
        if line.startswith("[") and "]" in line:
            ts = line[1 : line.index("]")]

        body = line.split("] ", 1)[-1] if "] " in line else line

        match = _LOCK.search(body)
        if match:
            events.append(
                DesyncEvent(
                    timestamp=ts,
                    domain=match.group(1).strip(),
                    event_type="LOCK",
                    detail=f"strategy #{match.group(2)}",
                )
            )
            continue

        match = _UNLOCK.search(body)
        if match:
            events.append(
                DesyncEvent(
                    timestamp=ts,
                    domain=match.group(1).strip(),
                    event_type="UNLOCK",
                    detail="re-learning",
                )
            )
            continue

        match = _FAIL.search(body)
        if match:
            events.append(
                DesyncEvent(
                    timestamp=ts,
                    domain=match.group(1).strip(),
                    event_type="FAIL",
                    detail=f"strategy #{match.group(2)}",
                )
            )
            continue

        match = _DESYNC_SEARCH.search(body)
        if match:
            proto, hostname = match.group(1), match.group(2).strip()
            if hostname:
                events.append(
                    DesyncEvent(
                        timestamp=ts,
                        domain=hostname,
                        event_type="DESYNC",
                        detail=proto,
                    )
                )

        if len(events) >= limit:
            break

    return list(reversed(events))


class _DesyncLogWorker(QThread):
    completed = pyqtSignal(list)

    def __init__(self, *, limit: int = 10, parent=None):
        super().__init__(parent)
        self._limit = int(limit)

    def run(self) -> None:
        if self.isInterruptionRequested():
            return
        events = parse_recent_desync_events(limit=self._limit)
        if not self.isInterruptionRequested():
            self.completed.emit(events)


class DesyncLogWidget(CardWidget):
    """Compact list of recent desync triggers by domain."""

    def __init__(self, *, language: str = "ru", parent=None):
        super().__init__(parent)
        self._language = str(language or "ru")
        self._worker: _DesyncLogWorker | None = None
        self._polling_enabled = False
        self._title = StrongBodyLabel("Что заблокировано (desync)", self)
        self._subtitle = CaptionLabel("Последние desync-срабатывания по доменам", self)
        self._empty_label = BodyLabel("Нет данных — включите debug-лог winws2", self)
        self._rows_layout = QVBoxLayout()
        self._rows_host = QWidget(self)
        self._rows_host.setLayout(self._rows_layout)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._rows_host)
        layout.addWidget(self._empty_label)

        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)

    def set_polling_enabled(self, enabled: bool) -> None:
        self._polling_enabled = bool(enabled)
        if self._polling_enabled:
            if not self._timer.isActive():
                self._timer.start()
            QTimer.singleShot(800, self.refresh)
        else:
            self._timer.stop()
            self._cancel_worker()

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.set_polling_enabled(True)

    def hideEvent(self, event):  # noqa: N802
        self.set_polling_enabled(False)
        super().hideEvent(event)

    def refresh(self) -> None:
        if self._worker_is_running():
            return
        self._worker = None
        worker = _DesyncLogWorker(limit=10, parent=self)
        worker.completed.connect(self._apply_events)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        worker.start()

    def _worker_is_running(self) -> bool:
        worker = self._worker
        if worker is None:
            return False
        try:
            return bool(worker.isRunning())
        except RuntimeError:
            self._worker = None
            return False

    def _on_worker_finished(self) -> None:
        self._worker = None

    def _cancel_worker(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is None:
            return
        try:
            worker.completed.disconnect(self._apply_events)
        except Exception:
            pass
        try:
            worker.finished.disconnect(self._on_worker_finished)
        except Exception:
            pass
        try:
            if worker.isRunning():
                worker.requestInterruption()
                worker.wait(200)
        except RuntimeError:
            pass
        except Exception:
            pass

    def _apply_events(self, events: list) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not events:
            self._empty_label.setVisible(True)
            self._rows_host.setVisible(False)
            return

        self._empty_label.setVisible(False)
        self._rows_host.setVisible(True)
        for event in events:
            time_text = getattr(event, "timestamp", "") or datetime.now().strftime("%H:%M:%S")
            domain = getattr(event, "domain", "")
            event_type = getattr(event, "event_type", "")
            detail = getattr(event, "detail", "")
            label = BodyLabel(
                f"[{time_text}] {event_type}: {domain} — {detail}",
                self._rows_host,
            )
            label.setWordWrap(True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._rows_layout.addWidget(label)
