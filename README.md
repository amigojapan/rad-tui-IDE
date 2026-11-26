# RAD-TUI 🖥️

**Rapid Application Development - Terminal User Interface**

A Visual Basic 1.0 for MS-DOS inspired visual IDE that runs on Linux. Design forms, place controls, write code, and run your applications - all in the terminal!

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows%20(WSL)-green.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20FreeBASIC-orange.svg)
![Version](https://img.shields.io/badge/version-2.2.0-brightgreen.svg)

## 🎯 Concept

RAD-TUI recreates the magic of early 90s visual programming environments like VB1 for MS-DOS, but for modern Linux terminals. It provides:

- **Visual Form Designer** - Drag and drop controls onto forms
- **Property Editor** - Edit control properties in real-time
- **Code Editor** - Write Python code with syntax highlighting
- **Runtime Mode** - Test your applications instantly
- **Project Management** - Save and load projects as JSON files
- **Menu System** - Design menus with submenus
- **Event System** - Multiple event types (click, change, focus, timer, etc.)
- **File I/O** - Read and write files from your applications
- **Templates** - Start projects from pre-built templates
- **Database** - SQLite integration for data-driven apps (v2.2.0)
- **Network** - HTTP operations and API integration (v2.2.0)
- **Advanced UI** - TreeView, TabControl, Charts, and more (v2.2.0)

## 🚀 Features

### Visual Design Environment
- 🖱️ **Mouse-driven interface** - Point, click, drag, and resize
- 🪟 **Draggable windows** - Move forms and toolboxes freely
- 🎨 **25 control types** including buttons, labels, text boxes, frames, and more
- 📐 **Visual resizing** - Grab handles to resize controls
- ✏️ **Property editing** - Edit names, captions, positions, and dimensions
- 📋 **Control parenting** - Place controls inside frames

### New in v2.2.0 🎉
- 🌳 **TreeView** - Hierarchical data display with expandable nodes
- 📑 **TabControl** - Multi-page interfaces with tabbed navigation
- 📊 **ProgressBar** - Visual progress indication for long operations
- 🎚️ **Slider** - Numeric value selection with dragging
- 🧰 **Toolbar** - Icon button strips for common actions
- 📟 **StatusBar** - Multi-panel information display
- ↔️ **Splitter** - Resizable panel dividers
- 🎨 **ColorPicker** - Color selection with palettes
- 📈 **Chart** - Bar, line, and pie charts for data visualization
- 🗄️ **Database Module** - SQLite connectivity with transactions
- 🌐 **Network Module** - HTTP operations with JSON support
- 🔍 **Regex Module** - Pattern matching and text manipulation
- 🪟 **Custom Dialogs** - User-defined modal dialogs

### New in v2.3.0-dev 🌐 (WebAssembly/Web Export)
- 🌍 **Export to Web** - One-command ` --export-web` turns any `.json` project into a standalone `index.html` + `project.json` bundle
- 🐍 **Pyodide (Python-in-WASM)** - Original `code`/`on_click_*` handlers run unchanged in the browser, DOM-synced via `JSControl`
- 🖥️ **No server required** - `python3 -m http.server` or double-click; offline fallback for calculator/hello_world
- 🔄 **WASM-ready modules** - `database.py` → `sql.js`, `network` → `fetch` polyfill path prepared

### Previous Features (v2.1.0)
- 📝 **TextArea** - Multi-line text editor with scrolling
- 📊 **Grid Control** - Spreadsheet-like data grid
- 🖼️ **Picture Box** - Display ASCII/Unicode art
- 📁 **File I/O** - Open, read, write, and close files
- 📋 **Clipboard** - Copy and paste text
- 🎨 **Templates** - Notepad, Calculator, Database templates
- 🖱️ **Drag & Drop** - Drag data between controls
- 🐛 **Debugger** - Runtime debugging with breakpoints

### Code Development
- 🐍 **Python code-behind** - Write event handlers in Python
- 🌈 **Syntax highlighting** - Keywords, strings, numbers, comments
- ▶️ **Runtime execution** - Run forms with live code execution
- 🐛 **Runtime error display** - See errors in message boxes
- 📝 **Code editor** - Modal editor with cursor navigation
- 🐞 **Debugger** - Breakpoints, stepping, watches

### Event System
- **on_click** - Button and control clicks
- **on_change** - Value changes
- **on_focus/on_blur** - Focus events
- **on_timer** - Timer events
- **on_load/on_close** - Form lifecycle
- **on_menu** - Menu selection
- **on_cell_click/on_cell_edit** - Grid events
- **on_node_click/on_node_expand** - TreeView events (v2.2.0)
- **on_tab_change** - TabControl events (v2.2.0)
- **on_value_change** - Slider/ProgressBar events (v2.2.0)
- **on_color_select** - ColorPicker events (v2.2.0)

## 📁 Project Structure

```
radtui/
├── rad-tui-py.py              # Python v2.2 runtime + project shell (25 controls, DB/Network/Regex/Dialogs)
├── rad-tui-py-compat.py       # Terminal-compatible version
├── rad-tui-BASIC.bas          # FreeBASIC implementation
├── examples/                  # Example projects (18 total)
│   ├── hello_world.json       # Basic greeting
│   ├── calculator.json        # Functional calculator
│   ├── notepad.json           # Text editor
│   ├── database_browser_v22.json  # Database browser (v2.2.0)
│   ├── chart_viewer.json      # Chart demo (v2.2.0)
│   ├── web_api_client.json    # HTTP client (v2.2.0)
│   ├── file_explorer_v22.json # File manager (v2.2.0)
│   ├── tabbed_interface.json  # Tabs demo (v2.2.0)
│   ├── color_picker_demo.json # Colors (v2.2.0)
│   ├── custom_dialog_demo.json # Dialogs (v2.2.0)
│   └── README.md              # Examples documentation
├── docs/                      # Documentation
│   ├── README.md              # Documentation index
│   ├── API_REFERENCE_V22.md   # Complete v2.2.0 API reference
│   ├── DATABASE_TUTORIAL.md   # Database guide (v2.2.0)
│   ├── CHART_CONTROL_GUIDE.md # Chart guide (v2.2.0)
│   ├── NETWORK_GUIDE.md       # Network guide (v2.2.0)
│   ├── ADVANCED_CONTROLS_GUIDE.md # Advanced controls (v2.2.0)
│   ├── PROJECT_FORMAT_V22.md  # Project format (v2.2.0)
│   ├── ROADMAP_V22.md         # v2.2.0 roadmap
│   ├── HISTORY_V22.md         # v2.2.0 release notes
│   └── ...                    # Additional guides
├── src/                       # Source modules (v2.2+)
│   ├── treeview.py            # TreeView control
│   ├── tabcontrol.py          # TabControl
│   ├── progressbar.py         # ProgressBar
│   ├── slider.py              # Slider
│   ├── toolbar.py             # Toolbar
│   ├── statusbar.py           # StatusBar
│   ├── splitter.py            # Splitter
│   ├── colorpicker.py         # ColorPicker
│   ├── chart.py               # Chart
│   ├── database.py            # Database module
│   ├── network.py             # Network module
│   ├── regex.py               # Regex module
│   ├── custom_dialog.py       # Dialogs
│   ├── tui_runner.py          # Curses form runner
│   ├── export_web.py          # Web/WASM exporter (NEW)
│   └── ...                    # + legacy modules at repo root (old/)
├── old/                       # Archived legacy implementations
│   ├── rad-tui-py.py          # Pre-v2.2 designer (unfinished)
│   ├── rad-tui-py-v21*.py     # v2.1 variants
│   └── *.backup               # Backups
├── tests/                     # Testing utilities
├── HISTORY.md                 # Version history
├── HISTORY_V22.md           # Detailed v2.2.0 notes
└── README.md                  # This file
```

## 🎮 How to Run

### Python Version (Recommended)

```bash
# Interactive project shell
python3 rad-tui-py.py

# Launch an example form immediately
python3 rad-tui-py.py --run examples/file_explorer_v22.json

# List examples or run without a terminal
python3 rad-tui-py.py --list-examples
python3 rad-tui-py.py --run --headless examples/chart_viewer.json

# Export to standalone web (WASM) — no rebuild needed
python3 rad-tui-py.py --export-web examples/calculator.json --out dist/calc
python3 -m http.server --directory dist/calc  # open http://localhost:8000

# Inside the shell you can also use:
#   RAD-TUI> open examples/calculator.json
#   RAD-TUI> run

# Terminal-compatible version
python3 rad-tui-py-compat.py
```

### FreeBASIC Version

```bash
fbc rad-tui-BASIC.bas -o rad-tui-BASIC
./rad-tui-BASIC
```

## 🕹️ Quick Start

1. **Add a control**: Click in toolbox, then click on form
2. **Edit properties**: Click in Properties window
3. **Add code**: Double-click control to open code editor
4. **Run**: Click `[RUN ]` in menu bar

## 📋 Available Controls (25 Total)

| Type | Control | Since | Description |
|------|---------|-------|-------------|
| 1 | Label | 2.0 | Static text |
| 2 | Button | 2.0 | Clickable button |
| 3 | TextBox | 2.0 | Text input |
| 4 | CheckBox | 2.0 | Boolean checkbox |
| 5 | RadioButton | 2.0 | Single selection |
| 6 | ListBox | 2.0 | Selection list |
| 7 | ComboBox | 2.0 | Dropdown |
| 8 | Frame | 2.0 | Container |
| 9 | Timer | 2.0 | Background timer |
| 10 | Image | 2.0 | Picture display |
| 11 | Menu | 2.0 | Menu bar |
| 12 | PopupMenu | 2.0 | Context menu |
| 13 | Edit | 2.0 | Text edit |
| 14 | Memo | 2.0 | Text area |
| 15 | TextArea | 2.1 | Multi-line editor |
| 16 | Grid | 2.1 | Data grid |
| **17** | **TreeView** | **2.2** | **Hierarchical tree** |
| **18** | **TabControl** | **2.2** | **Tabbed pages** |
| **19** | **ProgressBar** | **2.2** | **Progress indicator** |
| **20** | **Slider** | **2.2** | **Value slider** |
| **21** | **Toolbar** | **2.2** | **Button toolbar** |
| **22** | **StatusBar** | **2.2** | **Status panels** |
| **23** | **Splitter** | **2.2** | **Panel divider** |
| **24** | **ColorPicker** | **2.2** | **Color selection** |
| **25** | **Chart** | **2.2** | **Data visualization** |

## 🐍 Code Example

```python
def on_click_btnSubmit():
    # Get input
    name = txtName.caption
    
    # Validate
    if len(name) == 0:
        msgbox("Please enter name")
        return
    
    # Database query (v2.2.0)
    db = Database()
    if db.connect("users.db"):
        result = db.execute_query(
            "SELECT * FROM users WHERE name = ?",
            (name,)
        )
        if not result.is_empty():
            lblStatus.caption = "User found!"
        db.disconnect()
    
    # HTTP request (v2.2.0)
    response = http_get(f"https://api.example.com/users/{name}")
    if response.is_success():
        data = response.json()
        chart.add_series("Data").data = data

# TreeView event (v2.2.0)
def on_node_click_treeFiles():
    node = treeFiles.get_selected()
    if node:
        lblStatus.caption = f"Selected: {node.text}"
```

## 📚 Documentation

- **[API_REFERENCE_V22.md](docs/API_REFERENCE_V22.md)** - Complete API reference
- **[DATABASE_TUTORIAL.md](docs/DATABASE_TUTORIAL.md)** - Database guide
- **[CHART_CONTROL_GUIDE.md](docs/CHART_CONTROL_GUIDE.md)** - Chart guide
- **[NETWORK_GUIDE.md](docs/NETWORK_GUIDE.md)** - Network operations
- **[ADVANCED_CONTROLS_GUIDE.md](docs/ADVANCED_CONTROLS_GUIDE.md)** - Advanced controls
- **[TUTORIAL.md](docs/TUTORIAL.md)** - Step-by-step tutorial

## 📋 Example Projects (18 Total)

### v2.2.0 Examples (8 New)
- **database_browser_v22.json** - SQLite database browser
- **chart_viewer.json** - Interactive charts
- **web_api_client.json** - REST API client
- **file_explorer_v22.json** - File manager with TreeView
- **tabbed_interface.json** - Multi-page settings dialog
- **color_picker_demo.json** - Color selection demo
- **custom_dialog_demo.json** - Custom dialogs showcase

### Previous Examples (10)
- notepad.json, calculator.json, csv_viewer.json, etc.

## 🛠️ Requirements

- Python 3.6+
- Terminal with UTF-8 and mouse support (optional)

## 📜 License

MIT License - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

Inspired by Microsoft Visual Basic 1.0 for MS-DOS (1992)

---

**Happy retro-coding!** 🎉
