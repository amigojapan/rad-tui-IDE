/* Ncurses-style browser terminal. Calculator and game rules run in demo.wasm. */
(() => {
  'use strict';
  const DEFAULT_URL = 'https://amjp.psy-k.org/futureshell/repo/webasm/tic-tac-toe.webasm.bin';
  const catalog = {
    games: [
      {id: 'minesweeper', icon: '💣🚩', name: 'minesweeper'},
      {id: 'tic-tac-toe', icon: '⭕❌', name: 'tic-tac-toe'}
    ],
    internet: [{id: 'futurebrowser', icon: '🌐', name: 'futurebrowser'}],
    tools: [
      {id: 'bash', icon: '🐚', name: 'bash'},
      {id: 'calc', icon: '🧮', name: 'calc'},
      {id: 'nano', icon: '📃', name: 'nano'}
    ]
  };
  const colors = {
    teal: '#008f93', dark: '#075b5f', light: '#c0c0c0', blue: '#0000aa',
    field: '#e3e3d8', ink: '#101917', white: '#f3f3e9', black: '#000000',
    yellow: '#f2d456', red: '#e5756e', deep: '#053337'
  };
  const canvas = document.getElementById('terminal');
  const ctx = canvas.getContext('2d');
  const input = document.getElementById('terminalInput');
  const statusElement = document.getElementById('status');
  const grid = {cols: 33, rows: 40, cw: 10, ch: 18, width: 330, height: 720};
  const segmenter = new Intl.Segmenter(undefined, {granularity: 'grapheme'});
  const state = {
    wasm: null, forms: null, folder: '', app: 'bash', keyboard: true, mode: 'ABC',
    shift: false, ctrl: false, alt: false, flag: false, focus: 0, symbolReturn: 'ABC',
    edit: '', command: '', url: DEFAULT_URL, note: '', nanoMessage: '',
    browserMessage: '', request: null, downloadedGame: null,
    notice: 'Loading WebAssembly…', menu: '',
    log: ['Starting shell...']
  };
  let hits = [];

  function loadNote() {
    try { return localStorage.getItem('rad-tui-demo-note') || ''; }
    catch (_) { return ''; }
  }
  function wasm(name, result = null, types = [], args = []) {
    return state.wasm.ccall(name, result, types, args);
  }
  function tttBoard() {
    if (!state.downloadedGame) return wasm('ttt_board', 'string');
    return Array.from({length: 9}, (_, index) =>
      String.fromCharCode(state.downloadedGame.ttt_cell(index))).join('');
  }
  function tttStatus() {
    if (!state.downloadedGame) return wasm('ttt_status', 'string');
    return ['Your turn (X)', 'You Win!', 'AI Wins!', 'Draw!'][state.downloadedGame.ttt_status_code()] || 'Game error';
  }
  function tttReset() {
    if (state.downloadedGame) state.downloadedGame.ttt_reset();
    else wasm('ttt_reset');
  }
  function tttMove(index) {
    if (state.downloadedGame) state.downloadedGame.ttt_move(index);
    else wasm('ttt_move', null, ['number'], [index]);
  }
  function notice(message) {
    state.notice = message;
    statusElement.textContent = message;
    draw();
  }
  function fill(x, y, w, h, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x * grid.cw, y * grid.ch, w * grid.cw, h * grid.ch);
  }
  function text(x, y, width, value, color = colors.ink, background = null, align = 'left') {
    if (y < 0 || y >= grid.rows || width <= 0) return;
    if (background) fill(x, y, width, 1, background);
    ctx.save();
    ctx.beginPath();
    ctx.rect(x * grid.cw, y * grid.ch, width * grid.cw, grid.ch);
    ctx.clip();
    ctx.fillStyle = color;
    const graphemes = Array.from(segmenter.segment(String(value)), item => item.segment);
    const cellWidth = glyph => /[\u{1100}-\u{11ff}\u{2e80}-\u{a4cf}\u{ac00}-\u{d7af}\u{1f000}-\u{1faff}]/u.test(glyph) ? 2 : 1;
    const units = graphemes.reduce((sum, glyph) => sum + cellWidth(glyph), 0);
    let start = 0;
    if (align === 'center') start = Math.floor((width - units) / 2);
    if (align === 'right') start = width - units;
    let used = Math.max(0, start);
    for (const glyph of graphemes) {
      const advance = cellWidth(glyph);
      if (used + advance > width) break;
      ctx.fillText(glyph, (x + used) * grid.cw + 1, (y + .76) * grid.ch);
      used += advance;
    }
    ctx.restore();
  }
  function line(y, color = colors.ink) {
    text(0, y, grid.cols, '─'.repeat(grid.cols), color);
  }
  function hit(x, y, w, h, action, data = '') {
    hits.push({x, y, w, h, action, data});
    return hits.length - 1;
  }
  function button(x, y, w, h, label, action, data = '', base = colors.light) {
    if (y < 0 || y + h > grid.rows || w < 3) return;
    hit(x, y, w, h, action, data);
    const fg = base === colors.blue || base === colors.red ? colors.white : colors.ink;
    if (h === 1) {
      fill(x, y, w, 1, base);
      text(x, y, 1, '│', colors.white, colors.light);
      text(x + 1, y, w - 2, label, fg, null, 'center');
      text(x + w - 1, y, 1, '│', colors.ink, colors.light);
    } else {
      fill(x, y, w, h, colors.light);
      fill(x + 1, y + 1, w - 2, h - 2, base);
      text(x, y, 1, '┌', colors.white);
      text(x + 1, y, w - 2, '─'.repeat(w - 2), colors.white);
      text(x + w - 1, y, 1, '┐', colors.ink);
      for (let row = 1; row < h - 1; row++) {
        text(x, y + row, 1, '│', colors.white);
        text(x + w - 1, y + row, 1, '│', colors.ink);
      }
      text(x + 1, y + Math.floor(h / 2), w - 2, label, fg, null, 'center');
      text(x, y + h - 1, 1, '└', colors.white);
      text(x + 1, y + h - 1, w - 2, '─'.repeat(w - 2), colors.ink);
      text(x + w - 1, y + h - 1, 1, '┘', colors.ink);
    }
  }
  function wrap(value, width) {
    const output = [];
    for (const original of String(value).split('\n')) {
      let remaining = original;
      if (!remaining) { output.push(''); continue; }
      while (remaining.length > width) {
        output.push(remaining.slice(0, width));
        remaining = remaining.slice(width);
      }
      output.push(remaining);
    }
    return output;
  }
  function terminalArea() {
    const buttonH = grid.rows >= 32 ? 3 : 1;
    const keyRows = ['かな', 'NAV', 'SYM'].includes(state.mode) ? 4 : 3;
    const keyboardStart = state.keyboard ? grid.rows - (keyRows + 3) * buttonH : -1;
    const toggleY = state.keyboard ? -1 : grid.rows - buttonH;
    const shellH = Math.max(1, (state.keyboard ? keyboardStart : toggleY) - 2);
    return {top: 1, bottom: shellH, shellH, commandY: 1 + shellH,
      keyboardStart, toggleY, buttonH, keyRows, shellW: grid.cols - 1};
  }
  function drawHeader() {
    fill(0, 0, grid.cols, 1, colors.light);
    button(0, 0, 10, 1, '⌂ Home', 'home');
  }
  function drawDesktop(area) {
    fill(0, area.top, area.shellW, area.shellH, colors.light);
    const navW = Math.min(11, Math.max(6, Math.floor(area.shellW / 4)));
    button(0, area.top, navW, 1, '← Back', 'back');
    button(navW, area.top, navW, 1, 'Refresh', 'refresh');
    const pathX = Math.min(area.shellW - 1, navW * 2 + 1);
    text(pathX, area.top, area.shellW - pathX,
      state.folder ? `DTF/${state.folder}` : 'DTF', colors.ink, colors.teal);
    const entries = state.folder ? catalog[state.folder] : Object.keys(catalog).sort();
    const rowH = area.shellH >= 18 ? 3 : 1;
    const columns = Math.max(1, Math.min(4, Math.floor(area.shellW / 20)));
    const gridW = Math.min(area.shellW, columns * 20);
    const x = Math.floor((area.shellW - gridW) / 2);
    const tileW = Math.floor(gridW / columns);
    entries.forEach((entry, index) => {
      const y = area.top + 2 + Math.floor(index / columns) * rowH;
      if (y + rowH - 1 >= area.bottom) return;
      const folder = typeof entry === 'string';
      const label = folder ? `${entry === 'internet' ? '🌐' : '🗂️'} ${entry}` : `${entry.icon} ${entry.name}`;
      button(x + (index % columns) * tileW, y, tileW, rowH,
        label, folder ? 'folder' : 'app', folder ? entry : entry.id);
    });
    text(navW, area.bottom, area.shellW - navW * 2,
      `${entries.length} items  •  page 1/1`, colors.ink, colors.teal);
  }
  function drawBash(area) {
    const all = state.log.flatMap(entry => wrap(entry, area.shellW));
    const height = Math.max(1, area.shellH);
    const visible = all.slice(-height);
    visible.forEach((entry, index) => text(0, area.top + index, area.shellW, entry));
  }
  function drawProjectForm(name, area) {
    const form = state.forms[name];
    let formW = form.w, formH = form.h, formX = form.x, formY = form.y;
    if (name === 'futurebrowser') {
      formW = area.shellW; formH = area.shellH; formX = formY = 0;
    }
    const ox = Math.max(0, Math.min(formX, area.shellW - formW));
    const oy = Math.max(0, Math.min(formY, area.shellH - formH));
    fill(ox, area.top + oy, formW, formH, colors.light);

    for (const control of form.controls) {
      if (control.tool_type === 14 || control.x < 0 || control.y < 0) continue;
      let {x, y, w, h} = control;
      let caption = control.caption;
      if (name === 'futurebrowser') {
        if (control.name_id === 'lbl_url' || control.name_id === 'txt_url') w = Math.max(1, formW - 4);
        if (control.name_id === 'btn_go') x = Math.max(0, Math.floor((formW - 7) / 2));
      }
      if (name === 'calc' && control.name_id === 'display') caption = wasm('calc_display', 'string');
      if (name === 'tic-tac-toe') {
        if (control.name_id === 'lbl_status') caption = tttStatus();
        else if (/^btn[0-8]$/.test(control.name_id))
          caption = tttBoard()[Number(control.name_id.slice(3))];
      }
      if (name === 'minesweeper') {
        if (control.name_id === 'face_txt')
          caption = wasm('ms_status', 'string') === 'game over' ? '(T_T)' : '(^_^)';
        else if (control.name_id === 'time_txt') caption = String(wasm('ms_seconds', 'number'));
        else if (/^b[0-9]_[0-9]$/.test(control.name_id)) {
          const index = Number(control.name_id[1]) * 10 + Number(control.name_id[3]);
          const mark = wasm('ms_board', 'string')[index];
          caption = mark === '.' ? '' : mark;
        }
      }
      if (name === 'futurebrowser' && control.name_id === 'txt_url') caption = state.url;
      const cx = ox + x, cy = area.top + oy + y;
      if (control.tool_type === 3) {
        let action = '', data = '';
        if (name === 'calc') { action = 'calc'; data = caption; }
        else if (name === 'tic-tac-toe') {
          action = control.name_id === 'btn_reset' ? 'tttReset' : 'ttt';
          data = control.name_id.slice(3);
        } else if (name === 'minesweeper') {
          action = 'mine';
          data = String(Number(control.name_id[1]) * 10 + Number(control.name_id[3]));
        } else if (name === 'futurebrowser') action = 'go';
        const base = name === 'minesweeper' && caption === '*' ? colors.red :
          control.bg_color === 13 ? colors.blue : colors.light;
        button(cx, cy, w, h, caption, action, data, base);
      } else if (control.tool_type === 9 || control.tool_type === 13) {
        for (let row = 0; row < h; row++) {
          fill(cx, cy + row, w, 1, colors.teal);
          text(cx, cy + row, w, String(caption).split('\n')[row] || '');
        }
        if (control.name_id === 'txt_url') hit(cx, cy, w, h, 'edit', 'url');
      }
    }
    if (form.menus.length) {
      let x = 1;
      for (const label of form.menus) {
        const width = label.length + 2;
        text(x, area.top, width, ` ${label} `, colors.white, colors.blue);
        hit(x, area.top, width, 1, 'menu', label);
        x += label.length + 3;
      }
      if (state.menu) {
        const menuX = state.menu === 'View' ? 1 : 8;
        const label = state.menu === 'View' ? 'Standard' : 'About';
        button(menuX, area.top + 1, 15, 3, label, 'menuItem', label);
      }
    }
    if (name === 'futurebrowser' && state.browserMessage)
      wrap(state.browserMessage, Math.max(1, area.shellW - 4)).slice(0, 4)
        .forEach((line, index) => text(2, area.top + 9 + index, area.shellW - 4, line));
  }
  function drawNano(area) {
    const w = area.shellW;
    text(0, area.top, w, '       New Buffer', colors.ink, colors.light);
    const lines = state.note.split('\n').flatMap(value => wrap(value, w));
    lines.slice(0, Math.max(0, area.shellH - 4)).forEach((value, index) => {
      if (value) text(0, area.top + 1 + index, Math.min(w, value.length),
        value, colors.white, colors.black);
    });
    hit(0, area.top + 1, w, Math.max(1, area.shellH - 4), 'edit', 'note');
    if (state.edit === 'note') {
      const row = Math.min(area.shellH - 4, Math.max(1, lines.length));
      text(0, area.top + row, 1, '▌', colors.white, colors.black);
    }
    const statusY = area.top + area.shellH - 3;
    text(0, statusY, w, state.nanoMessage || 'Welcome to nano.  For basic help',
      colors.ink, colors.light);
    const shortcuts = [
      [['^G','Help','nanoHelp'],['^O','Write Out','saveNote'],['^W','Where Is','nanoSearch']],
      [['^X','Exit','nanoExit'],['^R','Read File','loadNote'],['^\\','Replace','nanoReplace']]
    ];
    shortcuts.forEach((row, rowIndex) => row.forEach(([key, label, action], index) => {
      const x = Math.floor(index * w / 3);
      const end = Math.floor((index + 1) * w / 3);
      text(x, statusY + 1 + rowIndex, 2, key, colors.ink, colors.light);
      text(x + 2, statusY + 1 + rowIndex, end - x - 2,
        ' ' + label, colors.white, colors.black);
      hit(x, statusY + 1 + rowIndex, end - x, 1, action);
    }));
  }
  function drawKeyboard(area) {
    const keyboardW = Math.min(30, grid.cols);
    const left = Math.max(0, Math.floor((grid.cols - keyboardW) / 2));
    const place = (labels, y, action, values = labels, bases = []) => {
      let x = left;
      labels.forEach((label, index) => {
        const w = Math.floor(keyboardW / labels.length) + (index < keyboardW % labels.length ? 1 : 0);
        button(x, y, w, area.buttonH, label, action, values[index], bases[index] || colors.light);
        x += w;
      });
    };
    if (!state.keyboard) {
      place([`↑ Keyboard ${state.mode}`], area.toggleY, 'keyboard');
      return;
    }
    const modes = ['ABC', '123', 'かな', 'ROM', 'NAV'];
    place(modes, area.keyboardStart, 'mode', modes,
      modes.map(mode => mode === state.mode ? colors.blue : colors.light));
    const modY = area.keyboardStart + area.buttonH;
    place(['Ctrl', state.shift ? 'Shift' : 'Shift', 'Alt', '↓'], modY,
      'key', ['Ctrl', 'Shift', 'Alt', 'Hide'],
      [state.ctrl ? colors.blue : colors.light,
        state.shift ? colors.blue : colors.light,
        state.alt ? colors.blue : colors.light, colors.light]);
    const keyY = modY + area.buttonH;
    let rows;
    if (state.mode === 'ABC' || state.mode === 'ROM') {
      rows = ['qwertyuiop', 'asdfghjkl', 'zxcvbnm'].map(row => Array.from(row));
    } else if (state.mode === 'SYM') {
      const labels = ['!','@','#','$','%','^','&','*','(',')','_','+','{','}','|','~',
        '`','-','=','[',']','\\',';','\'',',','.','/',':','\"','<','>','?'];
      rows = [labels.slice(0,8), labels.slice(8,16), labels.slice(16,24), labels.slice(24,32)];
    } else if (state.mode === '123') {
      const labels = Array.from('1234567890');
      rows = [labels.slice(0,3), labels.slice(3,6), labels.slice(6,10)];
    } else if (state.mode === 'NAV') {
      const labels = ['←','↑','→','↓','Home','End','PgUp','PgDn','Del','Ins','F1','F2'];
      rows = [labels.slice(0,3), labels.slice(3,6), labels.slice(6,9), labels.slice(9,12)];
    } else {
      const labels = ['あ','か','さ','た','な','は','ま','や','ら','゛','わ','小'];
      rows = [labels.slice(0,3), labels.slice(3,6), labels.slice(6,9), labels.slice(9,12)];
    }
    rows.forEach((row, index) => place(row, keyY + index * area.buttonH, 'key'));
    place(['Sp','Bk','Ent','Tab','Esc','SYM'], keyY + area.keyRows * area.buttonH,
      'key', ['Sp','Bk','Ent','Tab','Esc','SYM'],
      [colors.light, colors.light, colors.light, colors.light, colors.light,
        state.mode === 'SYM' ? colors.blue : colors.light]);
  }
  function drawCommand(area) {
    const y = area.commandY;
    fill(0, y, grid.cols, 1, colors.teal);
    text(0, y, grid.cols, state.command + (state.edit === 'command' ? '▌' : ''));
    hit(0, y, grid.cols, 1, 'edit', 'command');
  }
  function draw() {
    if (!ctx || grid.rows < 18) return;
    hits = [];
    ctx.font = `${Math.max(12, Math.round(grid.cw * 1.68))}px "DejaVu Sans Mono", "Liberation Mono", monospace`;
    ctx.textBaseline = 'alphabetic';
    fill(0, 0, grid.cols, grid.rows, colors.light);
    drawHeader();
    const area = terminalArea();
    fill(0, area.top, grid.cols, area.shellH, colors.teal);
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, area.top * grid.ch, area.shellW * grid.cw, area.shellH * grid.ch);
    ctx.clip();
    if (!state.wasm || !state.forms) text(0, area.top, grid.cols - 1, 'Starting shell...');
    else if (!state.app) drawDesktop(area);
    else if (['calc', 'tic-tac-toe', 'minesweeper', 'futurebrowser'].includes(state.app))
      drawProjectForm(state.app, area);
    else if (state.app === 'bash') drawBash(area);
    else if (state.app === 'nano') drawNano(area);
    ctx.restore();
    for (let y = area.top; y <= area.bottom; y++)
      text(grid.cols - 1, y, 1, '▒', colors.ink, colors.teal);
    drawCommand(area);
    drawKeyboard(area);
    if (state.focus >= hits.length) state.focus = 0;
    canvas.dataset.screen = state.app || 'DT';
    canvas.dataset.folder = state.folder;
    canvas.dataset.keyboard = state.keyboard ? 'visible' : 'hidden';
    canvas.dataset.downloaded = state.downloadedGame ? 'yes' : 'no';
    canvas.dataset.board = state.app === 'tic-tac-toe' ? tttBoard() : '';
    const detail = state.app === 'calc' ? ` Display ${wasm('calc_display', 'string')}.` :
      state.app === 'tic-tac-toe' ? ` ${tttStatus()}.` :
      state.app === 'minesweeper' ? ` ${wasm('ms_status', 'string')}. Flags ${Array.from(wasm('ms_board', 'string')).filter(cell => cell === 'F').length}.` : '';
    canvas.setAttribute('aria-label', `Phone Shell terminal. ${state.app || 'DT desktop'} in DTF${state.folder ? '/' + state.folder : ''}.${detail} Tab selects controls; Enter activates. ${state.notice}`);
  }
  function resize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    grid.width = rect.width;
    grid.height = rect.height;
    grid.cols = Math.max(33, Math.min(72, Math.floor(rect.width / 10.5)));
    grid.cw = rect.width / grid.cols;
    grid.rows = Math.max(18, Math.floor(rect.height / (grid.cw * 1.72)));
    grid.ch = rect.height / grid.rows;
    canvas.dataset.cols = String(grid.cols);
    canvas.dataset.rows = String(grid.rows);
    draw();
  }
  function openApp(id) {
    if (!Object.values(catalog).flat().some(item => item.id === id)) return;
    leaveApp();
    state.app = id;
    state.focus = 0;
    state.menu = '';
    if (id === 'calc') wasm('calc_reset');
    if (id === 'tic-tac-toe') tttReset();
    if (id === 'minesweeper') { wasm('ms_reset'); state.flag = false; }
    if (id === 'nano') { state.note = ''; state.nanoMessage = ''; }
    draw();
  }
  function leaveApp() {
    if (state.request) { state.request.abort(); state.request = null; }
    state.downloadedGame = null;
    state.app = null;
    state.menu = '';
    state.edit = '';
    input.blur();
  }
  function home() {
    leaveApp();
    state.folder = '';
    state.keyboard = false;
    state.command = '';
    state.focus = 0;
    notice('Home · DT loaded');
  }
  function focusEdit(target) {
    if (target === 'readonly') return;
    state.edit = target;
    input.value = state[target];
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
    draw();
  }
  function saveNote() {
    try {
      localStorage.setItem('rad-tui-demo-note', state.note);
      state.nanoMessage = 'Wrote 1 line';
      notice('Nano · saved in this browser');
    } catch (_) { state.nanoMessage = 'Browser storage unavailable'; notice(state.nanoMessage); }
  }
  function runCommand(raw) {
    const command = raw.trim();
    state.command = '';
    input.value = '';
    if (!command) { draw(); return; }
    state.log.push(`$ ${command}`);
    const [verb, ...rest] = command.split(/\s+/);
    const arg = rest.join(' ');
    if (command === './DT/DT.bin' || command === 'DT' || command === 'home') { home(); return; }
    if (verb === 'help') state.log.push('help ls pwd cd <folder> open <app> clear echo <text> date');
    else if (verb === 'pwd') state.log.push('/phoneapps/DT/DTF' + (state.folder ? '/' + state.folder : ''));
    else if (verb === 'ls') state.log.push(state.folder ? catalog[state.folder].map(item => item.name + '.bin').join('  ') : Object.keys(catalog).join('  '));
    else if (verb === 'cd' && (arg === '..' || arg === '/')) { state.folder = ''; state.log.push('DTF'); }
    else if (verb === 'cd' && Object.prototype.hasOwnProperty.call(catalog, arg)) { state.folder = arg; state.log.push(`DTF/${arg}`); }
    else if (verb === 'cd') state.log.push(`No such folder: ${arg}`);
    else if (verb === 'echo') state.log.push(arg);
    else if (verb === 'date') state.log.push(new Date().toString());
    else if (verb === 'clear') state.log = [];
    else {
      const requested = verb === 'open' ? arg : verb;
      const app = Object.values(catalog).flat().find(item => item.id === requested || item.name === requested || item.name + '.bin' === requested);
      if (app) { openApp(app.id); return; }
      state.log.push(`Command not found: ${command}`);
    }
    if (state.log.length > 100) state.log.splice(0, state.log.length - 100);
    leaveApp();
    state.app = 'bash';
    draw();
  }
  function browserMessage(message) { state.browserMessage = message; notice(message); }
  async function go() {
    state.url = state.edit === 'url' ? input.value.trim() : state.url.trim();
    let parsed;
    try { parsed = new URL(state.url); }
    catch (_) { browserMessage('Enter an HTTP(S) URL ending in .bin'); return; }
    if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.pathname.endsWith('.bin')) {
      browserMessage('Enter an HTTP(S) URL ending in .bin'); return;
    }
    if (state.request) state.request.abort();
    const controller = new AbortController();
    state.request = controller;
    browserMessage('Connecting…');
    try {
      const response = await fetch(state.url, {signal: controller.signal});
      if (!response.ok) { browserMessage(response.status === 404 ? '404 not found' : `HTTP ${response.status}`); return; }
      const total = Number(response.headers.get('content-length')) || 0;
      let received = 0;
      const chunks = [];
      if (response.body) {
        const reader = response.body.getReader();
        while (true) {
          const {done, value} = await reader.read();
          if (done) break;
          received += value.byteLength;
          if (received > 16 * 1024 * 1024) throw new Error('WebAssembly file exceeds 16 MiB');
          chunks.push(value);
          browserMessage(total ? `Downloading ${Math.min(100, Math.round(received * 100 / total))}% · ${received} bytes` : `Downloading ${received} bytes`);
        }
      } else {
        const data = new Uint8Array(await response.arrayBuffer());
        received = data.byteLength;
        if (received > 16 * 1024 * 1024) throw new Error('WebAssembly file exceeds 16 MiB');
        chunks.push(data);
      }
      if (controller.signal.aborted || state.request !== controller) return;
      const bytes = new Uint8Array(received);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
      browserMessage(`Downloaded ${received} bytes. Starting WebAssembly…`);
      const {instance} = await WebAssembly.instantiate(bytes, {});
      const game = instance.exports;
      if (!['ttt_reset', 'ttt_move', 'ttt_cell', 'ttt_status_code'].every(name => typeof game[name] === 'function'))
        throw new Error('Downloaded WebAssembly is not a tic-tac-toe app');
      if (controller.signal.aborted || state.request !== controller) return;
      leaveApp();
      state.downloadedGame = game;
      if (typeof game.ttt_seed === 'function') game.ttt_seed(Date.now() >>> 0);
      game.ttt_reset();
      state.app = 'tic-tac-toe';
      notice('Running downloaded WebAssembly · Home closes it');
    } catch (error) {
      if (error.name !== 'AbortError' && !controller.signal.aborted) {
        const detail = error instanceof WebAssembly.CompileError || error instanceof WebAssembly.LinkError ?
          'Downloaded file is not compatible WebAssembly' :
          error instanceof TypeError ? 'Request failed; server may block CORS.' : error.message;
        browserMessage(detail);
      }
    } finally {
      if (state.request === controller) state.request = null;
    }
  }
  function activate(action, data = '', rightClick = false) {
    if ((!state.wasm || !state.forms) && !['home', 'keyboard'].includes(action)) return;
    if (action === 'home') home();
    else if (action === 'keyboard') { state.keyboard = !state.keyboard; draw(); }
    else if (action === 'back') { if (state.app) leaveApp(); else state.folder = ''; draw(); }
    else if (action === 'refresh') draw();
    else if (action === 'folder') { state.folder = data; draw(); }
    else if (action === 'app') openApp(data);
    else if (action === 'edit') focusEdit(data);
    else if (action === 'command') runCommand(state.command);
    else if (action === 'calc') { wasm('calc_press', 'string', ['string'], [({'÷':'/', '×':'*', '−':'-'})[data] || data]); draw(); }
    else if (action === 'ttt') { tttMove(Number(data)); draw(); }
    else if (action === 'tttReset') { tttReset(); draw(); }
    else if (action === 'msReset') { wasm('ms_reset'); draw(); }
    else if (action === 'flagMode') { state.flag = !state.flag; draw(); }
    else if (action === 'mine') { wasm(rightClick || state.flag ? 'ms_flag' : 'ms_reveal', null, ['number'], [Number(data)]); draw(); }
    else if (action === 'saveNote') saveNote();
    else if (action === 'nanoExit') { leaveApp(); draw(); }
    else if (action === 'loadNote') { state.note = loadNote(); state.nanoMessage = 'Read from browser storage'; draw(); }
    else if (action === 'nanoHelp') { state.nanoMessage = '^O saves  ^X exits  ^R reads'; draw(); }
    else if (action === 'nanoSearch') { state.nanoMessage = 'Search is not available in this web demo'; draw(); }
    else if (action === 'nanoReplace') { state.nanoMessage = 'Replace is not available in this web demo'; draw(); }
    else if (action === 'clearNote') { state.note = ''; if (state.edit === 'note') input.value = ''; draw(); }
    else if (action === 'go') go();
    else if (action === 'menu') { state.menu = state.menu === data ? '' : data; draw(); }
    else if (action === 'menuItem') { state.menu = ''; notice(data === 'About' ? 'TUI Python Calculator · rad-tui-IDE' : 'Already in Standard view.'); }
    else if (action === 'mode') { state.mode = data; draw(); }
    else if (action === 'key') virtualKey(data);
  }
  function virtualKey(key) {
    if (key === 'Hide') { state.keyboard = false; draw(); return; }
    if (key === 'SYM') {
      if (state.mode === 'SYM') state.mode = state.symbolReturn;
      else { state.symbolReturn = state.mode; state.mode = 'SYM'; }
      draw();
      return;
    }
    if (key === 'Ctrl') { state.ctrl = !state.ctrl; notice(`Ctrl ${state.ctrl ? 'on' : 'off'}`); return; }
    if (key === 'Alt') { state.alt = !state.alt; notice(`Alt ${state.alt ? 'on' : 'off'}`); return; }
    if (key === 'Shift') { state.shift = !state.shift; notice(`Shift ${state.shift ? 'on' : 'off'}`); return; }
    if (state.ctrl && state.app === 'nano') {
      const shortcut = {o:'saveNote',x:'nanoExit',r:'loadNote',g:'nanoHelp'}[key.toLowerCase()];
      if (shortcut) { state.ctrl = false; activate(shortcut); return; }
    }
    if (key === 'Esc') { if (state.app) { leaveApp(); draw(); } return; }
    if (!state.edit) focusEdit('command');
    if (key === 'Ent') {
      if (state.edit === 'command') runCommand(input.value);
      else if (state.edit === 'url') go();
      else input.setRangeText('\n', input.selectionStart, input.selectionEnd, 'end');
      return;
    }
    if (key === 'Bk' || key === 'Del') input.setRangeText('', Math.max(0, input.selectionStart - (key === 'Bk' ? 1 : 0)),
      Math.min(input.value.length, input.selectionEnd + (key === 'Del' ? 1 : 0)), 'end');
    else if (key === '←' || key === '→') {
      const position = Math.max(0, Math.min(input.value.length, input.selectionStart + (key === '←' ? -1 : 1)));
      input.setSelectionRange(position, position);
    } else if (key === 'Home') input.setSelectionRange(0, 0);
    else if (key === 'End') input.setSelectionRange(input.value.length, input.value.length);
    else if (key === 'Sp') input.setRangeText(' ', input.selectionStart, input.selectionEnd, 'end');
    else if (key === 'Tab') input.setRangeText('\t', input.selectionStart, input.selectionEnd, 'end');
    else if (key.length === 1) input.setRangeText(state.shift ? key.toUpperCase() : key, input.selectionStart, input.selectionEnd, 'end');
    input.dispatchEvent(new Event('input'));
    state.shift = false;
  }
  function point(event) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: Math.floor((event.clientX - rect.left) / grid.cw),
      y: Math.floor((event.clientY - rect.top) / grid.ch)
    };
  }
  function click(event, rightClick = false) {
    const {x, y} = point(event);
    const index = hits.findLastIndex(item => x >= item.x && x < item.x + item.w && y >= item.y && y < item.y + item.h);
    if (index < 0) { canvas.focus(); return; }
    state.focus = index;
    const item = hits[index];
    activate(item.action, item.data, rightClick);
    if (item.action !== 'edit') canvas.focus();
  }
  canvas.addEventListener('click', event => click(event));
  canvas.addEventListener('contextmenu', event => { event.preventDefault(); click(event, true); });
  input.addEventListener('input', () => { if (state.edit) { state[state.edit] = input.value; draw(); } });
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && state.edit !== 'note') {
      event.preventDefault();
      if (state.edit === 'command') runCommand(input.value);
      else if (state.edit === 'url') go();
    } else if (event.key === 'Escape') { event.preventDefault(); state.edit = ''; input.blur(); canvas.focus(); draw(); }
    else if (event.key === 'Tab') { event.preventDefault(); state.edit = ''; input.blur(); canvas.focus(); state.focus = (state.focus + 1) % hits.length; draw(); }
    else if (event.ctrlKey && state.edit === 'note') {
      const shortcut = {o:'saveNote',s:'saveNote',x:'nanoExit',r:'loadNote'}[event.key.toLowerCase()];
      if (shortcut) { event.preventDefault(); activate(shortcut); }
    }
  });
  canvas.addEventListener('keydown', event => {
    if (event.key === 'Tab') { event.preventDefault(); state.focus = (state.focus + (event.shiftKey ? hits.length - 1 : 1)) % hits.length; draw(); }
    else if (event.key === 'ArrowDown' || event.key === 'ArrowRight') { event.preventDefault(); state.focus = (state.focus + 1) % hits.length; draw(); }
    else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') { event.preventDefault(); state.focus = (state.focus + hits.length - 1) % hits.length; draw(); }
    else if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); const item = hits[state.focus]; if (item) activate(item.action, item.data); }
    else if (event.key === 'Escape') { event.preventDefault(); activate('back'); }
    else if (event.key.length === 1 && !event.ctrlKey && !event.altKey) { event.preventDefault(); focusEdit('command'); input.setRangeText(event.key, input.selectionStart, input.selectionEnd, 'end'); input.dispatchEvent(new Event('input')); }
  });
  window.addEventListener('resize', resize);
  new ResizeObserver(resize).observe(canvas);
  resize();
  if (typeof createPhoneDemo !== 'function') { notice('demo.js missing; run build.bash'); return; }
  Promise.all([
    createPhoneDemo({locateFile: file => file}),
    fetch('forms.json').then(response => {
      if (!response.ok) throw new Error('forms.json could not be loaded');
      return response.json();
    })
  ]).then(([instance, forms]) => {
    state.wasm = instance;
    state.forms = forms;
    wasm('calc_reset'); wasm('ttt_reset'); wasm('ms_reset');
    notice('WebAssembly ready · Tab, arrows, Enter and mouse work');
    canvas.focus();
  }).catch(error => notice('WebAssembly load failed: ' + error.message));
})();
