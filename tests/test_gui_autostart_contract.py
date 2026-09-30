from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


class _FakeShortcut:
    def __init__(self):
        self.TargetPath = ""
        self.Arguments = ""
        self.WorkingDirectory = ""
        self.IconLocation = ""
        self.saved = False

    def Save(self):
        self.saved = True


class _FakeShell:
    def __init__(self):
        self.created_paths = []
        self.shortcut = _FakeShortcut()

    def CreateShortcut(self, path: str):
        self.created_paths.append(path)
        return self.shortcut


class _FakeToggle:
    def __init__(self, checked: bool = False):
        self._checked = bool(checked)
        self.set_calls: list[tuple[bool, bool]] = []

    def isChecked(self) -> bool:  # noqa: N802
        return self._checked

    def setChecked(self, checked: bool, block_signals: bool = False):  # noqa: N802
        self.set_calls.append((bool(checked), bool(block_signals)))
        self._checked = bool(checked)


class GuiAutostartContractTests(unittest.TestCase):
    def test_creates_user_startup_shortcut(self) -> None:
        from autostart import startup_shortcut_api

        shell = _FakeShell()
        exe_path = r"C:\Program Files\RKNHS\RKNHS.exe"
        shortcut_path = (
            r"C:\Users\Tester\AppData\Roaming\Microsoft\Windows\Start Menu"
            r"\Programs\Startup\RKNHS.lnk"
        )

        with (
            patch.object(startup_shortcut_api, "_dispatch_shell", return_value=shell),
            patch.object(startup_shortcut_api, "delete_legacy_startup_shortcuts", return_value=0),
            patch.object(Path, "mkdir", return_value=None),
        ):
            result = startup_shortcut_api.create_or_update_startup_shortcut(
                exe_path,
                shortcut_path=shortcut_path,
            )

        self.assertTrue(result)
        self.assertEqual(shell.created_paths, [shortcut_path])
        self.assertEqual(shell.shortcut.TargetPath, exe_path)
        self.assertEqual(shell.shortcut.Arguments, "--tray")
        self.assertEqual(shell.shortcut.WorkingDirectory, r"C:\Program Files\RKNHS")
        self.assertEqual(shell.shortcut.IconLocation, exe_path)
        self.assertTrue(shell.shortcut.saved)

    def test_enable_gui_autostart_returns_readable_error_message(self) -> None:
        from autostart.public import enable_gui_autostart

        with (
            patch("autostart.startup_shortcut_api.delete_startup_shortcut", return_value=False),
            patch("autostart.startup_shortcut_api.create_or_update_startup_shortcut", return_value=False),
        ):
            result = enable_gui_autostart()

        self.assertFalse(result.success)
        self.assertFalse(result.restart_requested)
        self.assertIn("Не удалось включить автозапуск", result.message)

    def test_autostart_error_notification_payload_is_user_readable(self) -> None:
        from autostart.ui.notifications import build_autostart_error_notification

        payload = build_autostart_error_notification("COM raw details")

        self.assertEqual(payload["level"], "error")
        self.assertEqual(payload["title"], "Автозапуск не включён")
        self.assertIn("COM raw details", payload["content"])
        self.assertEqual(payload["source"], "autostart.gui")
        self.assertEqual(payload["queue"], "immediate")

    def test_gui_autostart_lives_in_program_settings_snapshot(self) -> None:
        from core.runtime.program_settings_runtime_service import ProgramSettingsRuntimeService

        settings = {
            "program": {
                "dpi_autostart": True,
                "gui_autostart_enabled": True,
                "defender_disabled": False,
                "max_blocked": False,
            },
            "window": {
                "tray_close_mode": "normal",
            },
        }
        with (
            patch("settings.store.read_settings", return_value=settings),
            patch("windows_features.defender_manager.WindowsDefenderManager") as defender_cls,
            patch("windows_features.max_blocker.is_max_blocked", return_value=False),
        ):
            defender_cls.return_value.is_defender_disabled.return_value = False
            snapshot = ProgramSettingsRuntimeService().read_snapshot()

        self.assertTrue(snapshot.gui_autostart_enabled)
        self.assertEqual(snapshot.revision[1], True)

    def test_gui_autostart_toggle_uses_program_settings_action(self) -> None:
        from autostart.public import GuiAutostartResult
        from program_settings.commands import set_gui_autostart_enabled

        with (
            patch("autostart.public.enable_gui_autostart", return_value=GuiAutostartResult(success=True)) as enable,
            patch("autostart.public.save_gui_autostart_enabled", return_value=True) as save,
        ):
            result = set_gui_autostart_enabled(True)

        enable.assert_called_once()
        save.assert_called_once_with(True)
        self.assertEqual(result.level, "success")
        self.assertIsNone(result.revert_checked)

    def test_gui_autostart_snapshot_sync_blocks_toggle_signal(self) -> None:
        from core.runtime.program_settings_runtime_service import ProgramSettingsSnapshot
        from presets.ui.control.control_page_runtime_shared import apply_program_settings_toggles

        toggle = _FakeToggle(False)
        snapshot = ProgramSettingsSnapshot(
            revision=(False, True, "normal", False, False),
            auto_dpi_enabled=False,
            gui_autostart_enabled=True,
            tray_close_mode="normal",
            defender_disabled=False,
            max_blocked=False,
        )

        apply_program_settings_toggles(snapshot, gui_autostart_toggle=toggle)

        self.assertEqual(toggle.set_calls, [(True, True)])

    def test_gui_autostart_toggle_is_top_program_settings_row_for_both_modes(self) -> None:
        import inspect

        import presets.ui.control.zapret1.sections_build as winws1_sections
        import presets.ui.control.zapret2.sections_build as winws2_sections

        for source in (
            inspect.getsource(winws1_sections.build_winws1_pages_settings_sections),
            inspect.getsource(winws2_sections.build_winws2_pages_settings_sections),
        ):
            self.assertIn("gui_autostart_toggle", source)
            self.assertLess(
                source.index("program_settings_card.addSettingCard(gui_autostart_toggle)"),
                source.index("program_settings_card.addSettingCard(auto_dpi_toggle)"),
            )

    def test_autostart_is_no_longer_registered_as_standalone_page(self) -> None:
        import ui.pages as pages
        from app.page_names import PageName
        from app.search_index import SEARCH_ENTRIES
        from ui.navigation.schema import PAGE_ROUTE_SPECS
        from ui.page_composition import PAGE_DEPS_BUILDERS

        self.assertFalse(hasattr(PageName, "AUTOSTART"))
        self.assertNotIn("AutostartPage", pages.__all__)
        self.assertFalse(
            any(entry.entry_id.startswith("autostart.") for entry in SEARCH_ENTRIES)
        )
        self.assertFalse(
            any(
                str(getattr(page_name, "name", "")) == "AUTOSTART"
                for page_name in (*PAGE_ROUTE_SPECS.keys(), *PAGE_DEPS_BUILDERS.keys())
            )
        )


if __name__ == "__main__":
    unittest.main()
