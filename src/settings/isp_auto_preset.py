"""Detect ISP and auto-select winws2 preset on startup."""

from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass

from log.log import log
from settings.mode import ENGINE_WINWS2, SELECTED_SOURCE_PRESET_FILE_NAME_KEY_WINWS2
from settings.store import (
    get_isp_auto_preset_applied,
    get_isp_auto_preset_enabled,
    get_selected_source_preset_file_name,
    set_isp_auto_preset_applied,
    set_selected_source_preset_file_name,
)

_IP_LOOKUP_URL = "http://ip-api.com/json/?fields=status,isp,org,as,query"
_LOOKUP_TIMEOUT_SEC = 6

# Preset file names inside presets/winws2_builtin (or winws2).
_ISP_PRESET_FILES: dict[str, str] = {
    "rostelecom": "Ростелеком.txt",
    "mgts": "general ALT11.txt",
    "domru": "general ALT10.txt",
}

_ISP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rostelecom", re.compile(r"rostelecom|ростелеком|rt\.ru|pjsc\s+\"?rostelecom", re.I)),
    ("mgts", re.compile(r"\bmgts\b|мгтс|comcor|multiservice", re.I)),
    ("domru", re.compile(r"dom\.ru|дом\.ру|\berth\b|domru|эри\-?тел", re.I)),
)


@dataclass(frozen=True, slots=True)
class IspDetectionResult:
    isp_key: str | None
    isp_label: str
    preset_file: str | None


def _fetch_ip_info() -> dict:
    request = urllib.request.Request(
        _IP_LOOKUP_URL,
        headers={"User-Agent": "RKNHS/1.0"},
    )
    with urllib.request.urlopen(request, timeout=_LOOKUP_TIMEOUT_SEC) as response:
        payload = response.read().decode("utf-8", errors="ignore")
    data = json.loads(payload)
    if not isinstance(data, dict) or str(data.get("status") or "").lower() != "success":
        return {}
    return data


def detect_isp_from_network() -> IspDetectionResult:
    try:
        info = _fetch_ip_info()
    except Exception as exc:
        log(f"ISP auto-preset: не удалось определить провайдера: {exc}", "DEBUG")
        return IspDetectionResult(None, "", None)

    haystack = " ".join(
        str(info.get(key) or "")
        for key in ("isp", "org", "as")
    ).strip()
    if not haystack:
        return IspDetectionResult(None, "", None)

    for isp_key, pattern in _ISP_PATTERNS:
        if pattern.search(haystack):
            preset = _ISP_PRESET_FILES.get(isp_key)
            log(f"ISP auto-preset: определён {isp_key} ({haystack})", "INFO")
            return IspDetectionResult(isp_key, haystack, preset)

    log(f"ISP auto-preset: провайдер не распознан ({haystack})", "DEBUG")
    return IspDetectionResult(None, haystack, None)


def _preset_exists(file_name: str) -> bool:
    import os

    from config.config import MAIN_DIRECTORY

    for folder in ("presets/winws2_builtin", "presets/winws2"):
        path = os.path.join(MAIN_DIRECTORY, folder, file_name)
        if os.path.isfile(path):
            return True
    return False


@dataclass(frozen=True, slots=True)
class IspApplyResult:
    applied: bool
    isp_label: str = ""
    preset_file: str = ""


def maybe_apply_isp_preset(*, force: bool = False) -> bool:
    return bool(maybe_apply_isp_preset_detailed(force=force).applied)


def maybe_apply_isp_preset_detailed(*, force: bool = False) -> IspApplyResult:
    """Apply ISP-specific preset once when enabled and no preset selected yet."""
    if not get_isp_auto_preset_enabled() and not force:
        return IspApplyResult(False)

    if get_isp_auto_preset_applied() and not force:
        return IspApplyResult(False)

    current = str(get_selected_source_preset_file_name(ENGINE_WINWS2) or "").strip()
    if current and not force:
        set_isp_auto_preset_applied(True)
        return IspApplyResult(False)

    detection = detect_isp_from_network()
    preset_file = str(detection.preset_file or "").strip()
    if not preset_file:
        return IspApplyResult(False, isp_label=str(detection.isp_label or ""))
    if not _preset_exists(preset_file):
        log(f"ISP auto-preset: файл пресета не найден: {preset_file}", "WARNING")
        return IspApplyResult(False, isp_label=str(detection.isp_label or ""))

    if not set_selected_source_preset_file_name(ENGINE_WINWS2, preset_file):
        return IspApplyResult(False, isp_label=str(detection.isp_label or ""))

    set_isp_auto_preset_applied(True)
    log(f"ISP auto-preset: выбран пресет {preset_file} для {detection.isp_label}", "INFO")
    return IspApplyResult(
        True,
        isp_label=str(detection.isp_label or detection.isp_key or ""),
        preset_file=preset_file,
    )
