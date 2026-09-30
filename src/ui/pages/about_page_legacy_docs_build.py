"""In-app preset documentation for About (RKNHS mental model)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtWidgets import QVBoxLayout
from qfluentwidgets import BodyLabel, CaptionLabel, StrongBodyLabel


@dataclass(slots=True)
class AboutPageLegacyDocsWidgets:
    legacy_docs_group: object | None = None
    legacy_course_group: object | None = None


def build_about_page_legacy_docs_content(
    layout: QVBoxLayout,
    *,
    tr_fn: Callable[[str, str], str],
    content_parent,
) -> AboutPageLegacyDocsWidgets:
    title = StrongBodyLabel(
        tr_fn("page.about.legacy_docs.group", "Как устроены пресеты"),
        content_parent,
    )
    layout.addWidget(title)

    note = BodyLabel(
        tr_fn(
            "page.about.legacy_docs.note",
            "Пресет — набор профилей обхода DPI. Выберите его в «Мои пресеты», затем включите обход на Control.",
        ),
        content_parent,
    )
    note.setWordWrap(True)
    layout.addWidget(note)

    steps_title = StrongBodyLabel(
        tr_fn("page.about.legacy_docs.course.group", "Быстрые шаги"),
        content_parent,
    )
    layout.addWidget(steps_title)

    for title_key, title_default, desc_key, desc_default in (
        (
            "page.about.legacy_docs.preset.title",
            "Пресет",
            "page.about.legacy_docs.preset.desc",
            "Конфиг в «Мои пресеты» — применяется после запуска обхода",
        ),
        (
            "page.about.legacy_docs.profile.title",
            "Профиль",
            "page.about.legacy_docs.profile.desc",
            "Блок фильтров и стратегий внутри пресета",
        ),
        (
            "page.about.legacy_docs.blockcheck.title",
            "BlockCheck",
            "page.about.legacy_docs.blockcheck.desc",
            "Тест стратегий; Apply пишет в текущий пресет Control",
        ),
    ):
        caption = CaptionLabel(
            f"{tr_fn(title_key, title_default)} — {tr_fn(desc_key, desc_default)}",
            content_parent,
        )
        caption.setWordWrap(True)
        layout.addWidget(caption)

    return AboutPageLegacyDocsWidgets(
        legacy_docs_group=title,
        legacy_course_group=steps_title,
    )


__all__ = ["AboutPageLegacyDocsWidgets", "build_about_page_legacy_docs_content"]
