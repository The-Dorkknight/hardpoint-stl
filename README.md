# Hardpoint STL

**WORK IN PROGRESS: MANY FEATURES MAY BE BROKEN** · version 0.1.0-wip · source-available, non-commercial

An ordinary binary `.stl` that also remembers which CAD face each triangle came from, what kind
of surface that face is, and where its corners are. Slicers read it as a normal STL. A
mesh-to-CAD converter that knows the format can rebuild the solid without guessing.

> **Licence and no warranty.** Copyright Matthew Armstrong. Licensed under the
> [PolyForm Noncommercial License 1.0.0](LICENSE.md): free to use and change for non-commercial
> purposes, no commercial use without separate permission from the author. This is
> *source-available*, not open source. **The software and file format are provided as is, with no
> warranty and no liability**; this is not legal advice. Third-party parts keep their own
> licences ([THIRD_PARTY.md](THIRD_PARTY.md)).

![One hardpoint STL drawn three ways: the mesh a slicer sees, the face colours stored in the file, and the surface types with hardpoints](docs/images/hardpoint-part.webp)

*Drawn from `examples/bracket_hardpoint.stl` by `tools/make_illustrations.py`.*

## What is in here

| Part | What it is |
| --- | --- |
| [`HARDPOINT_STL.md`](HARDPOINT_STL.md) | The format specification (version 1) |
| [`DESIGN_NOTES.md`](DESIGN_NOTES.md) | The research: how slicers read STL, why the format looks like this, measurements, what was tried and dropped, risks, ideas |
| `src/hstl.py` | Reference reader and writer, standard library only. Command line: `info`, `verify`, `strip` |
| `plugins/FreeCAD/HardpointSTL/` | FreeCAD workbench: **Export hardpoint STL** |
| `plugins/Fusion/HardpointSTL/` | Autodesk Fusion add-in: **Export hardpoint STL** |
| `examples/` | Two parts, each as a hardpoint STL and as a plain STL with the same triangles |
| `tests/`, `tools/` | Self-checks, a check to run inside real FreeCAD, and the scripts that draw the pictures and examples |

## What exists and what doesn't

| | Status |
| --- | --- |
| The format (version 1), reference reader and writer | Written; tested on Linux with simulated CAD parts |
| FreeCAD and Fusion exporters | Written; tested only against stand-ins for those programs. **Never run in real FreeCAD or Fusion** |
| Reading the labels in a converter | Not in this repository. The format was developed alongside STL2STEP, a separate mesh-to-STEP converter; the measurements in the notes come from it |
| Opening a hardpoint STL in a real slicer | **Not tried.** Checked against the loaders Cura and PrusaSlicer-family slicers use (numpy-stl, the admesh binary/text test) and trimesh, not the programs themselves |
| STEP-to-hardpoint-STL command, viewer, other CAD programs | Not written (see the ideas list in the notes) |
| Windows and macOS | Not tested (everything ran on Linux) |

## Install (one step)

1. Download the repository (green **Code** button → **Download ZIP**) or the zip on the
   Releases page on GitHub, and unzip it anywhere.
2. **Double-click** the start file for your system:
   - Linux: `Hardpoint-STL-Linux.sh` (choose *Run* if asked)
   - Mac: `Hardpoint-STL-Mac.command` (if macOS refuses, right-click → Open)
   - Windows: `Hardpoint-STL-Windows.bat`

   It needs Python 3 and nothing else. It copies the FreeCAD workbench (and, on Windows or
   Mac, the Fusion add-in) into the right folder if the program is installed, reads the copy
   back to check it, and checks the example files. It cannot start FreeCAD or Fusion, so it
   cannot confirm they load the plug-in.
3. Restart FreeCAD or Fusion.

**By hand, FreeCAD:** copy the folder `plugins/FreeCAD/HardpointSTL` into FreeCAD's user `Mod`
folder (in FreeCAD's Python console, type `FreeCAD.getUserAppDataDir()` to see where that is;
`Mod` is inside it). **By hand, Fusion:** *Utilities → Add-Ins → Scripts and
Add-Ins → green plus* and choose `plugins/Fusion/HardpointSTL`.

## Use

**FreeCAD.** Choose the **Hardpoint STL** workbench, select one or more solids in the model
tree, click **Export hardpoint STL**, set the surface deviation (default 0.05 mm) and angle
(15°), and choose where to save. A summary shows the faces, surface types, hardpoints and
whether the mesh is watertight. Any problem is listed there too.

**Fusion.** *Utilities → Add-Ins* → **Export hardpoint STL** (and on the Mesh tab if your
version has the panel). Select solid bodies, set the same two numbers, save.

**Command line** (any system with Python 3):

```
python src/hstl.py info   examples/bracket_hardpoint.stl     what the file contains
python src/hstl.py verify examples/bracket_hardpoint.stl     check it against the format rules
python src/hstl.py strip  examples/bracket_hardpoint.stl plain.stl    the same triangles, labels removed
```

**From Python:** `import hstl`, then `hstl.encode(coords, tris, tri_face, face_type, hard_points, ...)`
returns the file bytes and a report; `hstl.read` and `hstl.decode` read them back. The format
is described byte by byte in [HARDPOINT_STL.md](HARDPOINT_STL.md).

## How it stays an ordinary STL

A binary STL has exactly two places slicers ignore: the 80-byte header and the 2-byte attribute
field after each triangle. The labels live only there, so the triangles, the file size and the
extension are exactly those of a plain STL. (Appending data after the triangles was tried and
breaks common loaders; see the notes.)

![Byte layout of a binary STL with the header and the 2 attribute bytes of each triangle highlighted, and the meaning of each of the 16 attribute bits](docs/images/hardpoint-layout.webp)

![A CAD model becomes a hardpoint STL; a slicer reads the triangles, a converter reads the labels](docs/images/hardpoint-workflow.webp)

Labels are hints. A checksum in the header (CRC-32 of the triangle data) shows whether the mesh
was edited after labelling; a reader must then ignore the labels. Any program that re-saves the
STL will drop them, and ASCII (text) STL cannot carry them.

## Does it help? (measured with STL2STEP, not included here)

On three test parts, converting the labelled file gave a STEP with fewer, more correct faces
than converting the same triangles as a plain STL:

![STEP face counts for three test parts from a plain STL and from its hardpoint twin, with the face count of the original CAD model marked](docs/images/hardpoint-results.webp)

The knob went from 1,103 faces (14 s) to 8 (2 s); the original CAD model has 4. These numbers
come from STL2STEP 0.2.0-wip and cannot be re-run from this repository. The full table, the
method and the caveats are in [DESIGN_NOTES.md](DESIGN_NOTES.md#measured-results).

## Tests

```
python tests/test_hstl.py          format round trip, tamper check, verify, strip (standard library only)
python tests/test_install.py       the installer, against a throw-away home folder (standard library only)
python tests/test_hardpoint_cad.py the format on real CAD geometry and the plug-in logic against stand-ins
                                   (needs: pip install cadquery-ocp numpy trimesh numpy-stl)
```

**The one check that matters most and has not been done:** run `tests/freecad_selfcheck.py`
inside real FreeCAD (Macro → Macros… → Create, paste the file, Execute). It builds a test part,
exports it with the workbench's own code, reads the file back and ends with a `RESULT: PASS` or
`FAIL` line. The script itself has never been run in real FreeCAD either; if it fails, the output
is useful in an issue.

## Known limitations

- Not run in real FreeCAD, Fusion or any slicer. Older FreeCAD (before 1.0) may not accept the
  meshing call the workbench uses; it reports a clear error.
- Whether Fusion's per-face meshes join into a closed mesh is unknown; the add-in checks and
  falls back to meshing the whole body, then transferring the face labels.
- Cone and torus faces are labelled but a converter must support them.
- Viewers that show per-triangle STL colours may show the labels as colours or ignore them.
- More than 32 faces that all touch each other cannot be coloured; the writer refuses with an error.

The full list of risks and open work is in [DESIGN_NOTES.md](DESIGN_NOTES.md).

## Troubleshooting

| Problem | Try |
| --- | --- |
| The launcher says Python 3 was not found | Install Python 3 from python.org and run it again |
| The launcher says FreeCAD/Fusion "not found" | Start the program once so it creates its user folder, or copy the plug-in in by hand (above) |
| No *Hardpoint STL* workbench after restarting FreeCAD | Open *View → Panels → Report view* and look for an error mentioning `HardpointSTL`; send it in an issue |
| `verify` says "not a hardpoint STL" | The file was re-saved by another program (labels dropped), edited after export, or is a plain/text STL |
| Linux: the `.sh` file opens in a text editor | Right-click → Properties → Permissions → allow executing, or run `bash Hardpoint-STL-Linux.sh` |

## More

[HARDPOINT_STL.md](HARDPOINT_STL.md) · [DESIGN_NOTES.md](DESIGN_NOTES.md) · [HOW_IT_WORKS.md](HOW_IT_WORKS.md) ·
[CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) ·
[THIRD_PARTY.md](THIRD_PARTY.md) · [examples/](examples/)
