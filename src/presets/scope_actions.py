"""Select LIGHT / WIDE / scenario presets without opening the main window."""

from __future__ import annotations

import os
from typing import Any

from config.config import MAIN_DIRECTORY
from presets.preset_clarity import resolve_recommended_light_preset
from presets.scenario_profiles import (
    ScenarioApplyResult,
    resolve_recommended_wide_preset,
    resolve_scenario_preset,
)
from settings.mode import is_zapret1_launch_method, is_zapret2_launch_method
from settings.store import set_active_scenario_id


def _preset_folders(launch_method: str) -> list[str]:
    if is_zapret2_launch_method(launch_method):
        return ["presets/builtin/winws2", "presets/winws2", "presets/winws2_builtin"]
    if is_zapret1_launch_method(launch_method):
        return ["presets/builtin/winws1", "presets/winws1", "presets/winws1_builtin"]
    return []


def make_preset_exists(presets_feature: Any, launch_method: str):
    folders = _preset_folders(launch_method)

    def _exists(file_name: str) -> bool:
        for folder in folders:
            path = os.path.join(MAIN_DIRECTORY, folder, file_name)
            if os.path.isfile(path):
                return True
        try:
            manifests = presets_feature.list_preset_manifests(launch_method) or []
        except Exception:
            return False
        target = str(file_name or "").strip().lower()
        for item in manifests:
            name = str(getattr(item, "file_name", None) or getattr(item, "name", None) or item or "")
            if name.strip().lower() == target:
                return True
        return False

    return _exists


def select_preset_file(presets_feature: Any, launch_method: str, file_name: str) -> str | None:
    chosen = str(file_name or "").strip()
    if not chosen:
        return None
    try:
        presets_feature.select_preset(launch_method, chosen)
    except Exception:
        return None
    return chosen


def apply_light_bypass(presets_feature: Any, launch_method: str) -> str | None:
    exists = make_preset_exists(presets_feature, launch_method)
    chosen = resolve_recommended_light_preset(
        launch_method=launch_method,
        preset_exists=exists,
    )
    if not chosen:
        return None
    selected = select_preset_file(presets_feature, launch_method, chosen)
    if selected:
        try:
            set_active_scenario_id("youtube_only")
        except Exception:
            pass
    return selected


def apply_wide_bypass(presets_feature: Any, launch_method: str) -> str | None:
    exists = make_preset_exists(presets_feature, launch_method)
    chosen = resolve_recommended_wide_preset(
        launch_method=launch_method,
        preset_exists=exists,
    )
    if not chosen:
        return None
    selected = select_preset_file(presets_feature, launch_method, chosen)
    if selected:
        try:
            set_active_scenario_id("max_coverage")
        except Exception:
            pass
    return selected


def apply_scenario_profile(
    presets_feature: Any,
    launch_method: str,
    scenario_id: str,
) -> ScenarioApplyResult:
    sid = str(scenario_id or "").strip().lower()
    exists = make_preset_exists(presets_feature, launch_method)
    chosen = resolve_scenario_preset(
        scenario_id=sid,
        launch_method=launch_method,
        preset_exists=exists,
    )
    if not chosen:
        return ScenarioApplyResult(
            ok=False,
            scenario_id=sid,
            message="Не найден подходящий пресет для сценария",
        )
    selected = select_preset_file(presets_feature, launch_method, chosen)
    if not selected:
        return ScenarioApplyResult(
            ok=False,
            scenario_id=sid,
            message="Не удалось выбрать пресет",
        )
    try:
        set_active_scenario_id(sid)
    except Exception:
        pass
    return ScenarioApplyResult(
        ok=True,
        scenario_id=sid,
        preset_name=selected,
        message=f"Сценарий применён: {selected}",
    )


__all__ = [
    "apply_light_bypass",
    "apply_scenario_profile",
    "apply_wide_bypass",
    "make_preset_exists",
    "select_preset_file",
]
