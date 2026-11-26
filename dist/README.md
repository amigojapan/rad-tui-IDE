# FutureShell distribution

This directory is a self-contained copy of the current FutureShell projects.
The existing `projects/phoneapps` and `rad_tui_basic_pkg` directories stay in
place. `python3 dist/rebuild.py` refreshes this copy from them.

| Directory | Contents |
| --- | --- |
| `source/phoneapps` | RAD-TUI JSON projects, C++/C/Python source, and desktop icon metadata |
| `source/rad_tui_basic_pkg` | A copy of the IDE source used by the launchers |
| `bin` | The `rad-tui-ide` command for this distribution |
| `ports/native-python` | Python-backed Bash `.bin` launchers |
| `ports/amd64` | Bash `.bin` launchers and the current x86-64 ELF files in `artifacts` |
| `ports/arm64` | Portable Bash `.bin` launchers that use the JSON/Python runtime |
| `ports/riscv64` | Portable Bash `.bin` launchers that use the JSON/Python runtime |
| `ports/webasm` | Bash `.bin` launchers for a terminal and the WebAssembly site in `site` |

All **launcher** `.bin` files are executable Bash scripts with the same paths
and names as the original apps. Each calls `rad-tui-ide -run` on its matching
JSON file under `source/phoneapps`. `minesweeper.bin` uses `ms.json`. Bash and
Nano have small JSON projects in `source/phoneapps` that open their commands.
The `bin/rad-tui-ide` command runs the bundled IDE source using Python 3, so
an installed PyPI package is not required. On a machine with `rad-tui-ide`
already installed, the command syntax is the same.

Start FutureShell with DT open from any working directory:

```bash
./dist/ports/native-python/phone_shell.bin
```

Or run a project directly through the bundled IDE:

```bash
RAD_TUI_PROJECT_DIR="$PWD/dist/ports/native-python" \
  ./dist/bin/rad-tui-ide -run ./dist/source/phoneapps/phone_shell.json
```

The port launchers set the project directory to their port root (or to `DT`
for `DT.bin`). The phone shell starts `DT/DT.bin` directly, and Home stops the
current app, removes `o.out` from the port root, and starts DT again. DT finds its `DTF` folders, while Future
Browser finds its download runner. That adjustment lives
only in the bundled IDE copy. Direct `rad-tui-ide -run` uses the JSON file's
own directory unless `RAD_TUI_PROJECT_DIR` is set.

Minesweeper, Tic Tac Toe, and Calculator keep their original compact forms and
three-row button borders when the terminal has room. They fit their controls
to shorter terminals. When the keyboard is hidden, Minesweeper uses the
otherwise empty command row to keep its numbers inside three-row cells at
24-row terminal heights. It uses two-row cells only when less space is
available. Minesweeper has a Restart Game button above the board
that clears the board, timer, and game-over state. The amd64 ELF artifacts and
WebAssembly demo use the same layouts. Nano reads the current terminal size
after the on-screen keyboard closes, so it fills the available shell area.
The bundled IDE also reapplies form layouts when its terminal changes size,
including when the phone shell hides its keyboard.
DT uses 🎮 for `games` and 🔨 for `tools`; each icon is a
single two-cell emoji so it does not add a variation-selector cell to a TUI
button.

The ARM64 and RISC-V directories are usable through Python 3 and Bash; they
do **not** contain cross-compiled native ELF executables yet. The amd64
`artifacts/phone_shell.elf` is rebuilt for this distribution: it starts DT and
its Home button removes `o.out` and returns to DT. The other ELF files in
`artifacts` are build outputs; the matching `.bin` launchers remain Bash
scripts as requested. The WebAssembly
browser app is the existing deployable `site`; serve that directory over HTTP
or HTTPS and open `index.html`:

```bash
cd dist/ports/webasm/site
python3 -m http.server 8000
```

`site/tic-tac-toe.webasm.bin` and `site/sample-download.bin` are raw download
data used by the browser, not Bash launchers. The former must retain its URL
and binary format for the existing browser demo to work. A browser cannot run
the Bash port launchers, so it runs the WebAssembly modules in `site` instead.

The amd64 Future Browser runner retains its existing sandbox for downloaded
ELF apps. The other terminal ports use the matching local JSON project when a
download URL names one; they require Python 3, Bash, and the named tool
(`nano` for Nano). All terminal ports require a UTF-8 capable terminal with
ncurses support.
