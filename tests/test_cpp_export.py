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
from rad_tui_basic.rad_tui_py import Window  # noqa: E402


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
                    self.assertEqual(scope['txt_shell'].y, 1)
                    self.assertEqual((scope['btn_home'].x, scope['btn_home'].y,
                                      scope['btn_home'].w, scope['btn_home'].h),
                                     (0, 0, min(10, cols), 1))
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
                    self.assertEqual((scope['btn_home'].x, scope['btn_home'].y), (0, 0))
                    self.assertEqual(scope['btn_keyboard_toggle'].x, left)
                    self.assertEqual(scope['btn_keyboard_toggle'].y + scope['btn_keyboard_toggle'].h,
                                     form.h)

    def test_python_home_stops_foreground_app_and_starts_dt(self):
        project = json.loads((ROOT / 'projects/phone_shell.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'projects').mkdir()
            (root / 'DT').write_text('#!/bin/sh\n')
            scope = {'PROJECT_DIR': str(root / 'projects')}
            exec(project['code'], scope)
            process = SimpleNamespace(pid=4321, poll=lambda: None,
                                      wait=lambda timeout: 0)
            scope.update(shell_master=42, shell_process=process,
                         terminal=object(), keyboard_visible=True)
            events = []
            scope['cleanup_shell'] = lambda: events.append('cleanup')
            scope['on_form_load'] = lambda: events.append('restart')
            scope['layout'] = lambda: events.append('layout')
            scope['send_shell'] = lambda command: events.append(command)
            with patch.object(scope['os'], 'tcgetpgrp', return_value=5432), \
                    patch.object(scope['os'], 'getpgid', return_value=4321), \
                    patch.object(scope['os'], 'killpg', side_effect=lambda group, sig:
                                 events.append((group, sig))), \
                    patch.object(scope['time'], 'sleep'):
                scope['on_click_btn_home']()
            self.assertIn((5432, scope['signal'].SIGTERM), events)
            self.assertIn((4321, scope['signal'].SIGTERM), events)
            self.assertIn((5432, scope['signal'].SIGKILL), events)
            self.assertIn((4321, scope['signal'].SIGKILL), events)
            self.assertIn('cleanup', events)
            self.assertIn('restart', events)
            self.assertFalse(scope['keyboard_visible'])
            self.assertEqual(events[-1], 'cd -- ' + scope['shlex'].quote(str(root)) +
                             ' && ./DT\r')


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

    def test_native_phone_home_closes_app_and_launches_dt(self):
        project = Window.from_dict(json.loads(
            (ROOT / 'projects/phone_shell.json').read_text())).to_dict()
        source = export_cpp(project, self.folder / 'phone_home.cpp')
        app = self.folder / 'app.sh'
        app.write_text('#!/bin/sh\nprintf "%s" "$$" > app.pid\nexec sleep 30\n')
        app.chmod(0o755)
        desktop = self.folder / 'DT'
        desktop.write_text('#!/bin/sh\nprintf HOME_OK > home_marker\n')
        desktop.chmod(0o755)
        harness = self.folder / 'phone_home_harness.cpp'
        harness.write_text(
            '#define main exported_main\n'
            f'#include "{source}"\n'
            '#undef main\n'
            '#include <fstream>\n#include <thread>\n'
            'int main() {\n'
            '  std::setlocale(LC_ALL, "");\n'
            '  initscr(); cbreak(); noecho();\n'
            '  phone.start();\n'
            '  auto root = phone.desktop_root();\n'
            '  phone.pty.send("cd -- " + phone.shell_quote(root.string()) + " && ./app.sh\\r");\n'
            '  auto wait_file = [&](const char* name) {\n'
            '    for (int count = 0; count < 150; ++count) {\n'
            '      if (std::filesystem::exists(root / name)) return true;\n'
            '      std::this_thread::sleep_for(std::chrono::milliseconds(20));\n'
            '    }\n'
            '    return false;\n'
            '  };\n'
            '  bool app_started = wait_file("app.pid");\n'
            '  int app_pid = -1; if (app_started) std::ifstream(root / "app.pid") >> app_pid;\n'
            '  MEVENT tap{}; tap.x = 1; tap.y = 0; tap.bstate = BUTTON1_CLICKED;\n'
            '  phone.mouse(tap);\n'
            '  bool home_visible = phone.c("btn_home").x == 0 && phone.c("btn_home").y == 0 &&\n'
            '      phone.c("txt_shell").y == 1 && !phone.keyboard_visible;\n'
            '  bool launched = wait_file("home_marker");\n'
            '  bool app_stopped = app_pid > 0 && kill(app_pid, 0) == -1 && errno == ESRCH;\n'
            '  if (!app_stopped && app_pid > 0) {\n'
            '    std::ifstream status("/proc/" + std::to_string(app_pid) + "/stat");\n'
            '    int pid = 0; std::string command; char state = 0;\n'
            '    if (status >> pid >> command >> state) app_stopped = state == \'Z\';\n'
            '  }\n'
            '  phone.pty.stop(); endwin();\n'
            '  return !app_started ? 11 : !home_visible ? 12 : !launched ? 13 :\n'
            '      !app_stopped ? 14 : 0;\n'
            '}\n')
        binary = self.folder / 'phone_home_harness'
        subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                        str(harness), '-lncursesw', '-o', str(binary)],
                       check=True, capture_output=True, text=True)
        process, master = self.launch(binary)
        read_pty(master, 0.2)
        self.assertEqual(process.wait(timeout=8), 0)
        self.assertEqual((self.folder / 'home_marker').read_text(), 'HOME_OK')

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
            '  phone.terminal.feed(L"\\033]777;rad-tui;hide-");\n'
            '  phone.terminal.feed(L"keyboard\\007"); phone.handle_terminal_commands();\n'
            '  bool dismissed = !phone.keyboard_visible &&\n'
            '      phone.c("btn_keyboard_toggle").y + phone.c("btn_keyboard_toggle").h == form_h;\n'
            '  phone.keyboard_visible = true; phone.layout();\n'
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
            '      !wide_form ? 19 : !compact ? 20 : !dismissed ? 21 : !symbols ? 22 :\n'
            '      !symbol_input ? 23 : !restored ? 24 : !digits ? 25 : 0;\n'
            '}\n')
        binary = self.folder / 'ime_harness'
        subprocess.run(['g++', '-std=c++17', '-O2', str(harness), '-lncursesw',
                        '-o', str(binary)], check=True, capture_output=True, text=True)
        process, master = self.launch(binary)
        read_pty(master, 0.2)
        self.assertEqual(process.wait(timeout=2), 0)

    def test_dt_exports_and_navigates_with_native_callbacks(self):
        project = Window.from_dict(json.loads((ROOT / 'projects/DT/DT.json').read_text())).to_dict()
        source = export_cpp(project, self.folder / 'DT.cpp')
        desktop = self.folder / 'DTF'
        (desktop / 'games' / 'arcade').mkdir(parents=True)
        (desktop / 'tools').mkdir()
        program = desktop / 'play.bin'
        program.write_text('#!/bin/sh\nprintf launched > marker.txt\n')
        program.chmod(0o755)
        (desktop / 'play.icons').write_text('🎮\n')
        harness = self.folder / 'DT_harness.cpp'
        harness.write_text(
            '#define main exported_main\n'
            f'#include "{source}"\n'
            '#undef main\n'
            'int main() {\n'
            '  std::setlocale(LC_ALL, "");\n'
            '  initscr(); cbreak(); noecho();\n'
            '  dispatch("on_form_load");\n'
            '  bool items = dt.entries.size() == 3 && controls.size() == dt.fixed_controls + 3;\n'
            '  bool icon = false; int game = -1, play = -1;\n'
            '  for (std::size_t i = 0; i < dt.entries.size(); ++i) {\n'
            '    if (dt.entries[i].filename() == "games") game = static_cast<int>(i);\n'
            '    if (dt.entries[i].filename() == "play.bin") {\n'
            '      play = static_cast<int>(i);\n'
            '      icon = controls[dt.fixed_controls + i].caption == "🎮 play";\n'
            '    }\n'
            '  }\n'
            '  if (game >= 0) dispatch("on_click_dt_entry_" + std::to_string(game));\n'
            '  bool nested = dt.current.filename() == "games" && dt.entries.size() == 1;\n'
            '  dispatch("on_click_btn_back");\n'
            '  bool back = dt.current == dt.root && dt.entries.size() == 3;\n'
            '  if (play >= 0) dispatch("on_click_dt_entry_" + std::to_string(play));\n'
            '  bool launched = std::filesystem::exists(dt.root / "marker.txt");\n'
            '  endwin(); return !items ? 11 : !icon ? 12 : !nested ? 13 :\n'
            '      !back ? 14 : !launched ? 15 : 0;\n'
            '}\n')
        binary = self.folder / 'DT_harness'
        subprocess.run(['g++', '-std=c++17', '-O2', str(harness), '-lncursesw',
                        '-o', str(binary)], check=True, capture_output=True, text=True)
        process, master = self.launch(binary)
        output = read_pty(master, 0.2)
        self.assertIn(b'777;rad-tui;hide-keyboard', output)
        self.assertEqual(process.wait(timeout=2), 0)
        self.assertEqual((desktop / 'marker.txt').read_text(), 'launched')

    def test_calculator_exports_and_calculates_with_native_callbacks(self):
        for variant in ('examples', 'phoneapps'):
            with self.subTest(variant=variant):
                project = Window.from_dict(json.loads(
                    (ROOT / 'projects' / variant / 'calc.json').read_text())).to_dict()
                source = export_cpp(project, self.folder / (variant + '_calc.cpp'))
                harness = self.folder / (variant + '_calc_harness.cpp')
                harness.write_text(
                    '#define main exported_main\n'
                    f'#include "{source}"\n'
                    '#undef main\n'
                    'int main() {\n'
                    '  std::setlocale(LC_ALL, "");\n'
                    '  initscr(); cbreak(); noecho();\n'
                    '  dispatch("on_form_load");\n'
                    '  dispatch("on_click_btn_7"); dispatch("on_click_btn_add");\n'
                    '  dispatch("on_click_btn_8"); dispatch("on_click_btn_eq");\n'
                    '  bool sum = calculator.current_val == "15" && calculator.display().caption == "15";\n'
                    '  dispatch("on_click_btn_mul"); dispatch("on_click_btn_2");\n'
                    '  dispatch("on_click_btn_eq");\n'
                    '  bool product = calculator.current_val == "30";\n'
                    '  dispatch("on_click_btn_c"); dispatch("on_click_btn_dot");\n'
                    '  dispatch("on_click_btn_5"); dispatch("on_click_btn_add");\n'
                    '  dispatch("on_click_btn_1"); dispatch("on_click_btn_eq");\n'
                    '  bool decimal = calculator.current_val == "1.5";\n'
                    '  dispatch("on_click_btn_ce");\n'
                    '  bool cleared = calculator.current_val == "0" && calculator.new_input;\n'
                    '  endwin(); return !sum ? 11 : !product ? 12 : !decimal ? 13 :\n'
                    '      !cleared ? 14 : 0;\n'
                    '}\n')
                binary = self.folder / (variant + '_calc_harness')
                subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                                str(harness), '-lncursesw', '-o', str(binary)],
                               check=True, capture_output=True, text=True)
                process, master = self.launch(binary)
                read_pty(master, 0.2)
                self.assertEqual(process.wait(timeout=2), 0)

    def test_tic_tac_toe_exports_and_plays_with_native_ai(self):
        for variant in ('examples', 'phoneapps'):
            with self.subTest(variant=variant):
                project = Window.from_dict(json.loads(
                    (ROOT / 'projects' / variant / 'tic-tac-toe.json').read_text())).to_dict()
                source = export_cpp(project, self.folder / (variant + '_tic.cpp'))
                harness = self.folder / (variant + '_tic_harness.cpp')
                harness.write_text(
                    '#define main exported_main\n'
                    f'#include "{source}"\n'
                    '#undef main\n'
                    'int main() {\n'
                    '  std::setlocale(LC_ALL, "");\n'
                    '  initscr(); cbreak(); noecho();\n'
                    '  dispatch("on_form_load"); dispatch("on_click_btn4");\n'
                    '  bool opening = tic_tac_toe.board[4] == \'X\' &&\n'
                    '      std::count(tic_tac_toe.board.begin(), tic_tac_toe.board.end(), \'O\') == 1;\n'
                    '  tic_tac_toe.board = {\'O\', \'O\', \' \', \'X\', \'X\', \' \', \' \', \' \', \' \'};\n'
                    '  tic_tac_toe.game_over = false; tic_tac_toe.ai_move();\n'
                    '  bool win = tic_tac_toe.board[2] == \'O\' && tic_tac_toe.game_over &&\n'
                    '      tic_tac_toe.control("lbl_status").caption == "AI Wins!";\n'
                    '  dispatch("on_click_btn_reset");\n'
                    '  tic_tac_toe.board = {\'X\', \'X\', \' \', \' \', \'O\', \' \', \' \', \' \', \' \'};\n'
                    '  tic_tac_toe.ai_move(); bool block = tic_tac_toe.board[2] == \'O\';\n'
                    '  dispatch("on_click_btn_reset");\n'
                    '  tic_tac_toe.board = {\'X\', \'X\', \' \', \' \', \'O\', \' \', \' \', \' \', \' \'};\n'
                    '  dispatch("on_click_btn2");\n'
                    '  bool player = tic_tac_toe.board[2] == \'X\' && tic_tac_toe.game_over &&\n'
                    '      tic_tac_toe.control("lbl_status").caption == "You Win!";\n'
                    '  endwin(); return !opening ? 11 : !win ? 12 : !block ? 13 : !player ? 14 : 0;\n'
                    '}\n')
                binary = self.folder / (variant + '_tic_harness')
                subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                                str(harness), '-lncursesw', '-o', str(binary)],
                               check=True, capture_output=True, text=True)
                process, master = self.launch(binary)
                read_pty(master, 0.2)
                self.assertEqual(process.wait(timeout=2), 0)

    def test_minesweeper_exports_and_handles_reveal_flag_bomb_and_timer(self):
        for variant in ('examples', 'phoneapps'):
            with self.subTest(variant=variant):
                project = Window.from_dict(json.loads(
                    (ROOT / 'projects' / variant / 'ms.json').read_text())).to_dict()
                source = export_cpp(project, self.folder / (variant + '_ms.cpp'))
                harness = self.folder / (variant + '_ms_harness.cpp')
                harness.write_text(
                    '#define main exported_main\n'
                    f'#include "{source}"\n'
                    '#undef main\n'
                    'int main() {\n'
                    '  std::setlocale(LC_ALL, "");\n'
                    '  initscr(); cbreak(); noecho();\n'
                    '  dispatch("on_form_load");\n'
                    '  int bombs = 0; for (auto& row : minesweeper.bombs)\n'
                    '      for (bool cell : row) bombs += cell;\n'
                    '  dispatch("on_tick_timer1");\n'
                    '  bool timer = minesweeper.control("time_txt").caption == "1";\n'
                    '  for (auto& row : minesweeper.bombs) row.fill(false);\n'
                    '  minesweeper.bombs[0][0] = true;\n'
                    '  dispatch("on_right_click_b1_1");\n'
                    '  bool flag = minesweeper.cell(1, 1).caption == "F";\n'
                    '  dispatch("on_right_click_b1_1");\n'
                    '  dispatch("button_down_b9_9");\n'
                    '  bool pressed = minesweeper.control("face_txt").caption == "(.O.)";\n'
                    '  dispatch("on_button_up_b9_9");\n'
                    '  bool revealed = minesweeper.cell(9, 9).caption == "-" &&\n'
                    '      minesweeper.cell(0, 1).caption == "1";\n'
                    '  ungetch(\'x\'); dispatch("on_click_b0_0");\n'
                    '  bool lost = minesweeper.game_over && minesweeper.cell(0, 0).caption == "*" &&\n'
                    '      minesweeper.cell(0, 0).bg_color == 15;\n'
                    '  dispatch("on_tick_timer1"); bool stopped = !running;\n'
                    '  endwin(); return bombs != 10 ? 11 : !timer ? 12 : !flag ? 13 :\n'
                    '      !pressed ? 14 : !revealed ? 15 : !lost ? 16 : !stopped ? 17 : 0;\n'
                    '}\n')
                binary = self.folder / (variant + '_ms_harness')
                subprocess.run(['g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
                                str(harness), '-lncursesw', '-o', str(binary)],
                               check=True, capture_output=True, text=True)
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
