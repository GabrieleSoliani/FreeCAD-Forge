# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: workbench unificato in stile SolidWorks.


class ForgeWorkbench(Workbench):
    """Ambiente unico per parti, assiemi e tavole, con command manager a schede."""

    def __init__(self):
        import os
        import forgelib

        icon = os.path.join(
            os.path.dirname(os.path.dirname(forgelib.__file__)),
            "Resources",
            "icons",
            "ForgeWorkbench.svg",
        )
        self.__class__.Icon = icon
        self.__class__.MenuText = "Forge"
        self.__class__.ToolTip = (
            "Ambiente unificato in stile SolidWorks: schizzo, feature, superfici, "
            "valutazione, assieme e tavola senza cambiare workbench"
        )
        self._manager = None

    def Initialize(self):
        import importlib
        import FreeCAD
        import FreeCADGui
        from forgelib.ui import catalog

        for name, required in catalog.GUI_MODULES:
            try:
                importlib.import_module(name)
            except ImportError as err:
                if required:
                    raise
                FreeCAD.Console.PrintLog(f"Forge: modulo {name} non disponibile: {err}\n")
        for name in catalog.PYTHON_COMMAND_MODULES:
            try:
                importlib.import_module(name)
            except Exception as err:
                FreeCAD.Console.PrintLog(f"Forge: comandi di {name} non caricati: {err}\n")

        available = set(FreeCADGui.listCommands())
        for tab in catalog.TABS:
            commands, missing = catalog.resolve_commands(tab.commands, available)
            if missing:
                FreeCAD.Console.PrintLog(
                    f"Forge: scheda {tab.label}, comandi assenti: {', '.join(missing)}\n"
                )
            if commands:
                self.appendToolbar(tab.toolbar_name, commands)
                self.appendMenu(["&Forge", tab.label], commands)

    def Activated(self):
        from forgelib.ui import catalog
        from forgelib.ui.command_manager import CommandManager

        if self._manager is None:
            self._manager = CommandManager(catalog.TABS)
        self._manager.activate()

    def Deactivated(self):
        if self._manager is not None:
            self._manager.deactivate()

    def ContextMenu(self, recipient):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(ForgeWorkbench())

FreeCAD.__unit_test__ += ["ForgeTests.TestForgeGui"]
