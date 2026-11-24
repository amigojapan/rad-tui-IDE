"""Integration checks for generated, Python-free C++ exports."""

import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shutil
import string
import struct
import subprocess
import sys
import tempfile
import termios
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rad_tui_basic_pkg' / 'src'))

from rad_tui_basic.cpp_export import CppExportError, export_cpp  # noqa: E402


class PhoneLayoutTests(unittest.TestCase):
    def test_python_phone_form_fills_screen_and_keyboard_stays_centered(self):
        project = json.loads((ROOT / 'projects/phone_shell.json').read_text())
        self.assertNotIn('btn_interrupt', {item['name_id'] for item in project['controls']})
        for cols, lines in ((33, 100), (80, 40), (28, 24), (50, 120)):
            for standalone in (False, True):
                with self.subTest(cols=cols, lines=lines, standalone=standalone), patch.object(
                        sys, '_is_standalone_run', standalone, create=True):
                    scope = {'Form1': SimpleNamespace(x=0, y=1, w=33, h=100)}
                    scope.update({item['name_id']: SimpleNamespace(**item)
                                  for item in project['controls']})
                    exec(project['code'], scope)
                    scope.update(curses=SimpleNamespace(COLS=cols, LINES=lines),
                                 mode='ABC', keyboard_visible=True, candidate_options=[],
                                 candidate_index=0, ctrl_latch=False, alt_latch=False,
                                 shift_latch=False, caps_lock=False)
                    scope['layout']()
                    form = scope['Form1']
                    self.assertEqual((form.x, form.y, form.w, form.h),
                                     (0, 0 if standalone else 1, cols,
                                      lines if standalone else lines - 1))
                    self.assertEqual((scope['txt_shell'].x, scope['txt_shell'].w), (0, cols))
                    self.assertEqual(scope['txt_shell'].y, 0)
                    self.assertEqual(scope['btn_symbols'].y + scope['btn_symbols'].h, form.h)
                    left = (form.w - min(30, form.w)) // 2
                    self.assertEqual(scope['btn_abc'].x, left)
                    self.assertEqual(scope['btn_symbols'].x + scope['btn_symbols'].w,
                                     left + min(30, form.w))
                    for keyboard_mode, count in (('ABC', 26), ('ROM', 26), ('123', 10),
                                                 ('かな', 12), ('NAV', 12), ('SYM', 32)):
                        scope['mode'] = keyboard_mode
                        scope['layout']()
                        keys = [scope[f'key_{i:02d}'] for i in range(32)]
                        visible = [key for key in keys if key.x >= 0]
                        self.assertEqual(len(visible), count)
                        self.assertEqual(max(key.y + key.h for key in visible),
                                         scope['btn_space'].y)
                        self.assertEqual(scope['btn_symbols'].y + scope['btn_symbols'].h,
                                         form.h)
                        for row_y in {key.y for key in visible}:
                            row = sorted((key for key in visible if key.y == row_y),
                                         key=lambda key: key.x)
                            self.assertEqual(row[0].x, left)
                            self.assertEqual(row[-1].x + row[-1].w, left + min(30, cols))
                            self.assertTrue(all(a.x + a.w == b.x for a, b in zip(row, row[1:])))
                        if keyboard_mode in ('ABC', 'ROM'):
                            self.assertEqual(''.join(key.caption.lower() for key in visible),
                                             'qwertyuiopasdfghjklzxcvbnm')
                        elif keyboard_mode == '123':
                            self.assertEqual({key.caption for key in visible}, set(string.digits))
                        elif keyboard_mode == 'SYM':
                            self.assertEqual({key.caption for key in visible},
                                             set(string.punctuation))
                    scope['mode'] = 'ABC'
                    scope['symbol_return_mode'] = 'ABC'
                    scope['layout']()
                    scope['on_click_btn_symbols']()
                    self.assertEqual(scope['mode'], 'SYM')
                    scope['press_key'](0)
                    self.assertEqual(scope['txt_command'].caption, '!')
                    scope['on_click_btn_symbols']()
                    self.assertEqual(scope['mode'], 'ABC')
                    self.assertEqual(scope['layout_rows'], (lines, cols))
                    scope['keyboard_visible'] = False
                    scope['layout']()
                    self.assertEqual(scope['btn_keyboard_toggle'].x, left)
                    self.assertEqual(scope['btn_keyboard_toggle'].y + scope['btn_keyboard_toggle'].h,
                                     form.h)


def read_pty(master, seconds):
    result = bytearray()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if select.select([master], [], [], 0.05)[0]:
            try:
                result.extend(os.read(master, 65536))
            except OSError:
                break
    return bytes(result)


@unittest.skipUnless(shutil.which('g++') and sys.platform.startswith('linux'),
                     'requires Linux, g++, and ncursesw')
class CppExportIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def compile(self, project, name):
        source = export_cpp(project, self.folder / (name + '.cpp'))
        binary = self.folder / name
        subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                        str(source), '-lncursesw', '-o', str(binary)],
                       check=True, capture_output=True, text=True)
        return binary

    def launch(self, binary):
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 120, 50, 0, 0))
        process = subprocess.Popen([str(binary)], stdin=slave, stdout=slave,
                                   stderr=slave, env={**os.environ, 'TERM': 'xterm-256color'})
        os.close(slave)
        self.addCleanup(lambda: os.close(master))
        def stop():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
        self.addCleanup(stop)
        return process, master

    def test_simple_callback_runs_in_compiled_app(self):
        project = json.loads((ROOT / 'projects/examples/cpp-export-demo.json').read_text())
        project['code'] = ('def on_form_load():\n'
                           '    lbl_intro.caption = "NATIVE_CALLBACK_OK"\n')
        project['controls'][-1]['code'] = ('def on_click_btn_ok():\n'
                                           '    if chk_option.value:\n'
                                           '        txt_name.caption = "Enabled"\n'
                                           '    else:\n'
                                           '        txt_name.caption = "Disabled"\n')
        process, master = self.launch(self.compile(project, 'callback'))
        output = read_pty(master, 0.6)
        self.assertIn(b'NATIVE_CALLBACK_OK', output)
        self.assertIsNone(process.poll())

    def test_timer_callback_runs_in_compiled_app(self):
        project = json.loads((ROOT / 'projects/examples/cpp-export-demo.json').read_text())
        project['controls'].append({
            'name_id': 'ticker', 'tool_type': 14, 'x': -50, 'y': 1,
            'w': 1, 'h': 1, 'caption': '', 'interval': 50,
            'code': 'def on_tick_ticker():\n    lbl_intro.caption = "NATIVE_TIMER_OK"\n',
        })
        process, master = self.launch(self.compile(project, 'timer'))
        self.assertIn(b'NATIVE_TIMER_OK', read_pty(master, 0.6))
        self.assertIsNone(process.poll())

    @unittest.skipUnless(shutil.which('nano'), 'requires nano')
    def test_phone_shell_runs_command_and_curses_editor(self):
        project = json.loads((ROOT / 'projects/phone_shell.json').read_text())
        process, master = self.launch(self.compile(project, 'phone'))
        read_pty(master, 0.6)
        os.write(master, b'echo NATIVE_SHELL_OK\r')
        self.assertIn(b'NATIVE_SHELL_OK', read_pty(master, 0.8))
        os.write(master, b'nano\r')
        output = read_pty(master, 1.0)
        self.assertTrue(b'New Buffer' in output or b'Welcome to nano' in output)
        os.write(master, b'\x18')
        read_pty(master, 0.4)
        self.assertIsNone(process.poll())

    def test_phone_shell_ime_works_while_keyboard_is_minimized(self):
        project = json.loads((ROOT / 'projects/phone_shell.json').read_text())
        source = export_cpp(project, self.folder / 'phone_ime.cpp')
        harness = self.folder / 'ime_harness.cpp'
        harness.write_text(
            '#define main exported_main\n'
            f'#include "{source}"\n'
            '#undef main\n'
            'int main() {\n'
            '  std::setlocale(LC_ALL, "");\n'
            '  initscr(); cbreak(); noecho();\n'
            '  phone.init_romaji(); phone.mode = "ABC"; phone.command_set(""); phone.layout();\n'
            '  origin_x = 0; origin_y = 0;\n'
            '  bool edges = inside_form(0, 0) && inside_form(COLS - 1, LINES - 1) &&\n'
            '      hit_control(0, 0) >= 0;\n'
            '  MEVENT mode_tap{}; mode_tap.x = phone.c("btn_rom").x + 1;\n'
            '  mode_tap.y = phone.c("btn_rom").y + origin_y + 1; mode_tap.bstate = BUTTON1_RELEASED;\n'
            '  phone.mouse(mode_tap); bool touch_mode = phone.mode == "ROM";\n'
            '  for (char ch : std::string("nihon")) phone.physical(ch);\n'
            '  bool kana = phone.command() == "にほん";\n'
            '  phone.space();\n'
            '  bool options = !phone.candidate_options.empty() && phone.candidate_options[0] == "日本";\n'
            '  phone.enter(); bool kanji = phone.command() == "日本";\n'
            '  MEVENT hide_tap{}; hide_tap.x = phone.c("btn_keyboard_toggle").x + 1;\n'
            '  hide_tap.y = phone.c("btn_keyboard_toggle").y + origin_y + 1;\n'
            '  hide_tap.bstate = BUTTON1_RELEASED;\n'
            '  phone.mouse(hide_tap); bool minimized = !phone.keyboard_visible;\n'
            '  phone.physical(\'q\'); phone.physical(\'z\');\n'
            '  bool toggled = phone.mode == "ABC";\n'
            '  phone.physical(\'/\'); phone.physical(\'q\'); phone.physical(\'z\');\n'
            '  bool escape = phone.command() == "日本qz";\n'
            '  bool wide_form = form_w == COLS && form_h == LINES && form_y == 0;\n'
            '  resizeterm(24, 28); phone.keyboard_visible = true; phone.layout();\n'
            '  bool compact = form_w == 28 && form_h == 24 && phone.c("btn_space").h == 1 &&\n'
            '      phone.c("btn_space").y + 1 == form_h && phone.c("btn_abc").x == 0 &&\n'
            '      phone.c("txt_shell").x == 0 && phone.c("txt_shell").w == 28;\n'
            '  phone.click("btn_symbols");\n'
            '  bool symbols = phone.mode == "SYM" && phone.key(0).caption == "!" &&\n'
            '      phone.key(31).caption == "?" && phone.key(31).x >= 0;\n'
            '  phone.press_key(31); bool symbol_input = phone.command().back() == \'?\';\n'
            '  phone.click("btn_symbols");\n'
            '  bool restored = phone.mode == "ABC" && phone.key(26).x < 0 &&\n'
            '      phone.c("btn_symbols").y + phone.c("btn_symbols").h == form_h;\n'
            '  phone.click("btn_num");\n'
            '  bool digits = phone.key(9).caption == "0" && phone.key(10).x < 0;\n'
            '  endwin(); return !edges ? 11 : !touch_mode ? 12 : !kana ? 13 : !options ? 14 :\n'
            '      !kanji ? 15 : !minimized ? 16 : !toggled ? 17 : !escape ? 18 :\n'
            '      !wide_form ? 19 : !compact ? 20 : !symbols ? 21 : !symbol_input ? 22 :\n'
            '      !restored ? 23 : !digits ? 24 : 0;\n'
            '}\n')
        binary = self.folder / 'ime_harness'
        subprocess.run(['g++', '-std=c++17', '-O2', str(harness), '-lncursesw',
                        '-o', str(binary)], check=True, capture_output=True, text=True)
        process, master = self.launch(binary)
        read_pty(master, 0.2)
        self.assertEqual(process.wait(timeout=2), 0)

    def test_unsupported_callback_has_location_and_no_output(self):
        project = json.loads((ROOT / 'projects/examples/cpp-export-demo.json').read_text())
        project['controls'][-1]['code'] = ('def on_click_btn_ok():\n'
                                           '    for item in [1, 2]:\n'
                                           '        pass\n')
        path = self.folder / 'unsupported.cpp'
        with self.assertRaisesRegex(CppExportError, r'control btn_ok.*line 2.*For'):
            export_cpp(project, path)
        self.assertFalse(path.exists())
        project['controls'][-1]['code'] = ('def on_mouse_btn_ok():\n'
                                           '    msgbox("mouse")\n')
        with self.assertRaisesRegex(CppExportError, r'control btn_ok.*line 1.*not supported'):
            export_cpp(project, path)
        self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
