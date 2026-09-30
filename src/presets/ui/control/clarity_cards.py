"""Shared Control cards: howto + light bypass + offline lists pack."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ControlClarityCards:
    howto_card: object | None = None
    light_bypass_card: object | None = None
    offline_pack_card: object | None = None


def build_control_clarity_cards(
    *,
    tr_fn,
    content_parent,
    setting_card_group_cls,
    push_setting_card_cls,
    on_open_howto,
    on_apply_light_bypass,
    on_open_blockcheck=None,
    on_open_vpn_split=None,
    on_import_lists_pack=None,
    on_restore_lists_pack=None,
    on_export_lists_pack=None,
) -> ControlClarityCards:
    from presets.ui.control.shared_builders import build_deferred_themed_push_setting_card_common
    from ui.fluent_widgets import enable_setting_card_group_auto_height

    group = setting_card_group_cls(
        tr_fn("page.control.howto.title", "Как это устроено"),
        content_parent,
    )

    howto_card = build_deferred_themed_push_setting_card_common(
        push_setting_card_cls=push_setting_card_cls,
        button_text=tr_fn("page.control.howto.open", "Понятно"),
        icon_name="fa5s.info-circle",
        icon_color="#5CD6FF",
        title_text=tr_fn("page.control.howto.title", "Как это устроено"),
        content_text=tr_fn(
            "page.control.howto.body",
            "1) Выберите пресет → 2) Включите обход → 3) При проблеме Blockcheck",
        ),
        on_click=on_open_howto,
        button_accessible_name=tr_fn("page.control.howto.title", "Как это устроено"),
        parent=content_parent,
    )
    group.addSettingCard(howto_card)

    if callable(on_open_blockcheck):
        blockcheck_card = build_deferred_themed_push_setting_card_common(
            push_setting_card_cls=push_setting_card_cls,
            button_text=tr_fn("page.control.howto.open_blockcheck", "Blockcheck"),
            icon_name="fa5s.search",
            icon_color="#F0B429",
            title_text=tr_fn("page.control.howto.open_blockcheck", "Blockcheck"),
            content_text=tr_fn(
                "page.blockcheck.subtitle",
                "Проверка блокировок; Apply пишет в текущий пресет",
            ),
            on_click=on_open_blockcheck,
            button_accessible_name=tr_fn("page.control.howto.open_blockcheck", "Blockcheck"),
            parent=content_parent,
        )
        group.addSettingCard(blockcheck_card)

    if callable(on_open_vpn_split):
        vpn_card = build_deferred_themed_push_setting_card_common(
            push_setting_card_cls=push_setting_card_cls,
            button_text=tr_fn("page.control.howto.open_vpn_split", "VPN Split"),
            icon_name="fa5s.random",
            icon_color="#3DDC97",
            title_text=tr_fn("page.control.howto.open_vpn_split", "VPN Split"),
            content_text=tr_fn(
                "page.vpn_split.subtitle",
                "Упрямые домены через VPN без расширения DPI",
            ),
            on_click=on_open_vpn_split,
            button_accessible_name=tr_fn("page.control.howto.open_vpn_split", "VPN Split"),
            parent=content_parent,
        )
        group.addSettingCard(vpn_card)

    light_bypass_card = build_deferred_themed_push_setting_card_common(
        push_setting_card_cls=push_setting_card_cls,
        button_text=tr_fn("page.control.light_bypass.button", "Включить"),
        icon_name="fa5s.feather",
        icon_color="#3DDC97",
        title_text=tr_fn("page.control.light_bypass.title", "Лёгкий обход"),
        content_text=tr_fn(
            "page.control.light_bypass.desc",
            "Переключить на узкий game-filter пресет — меньше нагрузка",
        ),
        on_click=on_apply_light_bypass,
        button_accessible_name=tr_fn("page.control.light_bypass.title", "Лёгкий обход"),
        parent=content_parent,
    )
    group.addSettingCard(light_bypass_card)

    offline_pack_card = None
    if callable(on_import_lists_pack):
        offline_pack_card = build_deferred_themed_push_setting_card_common(
            push_setting_card_cls=push_setting_card_cls,
            button_text=tr_fn("page.control.offline_pack.import", "Импорт zip"),
            icon_name="fa5s.archive",
            icon_color="#5CD6FF",
            title_text=tr_fn("page.control.offline_pack.title", "Офлайн-пакет списков"),
            content_text=tr_fn(
                "page.control.offline_pack.desc",
                "Обновляет base-списки атомарно — текущие файлы не ломаются, пока идёт замена",
            ),
            on_click=on_import_lists_pack,
            button_accessible_name=tr_fn("page.control.offline_pack.title", "Офлайн-пакет списков"),
            parent=content_parent,
        )
        group.addSettingCard(offline_pack_card)

        if callable(on_restore_lists_pack):
            restore_card = build_deferred_themed_push_setting_card_common(
                push_setting_card_cls=push_setting_card_cls,
                button_text=tr_fn("page.control.offline_pack.restore", "Откат"),
                icon_name="fa5s.undo",
                icon_color="#F0B429",
                title_text=tr_fn("page.control.offline_pack.restore_title", "Откатить списки"),
                content_text=tr_fn(
                    "page.control.offline_pack.restore_desc",
                    "Вернуть предыдущий снимок base-списков",
                ),
                on_click=on_restore_lists_pack,
                button_accessible_name=tr_fn(
                    "page.control.offline_pack.restore_title",
                    "Откатить списки",
                ),
                parent=content_parent,
            )
            group.addSettingCard(restore_card)

        if callable(on_export_lists_pack):
            export_card = build_deferred_themed_push_setting_card_common(
                push_setting_card_cls=push_setting_card_cls,
                button_text=tr_fn("page.control.offline_pack.export", "Экспорт"),
                icon_name="fa5s.download",
                icon_color="#3DDC97",
                title_text=tr_fn("page.control.offline_pack.export_title", "Экспорт пакета"),
                content_text=tr_fn(
                    "page.control.offline_pack.export_desc",
                    "Сохранить текущие base-списки в zip для офлайн-обновления",
                ),
                on_click=on_export_lists_pack,
                button_accessible_name=tr_fn(
                    "page.control.offline_pack.export_title",
                    "Экспорт пакета",
                ),
                parent=content_parent,
            )
            group.addSettingCard(export_card)

    enable_setting_card_group_auto_height(group)

    return ControlClarityCards(
        howto_card=group,
        light_bypass_card=light_bypass_card,
        offline_pack_card=offline_pack_card,
    )


__all__ = ["ControlClarityCards", "build_control_clarity_cards"]
