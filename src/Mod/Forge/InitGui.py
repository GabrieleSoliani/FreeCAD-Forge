# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: workbench unificato in stile SolidWorks.


class ForgeWorkbench(Workbench):
    """Ambiente unico per parti, assiemi e tavole, con command manager a schede."""

    # Letto da ViewProviderSketch (patch al core, vedi CORE_PATCHES.md): la modifica di uno
    # schizzo resta in Forge invece di passare al workbench Sketcher.
    HandlesSketchEditing = True

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
        from forgelib import commands as forge_commands
        from forgelib.ui import catalog

        forge_commands.register()
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
            for toolbar, wanted in tab.all_toolbars():
                commands, missing = catalog.resolve_commands(wanted, available)
                if missing:
                    FreeCAD.Console.PrintLog(
                        f"Forge: toolbar {toolbar}, comandi assenti: {', '.join(missing)}\n"
                    )
                if commands:
                    self.appendToolbar(toolbar, commands)
            commands, _ = catalog.resolve_commands(tab.commands, available)
            if commands:
                self.appendMenu(["&Forge", tab.label], commands)
        self.appendMenu("&Forge", ["Separator"] + forge_commands.SETTINGS_COMMANDS)

    def Activated(self):
        from forgelib.ui import catalog
        from forgelib.ui.command_manager import CommandManager

        if self._manager is None:
            self._manager = CommandManager(catalog.TABS)
        self._manager.activate()

        from forgelib import commands as forge_commands

        forge_commands.offer_settings_once()

    def Deactivated(self):
        if self._manager is not None:
            self._manager.deactivate()

    def ContextMenu(self, recipient):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(ForgeWorkbench())

FreeCAD.__unit_test__ += ["ForgeTests.TestForgeGui"]
