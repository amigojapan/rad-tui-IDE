# Phone Shell WebAssembly demo

The Phone Shell screen uses the control positions, captions, palette, button
drawing rules, scrollbar, and keyboard row calculations from
`phoneapps/phone_shell.cpp`. It starts with the native shell layout: Home on
row 0, cyan shell area, command row, and the visible screen keyboard. Home
opens DT and hides the keyboard. The DT desktop includes the `games`,
`internet`, and `tools` folders from `phoneapps/DT/DTF`. Calculator, Tic Tac Toe, Minesweeper, Future
Browser, Bash, and Nano screens are available. Calculator and game rules run
in `demo.wasm`, compiled with Emscripten from `demo.cpp`. The terminal renderer
and browser-specific controls are in `app.js`. Future Browser downloads a
separate raw WebAssembly tic-tac-toe module and runs it inside the same form.

## Run

The built `demo.js` and `demo.wasm` are included here. From this directory:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000` in a browser. The screen keyboard is visible on
startup, as in native Phone Shell. Home closes the current app, hides the
keyboard, and opens DT. Click controls or use Tab, arrow keys, and Enter to
select them. The lower keyboard button hides or shows the screen keyboard.
Select the command row above it and type `help`, `ls`, `cd games`, `open calc`,
or other demo commands.
Open `http://localhost:8000/smoke.html` for an automated browser check of the
desktop and all six app screens.
Future Browser defaults to
`https://amjp.psy-k.org/futureshell/repo/webasm/tic-tac-toe.webasm.bin`.
Upload `../tic-tac-toe.webasm.bin` to that server path. The server must allow
cross-origin requests from the demo page. For a local download test, enter
`http://localhost:8000/tic-tac-toe.webasm.bin`. Enter or GO! starts the game;
Home closes it.

To rebuild with Emscripten:

```bash
bash build.bash
```

## Browser limits

The original phone shell uses a Linux pseudoterminal and launches native `.bin`
programs. Browsers cannot run its Bash process, `nano.bin`, or downloaded
amd64 Linux executables. The Bash and Nano screens here are browser versions:
the shell supports a small command set, and Nano saves text in localStorage.
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
URL; browsers normally block loading `demo.wasm` from a local file URL.
