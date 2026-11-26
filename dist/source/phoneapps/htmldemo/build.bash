#!/usr/bin/env bash
set -euo pipefail

demo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

# Keep each browser form tied to the checked-in RAD-TUI project controls.
python3 - "$demo_dir" <<'PY'
import json
import ast
from pathlib import Path
import sys

demo = Path(sys.argv[1])
phoneapps = demo.parent
projects = {
    'DT': phoneapps / 'DT' / 'DT.json',
    'calc': phoneapps / 'calc.json',
    'tic-tac-toe': phoneapps / 'tic-tac-toe.json',
    'minesweeper': phoneapps / 'ms.json',
    'futurebrowser': phoneapps / 'futurebrowser.json',
}
forms = {}
for name, path in projects.items():
    project = json.loads(path.read_text())
    forms[name] = {
        key: project[key] for key in ('x', 'y', 'w', 'h', 'title',
                                     'display_border_and_caption')
    }
    forms[name]['menus'] = [menu['label'] for menu in project.get('menus', [])]
    forms[name]['controls'] = [
        {key: control[key] for key in ('x', 'y', 'w', 'h', 'tool_type',
                                      'name_id', 'caption', 'bg_color')
         if key in control}
        for control in project['controls']
    ]
(demo / 'forms.json').write_text(json.dumps(forms, ensure_ascii=False, indent=2) + '\n')

# Use the native phone shell's kanji readings for browser candidate selection.
phone_shell_code = json.loads((phoneapps / 'phone_shell.json').read_text())['code']
for node in ast.parse(phone_shell_code).body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == 'KANJI_CANDIDATES'
        for target in node.targets
    ):
        kanji = ast.literal_eval(node.value)
        break
else:
    raise RuntimeError('KANJI_CANDIDATES missing from phone_shell.json')
# The loanword has no kanji spelling; offer the common kanji synonym as well.
kanji['てすと'] = ['試験']
(demo / 'kanji.json').write_text(json.dumps(kanji, ensure_ascii=False, indent=2) + '\n')

# The desktop and WebAssembly shell use the same source directory as native DT.
root = phoneapps / 'DT' / 'DTF'
catalog = {}
for directory in (root, *sorted(path for path in root.rglob('*') if path.is_dir())):
    relative = directory.relative_to(root).as_posix()
    key = '' if relative == '.' else relative
    entries = []
    for child in sorted(directory.iterdir(), key=lambda path: path.name.casefold()):
        if child.is_dir():
            icon_file = directory / f'{child.name}.icons'
            icon = icon_file.read_text().strip() if icon_file.is_file() else '🗂️'
            entries.append({'kind': 'folder', 'name': child.name,
                            'path': child.relative_to(root).as_posix(),
                            'icon': icon or '🗂️'})
        elif child.suffix == '.bin':
            icon_file = directory / f'{child.stem}.icons'
            icon = icon_file.read_text().strip() if icon_file.is_file() else '⚡'
            entries.append({'kind': 'app', 'name': child.stem,
                            'id': child.stem, 'icon': icon or '⚡'})
    catalog[key] = entries
(demo / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')

def cpp_string(value):
    return json.dumps(value, ensure_ascii=True)

lines = ['// Generated from DT/DTF by build.bash.',
         'struct ShellEntry { const char* parent; const char* name; const char* path; bool folder; };',
         'static const ShellEntry shell_entries[] = {']
for parent, entries in catalog.items():
    for entry in entries:
        path = entry['path'] if entry['kind'] == 'folder' else entry['id']
        lines.append('    {' + ', '.join((cpp_string(parent), cpp_string(entry['name']),
                                      cpp_string(path), 'true' if entry['kind'] == 'folder' else 'false')) + '},')
lines += ['};', '']
(demo / 'shell_catalog.h').write_text('\n'.join(lines))
PY

if command -v em++ >/dev/null 2>&1; then
    compiler=$(command -v em++)
elif [[ -n ${EMSDK:-} && -x $EMSDK/upstream/emscripten/em++ ]]; then
    compiler=$EMSDK/upstream/emscripten/em++
elif [[ -x ${HOME:-/nonexistent}/emsdk/upstream/emscripten/em++ ]]; then
    compiler=${HOME}/emsdk/upstream/emscripten/em++
else
    echo 'Emscripten em++ was not found. Install emsdk or source emsdk_env.sh.' >&2
    exit 1
fi
webasm_compiler=$(dirname "$(dirname "$compiler")")/bin/clang
if [[ ! -x $webasm_compiler ]]; then
    webasm_compiler=$(command -v clang || true)
fi
if [[ -z $webasm_compiler ]]; then
    echo 'A WebAssembly-capable clang is required.' >&2
    exit 1
fi
phoneapps_dir=$(dirname "$demo_dir")

# Keep toolchain cache files outside this distributable demo directory.
export EM_CACHE=${EM_CACHE:-${TMPDIR:-/tmp}/rad-tui-phone-demo-emcache}

"$compiler" -std=c++17 -O2 "$demo_dir/demo.cpp" \
    --no-entry \
    -sMODULARIZE=1 \
    -sEXPORT_NAME=createFutureShell \
    -sENVIRONMENT=web \
    -sFILESYSTEM=0 \
    -sALLOW_MEMORY_GROWTH=1 \
    -sEXPORTED_RUNTIME_METHODS=ccall \
    -sEXPORTED_FUNCTIONS='["_demo_version","_shell_boot","_shell_run","_shell_output","_shell_action","_shell_target","_shell_directory","_calc_reset","_calc_press","_calc_display","_ttt_reset","_ttt_move","_ttt_board","_ttt_status","_ms_reset","_ms_reveal","_ms_flag","_ms_board","_ms_status","_ms_seconds","_ms_tick"]' \
    -o "$demo_dir/futureshell.js"

# A separate raw Wasm module is served by Future Browser. It needs no JS
# loader and can be instantiated directly from the downloaded .bin response.
"$webasm_compiler" --target=wasm32 -O2 -nostdlib "$phoneapps_dir/tic-tac-toe-webasm.c" \
    -Wl,--no-entry -Wl,--export=ttt_seed -Wl,--export=ttt_reset \
    -Wl,--export=ttt_cell -Wl,--export=ttt_status_code \
    -Wl,--export=ttt_move \
    -o "$phoneapps_dir/tic-tac-toe.webasm.bin"
cp "$phoneapps_dir/tic-tac-toe.webasm.bin" "$demo_dir/tic-tac-toe.webasm.bin"

echo "Built $demo_dir/futureshell.js and $demo_dir/futureshell.wasm"
echo "Built $phoneapps_dir/tic-tac-toe.webasm.bin"
echo "Serve with: python3 -m http.server 8000 --directory '$demo_dir'"
