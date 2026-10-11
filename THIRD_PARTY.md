# Third-party software

The PolyForm Noncommercial licence in [LICENSE.md](LICENSE.md) covers **only the code written by Matthew Armstrong** in this repository. The components below are not included in the repository and each keeps its own licence (see the linked pages). Hardpoint STL is not affiliated with or endorsed by any of these projects or by Autodesk, the FreeCAD project, Bambu Lab or Prusa Research.

To use it you need only Python 3 (<https://www.python.org/>); the format library uses the standard library alone.

| Component | Used for | Project page |
|---|---|---|
| FreeCAD, Autodesk Fusion | host applications for the plug-ins (you install them yourself) | <https://www.freecad.org/> · <https://www.autodesk.com/products/fusion-360> |

Development and testing only: `tests/test_hardpoint_cad.py` and the scripts in `tools/` use cadquery-ocp / Open CASCADE Technology (<https://github.com/CadQuery/OCP>), NumPy (<https://numpy.org/>), trimesh (<https://github.com/mikedh/trimesh>), numpy-stl (<https://github.com/WoLpH/numpy-stl>), Matplotlib (<https://matplotlib.org/>) and Pillow (<https://python-pillow.org/>).

The research notes link to the source code and pages that were read (OrcaSlicer's admesh reader, Uranium, trimesh, FreeCAD, the Fusion API pages, stlToSolid, breptile); those projects keep their own licences and nothing from them is copied here.

Check each project's page for its licence terms before redistributing anything that includes it.
