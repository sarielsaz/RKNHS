"""Scenario profiles: ready-made modes on top of existing presets."""

from __future__ import annotations

from dataclasses import dataclass

from presets.preset_clarity import (
    LIGHT_PRESET_CANDIDATES_WINWS1,
    LIGHT_PRESET_CANDIDATES_WINWS2,
    PresetScope,
    classify_preset_scope,
)


SCENARIO_YOUTUBE = "youtube_only"
SCENARIO_GAMES_DISCORD = "games_discord"
SCENARIO_MAX_COVERAGE = "max_coverage"

VALID_SCENARIO_IDS = frozenset(
    {
        SCENARIO_YOUTUBE,
        SCENARIO_GAMES_DISCORD,
        SCENARIO_MAX_COVERAGE,
    }
)

WIDE_PRESET_CANDIDATES_WINWS2: tuple[str, ...] = (
    "Default (circular).txt",
    "multisplit (circular).txt",
    "ALL TCP & UDP v3_2.txt",
    "ALL TCP & UDP v1.txt",
    "fake (circular).txt",
)

WIDE_PRESET_CANDIDATES_WINWS1: tuple[str, ...] = (
    "Default.txt",
    "general 1.9.9a.txt",
)

GAMES_PRESET_CANDIDATES_WINWS2: tuple[str, ...] = (
    "Gaming (game filter).txt",
    "Default v1 (game filter).txt",
    "Default (game filter).txt",
    "Ultimate Main Riot + Valorant (game filter).txt",
)

GAMES_PRESET_CANDIDATES_WINWS1: tuple[str, ...] = (
    "general 1.9.9a (game filter).txt",
    "Default v1.txt",
    "Default.txt",
)

YOUTUBE_PRESET_CANDIDATES_WINWS2: tuple[str, ...] = (
    "Default v1 (game filter).txt",
    "Default (game filter).txt",
    "Default v2 (game filter).txt",
    *LIGHT_PRESET_CANDIDATES_WINWS2,
)

YOUTUBE_PRESET_CANDIDATES_WINWS1: tuple[str, ...] = (
    *LIGHT_PRESET_CANDIDATES_WINWS1,
)


@dataclass(frozen=True, slots=True)
class ScenarioProfile:
    scenario_id: str
    title_ru: str
    title_en: str
    desc_ru: str
    desc_en: str
    target_scope: PresetScope

    def title(self, *, language: str = "ru") -> str:
        return self.title_ru if language == "ru" else self.title_en

    def description(self, *, language: str = "ru") -> str:
        return self.desc_ru if language == "ru" else self.desc_en


SCENARIO_CATALOG: tuple[ScenarioProfile, ...] = (
    ScenarioProfile(
        scenario_id=SCENARIO_YOUTUBE,
        title_ru="Только YouTube",
        title_en="YouTube only",
        desc_ru="Узкий обход под видео — меньше нагрузка",
        desc_en="Narrow bypass for video — lower load",
        target_scope=PresetScope.LIGHT,
    ),
    ScenarioProfile(
        scenario_id=SCENARIO_GAMES_DISCORD,
        title_ru="Игры + Discord",
        title_en="Games + Discord",
        desc_ru="Игровой фильтр и голосовой трафик",
        desc_en="Game filter and voice traffic",
        target_scope=PresetScope.LIGHT,
    ),
    ScenarioProfile(
        scenario_id=SCENARIO_MAX_COVERAGE,
        title_ru="Максимальный охват",
        title_en="Max coverage",
        desc_ru="Широкий перехват — если лёгкий не хватает",
        desc_en="Wide divert — when light mode is not enough",
        target_scope=PresetScope.WIDE,
    ),
)


def get_scenario(scenario_id: str) -> ScenarioProfile | None:
    key = str(scenario_id or "").strip().lower()
    for item in SCENARIO_CATALOG:
        if item.scenario_id == key:
            return item
    return None


def _candidates_for(scenario_id: str, *, launch_method: str) -> tuple[str, ...]:
    from settings.mode import is_zapret1_launch_method, is_zapret2_launch_method

    key = str(scenario_id or "").strip().lower()
    if is_zapret2_launch_method(launch_method):
        if key == SCENARIO_YOUTUBE:
            return YOUTUBE_PRESET_CANDIDATES_WINWS2
        if key == SCENARIO_GAMES_DISCORD:
            return GAMES_PRESET_CANDIDATES_WINWS2
        if key == SCENARIO_MAX_COVERAGE:
            return WIDE_PRESET_CANDIDATES_WINWS2
    elif is_zapret1_launch_method(launch_method):
        if key == SCENARIO_YOUTUBE:
            return YOUTUBE_PRESET_CANDIDATES_WINWS1
        if key == SCENARIO_GAMES_DISCORD:
            return GAMES_PRESET_CANDIDATES_WINWS1
        if key == SCENARIO_MAX_COVERAGE:
            return WIDE_PRESET_CANDIDATES_WINWS1
    return ()


def resolve_scenario_preset(
    *,
    scenario_id: str,
    launch_method: str,
    preset_exists,
) -> str | None:
    for name in _candidates_for(scenario_id, launch_method=launch_method):
        try:
            if preset_exists(name):
                return name
        except Exception:
            continue
    return None


def resolve_recommended_wide_preset(*, launch_method: str, preset_exists) -> str | None:
    return resolve_scenario_preset(
        scenario_id=SCENARIO_MAX_COVERAGE,
        launch_method=launch_method,
        preset_exists=preset_exists,
    )


def detect_active_scenario(*, file_name: str = "", source_text: str = "") -> str | None:
    name = str(file_name or "").strip().lower()
    scope = classify_preset_scope(file_name=file_name, source_text=source_text)
    if "gaming" in name or "valorant" in name or "riot" in name or "discord" in name:
        return SCENARIO_GAMES_DISCORD
    if scope is PresetScope.WIDE or "circular" in name or name.startswith("all tcp"):
        return SCENARIO_MAX_COVERAGE
    if scope is PresetScope.LIGHT or "game filter" in name:
        return SCENARIO_YOUTUBE
    return None


@dataclass(frozen=True, slots=True)
class ScenarioApplyResult:
    ok: bool
    scenario_id: str
    preset_name: str = ""
    message: str = ""


__all__ = [
    "GAMES_PRESET_CANDIDATES_WINWS1",
    "GAMES_PRESET_CANDIDATES_WINWS2",
    "SCENARIO_CATALOG",
    "SCENARIO_GAMES_DISCORD",
    "SCENARIO_MAX_COVERAGE",
    "SCENARIO_YOUTUBE",
    "ScenarioApplyResult",
    "ScenarioProfile",
    "VALID_SCENARIO_IDS",
    "WIDE_PRESET_CANDIDATES_WINWS1",
    "WIDE_PRESET_CANDIDATES_WINWS2",
    "YOUTUBE_PRESET_CANDIDATES_WINWS1",
    "YOUTUBE_PRESET_CANDIDATES_WINWS2",
    "detect_active_scenario",
    "get_scenario",
    "resolve_recommended_wide_preset",
    "resolve_scenario_preset",
]
