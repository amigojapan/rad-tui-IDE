#!/usr/bin/env bash
# This sandbox applies only to ELF files downloaded by Future Browser.
# Phone Shell, DT, DTF, and their installed apps run outside it.
set -euo pipefail

if (( $# != 1 )); then
    echo "Usage: $0 URL-to-app.amd64.bin" >&2
    exit 2
fi

url=$1
case $url in
    http://*|https://*) ;;
    *) echo 'Error: only HTTP(S) download URLs are allowed.' >&2; exit 2 ;;
esac
url_path=${url%%#*}
url_path=${url_path%%\?*}
filename=${url_path##*/}
if [[ $filename != *.bin ]]; then
    echo 'Error: the URL filename must end in .bin (for example, app.amd64.bin).' >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ $(cat "$script_dir/.dist-port") != amd64 || $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    # Native amd64 ELF files cannot execute on another OS or CPU. Run the
    # matching local RAD-TUI Python project when one is available.
    app_name=${filename%.bin}
    app_name=${app_name%.amd64}
    app_name=${app_name%.webasm}
    app_name=${app_name%.arm64}
    app_name=${app_name%.riscv64}
    [[ $app_name != minesweeper ]] || app_name=ms
    project_path=$script_dir/../../source/phoneapps/$app_name.json
    if [[ ! -f $project_path ]]; then
        echo "Error: no Python project found for $filename ($project_path)." >&2
        exit 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo 'Error: python3 is required for this platform.' >&2
        exit 1
    fi
    source_dir=$script_dir/../../source/rad_tui_basic_pkg/src
    if [[ -d $source_dir ]]; then
        export PYTHONPATH="$source_dir${PYTHONPATH:+:$PYTHONPATH}"
    fi
    echo "Running Python version: $app_name" >&2
    export RAD_TUI_PROJECT_DIR="$script_dir"
    exec "$script_dir/../../bin/rad-tui-ide" -run "$project_path"
fi

for tool in wget bwrap readelf realpath sed; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Error: $tool is required." >&2
        exit 1
    fi
done

umask 077
download_path=$script_dir/o.out
if [[ -e $download_path || -L $download_path ]]; then
    echo "Error: $download_path already exists. Remove it before downloading." >&2
    exit 1
fi
staged_path=$(mktemp "$script_dir/.o.out.XXXXXXXX")
cleanup() {
    if [[ -e $download_path && -e /proc/self/fd/4 &&
          $download_path -ef /proc/self/fd/4 ]]; then
        rm -f -- "$download_path"
    elif [[ -e $download_path && -e $staged_path &&
            $download_path -ef $staged_path ]]; then
        rm -f -- "$download_path"
    fi
    rm -f -- "$staged_path"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

echo 'Downloading (numeric percent shown below)...' >&2
wget --no-config --no-netrc --no-cookies --no-hsts \
    --quiet --show-progress --progress=bar:force:noscroll \
    --output-document="$staged_path" -- "$url"
chmod +x "$staged_path"

header=$(LC_ALL=C readelf -h "$staged_path" 2>/dev/null) || {
    echo 'Error: the download is not an ELF executable.' >&2
    exit 1
}
if [[ ! $header =~ Class:[[:space:]]*ELF64 ]] ||
   [[ ! $header =~ Machine:[[:space:]]*Advanced[[:space:]]Micro[[:space:]]Devices[[:space:]]X86-64 ]]; then
    echo 'Error: the download is not an amd64 ELF executable.' >&2
    exit 1
fi

segments=$(LC_ALL=C readelf -l "$staged_path" 2>/dev/null) || {
    echo 'Error: the ELF program headers are invalid.' >&2
    exit 1
}
dynamic=$(LC_ALL=C readelf -d "$staged_path" 2>/dev/null) || {
    echo 'Error: the ELF dynamic section is invalid.' >&2
    exit 1
}
interpreter=$(printf '%s\n' "$segments" | sed -n 's/.*Requesting program interpreter: \([^]]*\)\].*/\1/p')
if [[ $segments == *INTERP* && -z $interpreter ]]; then
    echo 'Error: cannot identify the ELF interpreter.' >&2
    exit 1
fi

# Resolve only system libraries named by the ELF and their dependencies.
# Never run ldd on an untrusted download: parse its metadata with readelf.
resolve_library() {
    local name=$1 directory candidate resolved
    [[ $name =~ ^[a-zA-Z0-9][a-zA-Z0-9._+-]*$ ]] || return 1
    for directory in /lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu \
                     /lib64 /usr/lib64 /usr/local/lib; do
        candidate=$directory/$name
        [[ -f $candidate ]] || continue
        resolved=$(realpath -e -- "$candidate") || continue
        case $resolved in
            /lib/*|/lib64/*|/usr/lib/*|/usr/lib64/*|/usr/local/lib/*)
                printf '%s\n' "$candidate"
                return 0 ;;
        esac
    done
    return 1
}

declare -A library_paths=()
declare -a pending_libraries=()
mapfile -t pending_libraries < <(printf '%s\n' "$dynamic" |
    sed -n 's/.*Shared library: \[\([^]]*\)\].*/\1/p')
for ((index = 0; index < ${#pending_libraries[@]}; index++)); do
    library=${pending_libraries[index]}
    if [[ ! $library =~ ^[a-zA-Z0-9][a-zA-Z0-9._+-]*$ ]]; then
        echo "Error: unsafe ELF library name: $library" >&2
        exit 1
    fi
    [[ -n ${library_paths[$library]+present} ]] && continue
    library_path=$(resolve_library "$library") || {
        echo "Error: required system library is unavailable: $library" >&2
        exit 1
    }
    library_paths[$library]=$library_path
    library_dynamic=$(LC_ALL=C readelf -d "$library_path" 2>/dev/null) || {
        echo "Error: cannot inspect system library: $library_path" >&2
        exit 1
    }
    while IFS= read -r dependency; do
        pending_libraries+=("$dependency")
    done < <(printf '%s\n' "$library_dynamic" |
        sed -n 's/.*Shared library: \[\([^]]*\)\].*/\1/p')
done

if [[ -n $interpreter ]]; then
    case $interpreter in
        /lib64/ld-linux-x86-64.so.2|/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2|\
        /usr/lib64/ld-linux-x86-64.so.2|/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2) ;;
        *) echo "Error: unsupported ELF interpreter: $interpreter" >&2; exit 1 ;;
    esac
    interpreter_source=$(realpath -e -- "$interpreter") || {
        echo "Error: ELF interpreter is unavailable: $interpreter" >&2
        exit 1
    }
    case $interpreter_source in
        /lib/*|/lib64/*|/usr/lib/*|/usr/lib64/*) ;;
        *) echo 'Error: ELF interpreter resolves outside system libraries.' >&2; exit 1 ;;
    esac
fi

if ! ln -- "$staged_path" "$download_path"; then
    echo "Error: cannot create $download_path." >&2
    exit 1
fi

exec 4< "$download_path"
rm -f -- "$staged_path"
echo 'Running in an isolated read-only sandbox with network access...' >&2
sandbox=(--unshare-user --unshare-pid --unshare-ipc --unshare-uts
         --disable-userns --cap-drop ALL --new-session --die-with-parent
         --clearenv --tmpfs /)
declare -A sandbox_dirs=()
add_dir() {
    local path=$1 component current=''
    local -a components=()
    IFS=/ read -r -a components <<< "${path#/}"
    for component in "${components[@]}"; do
        [[ -n $component ]] || continue
        current+=/$component
        if [[ -z ${sandbox_dirs[$current]+present} ]]; then
            sandbox+=(--dir "$current")
            sandbox_dirs[$current]=1
        fi
    done
}
bind_file() {
    local source=$1 destination=$2
    add_dir "${destination%/*}"
    sandbox+=(--ro-bind "$source" "$destination")
}

if [[ -n $interpreter ]]; then
    bind_file "$interpreter_source" "$interpreter"
fi
for library in "${!library_paths[@]}"; do
    bind_file "${library_paths[$library]}" "${library_paths[$library]}"
done

# Network access is available to the app. Give libc only the system files
# needed to resolve names, without exposing /home, /run, or all of /etc.
for module in libnss_files.so.2 libnss_dns.so.2; do
    if module_path=$(resolve_library "$module"); then
        bind_file "$module_path" "$module_path"
    fi
done
add_dir /etc
exec 6< <(printf 'hosts: files dns\n')
sandbox+=(--perms 0444 --file 6 /etc/nsswitch.conf)
bind_system_file() {
    local destination=$1 source
    [[ -f $destination ]] || return 0
    source=$(realpath -e -- "$destination") || return 1
    case $source in
        /etc/*|/run/systemd/resolve/*|/run/NetworkManager/*|/run/resolvconf/*|/usr/lib/*)
            bind_file "$source" "$destination" ;;
        *) echo "Error: network config resolves outside system directories: $destination" >&2; return 1 ;;
    esac
}
for config in /etc/resolv.conf /etc/hosts /etc/host.conf \
              /etc/services /etc/protocols; do
    bind_system_file "$config"
done

# HTTPS clients need public CA certificates. These are system files only.
if [[ -d /etc/ssl/certs ]]; then
    add_dir /etc/ssl
    sandbox+=(--ro-bind /etc/ssl/certs /etc/ssl/certs)
    if [[ -f /etc/ssl/certs/ca-certificates.crt ]]; then
        sandbox+=(--setenv SSL_CERT_FILE /etc/ssl/certs/ca-certificates.crt
                  --setenv SSL_CERT_DIR /etc/ssl/certs
                  --setenv CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt)
    fi
fi
if [[ -d /usr/share/ca-certificates ]]; then
    add_dir /usr/share
    sandbox+=(--ro-bind /usr/share/ca-certificates /usr/share/ca-certificates)
fi

# A UTF-8 locale keeps ncurses text usable. It contains system locale data,
# never user files. The terminal emulator itself supplies the font.
for locale_dir in /usr/lib/locale/C.utf8 /usr/lib/locale/C.UTF-8; do
    if [[ -d $locale_dir ]]; then
        add_dir "${locale_dir%/*}"
        sandbox+=(--ro-bind "$locale_dir" "$locale_dir")
        break
    fi
done

locale_name=C.UTF-8
if [[ -d /usr/lib/locale/C.utf8 ]]; then
    locale_name=C.utf8
fi
sandbox+=(--setenv LANG "$locale_name" --setenv LC_ALL "$locale_name"
          --setenv NCURSES_NO_UTF8_ACS 1)

# Ncurses programs need terminal data. Copy one entry into the sandbox's
# private filesystem without exposing the host's terminfo directory.
for terminfo_file in /usr/share/terminfo/x/xterm-256color \
                     /lib/terminfo/x/xterm-256color \
                     /etc/terminfo/x/xterm-256color; do
    if [[ -f $terminfo_file ]]; then
        exec 5< "$terminfo_file"
        add_dir /terminfo/x
        sandbox+=(--perms 0444 --file 5 /terminfo/x/xterm-256color
                  --setenv TERM xterm-256color --setenv TERMINFO /terminfo)
        break
    fi
done

sandbox+=(--perms 0500 --file 4 /o.out)
bwrap "${sandbox[@]}" --remount-ro / --chdir / -- /o.out
