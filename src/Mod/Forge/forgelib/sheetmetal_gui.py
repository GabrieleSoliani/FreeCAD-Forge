# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi Forge per la lamiera: tabella di piega ed esportazione DXF dello sviluppo (M5)."""

import os

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib import sheetmetal
from forgelib.commands import icon_path

TABLE_HEADERS = ["Feature", "Angolo", "Raggio int.", "Spessore", "Fattore K", "Tolleranza", "Deduzione"]


def selected_unfold():
    for obj in FreeCADGui.Selection.getSelection():
        if hasattr(obj, "baseObject") and hasattr(obj, "KFactor"):
            return obj
    return None


def make_bend_table_sheet(unfold_obj):
    """Crea (o aggiorna) un foglio di calcolo con la tabella di piega dello sviluppo."""
    doc = unfold_obj.Document
    rows = sheetmetal.bend_table_for_unfold(unfold_obj)
    name = f"TabellaPiega_{unfold_obj.Name}"
    sheet = doc.getObject(name)
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", name)
        sheet.Label = f"Tabella di piega {unfold_obj.Label}"
    sheet.clearAll()
    columns = "ABCDEFG"
    for col, header in zip(columns, TABLE_HEADERS):
        sheet.set(f"{col}1", header)
    for i, row in enumerate(rows, start=2):
        values = [
            row.feature,
            f"={row.angle:.4f} deg",
            f"={row.radius:.4f} mm",
            f"={row.thickness:.4f} mm",
            f"={row.kfactor:.4f}",
            f"={row.allowance:.4f} mm",
            f"={row.deduction:.4f} mm",
        ]
        for col, value in zip(columns, values):
            sheet.set(f"{col}{i}", value)
    doc.recompute()
    return sheet, rows


class _BendTableCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_BendTable"),
            "MenuText": "Tabella di piega",
            "ToolTip": "Crea un foglio di calcolo con angolo, raggio, fattore K, tolleranza e "
            "deduzione di ogni piega dello sviluppo selezionato",
        }

    def IsActive(self):
        return selected_unfold() is not None

    def Activated(self):
        unfold_obj = selected_unfold()
        doc = unfold_obj.Document
        doc.openTransaction("Tabella di piega")
        try:
            make_bend_table_sheet(unfold_obj)
        finally:
            doc.commitTransaction()


class _ExportDxfCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_FlatDXF"),
            "MenuText": "Esporta sviluppo DXF",
            "ToolTip": "Esporta in DXF il contorno e le linee di piega dello sviluppo selezionato",
        }

    def IsActive(self):
        return selected_unfold() is not None

    def Activated(self):
        unfold_obj = selected_unfold()
        default = os.path.join(
            os.path.dirname(unfold_obj.Document.FileName or os.path.expanduser("~")),
            f"{unfold_obj.Label}.dxf",
        )
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            FreeCADGui.getMainWindow(), "Esporta sviluppo DXF", default, "DXF (*.dxf)"
        )
        if not path:
            return
        sheetmetal.export_flat_dxf(unfold_obj, path)
        FreeCAD.Console.PrintMessage(f"Forge: sviluppo esportato in {path}\n")


SHEETMETAL_FORGE_COMMANDS = ["Forge_BendTable", "Forge_ExportFlatDXF"]


def register():
    FreeCADGui.addCommand("Forge_BendTable", _BendTableCommand())
    FreeCADGui.addCommand("Forge_ExportFlatDXF", _ExportDxfCommand())
