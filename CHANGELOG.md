# RAD-TUI Python Edition - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.2.0] - 2024-01-15

### 🎉 Major Release - v2.2.0 "Advanced Controls & Connectivity"

This release brings 9 new UI controls, 4 powerful modules, and significant enhancements for building data-driven terminal applications.

### ✨ Added

#### New UI Controls (9)

- **TreeView** (Type 17) - Hierarchical tree display with expand/collapse, icons, and selection
  - TreeNode objects with parent/child relationships
  - Indentation with `[+]/[-]` expand/collapse indicators
  - Icon support and tag storage for custom data

- **TabControl** (Type 18) - Multi-page tabbed container
  - Horizontal and vertical tab orientations
  - TabPage containers for organizing controls
  - Close button support and programmatic tab switching

- **ProgressBar** (Type 19) - Visual progress indicator
  - Horizontal and vertical orientations
  - Configurable range and step increments
  - Percentage display and completion detection

- **Slider** (Type 20) - Interactive value selector
  - Mouse and keyboard input support
  - Tick marks and custom step increments
  - Percentage-based value calculation

- **Toolbar** (Type 21) - Command button container
  - Button, separator, and toggle button types
  - Icon and tooltip support
  - Horizontal and vertical layouts

- **StatusBar** (Type 22) - Multi-panel status display
  - Multiple status panels with auto-sizing
  - Simple text mode for basic usage
  - Panel text alignment options

- **Splitter** (Type 23) - Resizable panel divider
  - Horizontal and vertical orientations
  - Percentage-based positioning with constraints
  - Runtime position adjustment

- **ColorPicker** (Type 24) - Color selection control
  - RGB color model with hex conversion
  - Built-in color palette
  - Color clamping and validation

- **Chart** (Type 25) - Data visualization
  - Bar, line, and pie chart types
  - Multiple data series with auto-scaling
  - Legend, grid, and axis labels

#### New Modules (4)

- **Database Module** - SQLite connectivity
  - Connection management with parameterized queries
  - Transaction support (begin/commit/rollback)
  - QueryResult objects with column metadata
  - SQL injection protection via parameter binding

- **Network Module** - HTTP operations
  - GET/POST/PUT/DELETE request methods
  - Automatic JSON parsing for responses
  - Download progress callbacks
  - Timeout and redirect handling

- **Regex Module** - Pattern matching
  - Search, match, find_all operations
  - Replace with capture groups
  - Split functionality
  - Pre-compiled pattern caching

- **Custom Dialog Module** - Modal dialogs
  - Custom layout support with control placement
  - Modal and non-modal modes
  - DialogResult enumeration (OK, Cancel, Yes, No)
  - Value storage and retrieval

#### Documentation (12 files)

- `API_REFERENCE_V22.md` - Complete API documentation
- `DATABASE_TUTORIAL.md` - Step-by-step database guide
- `CHART_CONTROL_GUIDE.md` - Chart visualization tutorial
- `NETWORK_GUIDE.md` - HTTP operations guide
- `ADVANCED_CONTROLS_GUIDE.md` - TreeView, TabControl, etc.
- `PROJECT_FORMAT_V22.md` - JSON format specification
- `HISTORY_V22.md` - Detailed release notes
- `MIGRATION_GUIDE_V22.md` - v2.1.0 to v2.2.0 migration
- `QUICK_REFERENCE_V22.md` - Quick reference card
- `V22_EXAMPLES_SUMMARY.md` - Example project overview

#### Example Projects (8)

- `database_browser_v22.json` - Database connectivity demo
- `chart_viewer.json` - Data visualization with multiple chart types
- `web_api_client.json` - REST API integration
- `file_explorer_v22.json` - TreeView-based file browser
- `tabbed_interface.json` - Multi-tab application layout
- `color_picker_demo.json` - Color selection interface
- `custom_dialog_demo.json` - Custom dialog creation

#### Testing

- Comprehensive test suite (`test_v22_features.py`)
- 95 unit tests with 100% pass rate
- In-memory SQLite testing
- Mock HTTP response testing
- Integration tests for all example projects

### 🔧 Changed

- **Main Application** (`rad-tui-py-v22.py`)
  - Integrated all 12 new modules
  - Control types 17-25 registered in toolbox
  - Runtime namespace extended with database/network/regex functions
  - Event handlers wired for all new control events
  - Rendering dispatch updated for new control types

### 🔄 Deprecated

- None

### 🗑️ Removed

- None

### 🐛 Fixed

- None (initial v2.2.0 release)

### 🔒 Security

- Database module uses parameterized queries to prevent SQL injection
- Network module validates URLs and handles timeouts properly
- Regex module safely handles invalid patterns

### 📊 Performance

- Chart rendering optimized for terminal display
- Database connection pooling support
- Regex pattern compilation caching

---

## [Unreleased] - Web/WASM Export (2.3.0-dev)

### ✨ Added

- **Web Exporter** (`src/export_web.py`) — `python3 rad-tui-py.py --export-web <project.json> [--out dist]` generates `index.html` + `app.js` + `style.css` + `project.json` (verified on `calculator.json`, `hello_world_simple.json`).
- **Pyodide runtime** — Original Python `code`/`on_click_*`/`on_change_*` runs in-browser via `Pyodide v0.26.4` (WASM); controls bridged as `JSControl` with `js.updateControl` sync; `msgbox`/`end_app`/`input_box` proxied to DOM.
- **Curses → DOM mapping** — Absolute-positioned CSS mimics TUI (`x*8, y*18`); Button/Label/TextBox/CheckBox/ListBox/Frame/Memo/Grid initial renderers; server-side escaping (`json.dumps`) fixed `SyntaxError: unexpected character after line continuation` and button-order bug.
- **Fallback mode** — Offline JS fallback for calculator/hello_world when Pyodide unavailable.

### 🔧 Changed

- `rad-tui-py.py:1765` CLI now exposes `--export-web`/`--out` (README “How to Run” updated, project tree documents `export_web.py` + `old/`).

---

## [2.1.0] - 2024-01-14

### ✨ Added

#### Core Features
- Project-based application development
- JSON project file format
- Form designer with visual control placement
- Code editor with syntax highlighting
- Integrated debugger with breakpoints

#### UI Controls (16)
- Label, Button, TextBox, CheckBox
- RadioButton, ListBox, ComboBox
- Frame, Timer, Image
- Menu, PopupMenu
- Edit, Memo, Grid

#### Built-in Functions
- `msgbox()` - Display message boxes
- `input_box()` - Get user input
- `confirm_dialog()` - Yes/No confirmation
- `file_dialog()` - File selection
- File I/O operations

#### Documentation
- `README.md` - Project overview
- `HISTORY.md` - Version history
- `QUICK_START.md` - Getting started guide

---

## [2.0.0] - 2024-01-10

### ✨ Added

- Initial Python Edition release
- Terminal-based UI framework
- Curses-based rendering
- Event-driven architecture
- Basic control set (Label, Button, TextBox)

---

## Version Comparison

| Feature | v2.0.0 | v2.1.0 | v2.2.0 |
|---------|--------|--------|--------|
| Controls | 3 | 16 | 25 |
| Modules | 0 | 0 | 4 |
| Examples | 0 | 3 | 11 |
| Tests | 0 | 0 | 95 |
| Documentation | 2 | 5 | 17 |

---

## Future Roadmap

### v2.3.0 (Planned)
- [ ] Drag-and-drop form designer
- [ ] Property inspector panel
- [ ] Component library manager
- [ ] Export to standalone executable
- [ ] Plugin architecture

### v3.0.0 (Planned)
- [ ] GUI mode using Tkinter/PyQt
- [ ] Integrated database designer
- [ ] Visual query builder
- [ ] Report generator
- [ ] Multi-language support

---

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Python curses library for terminal rendering
- SQLite for embedded database functionality
- Contributors and testers from the RAD-TUI community
