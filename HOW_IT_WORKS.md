# How it works (plain English)

**WORK IN PROGRESS** · 0.1.0-wip

**What it reads:** in FreeCAD, the solids you select; in Fusion, the solid bodies you select.
It asks the program for each CAD face's triangles, the kind of surface, and the corner points.

**What it writes:** one `.stl` file, where you choose. Its triangles are the same ones a normal
STL export would give. The extra information sits in the 80-byte header and the 2 spare bytes
after each triangle, which slicers skip.

**What it never does:** it doesn't change your CAD document, doesn't open the network, doesn't
send anything anywhere, and doesn't touch other files. The installer (`src/install.py`) only
copies the plug-in folder into FreeCAD's or Fusion's user plug-in folder, reads the copy back to
compare it, and checks the example files.

**Reading it back:** `python src/hstl.py info file.stl` shows what a file holds, `verify` checks
it against the rules, `strip` writes a plain STL with the same triangles. A converter reads the
labels, checks them against the mesh, and builds the solid from the faces instead of guessing.

**Where labels are lost:** any program that re-saves the STL (most mesh editors, some slicers)
writes its own header and zeroes the spare bytes. A file whose triangles were changed after
export is detected by the checksum and treated as a plain STL.

Details: [HARDPOINT_STL.md](HARDPOINT_STL.md) (the format) and [DESIGN_NOTES.md](DESIGN_NOTES.md) (the research).
