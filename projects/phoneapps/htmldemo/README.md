# FutureShell WebAssembly demo

The FutureShell screen uses the control positions, captions, palette, button
drawing rules, scrollbar, and keyboard row calculations from
`phoneapps/phone_shell.cpp`. The page boots `futureshell.wasm` automatically
and starts with the native shell layout: Home on
row 0, cyan shell area, command row, and the visible screen keyboard. Home
opens DT and hides the keyboard. The DT desktop includes the `games`,
`internet`, and `tools` folders from `phoneapps/DT/DTF`; `catalog.json` and
the compiled shell catalog are generated from that directory and its `.icons`
files. Calculator, Tic Tac Toe, Minesweeper, Future
Browser, Bash, and Nano screens are available. Calculator and game rules run
in `futureshell.wasm`, compiled with Emscripten from `demo.cpp`. The shell
command state, directory navigation, and application launch decisions run in
the same WebAssembly module. The terminal renderer and browser-specific
controls are in `app.js`. Future Browser downloads a
separate raw WebAssembly tic-tac-toe module and runs it inside the same form.

## Run

The built `futureshell.js` and `futureshell.wasm` are included here. From this directory:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000` in a browser. FutureShell greets you with
`Welcome to FutureShell`, a blank line, and a `$` prompt ready for typing.
The terminal fills the browser viewport, including an enclosing iframe or
other browser container, and recalculates its character grid when resized.
The screen keyboard is visible on startup, as in native FutureShell. Home closes the current app, hides the
keyboard, and opens DT. Click controls or use Tab, arrow keys, and Enter to
select them. The lower keyboard button hides or shows the screen keyboard.
On Android, focusing the input does not request the system keyboard; use
FutureShell's screen keyboard or a physical keyboard instead.
ROM converts romaji to hiragana as you type. In かな mode, tap a kana key
repeatedly within 0.9 seconds to cycle its characters; ゛ and 小 modify the
preceding kana. In either Japanese mode, press Sp (or physical Space) after a
reading to show kanji, hiragana, and katakana candidates. Press Space again or
use arrow keys to cycle, then Ent/Enter to choose; tap a candidate to choose it
directly. Bk/Backspace cancels the selection. The candidate dictionary is
generated from `phone_shell.json` by `build.bash`, with `試験` added as a kanji
synonym for `てすと`.
Select the command row above it and type `help`, `ls`, `cd games`, `open calc`,
or other demo commands.
Open `http://localhost:8000/smoke.html` for an automated browser check of the
WebAssembly boot, shell commands, desktop, and all six app screens.
Future Browser defaults to
`https://amjp.psy-k.org/futureshell/repo/webasm/tic-tac-toe.webasm.bin`.
Upload `../tic-tac-toe.webasm.bin` to that server path. The server must allow
cross-origin requests from the demo page. For a local download test, enter
`http://localhost:8000/tic-tac-toe.webasm.bin`. Enter or GO! starts the game;
Home closes it.

## Install on Android

Publish this entire directory at a secure HTTPS URL, including
`manifest.webmanifest` and the `icons` directory. Open `index.html` in Chrome
on the phone, then choose **Install app** from the browser menu and launch
FutureShell from its home-screen icon. The manifest requests fullscreen mode,
so the installed app uses the screen without Chrome's address bar. The
browser's own tab still shows browser controls.

If you added FutureShell to the home screen before the manifest was published,
remove that old shortcut and install it again after the updated files are on
the server. A plain HTTP URL on another device is not a secure installation
origin; use HTTPS for the phone. `http://localhost` is suitable only when the
server is running on the same device.

To rebuild with Emscripten:

```bash
bash build.bash
```

To rebuild every native phone app and both WebAssembly files from the
repository root:

```bash
bash projects/phoneapps/build-all.bash
```

## Browser limits

The original phone shell uses a Linux pseudoterminal and launches native `.bin`
programs. Browsers cannot run that ELF file, its Bash process, `nano.bin`, or
downloaded amd64 executables directly. This is the first direct WebAssembly
port of FutureShell's command and app model, not a Linux distribution or a
GNU Bash port. Its shell currently supports `help`, `ls`, `pwd`, `cd`, `open`,
`clear`, `echo`, `date`, and a demo response to `bash --version`; it cannot run arbitrary Bash scripts or Linux
commands. The Nano screen is a read-only browser editor, not a compiled GNU
nano. Edits stay in memory: `^O` reports a read-only error, and `^X` reports
the error before a second `^X` discards the changes. Bash, Nano, and Future
Browser focus their input automatically when opened. A real GNU Bash and nano port would need a browser
process, terminal, and file-system layer shared with FutureShell.
Future Browser streams a `.bin` URL with download progress and instantiates it
as WebAssembly. This first downloadable app uses the `ttt_reset`, `ttt_move`,
`ttt_cell`, and `ttt_status_code` exports. ELF files and other modules without
those exports report an error. The built-in game and calculator logic also
runs in WebAssembly.

`build.bash` compiles `../tic-tac-toe-webasm.c` into
`../tic-tac-toe.webasm.bin` for upload and a copy here for local testing. The
`.bin` suffix is for the repository layout; the contents are WebAssembly.
The matching Linux x86-64 upload is `../tic-tac-toe.amd64.bin` for
`repo/amd64/tic-tac-toe.amd64.bin`. The native `../run-downloaded-bin.sh`
executes that ELF on Linux x86-64 and runs `../tic-tac-toe.json` through the
Python RAD-TUI runtime on other systems.

Serve these files over HTTP rather than opening `index.html` as a `file://`
URL; browsers normally block loading `futureshell.wasm` from a local file URL.
