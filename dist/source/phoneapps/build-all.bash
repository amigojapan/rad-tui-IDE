#!/usr/bin/env bash
set -euo pipefail

phoneapps_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
repo_dir=$(cd -- "$phoneapps_dir/../.." && pwd -P)
build_dir=$(mktemp -d "${TMPDIR:-/tmp}/rad-tui-phoneapps-build.XXXXXXXX")
trap 'rm -rf -- "$build_dir"' EXIT

# The JSON projects are the source of the native exports. Refresh only stale
# generated C++ files so a future JSON edit is included in this same build.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$repo_dir/rad_tui_basic_pkg/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 - "$phoneapps_dir" <<'PY'
import json
from pathlib import Path
import sys
from rad_tui_basic.cpp_export import export_cpp, generate_cpp

phoneapps = Path(sys.argv[1])
projects = (
    ('phone_shell.json', 'phone_shell.cpp'),
    ('DT/DT.json', 'DT/DT.cpp'),
    ('calc.json', 'calc.cpp'),
    ('tic-tac-toe.json', 'tic-tac-toe.cpp'),
    ('ms.json', 'ms.cpp'),
    ('futurebrowser.json', 'DT/DTF/internet/futurebrowser.cpp'),
)
for project_name, source_name in projects:
    project = json.loads((phoneapps / project_name).read_text())
    source_path = phoneapps / source_name
    if source_path.read_text() != generate_cpp(project):
        export_cpp(project, source_path)
        print(f'Regenerated {source_name}')
PY

build_native() {
    local source=$1 output=$2
    g++ -std=c++17 -O2 "$source" -lncursesw -o "$build_dir/$output"
    echo "Compiled $output"
}

build_native "$phoneapps_dir/phone_shell.cpp" phone_shell.bin
build_native "$phoneapps_dir/DT/DT.cpp" DT.bin
build_native "$phoneapps_dir/calc.cpp" calc.bin
build_native "$phoneapps_dir/tic-tac-toe.cpp" tic-tac-toe.bin
build_native "$phoneapps_dir/ms.cpp" minesweeper.bin
build_native "$phoneapps_dir/DT/DTF/internet/futurebrowser.cpp" futurebrowser.bin

# Build the bundled browser runtime, form data, and the downloadable Wasm app.
bash "$phoneapps_dir/htmldemo/build.bash"

install -m 775 "$build_dir/phone_shell.bin" "$phoneapps_dir/phone_shell.bin"
install -m 775 "$build_dir/phone_shell.bin" "$repo_dir/phone_shell.bin"
install -m 775 "$build_dir/DT.bin" "$phoneapps_dir/DT/DT.bin"
install -m 775 "$build_dir/DT.bin" "$repo_dir/DT"

for games_dir in "$phoneapps_dir/DT/DTF/games" "$phoneapps_dir/DTF/games"; do
    install -m 775 "$build_dir/minesweeper.bin" "$games_dir/minesweeper.bin"
    install -m 775 "$build_dir/tic-tac-toe.bin" "$games_dir/tic-tac-toe.bin"
done
for tools_dir in "$phoneapps_dir/DT/DTF/tools" "$phoneapps_dir/DTF/tools"; do
    install -m 775 "$build_dir/calc.bin" "$tools_dir/calc.bin"
done
install -m 775 "$build_dir/futurebrowser.bin" \
    "$phoneapps_dir/DT/DTF/internet/futurebrowser.bin"
install -m 775 "$build_dir/tic-tac-toe.bin" "$phoneapps_dir/tic-tac-toe.amd64.bin"
install -m 775 "$build_dir/tic-tac-toe.bin" "$phoneapps_dir/tic-tac-toe..amd64.bin"

# These .bin entries are shell scripts, not compiled executables. Keep the
# older DTF copy in sync with the active desktop's script launchers.
for launcher in bash nano; do
    source_script=$phoneapps_dir/DT/DTF/tools/$launcher.bin
    legacy_script=$phoneapps_dir/DTF/tools/$launcher.bin
    if ! cmp -s "$source_script" "$legacy_script"; then
        install -m 775 "$source_script" "$legacy_script"
    fi
done

echo 'Rebuilt native phone apps and both WebAssembly artifacts.'
