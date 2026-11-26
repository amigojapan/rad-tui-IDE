"""Callbacks embedded in futurebrowser.json."""

import curses
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit


def layout():
    Form1.x = Form1.y = 0
    Form1.w = max(3, curses.COLS)
    Form1.h = max(3, curses.LINES)
    lbl_url.x, lbl_url.y = 2, 1
    lbl_url.w, lbl_url.h = max(1, Form1.w - 4), 1
    txt_url.x, txt_url.y = 2, 3
    txt_url.w, txt_url.h = max(1, Form1.w - 4), 1
    btn_go.w, btn_go.h = min(7, Form1.w), 3
    btn_go.x, btn_go.y = max(0, (Form1.w - btn_go.w) // 2), 5


def on_form_load():
    layout()


def on_form_resize():
    layout()


def on_enter_txt_url():
    url = txt_url.caption.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or not parsed.path.endswith('.bin'):
        msgbox('Enter an HTTP(S) URL ending in .bin')
        return

    try:
        response = subprocess.run(
            ['wget', '--spider', '--server-response', '--timeout=10',
             '--tries=1', '--', url], capture_output=True, text=True, check=False)
    except OSError as exc:
        msgbox('Cannot check URL: ' + str(exc))
        return
    if response.returncode:
        if re.search(r'HTTP/\S+\s+404\b', response.stderr):
            msgbox('404 not found')
        else:
            msgbox('Cannot access URL')
        return

    project_dir = Path(PROJECT_DIR).resolve()
    runner = next((folder / 'run-downloaded-bin.sh'
                   for folder in (project_dir, *project_dir.parents)
                   if (folder / 'run-downloaded-bin.sh').is_file()), None)
    if runner is None:
        msgbox('Download runner not found')
        return

    suspended = False
    error = None
    result = None
    try:
        curses.def_prog_mode()
        curses.endwin()
        suspended = True
        result = subprocess.run([str(runner), url], cwd=str(runner.parent), check=False)
    except OSError as exc:
        error = str(exc)
    finally:
        if suspended:
            curses.reset_prog_mode()
            curses.curs_set(0)
    if error is not None:
        msgbox('Cannot run download: ' + error)
        return
    if result.returncode:
        msgbox('Download or app exited with code ' + str(result.returncode))


def on_form_enter():
    on_enter_txt_url()


def on_click_btn_go():
    on_enter_txt_url()
