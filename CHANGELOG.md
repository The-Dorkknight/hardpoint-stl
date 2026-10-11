# Changelog

## 0.1.0-wip (2026-10-10)

First release as its own project. **Work in progress.**

- Hardpoint STL format version 1 and its reference reader and writer (`src/hstl.py`), with
  `info`, `verify` and `strip` commands.
- FreeCAD workbench and Fusion add-in, each with **Export hardpoint STL**. Tested only against
  stand-ins for those programs, not in the real ones.
- Double-click installers for Linux, Mac and Windows.
- Research notes, format specification, drawings made from real data, four example files.
- Tests: format, installer, real CAD geometry (OpenCASCADE), and a check to run inside FreeCAD.

Developed as part of STL2STEP 0.2.0-wip (a separate mesh-to-STEP converter); the converter's side
is not included here.
