"""Regression for terminals that expose only 64 curses color pairs."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rad_tui_basic_pkg' / 'src'))

from rad_tui_basic import rad_tui_py  # noqa: E402


class ColorPairLimitTests(unittest.TestCase):
    def test_64_pair_terminal_never_uses_an_invalid_pair(self):
        initialized = []

        def initialize(index, fg, bg):
            self.assertLess(index, 64)
            initialized.append(index)

        def color_pair(index):
            self.assertLess(index, 64)
            return index

        with patch.object(rad_tui_py.curses, 'COLOR_PAIRS', 64, create=True), \
             patch.object(rad_tui_py.curses, 'init_pair', side_effect=initialize), \
             patch.object(rad_tui_py.curses, 'color_pair', side_effect=color_pair):
            rad_tui_py.init_ide_color_pairs()
            for fg in range(8):
                for bg in range(8):
                    rad_tui_py.ide_color_pair(fg, bg)

        self.assertIn(63, initialized)
        self.assertNotIn(64, initialized)


if __name__ == '__main__':
    unittest.main()
