from __future__ import annotations

import os
import tempfile
import unittest

from vpn_split.domain_import import parse_domain_lines
from vpn_split.domain_patterns import (
    discover_hosts_for_base,
    host_matches_pattern,
    hosts_to_resolve,
    normalize_domain_pattern,
)


class DomainWildcardTests(unittest.TestCase):
    def test_normalize_star_and_dot_forms(self):
        self.assertEqual(normalize_domain_pattern("*.cursor.sh"), "*.cursor.sh")
        self.assertEqual(normalize_domain_pattern(".cursor.sh"), "*.cursor.sh")
        self.assertEqual(normalize_domain_pattern("https://*.cursor.sh/path"), "*.cursor.sh")
        self.assertEqual(normalize_domain_pattern("cursor.sh"), "cursor.sh")
        self.assertEqual(normalize_domain_pattern("*cursor.sh"), "")
        self.assertEqual(normalize_domain_pattern("*"), "")

    def test_parse_lines_accepts_wildcards(self):
        text = """
        # cursor
        *.cursor.sh
        *.cursor-cdn.com
        cursorapi.com
        """
        self.assertEqual(
            parse_domain_lines(text),
            ["*.cursor.sh", "*.cursor-cdn.com", "cursorapi.com"],
        )

    def test_host_matches_pattern(self):
        self.assertTrue(host_matches_pattern("api5.cursor.sh", "*.cursor.sh"))
        self.assertTrue(host_matches_pattern("cursor.sh", "*.cursor.sh"))
        self.assertTrue(host_matches_pattern("agent.us.api5.cursor.sh", "*.cursor.sh"))
        self.assertFalse(host_matches_pattern("evilcursor.sh", "*.cursor.sh"))
        self.assertFalse(host_matches_pattern("cursor.sh.evil.com", "*.cursor.sh"))

    def test_discover_from_lists_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cursor.txt")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("cursor.sh\napi2.cursor.sh\napi5.cursor.sh\nother.com\n")
            hosts = discover_hosts_for_base("cursor.sh", lists_dirs=[tmp])
            self.assertIn("cursor.sh", hosts)
            self.assertIn("api2.cursor.sh", hosts)
            self.assertIn("api5.cursor.sh", hosts)
            self.assertNotIn("other.com", hosts)

    def test_hosts_to_resolve_wildcard_includes_builtins(self):
        hosts = hosts_to_resolve("*.cursor.sh", lists_dirs=[])
        self.assertIn("cursor.sh", hosts)
        self.assertIn("api2.cursor.sh", hosts)
        self.assertIn("api5.cursor.sh", hosts)


if __name__ == "__main__":
    unittest.main()
