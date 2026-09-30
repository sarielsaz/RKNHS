"""Scenario profile picker for Control page."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from qfluentwidgets import CaptionLabel, CardWidget, PushButton, StrongBodyLabel

from presets.scenario_profiles import SCENARIO_CATALOG, get_scenario
from ui.tech_type import format_hud_label


class ScenarioProfilesWidget(CardWidget):
    """Ready-made modes on top of presets — not preset files themselves."""

    scenarioRequested = pyqtSignal(str)

    def __init__(self, *, language: str = "ru", parent=None):
        super().__init__(parent)
        self._language = str(language or "ru")
        self._active_id = ""
        self._buttons: dict[str, PushButton] = {}

        self._title = StrongBodyLabel("", self)
        self._subtitle = CaptionLabel("", self)
        self._subtitle.setWordWrap(True)
        self._active = CaptionLabel("", self)

        buttons_row = QHBoxLayout()
        buttons_row.setContentsMargins(0, 0, 0, 0)
        buttons_row.setSpacing(8)

        for profile in SCENARIO_CATALOG:
            btn = PushButton(profile.title(language=self._language), self)
            btn.setProperty("scenario_id", profile.scenario_id)
            btn.clicked.connect(
                lambda _checked=False, sid=profile.scenario_id: self.scenarioRequested.emit(sid)
            )
            self._buttons[profile.scenario_id] = btn
            buttons_row.addWidget(btn, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addLayout(buttons_row)
        layout.addWidget(self._active)

        self.set_language(self._language)

    def set_language(self, language: str) -> None:
        self._language = str(language or "ru")
        ru = self._language == "ru"
        self._title.setText(format_hud_label("Сценарии" if ru else "Scenarios"))
        self._subtitle.setText(
            "Готовые режимы поверх пресетов — не отдельные файлы."
            if ru
            else "Ready-made modes on top of presets — not separate files."
        )
        for profile in SCENARIO_CATALOG:
            button = self._buttons.get(profile.scenario_id)
            if button is not None:
                button.setText(profile.title(language=self._language))
                button.setToolTip(profile.description(language=self._language))
        self.set_active_scenario(self._active_id)

    def set_active_scenario(self, scenario_id: str | None) -> None:
        self._active_id = str(scenario_id or "").strip()
        profile = get_scenario(self._active_id)
        ru = self._language == "ru"
        if profile is None:
            self._active.setText(
                "Сейчас: свой пресет" if ru else "Now: custom preset"
            )
        else:
            self._active.setText(
                (f"Сейчас: {profile.title(language=self._language)}" if ru else f"Now: {profile.title(language=self._language)}")
            )
        for sid, button in self._buttons.items():
            button.setEnabled(sid != self._active_id)


__all__ = ["ScenarioProfilesWidget"]
