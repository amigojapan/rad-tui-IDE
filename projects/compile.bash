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

g++ -std=c++17 -O2 "$source_file" -lncursesw -o "$output_file"
echo "Built $output_file"
