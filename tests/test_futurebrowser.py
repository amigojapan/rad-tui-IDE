"""The Future Browser project checks URLs before handing off to the runner."""

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'rad_tui_basic_pkg' / 'src'))


class FutureBrowserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        (self.folder / 'run-downloaded-bin.sh').write_text('#!/bin/sh\n')
        project = json.loads((ROOT / 'projects/phoneapps/futurebrowser.json').read_text())
        self.assertEqual(project['code'],
                         (ROOT / 'projects/phoneapps/futurebrowser.py').read_text())
        controls = {item['name_id']: item for item in project['controls']}
        self.default_url = 'https://amjp.psy-k.org/futureshell/repo/amd64/tic-tac-toe.amd64.bin'
        self.assertEqual(controls['txt_url']['caption'], self.default_url)
        self.assertEqual(controls['btn_go']['caption'], 'GO!')
        self.messages = []
        self.events = []
        self.scope = {
            'PROJECT_DIR': str(self.folder),
            'Form1': SimpleNamespace(),
            'lbl_url': SimpleNamespace(),
            'txt_url': SimpleNamespace(caption=self.default_url),
            'btn_go': SimpleNamespace(),
            'msgbox': self.messages.append,
        }
        exec(project['code'], self.scope)
        self.scope['curses'] = SimpleNamespace(
            COLS=33, LINES=24,
            def_prog_mode=lambda: self.events.append('save'),
            endwin=lambda: self.events.append('end'),
            reset_prog_mode=lambda: self.events.append('restore'),
            curs_set=lambda _: None)

    def test_missing_url_shows_404_and_does_not_run(self):
        self.scope['txt_url'].caption = 'https://example.test/missing.bin'
        missing = SimpleNamespace(returncode=8, stderr='  HTTP/1.1 404 Not Found\n')
        with patch.object(self.scope['subprocess'], 'run', return_value=missing) as run:
            self.scope['on_enter_txt_url']()
        self.assertEqual(self.messages, ['404 not found'])
        self.assertEqual(run.call_count, 1)
        self.assertEqual(self.events, [])

    def test_existing_url_runs_runner_with_visible_terminal(self):
        url = 'https://example.test/game.bin?token=123'
        self.scope['txt_url'].caption = url
        with patch.object(self.scope['subprocess'], 'run', side_effect=[
                SimpleNamespace(returncode=0, stderr='  HTTP/1.1 200 OK\n'),
                SimpleNamespace(returncode=0)]) as run:
            self.scope['on_enter_txt_url']()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0],
                         [str(self.folder / 'run-downloaded-bin.sh'), url])
        self.assertEqual(run.call_args.kwargs['cwd'], str(self.folder))
        self.assertEqual(self.events, ['save', 'end', 'restore'])
        self.assertEqual(self.messages, [])

    def test_runner_is_found_from_nested_internet_directory(self):
        internet = self.folder / 'DT' / 'DTF' / 'internet'
        internet.mkdir(parents=True)
        self.scope['PROJECT_DIR'] = str(internet)
        self.scope['txt_url'].caption = 'https://example.test/app.bin'
        with patch.object(self.scope['subprocess'], 'run', side_effect=[
                SimpleNamespace(returncode=0, stderr=''),
                SimpleNamespace(returncode=0)]) as run:
            self.scope['on_enter_txt_url']()
        self.assertEqual(run.call_args.args[0][0],
                         str(self.folder / 'run-downloaded-bin.sh'))
        self.assertEqual(self.messages, [])

    def test_go_button_loads_default_url(self):
        with patch.object(self.scope['subprocess'], 'run', side_effect=[
                SimpleNamespace(returncode=0, stderr=''),
                SimpleNamespace(returncode=0)]) as run:
            self.scope['on_click_btn_go']()
        self.assertEqual(run.call_args.args[0][1], self.default_url)
        self.assertEqual(self.messages, [])


if __name__ == '__main__':
    unittest.main()
