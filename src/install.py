# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Hardpoint STL 0.1.0-wip (WORK IN PROGRESS): one-step setup. Standard library only.

    python src/install.py            install into FreeCAD and Fusion if they are found
    python src/install.py --check    only report what it would do
    python src/install.py --version

What it does, and nothing else:
  1. Copies the FreeCAD workbench into FreeCAD's user "Mod" folder and the Fusion add-in into
     Fusion's "AddIns" folder (every one it finds on this computer).
  2. Reads every copied file back and compares it with the original.
  3. Checks the example files with the format's own rules.
It does not touch FreeCAD's or Fusion's own files and needs no internet. It cannot start FreeCAD
or Fusion, so it cannot confirm that they load the plug-in: restart the program and look for the
"Hardpoint STL" workbench (FreeCAD) or Utilities > Add-Ins (Fusion).
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import hstl  # noqa: E402
from version import __version__, BUILD_DATE  # noqa: E402

NAME = "HardpointSTL"
HOME = os.path.expanduser("~")


def freecad_mod_dirs(env=os.environ):
    """Possible FreeCAD user Mod folders on this system (a folder is used when its parent exists)."""
    if sys.platform.startswith("win"):
        base = env.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))
        cands = [os.path.join(base, "FreeCAD", "Mod"), os.path.join(base, "FreeCAD", "v1-1", "Mod")]
    elif sys.platform == "darwin":
        base = os.path.join(HOME, "Library", "Application Support", "FreeCAD")
        cands = [os.path.join(base, "Mod"), os.path.join(base, "v1-1", "Mod")]
    else:
        share = env.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share"))
        cands = [os.path.join(share, "FreeCAD", "Mod"), os.path.join(share, "FreeCAD", "v1-1", "Mod"),
                 os.path.join(HOME, ".var", "app", "org.freecad.FreeCAD", "data", "FreeCAD", "Mod"),
                 os.path.join(HOME, ".FreeCAD", "Mod")]
    return [c for c in cands if os.path.isdir(os.path.dirname(c))]


def fusion_addin_dirs(env=os.environ):
    if sys.platform.startswith("win"):
        base = env.get("APPDATA", os.path.join(HOME, "AppData", "Roaming"))
    elif sys.platform == "darwin":
        base = os.path.join(HOME, "Library", "Application Support")
    else:
        return []                                    # Fusion has no Linux version
    cand = os.path.join(base, "Autodesk", "Autodesk Fusion 360", "API", "AddIns")
    return [cand] if os.path.isdir(os.path.dirname(cand)) else []


def _files(folder):
    out = []
    for dp, dn, fn in os.walk(folder):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            if not f.endswith(".pyc"):
                out.append(os.path.relpath(os.path.join(dp, f), folder))
    return sorted(out)


def copy_and_check(src, dst):
    """Copy folder src to dst (replacing an older copy), read back. -> list of problems."""
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "settings.json"))
    bad = []
    for rel in _files(src):
        if rel == "settings.json":
            continue
        a, b = os.path.join(src, rel), os.path.join(dst, rel)
        if not os.path.isfile(b) or open(a, "rb").read() != open(b, "rb").read():
            bad.append(rel)
    return bad


def main(argv):
    if "--version" in argv:
        print(f"Hardpoint STL {__version__} (build {BUILD_DATE})")
        return 0
    dry = "--check" in argv
    print(f"Hardpoint STL {__version__} (build {BUILD_DATE}) - WORK IN PROGRESS\n")
    problems = 0
    jobs = [("FreeCAD", freecad_mod_dirs(), os.path.join(ROOT, "plugins", "FreeCAD", NAME)),
            ("Fusion", fusion_addin_dirs(), os.path.join(ROOT, "plugins", "Fusion", NAME))]
    for prog, dirs, src in jobs:
        if not os.path.isdir(src):
            print(f"{prog}: the plug-in folder is missing from this download ({src}).")
            problems += 1
            continue
        if not dirs:
            print(f"{prog}: not found on this computer, skipped.")
            continue
        for d in dirs:
            dst = os.path.join(d, NAME)
            if dry:
                print(f"{prog}: would install into {dst}")
                continue
            try:
                bad = copy_and_check(src, dst)
            except OSError as e:
                print(f"{prog}: could not install into {dst}: {e}")
                problems += 1
                continue
            if bad:
                print(f"{prog}: copied into {dst}, but these files did not read back identically: {bad}")
                problems += 1
            else:
                print(f"{prog}: installed into {dst} ({len(_files(src))} files, read back and compared: OK)")
    print()
    for f in sorted(os.listdir(os.path.join(ROOT, "examples"))):
        if f.endswith("_hardpoint.stl"):
            ok, lines = hstl.verify(os.path.join(ROOT, "examples", f))
            print(f"examples/{f}: " + ("passes the format checks" if ok else "FAILS the format checks"))
            problems += 0 if ok else 1
    print("\nNext: restart FreeCAD (choose the 'Hardpoint STL' workbench) or Fusion (Utilities > Add-Ins).")
    print("This script cannot start those programs, so it cannot confirm that they load the plug-in.")
    print("Not installed anything? Then neither program was found: copy plugins/FreeCAD/HardpointSTL into")
    print("FreeCAD's Mod folder by hand (see the README).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
