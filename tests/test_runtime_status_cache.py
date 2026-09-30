from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch


class RuntimeStatusCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        from app.runtime_status_cache import invalidate_runtime_status_cache

        invalidate_runtime_status_cache()

    def tearDown(self) -> None:
        from app.runtime_status_cache import invalidate_runtime_status_cache

        invalidate_runtime_status_cache()

    def test_dpi_cache_reuses_probe_within_ttl(self) -> None:
        from app import runtime_status_cache

        probe = unittest.mock.Mock(side_effect=[True, False])
        with patch.dict("sys.modules", {"tray_status_icon": SimpleNamespace(is_winws2_running=probe)}):
            # Import path uses tray_status_icon inside function — patch the imported name.
            with patch("tray_status_icon.is_winws2_running", probe):
                first = runtime_status_cache.get_cached_dpi_running(force=True)
                second = runtime_status_cache.get_cached_dpi_running(force=False)
        self.assertTrue(first)
        self.assertTrue(second)
        self.assertEqual(probe.call_count, 1)

    def test_dpi_cache_force_refreshes(self) -> None:
        from app import runtime_status_cache

        probe = unittest.mock.Mock(side_effect=[True, False])
        with patch("tray_status_icon.is_winws2_running", probe):
            first = runtime_status_cache.get_cached_dpi_running(force=True)
            second = runtime_status_cache.get_cached_dpi_running(force=True)
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(probe.call_count, 2)


if __name__ == "__main__":
    unittest.main()
