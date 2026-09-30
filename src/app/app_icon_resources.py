from __future__ import annotations

import os
import sys

from config.config import ICON_DEV_PATH, ICON_FILE, ICON_PATH, MAIN_DIRECTORY, is_dev_build_channel


def _app_icon_candidates() -> tuple[str, ...]:
    preferred_path = ICON_DEV_PATH if is_dev_build_channel() else ICON_PATH
    candidates: list[str] = []
    for candidate in (preferred_path, ICON_PATH):
        clean_path = str(candidate or "")
        if clean_path and clean_path not in candidates:
            candidates.append(clean_path)

    bundled_name = str(ICON_FILE or "RKNHS.ico")
    for base in (
        os.path.join(MAIN_DIRECTORY, "_internal", "ico"),
        getattr(sys, "_MEIPASS", ""),
    ):
        clean_base = str(base or "")
        if not clean_base:
            continue
        bundled_path = os.path.join(clean_base, bundled_name)
        if bundled_path not in candidates:
            candidates.append(bundled_path)

    return tuple(candidates)


def resolve_existing_app_icon_path() -> str:
    for candidate in _app_icon_candidates():
        if candidate and os.path.exists(candidate):
            return os.path.abspath(candidate)
    return ""


__all__ = ["resolve_existing_app_icon_path"]
