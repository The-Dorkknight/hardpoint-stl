# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
"""Hardpoint STL add-in for Autodesk Fusion (work in progress; not yet run in real Fusion).

Saves solid bodies as an ordinary binary STL that also remembers the CAD faces, surface types
and corners (see hardpoint_fusion.py for the export, hstl.py for the file format).
"""
import json
import os
import re
import sys
import traceback

import adsk.core
import adsk.fusion

try:
    from . import hardpoint_fusion
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hardpoint_fusion

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "resources", "hardpoint")
CMD_ID = "HardpointSTL_Export"
TITLE = "Hardpoint STL"
PANELS = ["SolidScriptsAddinsPanel"]                       # Utilities -> Add-Ins
EXTRA_PANELS = ["ParaMeshModifyPanel", "MeshModifyPanel"]  # Mesh tab, if these ids exist

app = adsk.core.Application.get()
ui = app.userInterface
_handlers = []


def _settings_path():
    p = os.path.join(HERE, "settings.json")
    try:
        with open(p, "a"):
            pass
        return p
    except OSError:
        return os.path.join(os.path.expanduser("~"), ".hardpoint_stl_fusion.json")


def load_settings():
    d = dict(hp_tol=0.05, hp_ang=15.0, hp_dir="")
    try:
        with open(_settings_path(), encoding="utf-8") as fh:
            d.update(json.load(fh))
    except Exception:
        pass
    return d


def save_settings(d):
    try:
        with open(_settings_path(), "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1)
    except Exception:
        pass


def _safe(s):
    return re.sub(r"[^\w\-. ]+", "_", s or "").strip() or "part"


class CreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            s = load_settings()
            cmd = args.command
            cmd.isExecutedWhenPreEmpted = False
            inp = cmd.commandInputs
            sel = inp.addSelectionInput("bodies", "Solid bodies", "Select the solid bodies to export")
            sel.addSelectionFilter("SolidBodies")
            sel.setSelectionLimits(1, 0)
            t = inp.addFloatSpinnerCommandInput("hp_tol", "Surface deviation mm", "", 0.001, 5.0, 0.01,
                                                float(s.get("hp_tol", 0.05)))
            t.tooltip = "How far the triangles may be from the true surface. Smaller = smoother curves, bigger file."
            a = inp.addFloatSpinnerCommandInput("hp_ang", "Angle (degrees)", "", 1.0, 45.0, 1.0,
                                                float(s.get("hp_ang", 15.0)))
            a.tooltip = "Largest angle between neighbouring triangles on a curve."
            inp.addTextBoxCommandInput(
                "hp_info", "", "The file is an ordinary STL: slicers see the same triangles as a normal "
                "export. Its spare bytes also record which triangles belong to which CAD face, the kind "
                "of surface, and the corners.", 4, True)
            h = ExecuteHandler()
            cmd.execute.add(h)
            _handlers.append(h)
        except Exception:
            ui.messageBox(TITLE + ":\n" + traceback.format_exc())


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inp = args.command.commandInputs
            s = load_settings()
            s["hp_tol"] = inp.itemById("hp_tol").value
            s["hp_ang"] = inp.itemById("hp_ang").value
            sel = inp.itemById("bodies")
            bodies = []
            for k in range(sel.selectionCount):
                b = adsk.fusion.BRepBody.cast(sel.selection(k).entity)
                if b:
                    bodies.append(b.nativeObject or b)       # component coordinates
            if not bodies:
                ui.messageBox("Select one or more solid bodies.", TITLE)
                return
            fd = ui.createFileDialog()
            fd.title, fd.filter = "Save hardpoint STL", "STL (*.stl)"
            fd.initialFilename = _safe(bodies[0].name) + ".stl"
            if s.get("hp_dir") and os.path.isdir(s["hp_dir"]):
                fd.initialDirectory = s["hp_dir"]
            if fd.showSave() != adsk.core.DialogResults.DialogOK:
                return
            path = fd.filename
            if not path.lower().endswith(".stl"):
                path += ".stl"
            info = hardpoint_fusion.export(bodies, path, float(s["hp_tol"]), float(s["hp_ang"]))
            s["hp_dir"] = os.path.dirname(path)
            save_settings(s)
            ui.messageBox(f"Saved {path}\n\n" + hardpoint_fusion.summary(info), TITLE)
        except Exception:
            ui.messageBox(TITLE + ":\n" + traceback.format_exc())


def run(context):
    try:
        cd = ui.commandDefinitions.itemById(CMD_ID)
        if cd:
            cd.deleteMe()
        cd = ui.commandDefinitions.addButtonDefinition(
            CMD_ID, "Export hardpoint STL",
            "Save solid bodies as an STL that slicers read as usual and that also remembers the CAD "
            "faces, surface types and corners.", RES)
        ch = CreatedHandler()
        cd.commandCreated.add(ch)
        _handlers.append(ch)
        for pid in PANELS + EXTRA_PANELS:
            panel = ui.allToolbarPanels.itemById(pid)
            if panel and not panel.controls.itemById(CMD_ID):
                panel.controls.addCommand(cd)
    except Exception:
        ui.messageBox(TITLE + " failed to start:\n" + traceback.format_exc())


def stop(context):
    try:
        for pid in PANELS + EXTRA_PANELS:
            panel = ui.allToolbarPanels.itemById(pid)
            c = panel.controls.itemById(CMD_ID) if panel else None
            if c:
                c.deleteMe()
        cd = ui.commandDefinitions.itemById(CMD_ID)
        if cd:
            cd.deleteMe()
        _handlers.clear()
    except Exception:
        ui.messageBox(TITLE + " stop:\n" + traceback.format_exc())
