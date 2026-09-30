"""User-facing application branding (RKNHS)."""

from __future__ import annotations

from config.build_info import APP_VERSION

APP_DISPLAY_NAME = "RKNHS"
APP_TAGLINE = "РКН сосет хуй"
APP_SHORT_TITLE = APP_DISPLAY_NAME
FORK_AUTHOR = "Sazzero"
FORK_DESCRIPTION = (
    "RKNHS — собственная модификация от Sazzero. "
    "Внешние ссылки на сторонние репозитории и каналы отключены."
)
FORK_AUTHOR_DESCRIPTION = (
    "Собственная модификация Sazzero с локальными доработками "
    "(VPN Split, ISP-пресеты, дашборд сервисов и др.)."
)

# Orchestra and premium UI gates are disabled in this fork.
FORCE_ORCHESTRA_UNLOCKED = True
FORCE_PREMIUM_UI = True

# Hide Donate/Premium page in sidebar and related entry points.
HIDE_DONATE_NAV = True

# Hide Obsidian/GitHub/community/training links across the UI.
HIDE_EXTERNAL_LINKS = True


def window_title() -> str:
    return f"{APP_DISPLAY_NAME} // console · v{APP_VERSION}"


def tray_tooltip(*, winws2_running: bool | None = None) -> str:
    base = window_title()
    if winws2_running is True:
        return f"{base} — winws2: работает"
    if winws2_running is False:
        return f"{base} — winws2: остановлен"
    return base


def apply_ui_branding(text: str) -> str:
    """Replace upstream naming in user-visible strings."""
    if not text:
        return text

    result = str(text)
    # Longer / more specific tokens first so "ZapretGUI" does not become "RKNHSGUI".
    replacements = (
        ("Zapret 2 GUI", APP_DISPLAY_NAME),
        ("Zapret2 GUI", APP_DISPLAY_NAME),
        ("Zapret-WinGUI", APP_DISPLAY_NAME),
        ("ZapretGUI", APP_DISPLAY_NAME),
        ("Zapret GUI", APP_DISPLAY_NAME),
        ("Zapret KVN", FORK_AUTHOR),
        ("ZapretKVN", FORK_AUTHOR),
        ("Zapret 2", APP_DISPLAY_NAME),
        ("Zapret2", APP_DISPLAY_NAME),
        ("ZAPRET2", APP_DISPLAY_NAME),
        ("Zapret 1", f"{APP_DISPLAY_NAME} Classic"),
        ("Zapret1", f"{APP_DISPLAY_NAME} Classic"),
        ("ZAPRET1", f"{APP_DISPLAY_NAME} Classic"),
        ("Zapret", APP_DISPLAY_NAME),
        ("ZAPRET", APP_DISPLAY_NAME),
        ("Запрета", APP_DISPLAY_NAME),
        ("запрета", APP_DISPLAY_NAME),
        ("Запрет", APP_DISPLAY_NAME),
        ("запрет", APP_DISPLAY_NAME),
    )
    for old, new in replacements:
        result = result.replace(old, new)
    return result
