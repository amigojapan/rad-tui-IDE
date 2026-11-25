#!/usr/bin/env bash
set -euo pipefail

if (( $# != 1 )); then
    echo "Usage: $0 URL-to-app.amd64.bin" >&2
    exit 2
fi

url=$1
url_path=${url%%#*}
url_path=${url_path%%\?*}
filename=${url_path##*/}
if [[ $filename != *.bin ]]; then
    echo 'Error: the URL filename must end in .bin (for example, app.amd64.bin).' >&2
    exit 2
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    # Native amd64 ELF files cannot execute on another OS or CPU. Run the
    # matching local RAD-TUI Python project when one is available.
    app_name=${filename%.bin}
    app_name=${app_name%.amd64}
    project_path=$script_dir/$app_name.json
    if [[ ! -f $project_path ]]; then
        echo "Error: no Python project found for $filename ($project_path)." >&2
        exit 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo 'Error: python3 is required for this platform.' >&2
        exit 1
    fi
    source_dir=$script_dir/../../rad_tui_basic_pkg/src
    if [[ -d $source_dir ]]; then
        export PYTHONPATH="$source_dir${PYTHONPATH:+:$PYTHONPATH}"
    fi
    echo "Running Python version: $app_name" >&2
    exec python3 -m rad_tui_basic.rad_tui_py -run "$project_path"
fi

for tool in wget bwrap readelf; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "Error: $tool is required." >&2
        exit 1
    fi
done

umask 077
download_path=$script_dir/a.out
if [[ -e $download_path || -L $download_path ]]; then
    echo "Error: $download_path already exists. Remove it before downloading." >&2
    exit 1
fi
staged_path=$(mktemp "$script_dir/.a.out.XXXXXXXX")
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
wget --quiet --show-progress --progress=bar:force:noscroll \
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
dynamic_linked=false
if [[ $segments == *INTERP* ]] || [[ $dynamic == *'(NEEDED)'* ]]; then
    dynamic_linked=true
fi

if ! ln -- "$staged_path" "$download_path"; then
    echo "Error: cannot create $download_path." >&2
    exit 1
fi

exec 4< "$download_path"
rm -f -- "$staged_path"
echo 'Running in a read only sandbox...' >&2
sandbox=(--unshare-user --unshare-pid --unshare-ipc --unshare-uts
         --disable-userns --cap-drop ALL --new-session --die-with-parent
         --clearenv --tmpfs / --dir /usr --dir /usr/share --dir /etc
         --perms 0500 --file 4 /a.out)

if [[ $dynamic_linked == true ]]; then
    # Keep the host filesystem hidden except for system libraries. This also
    # supplies the dynamic loader and locale data needed by libc.
    for library_dir in /lib /lib64 /usr/lib /usr/lib64; do
        if [[ -d $library_dir ]]; then
            sandbox+=(--ro-bind "$library_dir" "$library_dir")
        fi
    done
    if [[ -d /usr/local/lib ]]; then
        sandbox+=(--dir /usr/local --ro-bind /usr/local/lib /usr/local/lib)
    fi
elif [[ -d /usr/lib/locale ]]; then
    # Statically linked libc still loads UTF-8 locale data from disk.
    sandbox+=(--dir /usr/lib --ro-bind /usr/lib/locale /usr/lib/locale)
fi

# Fontconfig clients may read fonts. Terminal apps use the host terminal font.
for font_dir in /usr/share/fonts /etc/fonts; do
    if [[ -d $font_dir ]]; then
        sandbox+=(--ro-bind "$font_dir" "$font_dir")
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
        sandbox+=(--dir /terminfo --dir /terminfo/x
                  --perms 0444 --file 5 /terminfo/x/xterm-256color
                  --setenv TERM xterm-256color --setenv TERMINFO /terminfo)
        break
    fi
done

bwrap "${sandbox[@]}" --remount-ro / --chdir / -- /a.out
