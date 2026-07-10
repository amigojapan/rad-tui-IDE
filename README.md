# RAD-TUI 🖥️

**Rapid Application Development - Terminal User Interface**

A Visual Basic 1.0 for MS-DOS inspired visual IDE that runs on Linux. Design forms, place controls, write code, and run your applications - all in the terminal!

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20FreeBASIC-orange.svg)

## 🎯 Concept

RAD-TUI recreates the magic of early 90s visual programming environments like VB1 for MS-DOS, but for modern Linux terminals. It provides:

- **Visual Form Designer** - Drag and drop controls onto forms
- **Property Editor** - Edit control properties in real-time
- **Code Editor** - Write Python code with syntax highlighting
- **Runtime Mode** - Test your applications instantly
- **Project Management** - Save and load projects as JSON files

## 🚀 Features

### Visual Design Environment
- 🖱️ **Mouse-driven interface** - Point, click, drag, and resize
- 🪟 **Draggable windows** - Move forms and toolboxes freely
- 🎨 **16 control types** including buttons, labels, text boxes, and more
- 📐 **Visual resizing** - Grab handles to resize controls
- ✏️ **Property editing** - Edit names, captions, positions, and dimensions

### Code Development
- 🐍 **Python code-behind** - Write event handlers in Python
- 🌈 **Syntax highlighting** - Keywords, strings, numbers, and comments
- ▶️ **Runtime execution** - Run your forms with live code execution
- 🐛 **Runtime error display** - See errors in a message box

### Project Management
- 💾 **Save/Load projects** - JSON-based project files
- 📁 **File menu** - Standard save/load/exit operations
- 🔄 **Design/Runtime toggle** - Switch between design and test modes

## 📁 Project Structure

```
radtui/
├── rad-tui-py.py          # Python/curses implementation (recommended)
├── rad-tui-BASIC.bas      # FreeBASIC implementation
├── rad-tui-BASIC          # Compiled FreeBASIC binary
├── example1.json          # Sample "Hello Name" application
├── HISTORY.md             # Development history/changelog
├── LICENSE                # GPL v3 License
└── README.md              # This file
```

## 🎮 How to Run

### Python Version (Recommended)
```bash
# Requires Python 3 and curses support (usually built-in)
python3 rad-tui-py.py

# Or make executable and run:
chmod +x rad-tui-py.py
./rad-tui-py.py
```

### FreeBASIC Version
```bash
# If you have FreeBASIC installed:
fbc rad-tui-BASIC.bas -o rad-tui-BASIC

# Run the compiled binary:
./rad-tui-BASIC
```

## 🕹️ User Guide

### Getting Started
1. Run the application - you'll see:
   - A **Toolbox** on the left with available controls
   - A **Form** window in the center (your design surface)
   - A **Properties** window on the right

### Designing a Form

| Action | How To |
|--------|--------|
| **Add a control** | Click a tool in the toolbox, then click on the form |
| **Move a control** | Select "Move/Size" tool, then drag the control |
| **Resize a control** | Select control, then drag the ■ handle |
| **Edit properties** | Click a property value in the Properties window |
| **Write code** | Double-click a button to open the code editor |

### Available Controls

| Tool | Description |
|------|-------------|
| Move/Size | Select and manipulate existing controls |
| Check Box | Boolean checkbox control |
| Combo Box | Dropdown selection control |
| Command Btn | Clickable button (most common) |
| Dir List | Directory listing |
| Drive List | Drive selection |
| File List | File browser |
| Frame | Grouping container |
| HScrollBar | Horizontal scrollbar |
| Label | Static text display |
| List Box | Scrollable list |
| Option Btn | Radio button |
| Picture Box | Image display area |
| Text Box | Text input field |
| Timer | Background timer |
| VScrollBar | Vertical scrollbar |

### Writing Code

Double-click a **Command Button** to open the code editor. The code editor supports:

```python
def on_click_btnOK():
    msgbox("Hello, World!")
    txtName.caption = "Updated text"
```

**Special functions:**
- `msgbox(text)` - Display a message box
- Access other controls by their `name_id`: `txtName.caption`, `btnOK.caption`

### Menu Options

- **File → Save Project As** - Save your form to a JSON file
- **File → Load Project** - Load a previously saved project
- **File → Exit** - Quit the IDE
- **Run** - Switch to runtime mode to test your application
- **Stop** (in runtime) - Return to design mode

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `ESC` | Exit the IDE (from design mode) |
| `Enter` | Confirm property edit |
| `Backspace` | Delete character (in code/property editor) |
| Arrow keys | Navigate in code editor |

## 📋 Example Project

The included `example1.json` demonstrates a "Hello Name" application:

1. A **Text Box** (`txtName`) for name input
2. An **OK Button** (`btnOK`) with click handler
3. An **Output Text Box** (`txtOutput`) displaying the greeting

**Code behind the OK button:**
```python
def on_click_btnOK():
    msgbox("OK button clicked!")
    txtOutput.caption="Welcome "+txtName.caption+"!"
```

## 📦 Project File Format

Projects are saved as JSON with this structure:

```json
{
  "x": 16, "y": 2, "w": 36, "h": 17,
  "title": "Form 1",
  "controls": [
    {
      "x": 11, "y": 11, "w": 12, "h": 3,
      "tool_type": 3,
      "name_id": "btnOK",
      "caption": "OK",
      "code": "def on_click_btnOK():\\n    pass\\n"
    }
  ]
}
```

## 🛠️ Technical Details

### Python Implementation
- Uses `curses` library for terminal UI
- Supports mouse events (requires terminal with mouse support)
- Python syntax highlighting with regex tokenization
- Live code execution with `exec()` in controlled namespace

### FreeBASIC Implementation
- Native console graphics using `fbgfx`
- Object-oriented design with Types
- Direct console manipulation with `Locate` and `Color`

## 📝 Requirements

### Python Version
- Python 3.6+
- Linux terminal with:
  - Mouse support (xterm, gnome-terminal, konsole, etc.)
  - UTF-8 character support
  - 80x25 minimum terminal size

### FreeBASIC Version
- FreeBASIC compiler (`fbc`)
- Linux console

## 🐛 Known Limitations

- Terminal must support UTF-8 box drawing characters
- Mouse support required for visual design
- Minimum terminal size: 80 columns x 25 rows
- Python version has more features (save/load, code editor, runtime)
- FreeBASIC version is design-mode only

## 📜 License

This project is licensed under the **GNU General Public License v3.0** (GPL v3).

See [LICENSE](LICENSE) for full details.

## 🙏 Acknowledgments

Inspired by:
- Microsoft Visual Basic 1.0 for MS-DOS (1992)
- The simplicity of early visual programming environments
- The enduring appeal of terminal-based applications

---

**Happy retro-coding!** 🎉
