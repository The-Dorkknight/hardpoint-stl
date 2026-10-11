# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Hardpoint STL checks on real CAD geometry. Needs cadquery-ocp, numpy and trimesh
(numpy-stl optional):

    python tests/test_hardpoint_cad.py

What it covers
  format    CAD solid -> hardpoint STL -> reference reader gives back the same faces, types
            and hardpoints; the file is watertight, exactly plain-STL sized, refused when a
            byte of geometry changes; STL libraries read the same triangles as a plain twin.
  plug-ins  the FreeCAD and Fusion export logic, run against STAND-INS for those programs'
            objects (same attribute names, filled with OpenCASCADE geometry). This checks
            the plug-ins' own logic. It cannot show that the real programs behave as their
            documentation says: neither can run here.
"""
import math
import os
import struct
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import cadparts  # noqa: E402
import hstl  # noqa: E402

REC = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
PARTS = (("bracket", cadparts.bracket), ("knob", cadparts.knob))


def admesh_says_binary(data):
    """The binary/text test of the admesh STL reader (as in OrcaSlicer's stlinit.cpp)."""
    return any(b > 127 for b in data[84:84 + 128]) and (len(data) - 84) % 50 == 0


def same_partition(p, q):
    return len(set(zip(p, q))) == len(set(p)) == len(set(q))


def write_pair(tmp, name, shape, defl=0.05, ang=15.0):
    """-> (labelled path, plain twin path, encode info, inputs)"""
    coords, tris, tri_face, ftype, hard = cadparts.tessellate(shape, defl, ang)
    data, info = hstl.encode(coords, tris, tri_face, ftype, hard, units="mm", tol=defl, angle=ang, by="test")
    lab = os.path.join(tmp, f"{name}_hardpoint.stl")
    plain = os.path.join(tmp, f"{name}_plain.stl")
    open(lab, "wb").write(data)
    arr = np.frombuffer(data, REC, offset=84).copy()
    arr["a"] = 0
    open(plain, "wb").write(b"plain".ljust(80, b" ") + data[80:84] + arr.tobytes())
    return lab, plain, info, (coords, tris, tri_face, ftype, hard)


# ------------------------------------------------------------------ format
def test_format(tmp):
    import trimesh
    for name, mk in PARTS + (("bracket_coarse", cadparts.bracket),):
        defl, ang = (0.3, 30.0) if name.endswith("coarse") else (0.05, 15.0)
        lab, plain, info, (coords, tris, tri_face, ftype, hard) = write_pair(tmp, name, mk(), defl, ang)
        data = open(lab, "rb").read()
        assert info["watertight"], (name, info["open_edges"], info["bad_edges"])
        assert len(data) == 84 + 50 * info["triangles"] == os.path.getsize(plain)
        assert admesh_says_binary(data)
        words = np.frombuffer(data, REC, offset=84)["a"]
        assert not (words & 0xC060).any(), "reserved bits and bit 15 must be clear"
        assert trimesh.load(lab, file_type="stl").is_watertight
        try:
            import stl.mesh
            a = np.concatenate([m.vectors for m in stl.mesh.Mesh.from_multi_file(plain)])
            b = np.concatenate([m.vectors for m in stl.mesh.Mesh.from_multi_file(lab)])
            assert np.array_equal(a, b), "numpy-stl must read the same triangles from both files"
            via = "numpy-stl identical to plain twin"
        except ImportError:
            via = "numpy-stl not installed, skipped"

        doc = hstl.read(lab)
        assert doc and doc["crc_ok"]
        dec = hstl.decode(doc)
        written = [tri_face[i] for i in info["order"]]
        assert same_partition(dec["face"], written), "faces must come back as written"
        assert all(dec["type"][dec["face"][i]] == ftype[written[i]] for i in range(len(written)))
        assert len(dec["hardpoints"]) == len(hard) == info["hardpoints"]

        bad = bytearray(data)
        bad[84 + 12] ^= 1
        t = os.path.join(tmp, "tampered.stl")
        open(t, "wb").write(bytes(bad))
        assert hstl.read(t)["crc_ok"] is False and hstl.read(plain) is None

        # labels moved between two different meshes of the same solid (the Fusion fallback)
        c2, t2, f2, _, _ = cadparts.tessellate(mk(), defl * 1.7, ang * 1.5)
        got = hstl.transfer_faces(c2, t2, f2, coords, tris)
        share = sum(1 for x, y in zip(got, tri_face) if x == y) / len(tri_face)
        assert share > 0.995, share
        print(f"  format   {name}: {info['triangles']} triangles, {info['faces']} faces, {info['colours']} colours, "
              f"{info['hardpoints']} hardpoints; {via}; label transfer {100 * share:.1f}% right")


# ------------------------------------------------------------------ plug-in stand-ins
class _V:
    def __init__(self, x, y, z):
        self.x = self.X = x
        self.y = self.Y = y
        self.z = self.Z = z


FC_NAMES = {1: "Plane", 2: "Cylinder", 3: "Sphere", 4: "Cone", 5: "Toroid", 6: "BSplineSurface"}
FU_NAMES = {1: "Plane", 2: "Cylinder", 3: "Sphere", 4: "Cone", 5: "Torus", 6: "NurbsSurface"}


def _load_plugin(kind, module):
    folder = os.path.join(ROOT, "plugins", kind, "HardpointSTL")
    for m in ("hstl", module):
        sys.modules.pop(m, None)
    sys.path.insert(0, folder)
    try:
        return __import__(module)
    finally:
        sys.path.remove(folder)
        sys.modules.pop("hstl", None)
        sys.modules["hstl"] = hstl


def test_freecad_standin(tmp):
    hp = _load_plugin("FreeCAD", "hardpoint_fc")
    for name, mk in PARTS:
        shape = mk()
        _, _, _, ftype, hard = cadparts.tessellate(shape)
        faces = [types.SimpleNamespace(Surface=type(FC_NAMES[ftype[i]], (), {})()) for i in sorted(ftype)]
        sh = types.SimpleNamespace(Faces=faces, Vertexes=[_V(*p) for p in hard])

        def mesher(Shape, LinearDeflection, AngularDeflection, Relative, Segments, shape=shape, faces=faces):
            assert Segments is True and Relative is False
            c, t, tf, _, _ = cadparts.tessellate(shape, LinearDeflection, math.degrees(AngularDeflection))
            groups = {}
            for i, f in enumerate(tf):
                groups.setdefault(f, []).append(i)
            return types.SimpleNamespace(
                Topology=([_V(c[i], c[i + 1], c[i + 2]) for i in range(0, len(c), 3)],
                          [tuple(t[i:i + 3]) for i in range(0, len(t), 3)]),
                countSegments=lambda: len(faces), getSegment=lambda i: groups.get(i, []))
        path = os.path.join(tmp, f"{name}_freecad.stl")
        info = hp.export([sh], path, 0.05, 15.0, mesher=mesher)
        assert info["watertight"] and hstl.read(path)["header"]["by"] == "freecad"
        assert info["faces"] == len(faces) and info["hardpoints"] == len(hard)
        print(f"  FreeCAD stand-in  {name}: " + hp.summary(info).splitlines()[0])


class _Calc:
    def __init__(self, fn):
        self.fn, self.surfaceTolerance, self.maxNormalDeviation = fn, 0.0, 0.0

    def calculate(self):
        c, t = self.fn(self.surfaceTolerance * 10.0, math.degrees(self.maxNormalDeviation))
        return types.SimpleNamespace(nodeCoordinatesAsDouble=[x / 10.0 for x in c], nodeIndices=t)


def test_fusion_standin(tmp):
    hp = _load_plugin("Fusion", "hardpoint_fusion")
    for name, mk in PARTS:
        for broken in (False, True):
            shape = mk()
            _, _, _, ftype, hard = cadparts.tessellate(shape)

            def whole(tol, ang, shape=shape):
                c, t, _, _, _ = cadparts.tessellate(shape, tol, ang)
                return c, t

            def one(fi, shape=shape, broken=broken):
                def fn(tol, ang):
                    # broken: neighbouring faces meshed at different settings, so their edges don't join
                    k = 1.9 if (broken and fi % 2) else 1.0
                    c, t, tf, _, _ = cadparts.tessellate(shape, tol * k, ang * k)
                    return c, [v for i, f in enumerate(tf) if f == fi for v in t[3 * i:3 * i + 3]]
                return fn
            faces = [types.SimpleNamespace(
                geometry=types.SimpleNamespace(objectType="adsk::core::" + FU_NAMES[ftype[i]]),
                meshManager=types.SimpleNamespace(createMeshCalculator=lambda fn=one(i): _Calc(fn)))
                for i in sorted(ftype)]
            body = types.SimpleNamespace(
                faces=faces, name=name,
                vertices=[types.SimpleNamespace(geometry=_V(p[0] / 10.0, p[1] / 10.0, p[2] / 10.0)) for p in hard],
                meshManager=types.SimpleNamespace(createMeshCalculator=lambda: _Calc(whole)))
            path = os.path.join(tmp, f"{name}_fusion.stl")
            info = hp.export([body], path, 0.05, 15.0)
            assert info["watertight"] and hstl.is_hardpoint_stl(path)
            assert info["method"] == ("body" if broken else "faces")
            assert info["faces"] == len(faces) and info["hardpoints"] == len(hard)
            print(f"  Fusion stand-in   {name}, {'per-face meshes that do not join' if broken else 'per-face meshes join'}: "
                  f"route '{info['method']}', {info['triangles']} triangles, {info['faces']} faces")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        test_format(tmp)
        test_freecad_standin(tmp)
        test_fusion_standin(tmp)
    print("hardpoint CAD checks passed")


if __name__ == "__main__":
    main()
