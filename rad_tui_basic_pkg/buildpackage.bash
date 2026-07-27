#!/bin/bash
# 1. Clean previous build artifacts
rm -rf dist/ build/ *.egg-info

# 2. Build the package
pipx run build

# 3. Upload to PyPI
pipx run twine upload dist/*