# Contributing

**WORK IN PROGRESS: MANY FEATURES MAY BE BROKEN.** Bug reports, test results from real FreeCAD,
Fusion and slicers, other CAD exporters and pull requests are welcome.

- Open an issue first for anything big. Use the bug-report form.
- By contributing you agree your contribution is licensed under the same [PolyForm Noncommercial License 1.0.0](LICENSE.md) as the project, with the Required Notice `Copyright Matthew Armstrong (https://github.com/The-Dorkknight)` kept in every source file header.
- Only contribute code you have the right to contribute. Don't paste in code from projects with incompatible licences.
- `src/hstl.py` is copied into both plug-in folders (they must run on their own inside FreeCAD and Fusion). Change it in `src/` and copy it over; `python tests/test_hstl.py` checks the three copies match.
- Two rules for format changes: a labelled file must stay byte-identical in its triangles to its plain twin, and labels must stay hints that a reader checks. Raise the format version if the bit layout or header changes.
- Before a PR, run `python tests/test_hstl.py` and `python tests/test_install.py`, and `python tests/test_hardpoint_cad.py` if you touched the format or an exporter. [DESIGN_NOTES.md](DESIGN_NOTES.md) has the background and a list of open work.
