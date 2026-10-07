# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi generali di Forge (menu Forge)."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib import settings

SETTINGS_COMMANDS = ["Forge_ApplySolidWorksSettings", "Forge_RevertSettings"]


class _ApplySettings:
    def GetResources(self):
        return {
            "MenuText": "Impostazioni stile SolidWorks",
            "ToolTip": "Navigazione SolidWorks, Forge all'avvio e scorciatoie SolidWorks "
            "(F, Ctrl+1…Ctrl+8, Ctrl+B). Le impostazioni precedenti vengono salvate.",
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
