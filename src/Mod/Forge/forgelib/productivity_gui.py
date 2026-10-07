# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi Pack and Go e libreria personale (M8)."""

import os

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib import productivity
from forgelib.commands import icon_path


class _PackAndGoCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_PackAndGo"),
            "MenuText": "Pack and Go",
            "ToolTip": "Copia il documento e i file collegati della sua cartella in una nuova "
            "cartella, mantenendo i collegamenti",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if not doc.FileName:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(), "Pack and Go", "Salvare prima il documento.")
            return
        target = QtWidgets.QFileDialog.getExistingDirectory(
            FreeCADGui.getMainWindow(), "Cartella di destinazione (vuota)")
        if not target:
            return
        result = productivity.pack_and_go(doc, target)
        text = f"File copiati: {len(result.copied)}."
        if result.external:
            text += "\nNon copiati (fuori dalla cartella del documento):\n" + "\n".join(result.external)
        QtWidgets.QMessageBox.information(FreeCADGui.getMainWindow(), "Pack and Go", text)


class _LibraryAddCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_LibraryAdd"),
            "MenuText": "Aggiungi alla libreria",
            "ToolTip": "Salva l'oggetto selezionato nella libreria personale di componenti",
        }

    def IsActive(self):
        return len(FreeCADGui.Selection.getSelection()) == 1

    def Activated(self):
        obj = FreeCADGui.Selection.getSelection()[0]
        name, ok = QtWidgets.QInputDialog.getText(
            FreeCADGui.getMainWindow(), "Libreria personale", "Nome del componente:",
            QtWidgets.QLineEdit.Normal, obj.Label)
        if ok and name.strip():
            path = productivity.add_to_library(obj, name.strip())
            FreeCAD.Console.PrintMessage(f"Forge: componente salvato in {path}\n")


class _LibraryInsertCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_LibraryInsert"),
            "MenuText": "Inserisci dalla libreria",
            "ToolTip": "Inserisce un componente della libreria personale (come link se il "
            "documento è salvato)",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        paths = productivity.list_library()
        if not paths:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(), "Libreria personale",
                f"La libreria è vuota ({productivity.library_dir()}).")
            return
        names = [os.path.splitext(os.path.basename(p))[0] for p in paths]
        name, ok = QtWidgets.QInputDialog.getItem(
            FreeCADGui.getMainWindow(), "Libreria personale", "Componente:", names, 0, False)
        if not ok:
            return
        doc = FreeCAD.ActiveDocument
        doc.openTransaction("Inserisci dalla libreria")
        try:
            productivity.insert_from_library(doc, paths[names.index(name)])
        finally:
            doc.commitTransaction()


def register():
    FreeCADGui.addCommand("Forge_PackAndGo", _PackAndGoCommand())
    FreeCADGui.addCommand("Forge_LibraryAdd", _LibraryAddCommand())
    FreeCADGui.addCommand("Forge_LibraryInsert", _LibraryInsertCommand())
