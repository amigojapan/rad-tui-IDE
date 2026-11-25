#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
    echo "Usage: $0 <filename>.cpp" >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
source_file=$1

if [[ ! -f $source_file && -f $script_dir/$source_file ]]; then
    source_file=$script_dir/$source_file
fi
if [[ ! -f $source_file ]]; then
    echo "C++ source not found: $1" >&2
    exit 1
fi
if [[ $source_file != *.cpp ]]; then
    echo "Expected a .cpp file: $source_file" >&2
    exit 2
fi

source_dir=$(cd -- "$(dirname -- "$source_file")" && pwd -P)
source_file=$source_dir/$(basename -- "$source_file")
output_file=${source_file%.cpp}.bin

if command -v pkg-config >/dev/null 2>&1; then
    if ! pkg-config --exists ncursesw; then
        echo 'Static ncursesw development files are required.' >&2
        exit 1
    fi
    read -r -a ncurses_libs <<< "$(pkg-config --libs --static ncursesw)"
else
    ncurses_libs=(-lncursesw -ltinfo -ldl)
fi

build_dir=$(mktemp -d "$source_dir/.compilestatic.XXXXXXXX")
trap 'rm -rf -- "$build_dir"' EXIT
temporary_output=$build_dir/$(basename -- "$output_file")
g++ -std=c++17 -O2 -static "$source_file" "${ncurses_libs[@]}" -o "$temporary_output"
mv -- "$temporary_output" "$output_file"
echo "Built static $output_file"
