#!/usr/bin/env python3
"""Refresh the self-contained distribution without changing the repository layout."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


DIST = Path(__file__).resolve().parent
REPO = DIST.parent
PHONEAPPS = REPO / "projects" / "phoneapps"
SOURCE = DIST / "source" / "phoneapps"
PORTS = ("native-python", "amd64", "arm64", "riscv64", "webasm")
APPS = {
    "phone_shell.bin": "phone_shell.json",
    "DT/DT.bin": "DT/DT.json",
    "DT/DTF/games/minesweeper.bin": "ms.json",
    "DT/DTF/games/tic-tac-toe.bin": "tic-tac-toe.json",
    "DT/DTF/internet/futurebrowser.bin": "futurebrowser.json",
    "DT/DTF/tools/bash.bin": "bash.json",
    "DT/DTF/tools/calc.bin": "calc.json",
    "DT/DTF/tools/nano.bin": "nano.json",
}


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def replace_once(content: str, before: str, after: str, context: str) -> str:
    if content.count(before) != 1:
        raise RuntimeError(f"Cannot update {context}; expected one matching section")
    return content.replace(before, after)


def terminal_project(name: str) -> dict:
    return {
        "x": 0, "y": 0, "w": 80, "h": 24,
        "title": name.capitalize(), "name_id": "Form1",
        "display_border_and_caption": False,
        "pinned_topmost": False, "resizable": False, "hidden": False,
        "menus": [], "controls": [],
        "code": (
            "def on_form_load():\n"
            "    import curses\n"
            "    import os\n"
            "    curses.endwin()\n"
            f"    os.execvp({name!r}, [{name!r}])\n"
        ),
    }


def copy_sources() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    for src in PHONEAPPS.rglob("*"):
        if not src.is_file() or src.is_symlink():
            continue
        relative = src.relative_to(PHONEAPPS)
        if any(part in ("__pycache__", ".git") for part in relative.parts):
            continue
        if src.suffix in (".json", ".cpp", ".py", ".c", ".h", ".bash", ".sh", ".txt", ".icons", ".md", ".html", ".js", ".css", ".svg", ".webmanifest"):
            copy_file(src, SOURCE / relative)

    for name in ("bash", "nano"):
        (SOURCE / f"{name}.json").write_text(
            json.dumps(terminal_project(name), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    # Desktop folder icons are one code point each. Both are two terminal
    # cells wide, without a variation selector that could upset button width.
    for folder, icon in (("games", "🎮"), ("tools", "🔨")):
        icon_file = SOURCE / "DT" / "DTF" / f"{folder}.icons"
        icon_file.parent.mkdir(parents=True, exist_ok=True)
        icon_file.write_text(icon + "\n", encoding="utf-8")

    mine_path = SOURCE / "ms.json"
    mine_form = json.loads(mine_path.read_text(encoding="utf-8"))
    mine_form["y"] = 0
    mine_form["h"] = 26
    mine_form["controls"].append({
        "x": 0, "y": 0, "w": 15, "h": 3, "tool_type": 3,
        "name_id": "btn_restart", "caption": "Restart Game", "code": "",
        "bg_color": 12,
    })
    for control in mine_form["controls"]:
        if control["name_id"] == "face_txt":
            control["x"], control["w"] = 16, 9
        elif control["name_id"] == "time_txt":
            control["x"], control["w"] = 27, 8
    mine_form["code"] = '''def layout():
    import curses
    cols, lines = curses.COLS, curses.LINES
    Form1.x = 0
    Form1.y = 1 if lines >= 25 else 0
    Form1.w = min(35, max(1, cols))
    Form1.h = min(26, max(1, lines - Form1.y))
    roomy = lines - Form1.y >= 24
    middle = lines - Form1.y >= 22
    compact = lines - Form1.y >= 21
    face_txt.x, face_txt.y = min(16, max(0, Form1.w - 19)), (1 if roomy else 0)
    face_txt.w = min(9, max(1, Form1.w - face_txt.x))
    time_txt.x, time_txt.y = max(0, Form1.w - 8), (1 if roomy else 0)
    time_txt.w = min(8, Form1.w)
    btn_restart.x, btn_restart.y = 0, 0
    btn_restart.w = min(15, Form1.w)
    btn_restart.h = min(3, Form1.h) if roomy else 1
    cell_w = 4 if Form1.w >= 35 else max(1, min(3, (Form1.w - 2) // 10))
    for row in range(10):
        for col in range(10):
            button = globals()[f'b{row}_{col}']
            button.x = 2 + col * (3 if Form1.w >= 35 else cell_w)
            button.y = (3 + row * 2 if roomy else
                        1 + row * 2 if compact else 1 + row)
            button.w = cell_w
            button.h = 3 if roomy or middle else (2 if compact else 1)

def reset_game():
    import random
    import time
    bombs = set()
    while len(bombs) < 10:
        bombs.add((random.randint(0, 9), random.randint(0, 9)))
    globals()['bombs'] = bombs
    globals()['game_over'] = False
    face_txt.caption = '(^_^)'
    time_txt.caption = '0'
    timer1.last_tick = time.time() * 1000
    for row in range(10):
        for col in range(10):
            button = globals()[f'b{row}_{col}']
            button.caption = ''
            button.bg_color = 12
    layout()

def on_form_load():
    import os
    os.write(1, b'\\x1b]777;rad-tui;game-fullheight\\x07')
    reset_game()

def on_form_resize():
    layout()

def on_click_btn_restart():
    reset_game()
'''
    for control in mine_form["controls"]:
        if control["name_id"] == "timer1":
            control["code"] = replace_once(
                control["code"],
                "    if globals().get('game_over'):\n"
                "        if not globals().get('__msg__'):\n"
                "            import sys\n"
                "            sys.exit(0)\n"
                "        return",
                "    if globals().get('game_over'): return",
                "Minesweeper game-over timer",
            )
    mine_path.write_text(json.dumps(mine_form, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # These two forms also have fixed control rows taller than a short phone
    # viewport. Keep the original layout when it fits; compact it otherwise.
    tic_path = SOURCE / "tic-tac-toe.json"
    tic_form = json.loads(tic_path.read_text(encoding="utf-8"))
    tic_form["code"] += '''
_original_on_form_load = on_form_load
def fit_screen():
    import curses
    if '_original_geometry' not in globals():
        globals()['_original_geometry'] = {
            name: (globals()[name].x, globals()[name].y,
                   globals()[name].w, globals()[name].h)
            for name in [f'btn{i}' for i in range(9)] + ['lbl_status', 'btn_reset']}
    Form1.x = 0
    Form1.y = 1 if curses.LINES >= 20 else 0
    Form1.w = min(39, max(1, curses.COLS))
    Form1.h = min(22, max(1, curses.LINES - Form1.y))
    if curses.LINES >= 20:
        for name, geometry in _original_geometry.items():
            control = globals()[name]
            control.x, control.y, control.w, control.h = geometry
        return
    lbl_status.x, lbl_status.y = 1, 0
    lbl_status.w = max(1, Form1.w - 2)
    cell_w = max(3, min(7, (Form1.w - 4) // 3))
    left = max(0, (Form1.w - (3 * cell_w + 2)) // 2)
    step = 3 if curses.LINES >= 14 else 2
    for index in range(9):
        button = globals()[f'btn{index}']
        row, col = divmod(index, 3)
        button.x, button.y = left + col * (cell_w + 1), 2 + row * step
        button.w, button.h = cell_w, min(3, max(1, Form1.h - button.y))
    btn_reset.w = min(15, Form1.w)
    btn_reset.x = max(0, (Form1.w - btn_reset.w) // 2)
    btn_reset.y = 11 if step == 3 else 8
    btn_reset.h = max(1, min(3, Form1.h - btn_reset.y))

def on_form_load():
    _original_on_form_load()
    fit_screen()

def on_form_resize():
    fit_screen()
'''
    tic_path.write_text(json.dumps(tic_form, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    calc_path = SOURCE / "calc.json"
    calc_form = json.loads(calc_path.read_text(encoding="utf-8"))
    calc_form["code"] += '''
_original_on_form_load = on_form_load
def fit_screen():
    import curses
    if '_original_geometry' not in globals():
        globals()['_original_geometry'] = {
            control.name_id: (control.x, control.y, control.w, control.h)
            for control in Form1.controls if control.name_id}
    Form1.x = 0
    Form1.y = 1 if curses.LINES >= 24 else 0
    Form1.w = min(25, max(1, curses.COLS))
    Form1.h = min(25, max(1, curses.LINES - Form1.y))
    if curses.LINES >= 24:
        for name, geometry in _original_geometry.items():
            control = globals()[name]
            control.x, control.y, control.w, control.h = geometry
        return
    display.y = 0
    step = 3 if curses.LINES >= 17 else 2
    top = 2
    rows = (('btn_c', 'btn_ce', 'btn_div', 'btn_mul'),
            ('btn_7', 'btn_8', 'btn_9', 'btn_sub'),
            ('btn_4', 'btn_5', 'btn_6', 'btn_add'),
            ('btn_1', 'btn_2', 'btn_3', 'btn_eq'),
            ('btn_0', 'btn_dot'))
    for row, names in enumerate(rows):
        for name in names:
            button = globals()[name]
            button.y = top + row * step
            button.h = min(3, max(1, Form1.h - button.y))
    btn_eq.h = min(Form1.h - btn_eq.y, step + 3)

def on_form_load():
    _original_on_form_load()
    fit_screen()

def on_form_resize():
    fit_screen()
'''
    calc_path.write_text(json.dumps(calc_form, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    browser_forms = SOURCE / "htmldemo" / "forms.json"
    forms = json.loads(browser_forms.read_text(encoding="utf-8"))
    forms["minesweeper"]["h"] = mine_form["h"]
    forms["minesweeper"]["y"] = mine_form["y"]
    forms["minesweeper"]["controls"] = [
        {key: control[key] for key in ("x", "y", "w", "h", "tool_type", "name_id", "caption", "bg_color")
         if key in control}
        for control in mine_form["controls"]
    ]
    browser_forms.write_text(json.dumps(forms, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    browser_catalog = SOURCE / "htmldemo" / "catalog.json"
    catalog = json.loads(browser_catalog.read_text(encoding="utf-8"))
    for entry in catalog[""]:
        if entry["name"] in ("games", "tools"):
            entry["icon"] = "🎮" if entry["name"] == "games" else "🔨"
    browser_catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # In this distribution the phone shell hosts DT immediately. Home kills
    # the current terminal app and on_form_load starts DT again. This avoids
    # racing an interactive Bash prompt when sending the old Home command.
    shell_project = SOURCE / "phone_shell.json"
    shell_form = json.loads(shell_project.read_text(encoding="utf-8"))
    shell_code = shell_form["code"]
    shell_code = replace_once(
        shell_code,
        "    shell = env.get('SHELL', '/bin/bash')\n"
        "    if not os.path.isfile(shell): shell = '/bin/sh'\n"
        "    args = [shell, '-i']\n"
        "    if os.path.basename(shell) == 'bash': args = [shell, '--noprofile', '--norc', '-i']",
        "    args = [os.path.join(os.path.abspath(PROJECT_DIR), 'DT', 'DT.bin')]",
        "phone shell startup",
    )
    shell_code = replace_once(
        shell_code,
        "    layout()\n    send_shell('./DT/DT.bin\\r')\n",
        "    layout()\n",
        "phone shell Home",
    )
    shell_code = replace_once(
        shell_code,
        "    env.update(TERM='xterm-256color', PS1='$ ', PROMPT_COMMAND='',\n"
        "               COLUMNS=str(shell_w), LINES=str(txt_shell.h), NCURSES_NO_UTF8_ACS='1')",
        "    env.pop('COLUMNS', None)\n"
        "    env.pop('LINES', None)\n"
        "    env.update(TERM='xterm-256color', PS1='$ ', PROMPT_COMMAND='',\n"
        "               NCURSES_NO_UTF8_ACS='1')",
        "phone shell child terminal size",
    )
    shell_code = replace_once(
        shell_code,
        "    color_pairs = {}\n    decoder =",
        "    color_pairs = {}\n    globals()['game_fullheight'] = False\n    decoder =",
        "phone shell game height initialization",
    )
    shell_code = replace_once(
        shell_code,
        "        shell_h = max(1, toggle_y - txt_shell.y - 1 - candidate_h * candidates_visible)",
        "        shell_h = max(1, toggle_y - txt_shell.y - (0 if game_fullheight else 1)\n"
        "                      - candidate_h * candidates_visible)",
        "phone shell full-height game area",
    )
    shell_code = replace_once(
        shell_code,
        "    txt_command.y = txt_shell.y + shell_h",
        "    txt_command.y = txt_shell.y + shell_h\n"
        "    if game_fullheight and not keyboard_visible:\n"
        "        txt_command.x = -50",
        "phone shell hidden game command row",
    )
    shell_code = replace_once(
        shell_code,
        "def handle_terminal_commands():\n"
        "    global keyboard_visible\n"
        "    if '777;rad-tui;hide-keyboard' in terminal.osc_messages and keyboard_visible:\n"
        "        keyboard_visible = False\n"
        "        layout()\n"
        "    terminal.osc_messages.clear()",
        "def handle_terminal_commands():\n"
        "    global keyboard_visible, game_fullheight\n"
        "    messages = set(terminal.osc_messages)\n"
        "    if '777;rad-tui;game-fullheight' in messages:\n"
        "        game_fullheight = True\n"
        "        keyboard_visible = False\n"
        "        layout()\n"
        "    elif '777;rad-tui;hide-keyboard' in messages:\n"
        "        if keyboard_visible or game_fullheight:\n"
        "            game_fullheight = False\n"
        "            keyboard_visible = False\n"
        "            layout()\n"
        "    terminal.osc_messages.clear()",
        "phone shell game height request",
    )
    shell_form["code"] = shell_code
    shell_project.write_text(
        json.dumps(shell_form, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # The optional native amd64 ELF is runnable from artifacts/ as well. Give
    # it the same DT startup and Home behavior as the JSON/Python launcher.
    native_shell = SOURCE / "phone_shell.cpp"
    native_code = native_shell.read_text(encoding="utf-8")
    native_code = replace_once(
        native_code,
        '            const char* shell = getenv("SHELL");\n'
        '            if (!shell || access(shell, X_OK) != 0) shell = "/bin/sh";\n'
        '            std::string path(shell);\n'
        '            if (path.size() >= 4 && path.substr(path.size() - 4) == "bash")\n'
        '                execl(shell, shell, "--noprofile", "--norc", "-i", static_cast<char*>(nullptr));\n'
        '            else execl(shell, shell, "-i", static_cast<char*>(nullptr));',
        '            execl("./DT/DT.bin", "./DT/DT.bin", static_cast<char*>(nullptr));',
        "native phone shell startup",
    )
    native_code = replace_once(
        native_code,
        '        return size > 0\n'
        '            ? std::filesystem::path(std::string(executable, static_cast<std::size_t>(size))).parent_path()\n'
        '            : std::filesystem::current_path();',
        '        auto directory = size > 0\n'
        '            ? std::filesystem::path(std::string(executable, static_cast<std::size_t>(size))).parent_path()\n'
        '            : std::filesystem::current_path();\n'
        '        return directory.filename() == "artifacts" ? directory.parent_path() : directory;',
        "native phone shell port directory",
    )
    native_code = replace_once(
        native_code,
        '        if (!started) terminal.feed(L"[Shell could not start]\\n");\n'
        '        else pty.send("./DT/DT.bin\\r");',
        '        if (!started) terminal.feed(L"[DT could not start]\\n");',
        "native phone shell Home",
    )
    native_code = replace_once(
        native_code,
        '    int mouse_down = 0;',
        '    int mouse_down = 0;\n    bool home_mouse_pressed = false;',
        "native Home mouse state",
    )
    native_code = replace_once(
        native_code,
        '            setenv("COLUMNS", std::to_string(cols).c_str(), 1);\n'
        '            setenv("LINES", std::to_string(rows).c_str(), 1);',
        '            unsetenv("COLUMNS");\n'
        '            unsetenv("LINES");',
        "native child terminal size",
    )
    native_code = replace_once(
        native_code,
        '        const std::string& name = control_names[index];\n'
        '        if (name == "txt_shell"',
        '        const std::string& name = control_names[index];\n'
        '        if (name == "btn_home") {\n'
        '            if (event.bstate & BUTTON1_PRESSED) {\n'
        '                home_mouse_pressed = true;\n'
        '                home();\n'
        '            } else if (event.bstate & (BUTTON1_CLICKED | BUTTON1_RELEASED)) {\n'
        '                if (!home_mouse_pressed) home();\n'
        '                home_mouse_pressed = false;\n'
        '            }\n'
        '            return true;\n'
        '        }\n'
        '        if (name == "txt_shell"',
        "native Home mouse dispatch",
    )
    native_code = replace_once(
        native_code,
        "    bool started = false, shell_exit_reported = false, keyboard_visible = true;",
        "    bool started = false, shell_exit_reported = false, keyboard_visible = true;\n"
        "    bool game_fullheight = false;",
        "native phone shell game height state",
    )
    native_code = replace_once(
        native_code,
        "            shell_h = std::max(1, toggle_y - shell.y - 1 - candidate_h * candidates);",
        "            shell_h = std::max(1, toggle_y - shell.y - (game_fullheight ? 0 : 1)\n"
        "                               - candidate_h * candidates);",
        "native phone shell full-height game area",
    )
    native_code = replace_once(
        native_code,
        "        input.y = shell.y + shell_h;",
        "        input.y = shell.y + shell_h;\n"
        "        if (game_fullheight && !keyboard_visible) input.x = -50;",
        "native phone shell hidden game command row",
    )
    native_code = replace_once(
        native_code,
        "    void handle_terminal_commands() {\n"
        "        for (const auto& command : terminal.osc_messages)\n"
        "            if (command == \"777;rad-tui;hide-keyboard\" && keyboard_visible) {\n"
        "                keyboard_visible = false;\n"
        "                layout();\n"
        "            }\n"
        "        terminal.osc_messages.clear();\n"
        "    }",
        "    void handle_terminal_commands() {\n"
        "        const auto& messages = terminal.osc_messages;\n"
        "        if (std::find(messages.begin(), messages.end(),\n"
        "                      \"777;rad-tui;game-fullheight\") != messages.end()) {\n"
        "            game_fullheight = true;\n"
        "            keyboard_visible = false;\n"
        "            layout();\n"
        "        } else if (std::find(messages.begin(), messages.end(),\n"
        "                             \"777;rad-tui;hide-keyboard\") != messages.end() &&\n"
        "                   (keyboard_visible || game_fullheight)) {\n"
        "            game_fullheight = false;\n"
        "            keyboard_visible = false;\n"
        "            layout();\n"
        "        }\n"
        "        terminal.osc_messages.clear();\n"
        "    }",
        "native phone shell game height request",
    )
    native_code = replace_once(
        native_code,
        "        keyboard_visible = false;\n"
        "        candidate_options.clear(); candidate_index = 0;",
        "        keyboard_visible = false;\n"
        "        game_fullheight = false;\n"
        "        candidate_options.clear(); candidate_index = 0;",
        "native phone shell Home resets game height",
    )
    native_shell.write_text(native_code, encoding="utf-8")

    native_mine = SOURCE / "ms.cpp"
    mine_code = native_mine.read_text(encoding="utf-8")
    mine_code = replace_once(
        mine_code,
        "        game_over = false;\n    }\n\n    int adjacent",
        "        game_over = false;\n"
        "        control(\"face_txt\").caption = \"(^_^)\";\n"
        "        control(\"time_txt\").caption = \"0\";\n"
        "        for (int row = 0; row < 10; ++row)\n"
        "            for (int col = 0; col < 10; ++col) {\n"
        "                auto& button = cell(row, col);\n"
        "                button.caption.clear();\n"
        "                button.bg_color = 12;\n"
        "            }\n"
        "    }\n\n    int adjacent",
        "native Minesweeper reset",
    )
    mine_code = replace_once(
        mine_code,
        "        if (game_over) { running = false; return; }",
        "        if (game_over) return;",
        "native Minesweeper game over",
    )
    mine_code = replace_once(
        mine_code,
        "        if (button_h < 3 || w < 3) {",
        '''        if (button_h == 2 && w >= 3) {
            glyph(y, x, L'┌', 3, true, A_BOLD);
            for (int col = 1; col < w - 1; ++col)
                glyph(y, x + col, L'─', 3, true, A_BOLD);
            glyph(y, x + w - 1, L'┐', 2, true);
            glyph(y + 1, x, L'│', 3, true, A_BOLD);
            fill(y + 1, x + 1, w - 2, face, A_UNDERLINE);
            const int pad = std::max(0, (w - 2 - cells(c.caption)) / 2);
            text(y + 1, x + 1 + pad, std::max(0, w - 2 - pad),
                 c.caption, face, true, A_UNDERLINE);
            glyph(y + 1, x + w - 1, L'│', 2, true);
            return;
        }
        if (button_h < 3 || w < 3) {''',
        "native two-row Minesweeper buttons",
    )
    mine_code = replace_once(
        mine_code,
        "static void native_start_hook() {}\nstatic void native_tick_hook() {}",
        '''static void fit_minesweeper() {
    form_x = 0; form_y = LINES >= 25 ? 1 : 0;
    form_w = std::min(35, std::max(1, COLS));
    form_h = std::min(26, std::max(1, LINES - form_y));
    auto& face = minesweeper.control("face_txt");
    const bool roomy = LINES - form_y >= 24;
    const bool middle = LINES - form_y >= 22;
    const bool compact = LINES - form_y >= 21;
    face.x = std::min(16, std::max(0, form_w - 19));
    face.y = roomy ? 1 : 0;
    face.w = std::min(9, std::max(1, form_w - face.x));
    auto& timer = minesweeper.control("time_txt");
    timer.x = std::max(0, form_w - 8); timer.y = roomy ? 1 : 0;
    timer.w = std::min(8, form_w);
    const int cell_w = form_w >= 35 ? 4 : std::max(1, std::min(3, (form_w - 2) / 10));
    for (int row = 0; row < 10; ++row)
        for (int col = 0; col < 10; ++col) {
            auto& button = minesweeper.cell(row, col);
            button.x = 2 + col * (form_w >= 35 ? 3 : cell_w);
            button.y = roomy ? 3 + row * 2 :
                       compact ? 1 + row * 2 : 1 + row;
            button.w = cell_w;
            button.h = roomy || middle ? 3 : compact ? 2 : 1;
        }
    auto& restart = minesweeper.control("btn_restart");
    restart.x = 0; restart.y = 0;
    restart.w = std::min(15, form_w);
    restart.h = roomy ? std::min(3, form_h) : 1;
}
static void native_start_hook() {
    std::cout << "\033]777;rad-tui;game-fullheight\007" << std::flush;
    Control restart = minesweeper.cell(0, 0);
    restart.caption = "Restart Game";
    restart.bg_color = 12;
    controls.push_back(restart);
    control_names.push_back("btn_restart");
    fit_minesweeper();
}
static void native_tick_hook() { fit_minesweeper(); }''',
        "native Minesweeper responsive layout",
    )
    mine_code = replace_once(
        mine_code,
        '    if (name == "on_form_load") { minesweeper.start(); return; }',
        '    if (name == "on_form_load" || name == "on_click_btn_restart") { minesweeper.start(); return; }',
        "native Minesweeper Restart callback",
    )
    native_mine.write_text(mine_code, encoding="utf-8")

    native_tic = SOURCE / "tic-tac-toe.cpp"
    tic_code = native_tic.read_text(encoding="utf-8")
    tic_code = replace_once(
        tic_code,
        "static void native_tick_hook() {}",
        '''static void native_tick_hook() {
    static const auto original_controls = controls;
    form_x = 0; form_y = LINES >= 20 ? 1 : 0;
    form_w = std::min(39, std::max(1, COLS));
    form_h = std::min(22, std::max(1, LINES - form_y));
    if (LINES >= 20) {
        for (std::size_t i = 0; i < controls.size(); ++i) {
            controls[i].x = original_controls[i].x;
            controls[i].y = original_controls[i].y;
            controls[i].w = original_controls[i].w;
            controls[i].h = original_controls[i].h;
        }
        return;
    }
    auto& status = tic_tac_toe.control("lbl_status");
    status.x = 1; status.y = 0; status.w = std::max(1, form_w - 2);
    const int cell_w = std::max(3, std::min(7, (form_w - 4) / 3));
    const int left = std::max(0, (form_w - 3 * cell_w - 2) / 2);
    const int step = LINES >= 14 ? 3 : 2;
    for (int index = 0; index < 9; ++index) {
        auto& button = tic_tac_toe.control("btn" + std::to_string(index));
        button.x = left + (index % 3) * (cell_w + 1);
        button.y = 2 + (index / 3) * step;
        button.w = cell_w;
        button.h = std::min(3, std::max(1, form_h - button.y));
    }
    auto& restart = tic_tac_toe.control("btn_reset");
    restart.w = std::min(15, form_w);
    restart.x = std::max(0, (form_w - restart.w) / 2);
    restart.y = step == 3 ? 11 : 8;
    restart.h = std::max(1, std::min(3, form_h - restart.y));
}''',
        "native Tic Tac Toe compact layout",
    )
    native_tic.write_text(tic_code, encoding="utf-8")

    native_calc = SOURCE / "calc.cpp"
    calc_code = native_calc.read_text(encoding="utf-8")
    calc_code = replace_once(
        calc_code,
        "static void native_tick_hook() {}",
        '''static void native_tick_hook() {
    static const auto original_controls = controls;
    form_x = 0; form_y = LINES >= 24 ? 1 : 0;
    form_w = std::min(25, std::max(1, COLS));
    form_h = std::min(25, std::max(1, LINES - form_y));
    if (LINES >= 24) {
        for (std::size_t i = 0; i < controls.size(); ++i) {
            controls[i].x = original_controls[i].x;
            controls[i].y = original_controls[i].y;
            controls[i].w = original_controls[i].w;
            controls[i].h = original_controls[i].h;
        }
        return;
    }
    calculator.display().y = 0;
    const int step = LINES >= 17 ? 3 : 2;
    const int top = 2;
    const std::vector<std::vector<std::string>> rows = {
        {"btn_c", "btn_ce", "btn_div", "btn_mul"},
        {"btn_7", "btn_8", "btn_9", "btn_sub"},
        {"btn_4", "btn_5", "btn_6", "btn_add"},
        {"btn_1", "btn_2", "btn_3", "btn_eq"},
        {"btn_0", "btn_dot"}
    };
    for (std::size_t row = 0; row < rows.size(); ++row)
        for (const auto& name : rows[row]) {
            auto found = std::find(control_names.begin(), control_names.end(), name);
            auto& button = controls[static_cast<std::size_t>(found - control_names.begin())];
            button.y = top + static_cast<int>(row) * step;
            button.h = std::min(3, std::max(1, form_h - button.y));
        }
    auto found = std::find(control_names.begin(), control_names.end(), "btn_eq");
    auto& equals = controls[static_cast<std::size_t>(found - control_names.begin())];
    equals.h = std::max(1, std::min(form_h - equals.y, step + 3));
}''',
        "native calculator compact layout",
    )
    native_calc.write_text(calc_code, encoding="utf-8")

    browser_source = SOURCE / "htmldemo" / "app.js"
    browser_code = browser_source.read_text(encoding="utf-8")
    browser_code = replace_once(
        browser_code,
        "folder: '', app: 'bash', keyboard: true, mode: 'ABC',",
        "folder: '', app: null, keyboard: false, mode: 'ABC',",
        "web startup state",
    )
    browser_code = replace_once(
        browser_code,
        "notice('WebAssembly ready · FutureShell started');",
        "notice('WebAssembly ready · DT started');",
        "web startup status",
    )
    browser_code = replace_once(
        browser_code,
        "    if (name === 'futurebrowser') {\n"
        "      formW = area.shellW; formH = area.shellH; formX = formY = 0;\n"
        "    }\n"
        "    const ox =",
        "    if (name === 'futurebrowser') {\n"
        "      formW = area.shellW; formH = area.shellH; formX = formY = 0;\n"
        "    } else if ((name === 'minesweeper' && area.shellH < 24) ||\n"
        "               (name === 'tic-tac-toe' && area.shellH < 20) ||\n"
        "               (name === 'calc' && area.shellH < 24)) {\n"
        "      formY = 0; formH = area.shellH;\n"
        "    }\n"
        "    formW = Math.min(formW, area.shellW);\n"
        "    formH = Math.min(formH, Math.max(1, area.shellH - formY));\n"
        "    const ox =",
        "web form height",
    )
    browser_code = replace_once(
        browser_code,
        "      let {x, y, w, h} = control;\n"
        "      let caption = control.caption;",
        "      let {x, y, w, h} = control;\n"
        "      if (name === 'minesweeper' && area.shellH < 24) {\n"
        "        const compact = area.shellH >= 21;\n"
        "        const cellW = formW >= 35 ? 4 : Math.max(1, Math.min(3, Math.floor((formW - 2) / 10)));\n"
        "        if (/^b[0-9]_[0-9]$/.test(control.name_id)) {\n"
        "          x = 2 + Number(control.name_id[3]) * (formW >= 35 ? 3 : cellW);\n"
        "          y = 1 + Number(control.name_id[1]) * (compact ? 2 : 1);\n"
        "          w = cellW; h = area.shellH >= 22 ? 3 : compact ? 2 : 1;\n"
        "        } else if (control.name_id === 'face_txt') {\n"
        "          x = Math.min(16, Math.max(0, formW - 19)); y = 0; w = Math.min(9, formW - x);\n"
        "        } else if (control.name_id === 'time_txt') {\n"
        "          x = Math.max(0, formW - 8); y = 0; w = Math.min(8, formW);\n"
        "        } else if (control.name_id === 'btn_restart') {\n"
        "          x = 0; y = 0; w = Math.min(15, formW); h = 1;\n"
        "        }\n"
        "      } else if (name === 'tic-tac-toe' && area.shellH < 20) {\n"
        "        const cellW = Math.max(3, Math.min(7, Math.floor((formW - 4) / 3)));\n"
        "        const left = Math.max(0, Math.floor((formW - 3 * cellW - 2) / 2));\n"
        "        const step = formH >= 14 ? 3 : 2;\n"
        "        if (/^btn[0-8]$/.test(control.name_id)) {\n"
        "          const index = Number(control.name_id.slice(3));\n"
        "          x = left + (index % 3) * (cellW + 1); y = 2 + Math.floor(index / 3) * step;\n"
        "          w = cellW; h = Math.min(3, Math.max(1, formH - y));\n"
        "        } else if (control.name_id === 'lbl_status') { x = 1; y = 0; w = formW - 2; }\n"
        "        else if (control.name_id === 'btn_reset') {\n"
        "          w = Math.min(15, formW); x = Math.max(0, Math.floor((formW - w) / 2));\n"
        "          y = step === 3 ? 11 : 8; h = Math.max(1, Math.min(3, formH - y));\n"
        "        }\n"
        "      } else if (name === 'calc' && area.shellH < 24) {\n"
        "        const step = formH >= 17 ? 3 : 2;\n"
        "        const top = 2;\n"
        "        if (control.name_id === 'display') y = 0;\n"
        "        else {\n"
        "          const rows = ['c ce div mul', '7 8 9 sub', '4 5 6 add',\n"
        "                        '1 2 3 eq', '0 dot'];\n"
        "          const row = rows.findIndex(names => names.split(' ').some(id => 'btn_' + id === control.name_id));\n"
        "          if (row >= 0) { y = top + row * step; h = control.name_id === 'btn_eq' ?\n"
        "            Math.min(formH - y, step + 3) : Math.min(3, Math.max(1, formH - y)); }\n"
        "        }\n"
        "      }\n"
        "      let caption = control.caption;",
        "web compact layouts",
    )
    browser_code = replace_once(
        browser_code,
        "    } else {\n"
        "      fill(x, y, w, h, colors.light);\n"
        "      fill(x + 1, y + 1, w - 2, h - 2, base);",
        "    } else if (h === 2) {\n"
        "      fill(x, y, w, h, colors.light);\n"
        "      text(x, y, 1, '┌', colors.white);\n"
        "      text(x + 1, y, w - 2, '─'.repeat(w - 2), colors.white);\n"
        "      text(x + w - 1, y, 1, '┐', colors.ink);\n"
        "      text(x, y + 1, 1, '│', colors.white);\n"
        "      text(x + 1, y + 1, w - 2, label, fg, base, 'center');\n"
        "      text(x + w - 1, y + 1, 1, '│', colors.ink);\n"
        "      ctx.fillStyle = colors.ink;\n"
        "      ctx.fillRect((x + 1) * grid.cw, (y + 2) * grid.ch - 1,\n"
        "                   (w - 2) * grid.cw, 1);\n"
        "    } else {\n"
        "      fill(x, y, w, h, colors.light);\n"
        "      fill(x + 1, y + 1, w - 2, h - 2, base);",
        "web two-row button captions",
    )
    browser_code = replace_once(
        browser_code,
        "        } else if (name === 'minesweeper') {\n"
        "          action = 'mine';\n"
        "          data = String(Number(control.name_id[1]) * 10 + Number(control.name_id[3]));\n"
        "        } else if (name === 'futurebrowser') action = 'go';",
        "        } else if (name === 'minesweeper') {\n"
        "          action = control.name_id === 'btn_restart' ? 'msReset' : 'mine';\n"
        "          if (action === 'mine')\n"
        "            data = String(Number(control.name_id[1]) * 10 + Number(control.name_id[3]));\n"
        "        } else if (name === 'futurebrowser') action = 'go';",
        "web Minesweeper restart action",
    )
    browser_code = replace_once(
        browser_code,
        "    else if (action === 'msReset') { wasm('ms_reset'); draw(); }",
        "    else if (action === 'msReset') { wasm('ms_reset'); state.flag = false; draw(); }",
        "web Minesweeper restart reset",
    )
    browser_code = replace_once(
        browser_code,
        "  canvas.addEventListener('click', event => click(event));",
        "  let lastHomePointerDown = -Infinity;\n"
        "  canvas.addEventListener('pointerdown', event => {\n"
        "    const {x, y} = point(event);\n"
        "    if (event.button === 0 && y === 0 && x >= 0 && x < 10) {\n"
        "      lastHomePointerDown = performance.now();\n"
        "      home();\n"
        "      event.preventDefault();\n"
        "    }\n"
        "  });\n"
        "  canvas.addEventListener('click', event => {\n"
        "    const {x, y} = point(event);\n"
        "    if (y === 0 && x >= 0 && x < 10 &&\n"
        "        performance.now() - lastHomePointerDown < 750) return;\n"
        "    click(event);\n"
        "  });",
        "web Home pointer handling",
    )
    browser_source.write_text(browser_code, encoding="utf-8")

    browser_index = SOURCE / "htmldemo" / "index.html"
    index_code = browser_index.read_text(encoding="utf-8")
    index_code = replace_once(
        index_code,
        'app.js?v=romaji-recovery-1',
        'app.js?v=dist-mine-resize-1',
        'web app cache version',
    )
    browser_index.write_text(index_code, encoding="utf-8")

    smoke = SOURCE / "htmldemo" / "smoke.html"
    smoke_code = smoke.read_text(encoding="utf-8")
    smoke_code = replace_once(
        smoke_code,
        "  const home = () => click(5, 0);",
        "  const home = () => {\n"
        "    const rect = canvas.getBoundingClientRect();\n"
        "    canvas.dispatchEvent(new frame.contentWindow.PointerEvent('pointerdown', {\n"
        "      bubbles: true, button: 0,\n"
        "      clientX: rect.left + 5.5 * rect.width / cols,\n"
        "      clientY: rect.top + .5 * rect.height / Number(canvas.dataset.rows)\n"
        "    }));\n"
        "    click(5, 0);\n"
        "  };",
        "web smoke Home tap",
    )
    smoke_code = replace_once(
        smoke_code,
        "    check(canvas.dataset.screen === 'bash' && canvas.dataset.keyboard === 'visible', 'FutureShell startup');\n",
        "    check(canvas.dataset.screen === 'DT' && canvas.dataset.keyboard === 'hidden', 'DT startup');\n"
        "    check(d.activeElement === canvas, 'DT focused on boot');\n"
        "    folder(2); // tools\n"
        "    app(0); // Bash\n"
        "    check(canvas.dataset.screen === 'bash', 'Bash opens from DT');\n"
        "    click(Math.floor(cols / 2), Number(canvas.dataset.rows) - 2); // show keyboard\n"
        "    check(canvas.dataset.keyboard === 'visible', 'Bash keyboard opens');\n",
        "web smoke startup",
    )
    smoke_code = replace_once(
        smoke_code,
        "    check(d.activeElement === input, 'shell input focused on boot');",
        "    check(d.activeElement === input, 'shell input focused when Bash opens');",
        "web smoke Bash focus",
    )
    smoke_code = replace_once(
        smoke_code,
        "    shellCommand('cd games');",
        "    shellCommand('cd /');\n    shellCommand('cd games');",
        "web smoke folder navigation",
    )
    smoke_code = replace_once(
        smoke_code,
        "    click(3, 6, true); // right-click b0_0\n"
        "    check(canvas.getAttribute('aria-label').includes('Flags 1.'), 'Minesweeper flag');",
        "    click(3, 4, true); // first board row\n"
        "    check(canvas.getAttribute('aria-label').includes('Flags 1.'), 'Minesweeper flag');\n"
        "    click(30, 22, true); // last board row remains visible\n"
        "    check(canvas.getAttribute('aria-label').includes('Flags 2.'), 'Minesweeper bottom row');\n"
        "    click(7, 2); // Restart Game at top of form\n"
        "    check(canvas.getAttribute('aria-label').includes('Flags 0.'), 'Minesweeper restart');",
        "web Minesweeper layout and restart smoke",
    )
    smoke.write_text(smoke_code, encoding="utf-8")
    (SOURCE / "htmldemo" / "README.md").write_text(
        "# FutureShell WebAssembly source\n\n"
        "`demo.cpp`, `app.js`, `styles.css`, and `index.html` are the web "
        "demo sources. The distribution copy of `app.js` starts on DT; "
        "`smoke.html` checks startup, Home, and the subapps.\n\n"
        "Serve the ready-to-run files from `../../../ports/webasm/site`. "
        "To recompile WebAssembly, run the original "
        "`projects/phoneapps/htmldemo/build.bash` in the repository, "
        "then run `python3 dist/rebuild.py` to refresh this distribution.\n",
        encoding="utf-8",
    )

    package_src = REPO / "rad_tui_basic_pkg" / "src" / "rad_tui_basic"
    package_dst = DIST / "source" / "rad_tui_basic_pkg" / "src" / "rad_tui_basic"
    for src in package_src.rglob("*"):
        if not src.is_file() or src.is_symlink() or src.suffix in (".pyc", ".backup"):
            continue
        if "__pycache__" in src.parts:
            continue
        copy_file(src, package_dst / src.relative_to(package_src))
    for filename in ("pyproject.toml", "README.md", "LICENSE", "HISTORY.md"):
        src = REPO / "rad_tui_basic_pkg" / filename
        if src.is_file():
            copy_file(src, DIST / "source" / "rad_tui_basic_pkg" / filename)

    # The existing forms use PROJECT_DIR for shell commands, DT/DTF, and the
    # download runner. Only the distribution copy of the IDE needs this hook.
    ide = package_dst / "rad_tui_py.py"
    original = "run_globals_dict['PROJECT_DIR'] = os.path.dirname(os.path.abspath(project_file)) if project_file else os.getcwd()"
    replacement = (
        "run_globals_dict['PROJECT_DIR'] = os.path.abspath("
        "os.environ.get('RAD_TUI_PROJECT_DIR') or "
        "(os.path.dirname(os.path.abspath(project_file)) if project_file else os.getcwd()))"
    )
    code = ide.read_text(encoding="utf-8")
    if code.count(original) != 1:
        raise RuntimeError("IDE PROJECT_DIR hook changed; update dist/rebuild.py")
    code = code.replace(original, replacement)
    code = replace_once(
        code,
        "\n    run_mouse_capture_idx = -1\n",
        "\n    run_mouse_capture_idx = -1\n    home_mouse_pressed = False\n",
        "IDE Home mouse state",
    )
    code = replace_once(
        code,
        "                _, mx, my, _, bstate = curses.getmouse()\n"
        "                mouse_moved = (mx != old_mx or my != old_my)",
        "                _, mx, my, _, bstate = curses.getmouse()\n"
        "                home_handler = run_globals.get('on_click_btn_home') if run_mode else None\n"
        "                if callable(home_handler) and not main_form.hidden:\n"
        "                    home_control = next((control for control in main_form.controls\n"
        "                                         if control.name_id == 'btn_home'), None)\n"
        "                    if (home_control is not None and\n"
        "                            main_form.x + home_control.x <= mx < main_form.x + home_control.x + home_control.w and\n"
        "                            main_form.y + home_control.y <= my < main_form.y + home_control.y + home_control.h and\n"
        "                            bstate & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED | curses.BUTTON1_RELEASED)):\n"
        "                        activate_home = bool(bstate & curses.BUTTON1_PRESSED) or not home_mouse_pressed\n"
        "                        home_mouse_pressed = bool(bstate & curses.BUTTON1_PRESSED)\n"
        "                        run_mouse_capture_idx = run_mouse_capture_button = run_pressed_ctrl = -1\n"
        "                        mouse_down = False\n"
        "                        old_mx, old_my = mx, my\n"
        "                        if activate_home:\n"
        "                            try: home_handler()\n"
        "                            except Exception as e: run_globals['__msg__'] = f'Runtime Error:\\n{e}'\n"
        "                        continue\n"
        "                mouse_moved = (mx != old_mx or my != old_my)",
        "IDE Home mouse priority",
    )
    code = replace_once(
        code,
        "                if actual_h < 3 or c.w < 3:\n",
        "                if actual_h == 2 and c.w >= 3:\n"
        "                    write_clipped(draw_x, draw_y, '┌' + '─' * (c.w - 2), TOP_C)\n"
        "                    write_clipped(draw_x + c.w - 1, draw_y, '┐', BOT_C)\n"
        "                    pad = max(0, (c.w - 2 - d_len(c.caption)) // 2)\n"
        "                    interior = d_pad(' ' * pad + c.caption, c.w - 2)\n"
        "                    write_clipped(draw_x, draw_y + 1, '│', TOP_C)\n"
        "                    write_clipped(draw_x + 1, draw_y + 1, interior,\n"
        "                                  base_color | curses.A_UNDERLINE)\n"
        "                    write_clipped(draw_x + c.w - 1, draw_y + 1, '│', BOT_C)\n"
        "                    continue\n"
        "                if actual_h < 3 or c.w < 3:\n",
        "IDE two-row button borders",
    )
    code = replace_once(
        code,
        "        if ch == 27 and run_mode and run_globals.get('capture_physical_keys'):",
        "        if ch == curses.KEY_RESIZE:\n"
        "            curses.update_lines_cols()\n"
        "            trigger_resize(main_form)\n"
        "            stdscr.clear()\n"
        "            continue\n\n"
        "        if ch == 27 and run_mode and run_globals.get('capture_physical_keys'):",
        "IDE terminal resize callback",
    )
    code = replace_once(
        code,
        "                            elif my == 0 and left_click:",
        "                            elif my == 0 and left_click and menu_positions:",
        "IDE first-row controls without menus",
    )
    ide.write_text(code, encoding="utf-8")


def build_ports() -> None:
    write_executable(DIST / "bin" / "rad-tui-ide", '''#!/usr/bin/env bash
set -euo pipefail
dist_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
export PYTHONPATH="$dist_dir/source/rad_tui_basic_pkg/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m rad_tui_basic.rad_tui_py "$@"
''')

    for port_name in PORTS:
        port = DIST / "ports" / port_name
        port.mkdir(parents=True, exist_ok=True)
        (port / ".dist-port").write_text(port_name + "\n", encoding="utf-8")
        write_executable(port / "launcher.sh", '''#!/usr/bin/env bash
set -euo pipefail
port_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
dist_dir=$(cd -- "$port_dir/../.." && pwd -P)
run_project() {
    local project_json=$1 project_dir=$2
    export PATH="$dist_dir/bin:$PATH"
    export RAD_TUI_PROJECT_DIR="$port_dir/$project_dir"
    exec rad-tui-ide -run "$dist_dir/source/phoneapps/$project_json"
}
''')

        for relative, project_json in APPS.items():
            # DT's project directory must contain DTF; the other forms use
            # the port root for Home, shell cwd, and the download runner.
            project_dir = "DT" if relative == "DT/DT.bin" else "."
            script = f'''#!/usr/bin/env bash
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")" && pwd -P)
port_dir=$script_dir
while [[ ! -f $port_dir/.dist-port ]]; do
    [[ $port_dir != / ]] || {{ echo 'Port root not found' >&2; exit 1; }}
    port_dir=${{port_dir%/*}}
    [[ -n $port_dir ]] || port_dir=/
done
source "$port_dir/launcher.sh"
run_project {json.dumps(project_json)} {json.dumps(project_dir)}
'''
            write_executable(port / relative, script)

        # Preserve the desktop's folder icons and its writable folder layout.
        dtf = PHONEAPPS / "DT" / "DTF"
        for src in dtf.rglob("*.icons"):
            copy_file(src, port / "DT" / "DTF" / src.relative_to(dtf))
        for folder, icon in (("games", "🎮"), ("tools", "🔨")):
            (port / "DT" / "DTF" / f"{folder}.icons").write_text(icon + "\n", encoding="utf-8")
        for folder in ("games", "internet", "tools"):
            (port / "DT" / "DTF" / folder).mkdir(parents=True, exist_ok=True)

        runner_src = (PHONEAPPS / "run-downloaded-bin.sh").read_text(encoding="utf-8")
        runner_src = runner_src.replace(
            "if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then",
            "if [[ $(cat \"$script_dir/.dist-port\") != amd64 || $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then",
        )
        runner_src = runner_src.replace(
            "project_path=$script_dir/$app_name.json",
            "project_path=$script_dir/../../source/phoneapps/$app_name.json",
        ).replace(
            "source_dir=$script_dir/../../rad_tui_basic_pkg/src",
            "source_dir=$script_dir/../../source/rad_tui_basic_pkg/src",
        ).replace(
            "exec python3 -m rad_tui_basic.rad_tui_py -run \"$project_path\"",
            "export RAD_TUI_PROJECT_DIR=\"$script_dir\"\n    exec \"$script_dir/../../bin/rad-tui-ide\" -run \"$project_path\"",
        )
        runner_src = runner_src.replace(
            "app_name=${app_name%.amd64}\n    project_path=",
            "app_name=${app_name%.amd64}\n"
            "    app_name=${app_name%.webasm}\n"
            "    app_name=${app_name%.arm64}\n"
            "    app_name=${app_name%.riscv64}\n"
            "    [[ $app_name != minesweeper ]] || app_name=ms\n"
            "    project_path=",
        )
        # The downloaded file has one stable name in this distribution, and
        # Home removes that same file from the port root.
        runner_src = runner_src.replace("a.out", "o.out")
        write_executable(port / "run-downloaded-bin.sh", runner_src)

    # Keep native executables with their original code format and a different
    # extension; every launchable .bin in the port trees stays a Bash script.
    amd64 = DIST / "ports" / "amd64" / "artifacts"
    native_artifacts = {
        "DT/DT.elf": "DT/DT.bin",
        "DT/DTF/internet/futurebrowser.elf": "DT/DTF/internet/futurebrowser.bin",
        "tic-tac-toe.amd64.elf": "tic-tac-toe.amd64.bin",
    }
    for dst, src in native_artifacts.items():
        path = PHONEAPPS / src
        if path.is_file():
            copy_file(path, amd64 / dst)
    native_output = amd64 / "phone_shell.elf"
    if shutil.which("g++"):
        subprocess.run(
            ["g++", "-std=c++17", "-O2", str(SOURCE / "phone_shell.cpp"),
             "-lncursesw", "-o", str(native_output)],
            check=True,
        )
        subprocess.run(
            ["g++", "-std=c++17", "-O2", str(SOURCE / "ms.cpp"),
             "-lncursesw", "-o", str(amd64 / "DT/DTF/games/minesweeper.elf")],
            check=True,
        )
        for source_name, output_name in (
            ("tic-tac-toe.cpp", "DT/DTF/games/tic-tac-toe.elf"),
            ("calc.cpp", "DT/DTF/tools/calc.elf"),
        ):
            subprocess.run(
                ["g++", "-std=c++17", "-O2", str(SOURCE / source_name),
                 "-lncursesw", "-o", str(amd64 / output_name)],
                check=True,
            )
    else:
        print("Warning: g++ unavailable; amd64 ELF artifacts were not rebuilt")

    site = DIST / "ports" / "webasm" / "site"
    web_src = PHONEAPPS / "htmldemo"
    for src in web_src.rglob("*"):
        if not src.is_file() or src.is_symlink():
            continue
        if src.name in ("demo.cpp", "shell_catalog.h", "build.bash"):
            continue
        source_copy = SOURCE / "htmldemo" / src.relative_to(web_src)
        copy_file(source_copy if source_copy.is_file() else src,
                  site / src.relative_to(web_src))
    (site / "README.md").write_text(
        "# FutureShell WebAssembly site\n\n"
        "Serve this directory over HTTP or HTTPS, then open `index.html`.\n"
        "For a local test, run `python3 -m http.server 8000` here and visit "
        "`http://localhost:8000`. The browser loads `futureshell.wasm` "
        "on startup and opens DT first. Future Browser can load "
        "`http://localhost:8000/tic-tac-toe.webasm.bin`.\n\n"
        "The editable sources are under `../../../source/phoneapps/htmldemo`, "
        "and the matching RAD-TUI forms are under `../../../source/phoneapps`.\n",
        encoding="utf-8",
    )
    # The browser downloads this named WASM module. Its .bin suffix belongs
    # to the web protocol; it is a data artifact, not a port launcher.
    for filename in ("tic-tac-toe.webasm.bin",):
        src = PHONEAPPS / filename
        if src.is_file():
            copy_file(src, DIST / "ports" / "webasm" / "artifacts" / filename)


if __name__ == "__main__":
    copy_sources()
    build_ports()
    print(f"Distribution refreshed in {DIST}")
