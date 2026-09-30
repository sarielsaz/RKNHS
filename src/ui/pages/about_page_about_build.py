"""Build-helper вкладки «О программе» для About page."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon,
    HyperlinkLabel,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    SubtitleLabel,
)

from ui.accessibility import set_control_accessibility, set_state_text
from ui.fluent_widgets import SettingsCard
from ui.pages.about_page_accessibility import apply_about_buttons_accessibility
from ui.theme import get_cached_qta_pixmap


@dataclass(slots=True)
class AboutPageAboutWidgets:
    about_section_version_label: object
    about_app_name_label: object
    about_version_value_label: object
    update_btn: object
    about_section_subscription_label: object
    sub_status_icon: QLabel
    sub_status_label: object
    sub_desc_label: object
    premium_btn: object
    course_group: object
    youtube_course_card: object
    youtube_playlist_card: object
    legacy_docs_group: object | None = None
    legacy_course_group: object | None = None
    license_card: object | None = None
    license_status_label: object | None = None
    license_key_edit: object | None = None
    license_machine_id_label: object | None = None
    license_deactivate_btn: object | None = None


def set_subscription_status_accessibility(label, text: object) -> None:
    value = " ".join(str(text or "").strip().split())
    if not value:
        return
    set_state_text(label, f"Статус подписки: {value}")


def set_subscription_description_accessibility(label, text: object) -> None:
    value = " ".join(str(text or "").strip().split())
    if not value:
        return
    set_state_text(label, f"Описание подписки: {value}")


def set_about_version_accessibility(app_name_label, version_label, *, app_name: object, app_version: object) -> None:
    app_name_value = " ".join(str(app_name or "").strip().split())
    app_version_value = " ".join(str(app_version or "").strip().split())
    if app_name_value:
        set_state_text(app_name_label, f"Название программы: {app_name_value}")
    if app_version_value:
        set_state_text(version_label, f"Версия программы: {app_version_value}")


def _add_feature_row(layout: QVBoxLayout, *, text: str, accent_hex: str, parent) -> None:
    row = QHBoxLayout()
    row.setSpacing(10)
    dot = QLabel("▸", parent)
    dot.setStyleSheet(f"color: {accent_hex}; font-weight: 600;")
    dot.setFixedWidth(14)
    label = BodyLabel(text, parent)
    label.setWordWrap(True)
    row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
    row.addWidget(label, 1)
    layout.addLayout(row)


def build_about_page_about_content(
    layout: QVBoxLayout,
    *,
    tr_fn: Callable[[str, str], str],
    tokens,
    content_parent,
    app_version: str,
    make_section_label: Callable[[str], object],
    on_open_updates,
    on_open_premium,
    on_activate_license=None,
    on_deactivate_license=None,
    on_copy_machine_id=None,
    license_machine_id: str = "",
    license_status_text: str = "",
    license_status_valid: bool = False,
) -> AboutPageAboutWidgets:
    from app.branding import (
        ABOUT_FEATURES,
        ABOUT_INTRO,
        ABOUT_REQUIREMENTS_NOTE,
        APP_DISPLAY_NAME,
        FORK_AUTHOR,
        HIDE_DONATE_NAV,
        HIDE_EXTERNAL_LINKS,
        HIDE_LICENSE_UI,
        TELEGRAM_CONTACT_LABEL,
        TELEGRAM_CONTACT_URL,
    )

    about_section_version_label = make_section_label(
        tr_fn("page.about.section.overview", "О программе")
    )
    layout.addWidget(about_section_version_label)

    hero_card = SettingsCard()
    hero_layout = QVBoxLayout()
    hero_layout.setSpacing(14)

    header_row = QHBoxLayout()
    header_row.setSpacing(16)

    icon_label = QLabel()
    icon_label.setPixmap(get_cached_qta_pixmap("fa5s.shield-alt", color=tokens.accent_hex, size=44))
    icon_label.setFixedSize(52, 52)
    header_row.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

    title_col = QVBoxLayout()
    title_col.setSpacing(4)
    app_name_text = tr_fn("page.about.app_name", APP_DISPLAY_NAME)
    about_app_name_label = SubtitleLabel(app_name_text)
    about_version_value_label = CaptionLabel(
        tr_fn("page.about.version.value_template", "Версия {version} · автор {author}").format(
            version=app_version,
            author=FORK_AUTHOR,
        )
    )
    set_about_version_accessibility(
        about_app_name_label,
        about_version_value_label,
        app_name=app_name_text,
        app_version=app_version,
    )
    title_col.addWidget(about_app_name_label)
    title_col.addWidget(about_version_value_label)
    header_row.addLayout(title_col, 1)

    update_btn = PushButton(
        tr_fn("page.about.button.update_settings", "Обновления"),
        icon=FluentIcon.SYNC,
    )
    apply_about_buttons_accessibility(tr_fn=tr_fn, update_btn=update_btn)
    update_btn.clicked.connect(on_open_updates)
    header_row.addWidget(update_btn, 0, Qt.AlignmentFlag.AlignTop)
    hero_layout.addLayout(header_row)

    intro = BodyLabel(
        tr_fn("page.about.intro", ABOUT_INTRO),
        content_parent,
    )
    intro.setWordWrap(True)
    set_state_text(intro, "Описание программы RKNHS")
    set_control_accessibility(
        intro,
        name="Описание программы RKNHS",
        description=ABOUT_INTRO,
    )
    hero_layout.addWidget(intro)

    features_title = StrongBodyLabel(
        tr_fn("page.about.features.title", "Что умеет"),
        content_parent,
    )
    hero_layout.addWidget(features_title)

    for feature in ABOUT_FEATURES:
        _add_feature_row(
            hero_layout,
            text=feature,
            accent_hex=tokens.accent_hex,
            parent=content_parent,
        )

    note = CaptionLabel(
        tr_fn("page.about.requirements_note", ABOUT_REQUIREMENTS_NOTE),
        content_parent,
    )
    note.setWordWrap(True)
    hero_layout.addWidget(note)

    contact_row = QHBoxLayout()
    contact_row.setSpacing(8)
    contact_caption = CaptionLabel(
        tr_fn("page.about.contact.label", "Написать автору:"),
        content_parent,
    )
    contact_link = HyperlinkLabel(
        QUrl(TELEGRAM_CONTACT_URL),
        tr_fn("page.about.contact.telegram", TELEGRAM_CONTACT_LABEL),
        content_parent,
    )
    set_control_accessibility(
        contact_link,
        name="Telegram автора Alybion",
        description="Открывает Telegram-чат с автором проекта.",
    )
    contact_row.addWidget(contact_caption, 0)
    contact_row.addWidget(contact_link, 0)
    contact_row.addStretch(1)
    hero_layout.addLayout(contact_row)

    hero_card.add_layout(hero_layout)
    layout.addWidget(hero_card)

    license_card = None
    license_status_label = None
    license_key_edit = None
    license_machine_id_label = None
    license_deactivate_btn = None
    show_license = (
        not HIDE_LICENSE_UI
        and callable(on_activate_license)
        and callable(on_deactivate_license)
        and callable(on_copy_machine_id)
    )
    if show_license:
        from ui.pages.about_page_license_build import build_about_page_license_content

        license_widgets = build_about_page_license_content(
            layout,
            tr_fn=tr_fn,
            content_parent=content_parent,
            machine_id=license_machine_id,
            status_text=license_status_text,
            status_valid=license_status_valid,
            on_activate=on_activate_license,
            on_deactivate=on_deactivate_license,
            on_copy_machine_id=on_copy_machine_id,
        )
        license_card = license_widgets.license_card
        license_status_label = license_widgets.status_label
        license_key_edit = license_widgets.key_edit
        license_machine_id_label = license_widgets.machine_id_label
        license_deactivate_btn = license_widgets.deactivate_btn

    layout.addSpacing(16)

    about_section_subscription_label = None
    sub_status_icon = None
    sub_status_label = None
    sub_desc_label = None
    premium_btn = None

    if not HIDE_DONATE_NAV:
        about_section_subscription_label = make_section_label(
            tr_fn("page.about.section.subscription", "Подписка")
        )
        layout.addWidget(about_section_subscription_label)

        sub_card = SettingsCard()
        sub_layout = QVBoxLayout()
        sub_layout.setSpacing(12)

        sub_status_layout = QHBoxLayout()
        sub_status_layout.setSpacing(8)

        sub_status_icon = QLabel()
        sub_status_icon.setPixmap(get_cached_qta_pixmap("fa5s.user", color=tokens.fg_faint, size=18))
        sub_status_icon.setFixedSize(22, 22)
        sub_status_layout.addWidget(sub_status_icon)

        sub_status_label = StrongBodyLabel(
            tr_fn("page.about.subscription.free", "Free версия")
        )
        set_subscription_status_accessibility(sub_status_label, sub_status_label.text())
        sub_status_layout.addWidget(sub_status_label, 1)
        sub_layout.addLayout(sub_status_layout)

        sub_desc_label = CaptionLabel(
            tr_fn(
                "page.about.subscription.desc",
                "Подписка RKNHS Premium открывает доступ к дополнительным темам и приоритетной поддержке.",
            )
        )
        sub_desc_label.setWordWrap(True)
        set_subscription_description_accessibility(sub_desc_label, sub_desc_label.text())
        sub_layout.addWidget(sub_desc_label)

        sub_btns = QHBoxLayout()
        sub_btns.setSpacing(8)
        premium_btn = PrimaryPushButton(
            tr_fn("page.about.button.premium_vpn", "Premium"),
            icon=FluentIcon.HEART,
        )
        apply_about_buttons_accessibility(tr_fn=tr_fn, premium_btn=premium_btn)
        premium_btn.clicked.connect(on_open_premium)
        sub_btns.addWidget(premium_btn)
        sub_btns.addStretch()
        sub_layout.addLayout(sub_btns)

        sub_card.add_layout(sub_layout)
        layout.addWidget(sub_card)
        layout.addSpacing(16)

    course_group = None
    youtube_course_card = None
    youtube_playlist_card = None
    legacy_docs_group = None
    legacy_course_group = None
    if not HIDE_EXTERNAL_LINKS:
        try:
            from ui.pages.about_page_legacy_docs_build import build_about_page_legacy_docs_content

            legacy = build_about_page_legacy_docs_content(
                layout,
                tr_fn=tr_fn,
                content_parent=content_parent,
            )
            legacy_docs_group = legacy.legacy_docs_group
            legacy_course_group = legacy.legacy_course_group
        except Exception:
            pass
    else:
        # In-app tips without upstream external docs links.
        tips_title = StrongBodyLabel(
            tr_fn("page.about.legacy_docs.group", "Как пользоваться"),
            content_parent,
        )
        layout.addWidget(tips_title)
        tips_card = SettingsCard()
        tips_layout = QVBoxLayout()
        tips_layout.setSpacing(10)
        tips_body = BodyLabel(
            tr_fn(
                "page.about.howto.body",
                "1) Выберите пресет на главной и нажмите «Запуск».\n"
                "2) Для Cursor / отдельных сайтов — вкладка VPN Split "
                "(нужен установленный AmneziaWG и ваш .conf).\n"
                "3) Telegram: либо локальный прокси во вкладке Telegram, "
                "либо подсети Telegram в VPN Split.\n"
                "4) Закрытие окна: можно свернуть в трей и оставить DPI работать.",
            ),
            content_parent,
        )
        tips_body.setWordWrap(True)
        tips_layout.addWidget(tips_body)
        tips_card.add_layout(tips_layout)
        layout.addWidget(tips_card)
        legacy_docs_group = tips_title
        legacy_course_group = tips_card

    return AboutPageAboutWidgets(
        about_section_version_label=about_section_version_label,
        about_app_name_label=about_app_name_label,
        about_version_value_label=about_version_value_label,
        update_btn=update_btn,
        about_section_subscription_label=about_section_subscription_label,
        sub_status_icon=sub_status_icon,
        sub_status_label=sub_status_label,
        sub_desc_label=sub_desc_label,
        premium_btn=premium_btn,
        course_group=course_group,
        youtube_course_card=youtube_course_card,
        youtube_playlist_card=youtube_playlist_card,
        legacy_docs_group=legacy_docs_group,
        legacy_course_group=legacy_course_group,
        license_card=license_card,
        license_status_label=license_status_label,
        license_key_edit=license_key_edit,
        license_machine_id_label=license_machine_id_label,
        license_deactivate_btn=license_deactivate_btn,
    )
