# Example files

**WORK IN PROGRESS** (hardpoint-stl 0.1.0-wip)

Two test parts, each written twice with exactly the same triangles:

| File | What it is |
|---|---|
| `bracket_hardpoint.stl` | Bracket as a hardpoint STL: 1,180 triangles, 16 faces (7 planes, 8 cylinders, 1 cone), 25 hardpoints |
| `bracket_plain.stl` | The same triangles as a plain STL |
| `knob_hardpoint.stl` | Knob as a hardpoint STL: 2,958 triangles, 4 faces (plane, cylinder, sphere, torus), 4 hardpoints |
| `knob_plain.stl` | The same triangles as a plain STL |

Things to try:

- Load a pair in your slicer. They should look and slice the same. (This has not been tried
  in a real slicer yet; if they differ, please open an issue.)
- `python src/hstl.py info examples/bracket_hardpoint.stl`
- `python src/hstl.py verify examples/bracket_hardpoint.stl`
- `python src/hstl.py strip examples/bracket_hardpoint.stl my_plain.stl`, then compare with
  `bracket_plain.stl` (the triangles are identical; only the header differs).

The parts are not real products. They were built with OpenCASCADE for testing
(`tests/cadparts.py`) and written by `tools/make_examples.py`.
