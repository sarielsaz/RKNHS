from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from app.branding import HIDE_DONATE_NAV, HIDE_EXTERNAL_LINKS
from app.state_store import MainWindowStateStore
from ui.pages.about_page_about_build import build_about_page_about_content
from ui.pages.about_page import AboutPage
from ui.pages.about_page_tabs_build import build_about_page_tabs
from ui.theme import get_theme_tokens


class AboutPageAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._app = QApplication.instance() or QApplication([])

    def test_about_buttons_have_screen_reader_names(self) -> None:
        parent = QWidget()
        layout = QVBoxLayout(parent)

        widgets = build_about_page_about_content(
            layout,
            tr_fn=lambda _key, default: default,
            tokens=get_theme_tokens(),
            content_parent=parent,
            app_version="9.9.9",
            make_section_label=lambda text: QWidget(),
            on_open_updates=lambda: None,
            on_open_premium=lambda: None,
        )

        self.assertEqual(widgets.update_btn.accessibleName(), "Открыть настройки обновлений")
        self.assertEqual(
            widgets.update_btn.property("screenReaderStateText"),
            "Открыть настройки обновлений",
        )
        self.assertIn("автоматической проверки", widgets.update_btn.accessibleDescription())
        self.assertEqual(widgets.about_app_name_label.accessibleName(), "Название программы: RKNHS")
        self.assertEqual(
            widgets.about_app_name_label.property("screenReaderStateText"),
            "Название программы: RKNHS",
        )
        self.assertTrue(
            str(widgets.about_version_value_label.accessibleName()).startswith("Версия программы:")
        )
        self.assertIn("9.9.9", widgets.about_version_value_label.text())

        # RKNHS fork hides donate/premium UI, license block, and upstream course links.
        from app.branding import HIDE_LICENSE_UI

        self.assertTrue(HIDE_DONATE_NAV)
        self.assertTrue(HIDE_EXTERNAL_LINKS)
        self.assertTrue(HIDE_LICENSE_UI)
        self.assertIsNone(widgets.premium_btn)
        self.assertIsNone(widgets.sub_status_label)
        self.assertIsNone(widgets.course_group)
        self.assertIsNone(widgets.youtube_course_card)
        self.assertIsNone(widgets.youtube_playlist_card)
        self.assertIsNone(widgets.license_card)
        self.assertIsNotNone(widgets.legacy_docs_group)
        self.assertIsNotNone(widgets.legacy_course_group)

    def test_subscription_status_update_reads_state_for_screen_reader(self) -> None:
        page = AboutPage.__new__(AboutPage)
        page._ui_language = "ru"
        page.sub_status_icon = _IconWidget()
        page.sub_status_label = _TextWidget()

        AboutPage.update_subscription_status(page, True, 5)

        self.assertEqual(page.sub_status_label.text(), "Premium (осталось 5 дней)")
        self.assertEqual(page.sub_status_label.accessible_name, "Статус подписки: Premium (осталось 5 дней)")
        self.assertEqual(
            page.sub_status_label.property("screenReaderStateText"),
            "Статус подписки: Premium (осталось 5 дней)",
        )

    def test_about_tabs_read_current_section_for_screen_reader(self) -> None:
        widgets = build_about_page_tabs(
            tr_fn=lambda _key, default: default,
            on_switch_tab=lambda _index: None,
        )
        self.addCleanup(widgets.stacked_widget.deleteLater)

        self.assertEqual(widgets.tabs_pivot.accessibleName(), "Вкладки страницы о программе, выбрано: О программе")
        self.assertIn("О программе, Справка или Sazzero", widgets.tabs_pivot.accessibleDescription())
        self.assertEqual(
            widgets.tabs_pivot.items["about"].accessibleName(),
            "Вкладки страницы о программе: О программе, выбрано",
        )
        self.assertNotIn("support", widgets.tabs_pivot.items)

        widgets.tabs_pivot.setCurrentItem("help")

        self.assertEqual(widgets.tabs_pivot.accessibleName(), "Вкладки страницы о программе, выбрано: Справка")
        self.assertEqual(
            widgets.tabs_pivot.property("screenReaderStateText"),
            "Вкладки страницы о программе, выбрано: Справка",
        )
        self.assertEqual(
            widgets.tabs_pivot.items["about"].accessibleName(),
            "Вкладки страницы о программе: О программе, не выбрано",
        )
        self.assertEqual(
            widgets.tabs_pivot.items["help"].accessibleName(),
            "Вкладки страницы о программе: Справка, выбрано",
        )

    def test_about_language_refresh_keeps_screen_reader_names(self) -> None:
        page = AboutPage.__new__(AboutPage)
        page._ui_language = "ru"
        page.about_section_version_label = _TextWidget()
        page.about_app_name_label = _TextWidget()
        page.about_version_value_label = _TextWidget()
        page.update_btn = _TextWidget()
        page.about_section_subscription_label = _TextWidget()
        page.sub_desc_label = _TextWidget()
        page.premium_btn = _TextWidget()
        page._current_subscription_state = lambda: (False, None)
        page.update_subscription_status = lambda *_args: None

        AboutPage._retranslate_about_tab(page)

        self.assertEqual(page.about_app_name_label.accessible_name, "Название программы: RKNHS")
        self.assertEqual(
            page.about_app_name_label.property("screenReaderStateText"),
            "Название программы: RKNHS",
        )
        self.assertTrue(page.about_version_value_label.accessible_name.startswith("Версия программы: "))
        self.assertEqual(
            page.about_version_value_label.property("screenReaderStateText"),
            page.about_version_value_label.accessible_name,
        )
        self.assertEqual(page.update_btn.accessible_name, "Открыть настройки обновлений")
        self.assertEqual(page.update_btn.property("screenReaderStateText"), "Открыть настройки обновлений")
        self.assertIn("автоматической проверки", page.update_btn.accessible_description)
        self.assertIn("RKNHS Premium", page.sub_desc_label.property("screenReaderStateText"))
        self.assertEqual(page.premium_btn.accessible_name, "Открыть Premium и VPN")
        self.assertEqual(page.premium_btn.property("screenReaderStateText"), "Открыть Premium и VPN")
        self.assertIn("Premium", page.premium_btn.accessible_description)

    def test_about_page_hides_upstream_support_blocks_on_about_tab(self) -> None:
        page = AboutPage(
            open_premium=lambda: None,
            open_updates=lambda: None,
            create_open_action_worker=lambda *_args, **_kwargs: None,
            ui_state_store=MainWindowStateStore(),
        )
        self.addCleanup(page.cleanup)
        self.addCleanup(page.deleteLater)

        self.assertTrue(HIDE_EXTERNAL_LINKS)
        self.assertNotIn("support", page.tabs_pivot.items)
        self.assertEqual(page.stacked_widget.count(), 3)
        self.assertIsNone(page._support_discussions_card)
        self.assertIsNone(page._support_telegram_card)
        self.assertIsNone(page._support_discord_card)

        page.switch_to_tab("support")

        self.assertEqual(page.stacked_widget.currentIndex(), 0)
        self.assertEqual(page.tabs_pivot.currentRouteKey(), "about")


class _TextWidget:
    def __init__(self) -> None:
        self.text_value = ""
        self.accessible_name = ""
        self.accessible_description = ""
        self.properties = {}

    def setText(self, text: str) -> None:  # noqa: N802
        self.text_value = str(text)

    def text(self) -> str:
        return self.text_value

    def setAccessibleName(self, text: str) -> None:  # noqa: N802
        self.accessible_name = str(text)

    def setAccessibleDescription(self, text: str) -> None:  # noqa: N802
        self.accessible_description = str(text)

    def setProperty(self, name: str, value) -> None:  # noqa: N802
        self.properties[str(name)] = value

    def property(self, name: str):  # noqa: N802
        return self.properties.get(str(name))

    def accessibleName(self) -> str:  # noqa: N802
        return self.accessible_name

    def accessibleDescription(self) -> str:  # noqa: N802
        return self.accessible_description


class _IconWidget:
    def setPixmap(self, _pixmap) -> None:  # noqa: N802
        return None


if __name__ == "__main__":
    unittest.main()
