# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Run src/install.py against a throw-away home folder. Standard library only:  python tests/test_install.py"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    with tempfile.TemporaryDirectory() as home:
        env = dict(os.environ, HOME=home, USERPROFILE=home, XDG_DATA_HOME=os.path.join(home, ".local", "share"))
        os.makedirs(os.path.join(home, ".local", "share", "FreeCAD"))   # FreeCAD has been run once
        run = lambda *a: subprocess.run([sys.executable, os.path.join(ROOT, "src", "install.py"), *a],
                                        env=env, capture_output=True, text=True)
        r = run("--check")
        assert r.returncode == 0 and "would install into" in r.stdout, r.stdout + r.stderr
        assert not os.path.exists(os.path.join(home, ".local", "share", "FreeCAD", "Mod", "HardpointSTL")), "--check wrote files"
        if sys.platform.startswith("linux"):
            r = run()
            assert r.returncode == 0 and "read back and compared: OK" in r.stdout, r.stdout + r.stderr
            dst = os.path.join(home, ".local", "share", "FreeCAD", "Mod", "HardpointSTL")
            for f in ("InitGui.py", "hardpoint_fc.py", "hardpoint_stl_fc.py", "hstl.py", "package.xml",
                      os.path.join("Resources", "icons", "hardpoint.svg")):
                assert os.path.isfile(os.path.join(dst, f)), f
            assert run().returncode == 0, "a second run must replace the first cleanly"
    print("installer self-check passed")


if __name__ == "__main__":
    main()
