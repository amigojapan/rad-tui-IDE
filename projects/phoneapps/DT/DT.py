"""Callbacks embedded in DT.json by the project generator."""

import curses
import os
from pathlib import Path
import subprocess


ROOT = Path(PROJECT_DIR).resolve() / 'DTF'
current_dir = ROOT
entry_controls = []
entries = []
page = 0
last_layout_size = None


def icon_for(path, default='⚡'):
    for icon_file in (path.with_suffix('.icons'), Path(str(path) + '.icons')):
        try:
            icon = icon_file.read_text(encoding='utf-8').strip().split()
        except (OSError, UnicodeError):
            continue
        if icon:
            return icon[0]
    return default


def layout():
    global page, last_layout_size
    toolbar_rows = 0 if getattr(__import__('sys'), '_is_standalone_run', False) else 1
    Form1.x, Form1.y = 0, toolbar_rows
    Form1.w = max(3, curses.COLS)
    Form1.h = max(3, curses.LINES - toolbar_rows)
    width, height = Form1.w, Form1.h

    nav_width = min(11, max(6, width // 4))
    btn_back.x, btn_back.y, btn_back.w, btn_back.h = 0, 0, nav_width, 1
    btn_refresh.x, btn_refresh.y, btn_refresh.w, btn_refresh.h = nav_width, 0, nav_width, 1
    lbl_path.x, lbl_path.y = min(width - 1, 2 * nav_width + 1), 0
    lbl_path.w, lbl_path.h = max(1, width - lbl_path.x), 1
    relative = current_dir.relative_to(ROOT)
    lbl_path.caption = 'DTF' if relative == Path('.') else 'DTF/' + str(relative)

    row_height = 3 if height >= 18 else 1
    columns = max(1, min(4, width // 20))
    grid_width = min(width, columns * 20)
    grid_left = (width - grid_width) // 2
    tile_width = grid_width // columns
    rows = max(1, (height - 3) // row_height)
    page_size = columns * rows
    last_page = max(0, (len(entry_controls) - 1) // page_size)
    page = min(page, last_page)

    for button in entry_controls:
        button.x = -50
    for slot, button in enumerate(entry_controls[page * page_size:(page + 1) * page_size]):
        row, col = divmod(slot, columns)
        button.x = grid_left + col * tile_width
        button.y = 2 + row * row_height
        button.w = tile_width
        button.h = row_height

    footer_y = height - 1
    btn_prev.x, btn_prev.y, btn_prev.w, btn_prev.h = (0 if page > 0 else -50), footer_y, nav_width, 1
    btn_next.x, btn_next.y, btn_next.w, btn_next.h = (
        width - nav_width if page < last_page else -50), footer_y, nav_width, 1
    lbl_page.x, lbl_page.y, lbl_page.w, lbl_page.h = nav_width, footer_y, max(1, width - 2 * nav_width), 1
    lbl_page.caption = f'{len(entry_controls)} items  •  page {page + 1}/{last_page + 1}'
    last_layout_size = (curses.COLS, curses.LINES)


def scan_entries():
    global entry_controls, entries, page
    for button in entry_controls:
        Form1.controls.remove(button)
        globals().pop(button.name_id, None)
        globals().pop('on_click_' + button.name_id, None)
    entry_controls = []
    try:
        children = list(current_dir.iterdir())
        folders = sorted((path for path in children if path.is_dir() and not path.is_symlink()),
                         key=lambda path: path.name.casefold())
        programs = sorted((path for path in children if path.is_file() and path.suffix.lower() == '.bin'),
                          key=lambda path: path.name.casefold())
        entries = folders + programs
    except OSError as exc:
        entries = []
        msgbox('Cannot open folder: ' + str(exc))

    button_type = type(btn_back)
    for index, path in enumerate(entries):
        caption = (icon_for(path, '📁') + ' ' + path.name if path.is_dir()
                   else icon_for(path) + ' ' + path.stem)
        name = f'dt_entry_{index}'
        button = button_type(-50, 0, 1, 1, 3, name, caption)
        Form1.controls.append(button)
        globals()[name] = button
        globals()['on_click_' + name] = lambda item=path: open_entry(item)
        entry_controls.append(button)
    layout()


def open_entry(path):
    global current_dir, page
    if path.is_dir() and not path.is_symlink():
        current_dir = path
        page = 0
        scan_entries()
    elif path.is_file() and path.suffix.lower() == '.bin':
        launch_binary(path)


def launch_binary(path):
    suspended = False
    try:
        curses.def_prog_mode()
        curses.endwin()
        suspended = True
        result = subprocess.run([str(path)], cwd=str(path.parent), check=False)
        if result.returncode:
            msgbox(f'{path.name} exited with code {result.returncode}')
    except OSError as exc:
        msgbox(f'Cannot run {path.name}: {exc}')
    finally:
        if suspended:
            curses.reset_prog_mode()
            curses.curs_set(0)
        scan_entries()


def on_form_load():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / 'tools').mkdir(exist_ok=True)
    (ROOT / 'games').mkdir(exist_ok=True)
    if os.isatty(1):
        os.write(1, b'\x1b]777;rad-tui;hide-keyboard\x07')
    scan_entries()


def on_form_resize():
    layout()


def on_tick_dt_timer():
    try:
        size = os.get_terminal_size(0)
        if (size.columns, size.lines) != (curses.COLS, curses.LINES):
            curses.resizeterm(size.lines, size.columns)
    except OSError:
        pass
    if last_layout_size != (curses.COLS, curses.LINES):
        layout()


def on_click_btn_back():
    global current_dir, page
    if current_dir != ROOT:
        current_dir = current_dir.parent
        page = 0
        scan_entries()


def on_click_btn_refresh():
    scan_entries()


def on_click_btn_prev():
    global page
    if page:
        page -= 1
        layout()


def on_click_btn_next():
    global page
    page += 1
    layout()
