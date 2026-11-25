#!/usr/bin/env bash
set -euo pipefail

demo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

# Keep each browser form tied to the checked-in RAD-TUI project controls.
python3 - "$demo_dir" <<'PY'
import json
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
    -sEXPORT_NAME=createPhoneDemo \
    -sENVIRONMENT=web \
    -sFILESYSTEM=0 \
    -sALLOW_MEMORY_GROWTH=1 \
    -sEXPORTED_RUNTIME_METHODS=ccall \
    -sEXPORTED_FUNCTIONS='["_demo_version","_calc_reset","_calc_press","_calc_display","_ttt_reset","_ttt_move","_ttt_board","_ttt_status","_ms_reset","_ms_reveal","_ms_flag","_ms_board","_ms_status","_ms_seconds","_ms_tick"]' \
    -o "$demo_dir/demo.js"

# A separate raw Wasm module is served by Future Browser. It needs no JS
# loader and can be instantiated directly from the downloaded .bin response.
"$webasm_compiler" --target=wasm32 -O2 -nostdlib "$phoneapps_dir/tic-tac-toe-webasm.c" \
    -Wl,--no-entry -Wl,--export=ttt_seed -Wl,--export=ttt_reset \
    -Wl,--export=ttt_cell -Wl,--export=ttt_status_code \
    -Wl,--export=ttt_move \
    -o "$phoneapps_dir/tic-tac-toe.webasm.bin"
cp "$phoneapps_dir/tic-tac-toe.webasm.bin" "$demo_dir/tic-tac-toe.webasm.bin"

echo "Built $demo_dir/demo.js and $demo_dir/demo.wasm"
echo "Built $phoneapps_dir/tic-tac-toe.webasm.bin"
echo "Serve with: python3 -m http.server 8000 --directory '$demo_dir'"
