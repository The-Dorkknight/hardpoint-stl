# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Hardpoint STL command for FreeCAD: selected solids -> an ordinary STL that also remembers the
CAD faces (see hardpoint_fc.py for the export itself, hstl.py for the file format)."""
import os
import re

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui

try:
    from PySide import QtWidgets
except ImportError:  # old shim: widgets live in QtGui
    QtWidgets = QtGui

import hardpoint_fc

HERE = os.path.dirname(os.path.abspath(__file__))
ICONS = os.path.join(HERE, "Resources", "icons")
PARAMS = "User parameter:BaseApp/Preferences/Mod/HardpointSTL"
TITLE = "Hardpoint STL"


def prefs():
    return FreeCAD.ParamGet(PARAMS)


def _exec(dlg):
    return dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()


def _warn(msg):
    QtWidgets.QMessageBox.warning(FreeCADGui.getMainWindow(), TITLE, msg)


def _safe_name(s):
    return re.sub(r"[^\w\-. ]+", "_", s).strip() or "part"


def _selected():
    out = []
    for o in FreeCADGui.Selection.getSelection():
        if hasattr(o, "Shape") and not o.Shape.isNull() and o.Shape.Faces:
            out.append(o)
    return out


class HardpointDialog(QtWidgets.QDialog):
    def __init__(self, what):
        super().__init__(FreeCADGui.getMainWindow())
        self.setWindowTitle("Hardpoint STL — export")
        p = prefs()
        lay = QtWidgets.QFormLayout(self)
        info = QtWidgets.QLabel(
            what + "\n\nThe file is an ordinary STL — slicers see the same triangles as a normal "
            "export. Its spare bytes also record which triangles belong to which CAD face, what kind "
            "of surface each face is, and where the corners are, so a converter can turn it back into "
            "a solid without guessing.")
        info.setWordWrap(True)
        lay.addRow(info)
        self.dev = QtWidgets.QDoubleSpinBox()
        self.dev.setDecimals(3)
        self.dev.setRange(0.001, 5.0)
        self.dev.setSingleStep(0.01)
        self.dev.setSuffix(" mm")
        self.dev.setValue(p.GetFloat("HpDeviation", 0.05))
        self.dev.setToolTip("How far the triangles may be from the true surface. Smaller = smoother "
                            "curves and a bigger file.")
        lay.addRow("Surface deviation", self.dev)
        self.ang = QtWidgets.QDoubleSpinBox()
        self.ang.setDecimals(0)
        self.ang.setRange(1.0, 45.0)
        self.ang.setSuffix(" °")
        self.ang.setValue(p.GetFloat("HpAngle", 15.0))
        self.ang.setToolTip("Largest angle between neighbouring triangles on a curve.")
        lay.addRow("Angle", self.ang)
        bb = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def save(self):
        p = prefs()
        p.SetFloat("HpDeviation", self.dev.value())
        p.SetFloat("HpAngle", self.ang.value())


class HardpointCmd:
    def GetResources(self):
        return {"Pixmap": os.path.join(ICONS, "hardpoint.svg"), "MenuText": "Export hardpoint STL",
                "ToolTip": "Save the selected solid(s) as an STL that slicers read as usual, and that "
                           "also remembers the CAD faces and corners so it converts back to a solid "
                           "without guessing."}

    def IsActive(self):
        return True

    def Activated(self):
        objs = _selected()
        if not objs:
            _warn("Select one or more solid objects first (in the model tree or the 3D view).")
            return
        what = (f"'{objs[0].Label}'" if len(objs) == 1 else f"{len(objs)} objects, saved together in one file")
        dlg = HardpointDialog(what)
        if _exec(dlg) != QtWidgets.QDialog.Accepted:
            return
        dlg.save()
        p = prefs()
        start = os.path.join(p.GetString("LastDir", ""), _safe_name(objs[0].Label) + ".stl")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(FreeCADGui.getMainWindow(), "Save hardpoint STL",
                                                        start, "STL (*.stl)")
        if not path:
            return
        if not path.lower().endswith(".stl"):
            path += ".stl"
        p.SetString("LastDir", os.path.dirname(path))
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            info = hardpoint_fc.export([hardpoint_fc.global_shape(o) for o in objs], path,
                                       p.GetFloat("HpDeviation", 0.05), p.GetFloat("HpAngle", 15.0))
        except Exception as e:  # noqa
            QtWidgets.QApplication.restoreOverrideCursor()
            _warn(f"Couldn't export: {e}")
            return
        QtWidgets.QApplication.restoreOverrideCursor()
        text = hardpoint_fc.summary(info)
        FreeCAD.Console.PrintMessage(f"Hardpoint STL: saved {path}\n  " + text.replace("\n", "\n  ") + "\n")
        QtWidgets.QMessageBox.information(FreeCADGui.getMainWindow(), TITLE, f"Saved {path}\n\n{text}")




_registered = False


def register():
    global _registered
    if _registered:
        return
    FreeCADGui.addCommand("HardpointSTL_Export", HardpointCmd())
    _registered = True
