# RAD-TUI-IDE 🖥️

**Rapid Application Development - Terminal User Interface IDE**

A Visual Basic 1.0 for MS-DOS inspired visual IDE that runs on Linux terminal or windows powershell or macos terminal. Design forms, place controls, write code, and run your applications - all in the terminal!

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Language](https://img.shields.io/badge/language-Python%20%7C%20FreeBASIC-orange.svg)


<a href="https://www.youtube.com/watch?v=cOUGTNE0Kso"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_play_button_icon_%282013%E2%80%932017%29.svg" alt="Watch the video" width="100"></a>


![screenshot](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/latestRAD-TUI-IDEscreenshot.png)

## Example projects:
![tsukinoeditor](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tsukinoeditor.png)

![minesweeper](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/minesweeper.png)

![tictactoe](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/tictactoe.png)

![calc](https://raw.githubusercontent.com/amigojapan/rad-tui-IDE/refs/heads/main/calc.png)


## Installation & Usage Guide

### Linux (Debian / Ubuntu / Linux Mint)

**1. Install Python and venv**
Ensure your system repositories are up to date and install Python 3 along with the `venv` module:
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

**2. Setup and Run**
Create a virtual environment in your home directory, activate it, and launch the application:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```
*(Note: For Arch, Fedora, or other distributions, use your respective package manager like `pacman` or `dnf` to install Python 3.)*


### macOS

**1. Install Homebrew**
Run the following command in your terminal to install Homebrew (if you haven't already):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install Python**
Update Homebrew and install Python 3:
```bash
brew update
brew install python3
```

**3. Setup and Run**
Create a virtual environment, install the package, and run the IDE:
```bash
cd ~
python3 -m venv rad-tui-ide
source rad-tui-ide/bin/activate
pip install rad-tui-ide
rad-tui-ide
```


### Windows

**1. Install Python**
Download and install Python 3 from the [official Python website](https://www.python.org/downloads/) or via the Microsoft Store. **Make sure to check the box that says "Add Python to PATH"** during installation.

**2. Setup and Run**
Open PowerShell or Command Prompt and run the following commands:
```powershell
cd $env:USERPROFILE
python -m venv rad-tui-ide

# Activate the virtual environment
# On PowerShell:
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\rad-tui-ide\Scripts\Activate.ps1
# Or on Command Prompt:
# .\rad-tui-ide\Scripts\activate.bat

# Install and run
pip install rad-tui-ide
pip install windows-curses
rad-tui-ide

## 🎯 parameters
-jp starts the ide in Japanese
-es starts the ide in Spanish
-dark-mode starts the ide in dark-mode

## 🎯 Concept

RAD-TUI-IDE recreates the magic of early 90s visual programming environments like VB1 for MS-DOS, but for modern Linux terminals. It provides:

- **Visual Form Designer** - Drag and drop controls onto forms
- **Property Editor** - Edit control properties in real-time
- **Code Editor** - Write Python code with syntax highlighting in Tsukino editor
- **Runtime Mode** - Test your applications instantly
- **Project Management** - Save and load projects as JSON files

## 🚀 Features

### Visual Design Environment
- 🖱️ **Mouse-driven interface** - Point, click, drag, and resize
- 🪟 **Draggable windows** - Move forms and toolboxes freely
- 🎨 **11 control types** including buttons, labels, text boxes, and more
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
- 🔄 **Design/Runtime toggle** - Switch between design-time and run-time modes

## 🎮 How to Run

pip install rad-tui-ide

rad-tui-ide

rad-tui-ide -dark-mode

rad-tui-ide -run scriptname.json


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
| Check Box | Boolean checkbox control |
| Combo Box | Dropdown selection control |
| Command Btn | Clickable button (most common) |
| Frame | Grouping container |
| HScrollBar | Horizontal scrollbar |
| Label | Static text display |
| List Box | Scrollable list |
| Option Btn | Radio button |
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



## 🛠️ Technical Details

### Python Implementation
- Uses `curses` library for terminal UI
- Supports mouse events (requires terminal with mouse support)
- Python syntax highlighting

## 📝 Requirements

### Python Version
- Python 3.6+
- Linux terminal with:
  - Mouse support (xterm, gnome-terminal, konsole, etc.)
  - UTF-8 character support
  - 80x25 minimum terminal size

## 📜 License

This project is licensed under the **GNU General Public License v3.0** (GPL v3).

See [LICENSE](LICENSE) for full details.

## 🙏 Acknowledgments

Inspired by:
- Microsoft Visual Basic 1.0 for MS-DOS (1992)
- The simplicity of early visual programming environments
- The enduring appeal of terminal-based applications
