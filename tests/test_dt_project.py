"""Desktop project navigation, icons, launch behavior, and phone shell signal."""

import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rad_tui_basic_pkg' / 'src'))

from rad_tui_basic.rad_tui_py import Window  # noqa: E402


class DesktopProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project_dir = Path(self.temp.name)
        project = json.loads((ROOT / 'projects/phoneapps/DT/DT.json').read_text())
        self.assertEqual(project['code'], (ROOT / 'projects/phoneapps/DT/DT.py').read_text())
        self.form = Window.from_dict(project)
        self.messages = []
        self.scope = {'PROJECT_DIR': str(self.project_dir), 'Form1': self.form,
                      'msgbox': self.messages.append}
        self.scope.update({control.name_id: control for control in self.form.controls})
        exec(project['code'], self.scope)
        self.scope['curses'] = SimpleNamespace(
            COLS=80, LINES=24, def_prog_mode=lambda: None, endwin=lambda: None,
            reset_prog_mode=lambda: None, curs_set=lambda _: None)
        with patch.object(os, 'isatty', return_value=False):
            self.scope['on_form_load']()

    def test_creates_folders_and_navigates_every_level(self):
        desktop = self.project_dir / 'DTF'
        self.assertTrue((desktop / 'tools').is_dir())
        self.assertTrue((desktop / 'games').is_dir())
        self.assertEqual({button.caption for button in self.scope['entry_controls']},
                         {'🗂️ games', '🗂️ tools'})

        (desktop / 'games' / 'arcade').mkdir()
        self.scope['on_click_dt_entry_0']()
        self.assertEqual(self.scope['current_dir'], desktop / 'games')
        self.assertEqual([button.caption for button in self.scope['entry_controls']],
                         ['🗂️ arcade'])
        self.scope['on_click_dt_entry_0']()
        self.assertEqual(self.scope['current_dir'], desktop / 'games' / 'arcade')
        self.scope['on_click_btn_back']()
        self.assertEqual(self.scope['current_dir'], desktop / 'games')
        self.scope['on_click_btn_back']()
        self.assertEqual(self.scope['current_dir'], desktop)
        self.assertEqual(len(self.form.controls), 7 + len(self.scope['entry_controls']))

    def test_folder_icon_file_changes_folder_button(self):
        desktop = self.project_dir / 'DTF'
        (desktop / 'internet').mkdir()
        (desktop / 'internet.icons').write_text('🌐\n')
        self.scope['on_click_btn_refresh']()
        self.assertIn('🌐 internet',
                      {button.caption for button in self.scope['entry_controls']})

    def test_uses_icon_files_and_launches_binary_in_its_folder(self):
        desktop = self.project_dir / 'DTF'
        program = desktop / 'my tool.bin'
        program.write_text('#!/bin/sh\nprintf launched > marker.txt\n')
        program.chmod(0o755)
        (desktop / 'my tool.icons').write_text('🎮\n')
        fallback = desktop / 'plain.bin'
        fallback.write_text('#!/bin/sh\nexit 0\n')
        fallback.chmod(0o755)
        self.scope['on_click_btn_refresh']()
        captions = {button.caption for button in self.scope['entry_controls']}
        self.assertIn('🎮 my tool', captions)
        self.assertIn('⚡ plain', captions)
        button = next(button for button in self.scope['entry_controls']
                      if button.caption == '🎮 my tool')
        self.scope['on_click_' + button.name_id]()
        self.assertEqual((desktop / 'marker.txt').read_text(), 'launched')
        self.assertEqual(self.messages, [])

    def test_keeps_one_button_per_entry_across_pages(self):
        desktop = self.project_dir / 'DTF'
        for index in range(40):
            (desktop / f'program_{index:02d}.bin').touch()
        self.scope['on_click_btn_refresh']()
        self.assertEqual(len(self.scope['entry_controls']), 42)
        self.assertEqual(len(self.form.controls), 49)
        self.assertGreaterEqual(self.scope['btn_next'].x, 0)
        self.scope['on_click_btn_next']()
        self.assertEqual(self.scope['page'], 1)
        self.assertGreaterEqual(self.scope['btn_prev'].x, 0)
        self.assertTrue(any(button.x >= 0 for button in self.scope['entry_controls'][28:]))

    def test_reflows_after_terminal_resize(self):
        self.scope['curses'].LINES = 32
        self.scope['curses'].resizeterm = lambda lines, cols: None
        with patch.object(os, 'get_terminal_size', return_value=os.terminal_size((80, 32))):
            self.scope['on_tick_dt_timer']()
        self.assertEqual(self.form.h, 31)
        self.assertEqual(self.scope['btn_next'].y, 30)

    def test_phone_shell_understands_split_hide_keyboard_message(self):
        phone = json.loads((ROOT / 'projects/phoneapps/phone_shell.json').read_text())
        scope = {}
        exec(phone['code'], scope)
        terminal = scope['TerminalBuffer'](10, 5)
        scope['terminal'] = terminal
        scope['keyboard_visible'] = True
        layouts = []
        scope['layout'] = lambda: layouts.append(True)
        terminal.feed('\x1b]777;rad-tui;hide-')
        terminal.feed('keyboard\x07')
        scope['handle_terminal_commands']()
        self.assertFalse(scope['keyboard_visible'])
        self.assertEqual(layouts, [True])
        self.assertEqual(terminal.osc_messages, [])


if __name__ == '__main__':
    unittest.main()
