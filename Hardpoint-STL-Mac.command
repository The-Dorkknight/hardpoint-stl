#!/usr/bin/env bash
# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
# Hardpoint STL 0.1.0-wip (WORK IN PROGRESS). Double-click (if macOS refuses: right-click, Open) to install the
# FreeCAD workbench and check the example files. Changes nothing except the plug-in folder it copies.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "Python 3 was not found. Install Python 3 from python.org and try again."
else
  "$PY" src/install.py
fi
echo
read -r -p "Press Enter to close this window. " _
