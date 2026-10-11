# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Check "Export hardpoint STL" inside REAL FreeCAD. Takes a few seconds.

    FreeCADCmd tests/freecad_selfcheck.py        (the command may be freecadcmd or FreeCAD -c)

or, in FreeCAD's window: Macro -> Macros... -> Create, paste this whole file, Execute.

It builds a small test part in memory, exports it with the plug-in's own code, reads the
file back and prints PASS or FAIL for each check, ending with one RESULT line. The same text
is saved as freecad_selfcheck.txt in your temporary folder, to attach to a bug report.
Nothing in your documents is touched.

WORK IN PROGRESS. This script has NOT been run by the author: FreeCAD could not be
installed on the machine it was written on. If the script itself fails, that is useful too:
please send the output.
"""
import math
import os
import sys
import tempfile
import traceback

LINES = []


def say(text):
    LINES.append(text)
    try:
        import FreeCAD
        FreeCAD.Console.PrintMessage(text + "\n")
    except Exception:
        print(text)


def find_plugin():
    """The installed workbench, or the copy in this repository."""
    cands = [os.environ.get("HARDPOINTSTL_PLUGIN", "")]
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        cands.append(os.path.join(os.path.dirname(here), "plugins", "FreeCAD", "HardpointSTL"))
    except NameError:                      # pasted as a macro: no __file__
        pass
    try:
        import FreeCAD
        cands.append(os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "HardpointSTL"))
    except Exception:
        pass
    for c in cands:
        if c and os.path.isfile(os.path.join(c, "hardpoint_fc.py")):
            return c
    return None


def main():
    ok = True

    def check(name, passed, detail=""):
        nonlocal ok
        ok = ok and bool(passed)
        say(("PASS  " if passed else "FAIL  ") + name + (("  (" + str(detail) + ")") if detail != "" else ""))

    import FreeCAD
    import Part
    say("FreeCAD " + ".".join(str(x) for x in FreeCAD.Version()[:3]) + ", Python " + sys.version.split()[0])
    folder = find_plugin()
    check("plug-in folder found", folder is not None, folder or "set HARDPOINTSTL_PLUGIN to plugins/FreeCAD/HardpointSTL")
    if folder is None:
        return False
    if folder not in sys.path:
        sys.path.insert(0, folder)
    import hardpoint_fc
    import hstl

    # a plate with a boss and two holes: planes and cylinders
    V = FreeCAD.Vector
    shape = Part.makeBox(60, 40, 10, V(-30, -20, 0))
    shape = shape.fuse(Part.makeCylinder(8, 12, V(0, 0, 10), V(0, 0, 1)))
    for x in (-20, 20):
        shape = shape.cut(Part.makeCylinder(3, 30, V(x, 0, -5), V(0, 0, 1)))
    shape = shape.removeSplitter()
    n_faces = len(shape.Faces)
    say(f"test part: {n_faces} faces, {len(shape.Vertexes)} vertices, volume {shape.Volume:.2f} mm3")

    path = os.path.join(tempfile.gettempdir(), "freecad_selfcheck_hardpoint.stl")
    info = hardpoint_fc.export([shape], path, 0.05, 15.0)
    say("export: " + hardpoint_fc.summary(info).replace("\n", " | "))

    check("one group of triangles per CAD face (no notes from the exporter)", not info["notes"], info["notes"] or "")
    check("faces in the file = faces of the shape", info["faces"] == n_faces, f"{info['faces']} / {n_faces}")
    check("mesh is watertight", info["watertight"], f"open {info['open_edges']}, bad {info['bad_edges']}")
    check("surface types recognised (planes and cylinders, none unknown)",
          info["types"].get("plane", 0) >= 6 and info["types"].get("cylinder", 0) >= 3 and "unknown" not in info["types"],
          info["types"])
    check("every CAD vertex became a hardpoint", info["hardpoints"] > 0 and info["hardpoints_missed"] == 0,
          f"{info['hardpoints']} found, {info['hardpoints_missed']} missed")

    doc = hstl.read(path)
    check("file reads back as a hardpoint STL with a valid checksum", bool(doc and doc["crc_ok"]))
    if doc and doc["crc_ok"]:
        dec = hstl.decode(doc)
        check("reader rebuilds the same number of faces", len(dec["type"]) == n_faces, f"{len(dec['type'])} / {n_faces}")

    # the same triangles a normal FreeCAD mesh of this shape has?
    import MeshPart
    plain = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.05, AngularDeflection=math.radians(15.0),
                                   Relative=False)
    check("same triangle count as FreeCAD's own mesh of the shape",
          plain.CountFacets == info["triangles"] + info["dropped"],
          f"FreeCAD {plain.CountFacets}, hardpoint STL {info['triangles']} + {info['dropped']} dropped")

    # FreeCAD can open the file as an ordinary STL
    import Mesh
    back = Mesh.Mesh(path)
    check("FreeCAD opens the file as a normal STL", back.CountFacets == info["triangles"],
          f"{back.CountFacets} facets")
    check("and sees a solid mesh", back.isSolid(), "")
    say("file: " + path)
    return ok


try:
    RESULT = main()
except Exception:
    say(traceback.format_exc())
    RESULT = False
say("RESULT: " + ("PASS" if RESULT else "FAIL") + "  (Export hardpoint STL in real FreeCAD)")
try:
    with open(os.path.join(tempfile.gettempdir(), "freecad_selfcheck.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(LINES) + "\n")
except OSError:
    pass
