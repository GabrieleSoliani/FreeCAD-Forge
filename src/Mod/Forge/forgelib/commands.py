# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi generali di Forge (menu Forge)."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib import settings

SETTINGS_COMMANDS = ["Forge_ApplySolidWorksSettings", "Forge_RevertSettings"]
MENU_COMMANDS = ["Forge_RadialMenu"]


class _ApplySettings:
    def GetResources(self):
        return {
            "MenuText": "Impostazioni stile SolidWorks",
            "ToolTip": "Navigazione SolidWorks, Forge all'avvio e scorciatoie SolidWorks "
            "(F, Ctrl+1…Ctrl+8, Ctrl+B, S menu radiale). Le impostazioni precedenti vengono salvate.",
        }

    def IsActive(self):
        return not settings.is_applied()

    def Activated(self):
        if settings.apply():
            FreeCAD.Console.PrintMessage("Forge: impostazioni stile SolidWorks applicate.\n")


class _RevertSettings:
    def GetResources(self):
        return {
            "MenuText": "Ripristina impostazioni precedenti",
            "ToolTip": "Annulla le impostazioni stile SolidWorks applicate da Forge",
        }

    def IsActive(self):
        return settings.is_applied()

    def Activated(self):
        if settings.revert():
            FreeCAD.Console.PrintMessage("Forge: impostazioni precedenti ripristinate.\n")


def register():
    FreeCADGui.addCommand("Forge_ApplySolidWorksSettings", _ApplySettings())
    FreeCADGui.addCommand("Forge_RevertSettings", _RevertSettings())
    register_rollback()
    register_radial()


def offer_settings_once():
    """Alla prima attivazione di Forge propone le impostazioni stile SolidWorks.

    Non viene mostrato durante i test (RunMode "Internal") né se già proposto.
    """
    params = FreeCAD.ParamGet(settings.FORGE_PARAMS)
    if FreeCAD.ConfigGet("RunMode") == "Internal" or params.GetBool("SettingsOffered", False):
        return
    params.SetBool("SettingsOffered", True)
    if settings.is_applied():
        return

    box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
    box.setWindowTitle("FreeCAD Forge")
    box.setIcon(QtWidgets.QMessageBox.Question)
    box.setText("Applicare le impostazioni in stile SolidWorks?")
    box.setInformativeText(
        "Navigazione con il mouse SolidWorks, Forge come ambiente all'avvio e scorciatoie "
        "SolidWorks (F adatta, Ctrl+1…Ctrl+8 viste, Ctrl+B ricostruisci).\n\n"
        "Si possono annullare in qualsiasi momento dal menu Forge."
    )
    box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    box.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    def done(_result):
        if box.clickedButton() is box.button(QtWidgets.QMessageBox.Yes):
            FreeCADGui.runCommand("Forge_ApplySolidWorksSettings")

    box.finished.connect(done)
    QtCore.QTimer.singleShot(0, box.open)


def icon_path(name):
    import os

    import forgelib

    return os.path.join(
        os.path.dirname(os.path.dirname(forgelib.__file__)), "Resources", "icons", name + ".svg"
    )


class _RollbackCommand:
    """Sposta la rollback bar del corpo attivo."""

    def __init__(self, action, icon, text, tip):
        self._action = action
        self._icon = icon
        self._text = text
        self._tip = tip

    def GetResources(self):
        return {"Pixmap": icon_path(self._icon), "MenuText": self._text, "ToolTip": self._tip}

    def IsActive(self):
        from forgelib import rollback

        body = rollback.active_body()
        if body is None:
            return False
        pos = rollback.position(body)
        if self._action == "previous":
            return pos > 0
        return pos < len(rollback.solid_features(body))

    def Activated(self):
        from forgelib import rollback

        body = rollback.active_body()
        if body is None:
            return
        if self._action == "previous":
            rollback.step(body, -1)
        elif self._action == "next":
            rollback.step(body, 1)
        else:
            rollback.to_end(body)


ROLLBACK_COMMANDS = ["Forge_RollbackPrevious", "Forge_RollbackNext", "Forge_RollbackToEnd"]


def register_rollback():
    FreeCADGui.addCommand(
        "Forge_RollbackPrevious",
        _RollbackCommand("previous", "Forge_Rollback_prev", "Rollback indietro",
                         "Porta la rollback bar del corpo attivo indietro di una feature"),
    )
    FreeCADGui.addCommand(
        "Forge_RollbackNext",
        _RollbackCommand("next", "Forge_Rollback_next", "Rollback avanti",
                         "Porta la rollback bar del corpo attivo avanti di una feature"),
    )
    FreeCADGui.addCommand(
        "Forge_RollbackToEnd",
        _RollbackCommand("end", "Forge_Rollback_end", "Rollback alla fine",
                         "Riporta la rollback bar alla fine dell'albero (tutte le feature attive)"),
    )


class _RadialMenuCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_RadialMenu"),
            "MenuText": "Menu radiale",
            "ToolTip": "Menu circolare con i comandi del contesto corrente (tasto S con le "
            "impostazioni stile SolidWorks)",
        }

    def IsActive(self):
        return FreeCADGui.ActiveDocument is not None

    def Activated(self):
        from forgelib.ui.radial import show_radial_menu

        show_radial_menu()


def register_radial():
    FreeCADGui.addCommand("Forge_RadialMenu", _RadialMenuCommand())
