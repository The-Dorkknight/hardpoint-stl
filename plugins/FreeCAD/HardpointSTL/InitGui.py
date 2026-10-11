# Required Notice: Copyright Matthew Armstrong (https://github.com/The-Dorkknight)
# Licensed under the PolyForm Noncommercial License 1.0.0. No warranty.
# Hardpoint STL workbench for FreeCAD (work in progress).
import os
import FreeCAD
import FreeCADGui


class HardpointSTLWorkbench(FreeCADGui.Workbench):
    MenuText = "Hardpoint STL"
    ToolTip = "Export an ordinary STL that also remembers the CAD faces, surface types and corners"

    def __init__(self):
        import hardpoint_stl_fc
        self.__class__.Icon = os.path.join(os.path.dirname(hardpoint_stl_fc.__file__),
                                           "Resources", "icons", "hardpoint.svg")

    def Initialize(self):
        import hardpoint_stl_fc
        hardpoint_stl_fc.register()
        cmds = ["HardpointSTL_Export"]
        self.appendToolbar("Hardpoint STL", cmds)
        self.appendMenu("Hardpoint STL", cmds)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def ContextMenu(self, recipient):
        self.appendContextMenu("Hardpoint STL", ["HardpointSTL_Export"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(HardpointSTLWorkbench())
