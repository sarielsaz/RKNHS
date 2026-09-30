"""Preset mental-model helpers: scope (LIGHT/WIDE), apply state, recommended light preset."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

_WF_RANGE_WIDE = re.compile(
    r"--wf-(?:tcp|udp)(?:-(?:in|out))?\s*=\s*[^\s]*443-65535",
    re.IGNORECASE,
)
_IPSET_ALL = re.compile(r"--ipset(?:=|\s+)[^\s]*ipset-all", re.IGNORECASE)


class PresetScope(str, Enum):
    LIGHT = "light"
    WIDE = "wide"
    UNKNOWN = "unknown"


LIGHT_PRESET_CANDIDATES_WINWS2: tuple[str, ...] = (
    "Default v1 (game filter).txt",
    "Default (game filter).txt",
    "Default v2 (game filter).txt",
    "Gaming (game filter).txt",
)

LIGHT_PRESET_CANDIDATES_WINWS1: tuple[str, ...] = (
    "Default v1.txt",
    "Default.txt",
)


@dataclass(frozen=True, slots=True)
class PresetHudClarity:
    scope: PresetScope
    scope_label: str
    role_line: str
    apply_line: str
    details: str


def classify_preset_scope(*, file_name: str = "", source_text: str = "") -> PresetScope:
    name = str(file_name or "").strip().lower()
    text = str(source_text or "")
    if "game filter" in name or name.endswith("(game filter).txt"):
        return PresetScope.LIGHT
    if "circular" in name or "orchestra" in name:
        return PresetScope.WIDE
    if text:
        wide_hits = len(_WF_RANGE_WIDE.findall(text))
        if wide_hits >= 2 or (wide_hits >= 1 and _IPSET_ALL.search(text)):
            return PresetScope.WIDE
        if wide_hits == 0 and ("--hostlist=" in text or "--hostlist " in text):
            return PresetScope.LIGHT
        if wide_hits >= 1:
            return PresetScope.WIDE
    return PresetScope.UNKNOWN


def scope_label(scope: PresetScope, *, language: str = "ru") -> str:
    if scope is PresetScope.LIGHT:
        return "LIGHT" if language != "ru" else "ЛЁГКИЙ"
    if scope is PresetScope.WIDE:
        return "WIDE" if language != "ru" else "ШИРОКИЙ"
    return ""


def role_line_for_scope(scope: PresetScope, *, language: str = "ru") -> str:
    if language != "ru":
        if scope is PresetScope.LIGHT:
            return "Narrow divert — lower load"
        if scope is PresetScope.WIDE:
            return "Wide divert — higher load"
        return "DPI bypass via lists"
    if scope is PresetScope.LIGHT:
        return "Узкий перехват — меньше нагрузка"
    if scope is PresetScope.WIDE:
        return "Широкий перехват — выше нагрузка"
    return "Обход DPI по спискам"


def apply_state_line(*, dpi_running: bool, has_preset: bool, language: str = "ru") -> str:
    if not has_preset:
        return (
            "Select a preset in My presets"
            if language != "ru"
            else "Выберите пресет в «Мои пресеты»"
        )
    if dpi_running:
        return "Applied to running bypass" if language != "ru" else "Применён к запущенному обходу"
    return (
        "Saved — start bypass to apply"
        if language != "ru"
        else "Сохранён — включите обход, чтобы применить"
    )


def build_preset_hud_clarity(
    *,
    file_name: str = "",
    source_text: str = "",
    dpi_running: bool = False,
    language: str = "ru",
) -> PresetHudClarity:
    has_preset = bool(str(file_name or "").strip())
    scope = classify_preset_scope(file_name=file_name, source_text=source_text)
    tag = scope_label(scope, language=language)
    role = role_line_for_scope(scope, language=language)
    apply_line = apply_state_line(
        dpi_running=bool(dpi_running),
        has_preset=has_preset,
        language=language,
    )
    if tag:
        details = f"{tag} · {role} · {apply_line}"
    else:
        details = f"{role} · {apply_line}"
    return PresetHudClarity(
        scope=scope,
        scope_label=tag,
        role_line=role,
        apply_line=apply_line,
        details=details,
    )


def resolve_recommended_light_preset(
    *,
    launch_method: str,
    preset_exists,
) -> str | None:
    from settings.mode import is_zapret1_launch_method, is_zapret2_launch_method

    if is_zapret2_launch_method(launch_method):
        candidates = LIGHT_PRESET_CANDIDATES_WINWS2
    elif is_zapret1_launch_method(launch_method):
        candidates = LIGHT_PRESET_CANDIDATES_WINWS1
    else:
        return None
    for name in candidates:
        try:
            if preset_exists(name):
                return name
        except Exception:
            continue
    return None


__all__ = [
    "LIGHT_PRESET_CANDIDATES_WINWS1",
    "LIGHT_PRESET_CANDIDATES_WINWS2",
    "PresetHudClarity",
    "PresetScope",
    "apply_state_line",
    "build_preset_hud_clarity",
    "classify_preset_scope",
    "resolve_recommended_light_preset",
    "role_line_for_scope",
    "scope_label",
]
