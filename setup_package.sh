#!/bin/bash
# setup_package.sh - Restructures rad-tui-BASIC for PyPI publishing

echo "Creating standard Python package structure..."
mkdir -p rad_tui_basic_pkg/src/rad_tui_basic

# Move Python files and assets into the package module.
# We rename rad-tui-py.py to use underscores so it can be legally imported in Python.
cp rad-tui-py.py rad_tui_basic_pkg/src/rad_tui_basic/rad_tui_py.py 2>/dev/null
cp test.py rad_tui_basic_pkg/src/rad_tui_basic/ 2>/dev/null
cp *.png rad_tui_basic_pkg/src/rad_tui_basic/ 2>/dev/null
cp -r projects rad_tui_basic_pkg/src/rad_tui_basic/ 2>/dev/null
cp -r obsolete rad_tui_basic_pkg/src/rad_tui_basic/ 2>/dev/null

# Create __init__.py to make it a recognizable Python module
cat << 'EOF' > rad_tui_basic_pkg/src/rad_tui_basic/__init__.py
"""rad-tui-BASIC - A TUI BASIC environment"""
__version__ = "0.1.0"
EOF

# Copy metadata files to the project root
cp README.md rad_tui_basic_pkg/ 2>/dev/null || echo "# rad-tui-BASIC" > rad_tui_basic_pkg/README.md
cp LICENSE rad_tui_basic_pkg/ 2>/dev/null || touch rad_tui_basic_pkg/LICENSE
cp HISTORY.md rad_tui_basic_pkg/ 2>/dev/null || touch rad_tui_basic_pkg/HISTORY.md

# Create the modern pyproject.toml configuration using hatchling
cat << 'EOF' > rad_tui_basic_pkg/pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "rad-tui-basic"
version = "0.1.0"
description = "A TUI BASIC environment"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"} # Ensure this matches your actual license
authors = [
  {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
  # Add your project's pip dependencies here (e.g., "PySide6>=6.0.0", "textual")
]

# Optional: If you want users to run your app directly from the terminal after installing
# [project.scripts]
# rad-tui = "rad_tui_basic.rad_tui_py:main"

[tool.hatch.build.targets.wheel]
packages = ["src/rad_tui_basic"]

[tool.hatch.build.targets.sdist]
include = [
  "/src",
  "/README.md",
  "/LICENSE",
  "/HISTORY.md"
]
EOF

echo "Structure created successfully in rad_tui_basic_pkg/!"