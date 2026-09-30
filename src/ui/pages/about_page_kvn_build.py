"""Build-helper вкладки автора форка для About page."""

from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QFrame
from qfluentwidgets import SubtitleLabel


@dataclass(slots=True)
class AboutPageKvnWidgets:
    hero_wrap: object
    features_group: object | None = None
    yt_card: object | None = None
    game_card: object | None = None
    links_group: object | None = None
    tg_card: object | None = None
    bot_card: object | None = None
    bypass_card: object | None = None
    gh_card: object | None = None


def build_about_page_kvn_content(
    layout: QVBoxLayout,
    *,
    tokens,
    content_parent,
    on_open_kvn_channel,
    on_open_kvn_bot,
    on_open_kvn_bypass,
    on_open_kvn_github,
) -> AboutPageKvnWidgets:
    _ = (content_parent, on_open_kvn_channel, on_open_kvn_bot, on_open_kvn_bypass, on_open_kvn_github)
    try:
        from app.branding import FORK_AUTHOR, FORK_AUTHOR_DESCRIPTION
    except Exception:
        FORK_AUTHOR = "Sazzero"
        FORK_AUTHOR_DESCRIPTION = "Собственная модификация Sazzero."

    hero_wrap = QFrame()
    hero_wrap.setStyleSheet("QFrame { background: transparent; border: none; }")

    hero_layout = QVBoxLayout(hero_wrap)
    hero_layout.setContentsMargins(0, 8, 0, 0)
    hero_layout.setSpacing(8)

    hero_title = SubtitleLabel(FORK_AUTHOR)
    hero_title.setProperty("tone", "primary")
    hero_layout.addWidget(hero_title)

    subtitle = QLabel(FORK_AUTHOR_DESCRIPTION)
    subtitle.setWordWrap(True)
    subtitle.setStyleSheet(
        f"QLabel {{ color: {tokens.fg}; font-size: 15px; font-weight: 600; "
        f"font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif; }}"
    )
    hero_layout.addWidget(subtitle)

    desc = QLabel(
        "Форк RKNHS не связан со сторонними сообществами и внешними каналами поддержки."
    )
    desc.setWordWrap(True)
    desc.setStyleSheet(
        f"QLabel {{ color: {tokens.fg_muted}; font-size: 13px; "
        f"font-family: 'Segoe UI', sans-serif; padding-top: 4px; }}"
    )
    hero_layout.addWidget(desc)

    layout.addWidget(hero_wrap)
    layout.addStretch()

    return AboutPageKvnWidgets(hero_wrap=hero_wrap)
