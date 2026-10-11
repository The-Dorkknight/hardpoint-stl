# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Write the example files in examples/: two CAD parts, each as a hardpoint STL and as a
plain STL with exactly the same triangles.

    python tools/make_examples.py

The parts are built with OpenCASCADE (tests/cadparts.py), so the labels come from real CAD
faces. Needs cadquery-ocp, numpy.
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cadparts  # noqa: E402
import hstl  # noqa: E402

OUT = os.path.join(ROOT, "examples")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, make in (("bracket", cadparts.bracket), ("knob", cadparts.knob)):
        coords, tris, tri_face, ftype, hard = cadparts.tessellate(make(), 0.05, 15.0)
        data, info = hstl.encode(coords, tris, tri_face, ftype, hard, units="mm", tol=0.05, angle=15.0,
                                 by="cad-example")
        with open(os.path.join(OUT, f"{name}_hardpoint.stl"), "wb") as f:
            f.write(data)
        plain = bytearray(data)
        plain[:80] = b"plain STL, same triangles as the hardpoint twin".ljust(80, b" ")
        for i in range(info["triangles"]):
            struct.pack_into("<H", plain, 84 + 50 * i + 48, 0)
        with open(os.path.join(OUT, f"{name}_plain.stl"), "wb") as f:
            f.write(bytes(plain))
        print(f"{name}: {info['triangles']} triangles, {info['faces']} faces, {info['hardpoints']} hardpoints")


if __name__ == "__main__":
    main()
