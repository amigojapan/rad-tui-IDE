#!/usr/bin/env bash
set -euo pipefail
port_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
dist_dir=$(cd -- "$port_dir/../.." && pwd -P)
run_project() {
    local project_json=$1 project_dir=$2
    export PATH="$dist_dir/bin:$PATH"
    export RAD_TUI_PROJECT_DIR="$port_dir/$project_dir"
    exec rad-tui-ide -run "$dist_dir/source/phoneapps/$project_json"
}
