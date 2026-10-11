# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Test CAD solids, built with OpenCASCADE (the geometry kernel FreeCAD uses), and the
per-face tessellation FreeCAD's MeshPart produces: one mesh of the whole shape, read back
face by face in explorer order, reversed faces flipped.

Needs cadquery-ocp, numpy (cadquery-ocp). Used by test_hardpoint_cad.py and by
tools/make_illustrations.py.
"""
import math

from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import (BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCone, BRepPrimAPI_MakeCylinder,
                             BRepPrimAPI_MakeSphere)
from OCP.BRepTools import BRepTools
from OCP.GeomAbs import (GeomAbs_Cone, GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Sphere, GeomAbs_Torus)
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_REVERSED, TopAbs_VERTEX
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS

KIND = {GeomAbs_Plane: 1, GeomAbs_Cylinder: 2, GeomAbs_Sphere: 3, GeomAbs_Cone: 4, GeomAbs_Torus: 5}


def _st(cls, name):
    return getattr(cls, name + '_s', None) or getattr(cls, name)


def _ax(x, y, z, dz=1):
    return gp_Ax2(gp_Pnt(x, y, z), gp_Dir(0, 0, dz))


def bracket(fillet=True):
    s = BRepPrimAPI_MakeBox(gp_Pnt(-30, -20, 0), 60, 40, 10).Shape()
    s = BRepAlgoAPI_Fuse(s, BRepPrimAPI_MakeCylinder(_ax(0, 0, 10), 8, 12).Shape()).Shape()
    for x, r in ((-20, 3.0), (20, 3.0)):
        s = BRepAlgoAPI_Cut(s, BRepPrimAPI_MakeCylinder(_ax(x, 0, -5), r, 30).Shape()).Shape()
    s = BRepAlgoAPI_Cut(s, BRepPrimAPI_MakeCylinder(_ax(0, 0, -5), 4, 40).Shape()).Shape()
    # countersink (cone) on one hole
    s = BRepAlgoAPI_Cut(s, BRepPrimAPI_MakeCone(_ax(-20, 0, 7), 3.0, 6.0, 3.0).Shape()).Shape()
    if fillet:
        f = BRepFilletAPI_MakeFillet(s)
        ex = TopExp_Explorer(s, TopAbs_EDGE)
        seen = 0
        while ex.More():
            e = _st(TopoDS, 'Edge')(ex.Current())
            p0 = _st(BRep_Tool, 'Pnt')(_st(TopoDS, 'Vertex')(next(_sub(e, TopAbs_VERTEX))))
            vs = list(_sub(e, TopAbs_VERTEX))
            p1 = _st(BRep_Tool, 'Pnt')(_st(TopoDS, 'Vertex')(vs[-1]))
            # the four vertical corner edges of the plate
            if abs(p0.X() - p1.X()) < 1e-9 and abs(p0.Y() - p1.Y()) < 1e-9 and abs(abs(p0.X()) - 30) < 1e-9 \
                    and abs(p0.Z() - p1.Z()) > 5:
                f.Add(4.0, e)
                seen += 1
            ex.Next()
        if seen:
            s = f.Shape()
    return s


def knob():
    """Sphere on a cylinder with a torus fillet: cylinder, sphere, torus, plane faces."""
    s = BRepPrimAPI_MakeCylinder(_ax(0, 0, 0), 10, 20).Shape()
    s = BRepAlgoAPI_Fuse(s, BRepPrimAPI_MakeSphere(gp_Pnt(0, 0, 26), 12).Shape()).Shape()
    f = BRepFilletAPI_MakeFillet(s)
    ex = TopExp_Explorer(s, TopAbs_EDGE)
    while ex.More():
        e = _st(TopoDS, 'Edge')(ex.Current())
        vs = [_st(BRep_Tool, 'Pnt')(_st(TopoDS, 'Vertex')(v)) for v in _sub(e, TopAbs_VERTEX)]
        if vs and all(abs(p.Z()) < 1e-9 for p in vs):
            f.Add(2.0, e)
        ex.Next()
    return f.Shape()


def _sub(shape, kind):
    ex = TopExp_Explorer(shape, kind)
    while ex.More():
        yield ex.Current()
        ex.Next()


def tessellate(shape, defl=0.05, ang_deg=15.0):
    """-> coords, tris, tri_face, face_type, hard_points  (FreeCAD MeshPart order)."""
    _st(BRepTools, 'Clean')(shape)
    BRepMesh_IncrementalMesh(shape, defl, False, math.radians(ang_deg))
    coords, tris, tri_face, ftype = [], [], [], {}
    for fi, f in enumerate(_sub(shape, TopAbs_FACE)):
        face = _st(TopoDS, 'Face')(f)
        ftype[fi] = KIND.get(BRepAdaptor_Surface(face).GetType(), 6)
        loc = TopLoc_Location()
        tr = _st(BRep_Tool, 'Triangulation')(face, loc)
        if tr is None:
            continue
        trsf = loc.Transformation()
        base = len(coords) // 3
        for i in range(1, tr.NbNodes() + 1):
            p = tr.Node(i).Transformed(trsf)
            coords += (p.X(), p.Y(), p.Z())
        rev = face.Orientation() == TopAbs_REVERSED
        for i in range(1, tr.NbTriangles() + 1):
            a, b, c = tr.Triangle(i).Get()
            if rev:
                b, c = c, b
            tris += (base + a - 1, base + b - 1, base + c - 1)
            tri_face.append(fi)
    hard = []
    seen = set()
    for v in _sub(shape, TopAbs_VERTEX):
        p = _st(BRep_Tool, 'Pnt')(_st(TopoDS, 'Vertex')(v))
        k = (round(p.X(), 7), round(p.Y(), 7), round(p.Z(), 7))
        if k not in seen:
            seen.add(k)
            hard.append((p.X(), p.Y(), p.Z()))
    return coords, tris, tri_face, ftype, hard


def volume(shape):
    """Exact volume of the CAD solid, mm3."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    g = GProp_GProps()
    _st(BRepGProp, 'VolumeProperties')(shape, g)
    return g.Mass()
