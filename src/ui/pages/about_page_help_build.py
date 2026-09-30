"""Build-helper вкладки «Справка» для About page."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

from PyQt6.QtWidgets import QVBoxLayout

from qfluentwidgets import BodyLabel, CaptionLabel


@dataclass(slots=True)
class AboutPageHelpWidgets:
    motto_wrap: object | None = None
    docs_group: object | None = None
    forum_card: object | None = None
    info_card: object | None = None
    android_card: object | None = None
    github_card: object | None = None
    news_group: object | None = None
    telegram_card: object | None = None
    mastodon_card: object | None = None
    bastyon_card: object | None = None


def build_about_page_help_content(
    layout: QVBoxLayout,
    *,
    tr_fn: Callable[[str, str], str],
    tokens,
    content_parent,
    make_section_label: Callable[[str], object],
    hyperlink_card_cls,
    push_setting_card_cls,
    setting_card_group_cls,
    fluent_icon,
    on_open_forum,
    on_open_telegram_news,
) -> AboutPageHelpWidgets:
    _ = (
        tokens,
        hyperlink_card_cls,
        push_setting_card_cls,
        setting_card_group_cls,
        fluent_icon,
        on_open_forum,
        on_open_telegram_news,
    )
    try:
        from app.branding import FORK_DESCRIPTION
    except Exception:
        FORK_DESCRIPTION = "RKNHS — собственная модификация от Sazzero."

    layout.addWidget(make_section_label(tr_fn("page.about.tab.help", "СПРАВКА")))
    body = BodyLabel(FORK_DESCRIPTION, content_parent)
    body.setWordWrap(True)
    layout.addWidget(body)
    note = CaptionLabel(
        "Внешние ссылки на Obsidian, GitHub, Telegram и Discord в этом форке отключены.",
        content_parent,
    )
    note.setWordWrap(True)
    layout.addWidget(note)
    layout.addStretch()
    return AboutPageHelpWidgets()
