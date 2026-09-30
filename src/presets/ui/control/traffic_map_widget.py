"""Control page traffic route map widget."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import BodyLabel, CaptionLabel, CardWidget, StrongBodyLabel

from presets.traffic_map import TrafficLane, TrafficMapSnapshot, build_traffic_map_snapshot, collect_traffic_map_inputs
from ui.tech_type import format_hud_label

_REFRESH_INTERVAL_MS = 12_000


class _TrafficMapWorker(QThread):
    completed = pyqtSignal(object)

    def __init__(self, *, dpi_running: bool, language: str, parent=None):
        super().__init__(parent)
        self._dpi_running = bool(dpi_running)
        self._language = str(language or "ru")

    def run(self) -> None:
        try:
            inputs = collect_traffic_map_inputs(
                dpi_running=self._dpi_running,
                language=self._language,
            )
            snapshot = build_traffic_map_snapshot(**inputs)
        except Exception:
            snapshot = build_traffic_map_snapshot(
                dpi_running=self._dpi_running,
                language=self._language,
            )
        if not self.isInterruptionRequested():
            self.completed.emit(snapshot)


class _LaneRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dot = BodyLabel("●", self)
        self._dot.setFixedWidth(16)
        self._title = StrongBodyLabel("", self)
        self._state = BodyLabel("", self)
        self._detail = CaptionLabel("", self)
        self._detail.setWordWrap(True)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)
        text_col.addWidget(self._title)
        text_col.addWidget(self._detail)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(10)
        row.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text_col, 1)
        row.addWidget(self._state, 0, Qt.AlignmentFlag.AlignTop)

    def apply_lane(self, lane: TrafficLane) -> None:
        self._title.setText(lane.title)
        self._state.setText(lane.state_label)
        self._detail.setText(lane.detail)
        color = "#3DDC97" if lane.active else "rgba(140,156,176,0.48)"
        self._dot.setStyleSheet(f"color: {color};")


class TrafficMapWidget(CardWidget):
    """Plain-language map of where traffic goes right now."""

    def __init__(self, *, language: str = "ru", parent=None):
        super().__init__(parent)
        self._language = str(language or "ru")
        self._dpi_running = False
        self._worker: _TrafficMapWorker | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)

        self._title = StrongBodyLabel("", self)
        self._summary = CaptionLabel("", self)
        self._summary.setWordWrap(True)
        self._rows = [_LaneRow(self) for _ in range(4)]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.addWidget(self._title)
        layout.addWidget(self._summary)
        for row in self._rows:
            layout.addWidget(row)

        self._apply_title_text()
        self._apply_snapshot(
            build_traffic_map_snapshot(dpi_running=False, language=self._language)
        )

    def _apply_title_text(self) -> None:
        ru = self._language == "ru"
        self._title.setText(format_hud_label("Куда идёт трафик" if ru else "Where traffic goes"))

    def set_language(self, language: str) -> None:
        self._language = str(language or "ru")
        self._apply_title_text()
        if self.isVisible():
            self.refresh()

    def set_dpi_running(self, running: bool) -> None:
        next_value = bool(running)
        if self._dpi_running == next_value:
            return
        self._dpi_running = next_value
        if self.isVisible():
            self.refresh()

    def start_polling(self) -> None:
        if not self._timer.isActive():
            self._timer.start()
        self.refresh()

    def stop_polling(self) -> None:
        self._timer.stop()
        self._cancel_worker()

    def _worker_is_running(self) -> bool:
        worker = self._worker
        if worker is None:
            return False
        try:
            return bool(worker.isRunning())
        except RuntimeError:
            self._worker = None
            return False

    def _cancel_worker(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is None:
            return
        try:
            worker.completed.disconnect(self._on_worker_completed)
        except Exception:
            pass
        try:
            worker.finished.disconnect(self._on_worker_finished)
        except Exception:
            pass
        try:
            if worker.isRunning():
                worker.requestInterruption()
                worker.wait(250)
        except RuntimeError:
            pass
        except Exception:
            pass

    def refresh(self) -> None:
        if self._worker_is_running():
            return
        self._worker = None
        worker = _TrafficMapWorker(
            dpi_running=self._dpi_running,
            language=self._language,
            parent=self,
        )
        worker.completed.connect(self._on_worker_completed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        worker.start()

    def _on_worker_finished(self) -> None:
        self._worker = None

    def _on_worker_completed(self, snapshot: object) -> None:
        if isinstance(snapshot, TrafficMapSnapshot):
            self._apply_snapshot(snapshot)

    def _apply_snapshot(self, snapshot: TrafficMapSnapshot) -> None:
        self._summary.setText(snapshot.summary)
        for index, lane in enumerate(snapshot.lanes):
            if index < len(self._rows):
                self._rows[index].apply_lane(lane)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.start_polling()

    def hideEvent(self, event) -> None:
        self.stop_polling()
        super().hideEvent(event)


__all__ = ["TrafficMapWidget"]
