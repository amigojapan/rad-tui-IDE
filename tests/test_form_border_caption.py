"""Form border and caption behavior across project files and renderers."""

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rad_tui_basic_pkg' / 'src'))

from rad_tui_basic.cpp_export import generate_cpp  # noqa: E402
from rad_tui_basic.rad_tui_py import UIControl, Window  # noqa: E402


class Screen:
    def __init__(self):
        self.writes = []

    def addstr(self, y, x, value, attr):
        self.writes.append((y, x, value))


class FormBorderCaptionTests(unittest.TestCase):
    def test_legacy_default_and_project_round_trip(self):
        legacy = {'x': 0, 'y': 1, 'w': 20, 'h': 8, 'title': 'Example'}
        self.assertTrue(Window.from_dict(legacy).display_border_and_caption)
        form = Window.from_dict(legacy)
        form.display_border_and_caption = False
        self.assertFalse(Window.from_dict(form.to_dict()).display_border_and_caption)
        phone = json.loads((ROOT / 'projects/phoneapps/phone_shell.json').read_text())
        self.assertFalse(Window.from_dict(phone).display_border_and_caption)

    def test_border_is_visible_in_designer_without_caption(self):
        form = Window(0, 1, 20, 8, 'Example')
        colors = {'border': 1, 'bg': 2, 'btn_face': 3, 'btn_hl': 4,
                  'textbox': 5, 'handle': 6}
        form.display_border_and_caption = False
        runtime = Screen()
        form.draw(runtime, colors, run_mode=True)
        self.assertEqual(runtime.writes, [(y, 0, ' ' * 20) for y in range(1, 9)])

        designer = Screen()
        form.draw(designer, colors, run_mode=False)
        self.assertTrue(any('┌' in value for _, _, value in designer.writes))
        self.assertNotIn('Example', ''.join(value for y, _, value in designer.writes if y == 1))

        form.display_border_and_caption = True
        for run_mode in (False, True):
            visible = Screen()
            form.draw(visible, colors, run_mode=run_mode)
            self.assertTrue(any('┌' in value for _, _, value in visible.writes))
            self.assertIn('Example', ''.join(value for y, _, value in visible.writes if y == 1))

    def test_borderless_runtime_control_reaches_all_edges(self):
        form = Window(0, 0, 20, 8, 'Example')
        form.display_border_and_caption = False
        form.controls.append(UIControl(0, 0, 20, 8, 13, 'text',
                                       '\n'.join(['A' + ' ' * 18 + 'Z'] * 8)))
        colors = {'border': 1, 'bg': 2, 'btn_face': 3, 'btn_hl': 4,
                  'textbox': 5, 'handle': 6}
        screen = Screen()
        form.draw(screen, colors, run_mode=True)
        for y in (0, 7):
            self.assertIn((y, 0, 'A'), screen.writes)
            self.assertIn((y, 19, 'Z'), screen.writes)
        self.assertEqual(form.hit_control(0, 0), 0)
        self.assertEqual(form.hit_control(19, 7), 0)

    def test_cpp_export_reads_form_setting(self):
        project = json.loads((ROOT / 'projects/examples/cpp-export-demo.json').read_text())
        self.assertIn('form_display_border_and_caption = true;', generate_cpp(project))
        project['display_border_and_caption'] = False
        source = generate_cpp(project)
        self.assertIn('form_display_border_and_caption = false;', source)
        self.assertIn('if (form_display_border_and_caption)', source)


if __name__ == '__main__':
    unittest.main()
