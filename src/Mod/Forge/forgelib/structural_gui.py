# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi "Profilato strutturale" e "Distinta di taglio" (M5.2)."""

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib.commands import icon_path
from forgelib.features import profiles, structural

PARAMS = "User parameter:BaseApp/Preferences/Mod/Forge"


def selected_path():
    """(oggetto, spigoli) dalla selezione: spigoli selezionati oppure l'intero oggetto."""
    selection = FreeCADGui.Selection.getSelectionEx()
    if not selection:
        return None, []
    sel = selection[0]
    edges = [s for s in sel.SubElementNames if s.startswith("Edge")]
    return sel.Object, edges


def selected_members():
    return [
        o for o in FreeCADGui.Selection.getSelection()
        if isinstance(getattr(o, "Proxy", None), structural.StructuralMember)
    ]


def make_cut_list_sheet(doc, members, density=7.85e-6):
    sheet = doc.getObject("DistintaDiTaglio")
    if sheet is None:
        sheet = doc.addObject("Spreadsheet::Sheet", "DistintaDiTaglio")
        sheet.Label = "Distinta di taglio"
    sheet.clearAll()
    headers = ["Pos.", "Membro", "Profilo", "Lungh. asse", "Lungh. max", "Taglio inizio", "Taglio fine", "Massa"]
    for col, header in zip("ABCDEFGH", headers):
        sheet.set(f"{col}1", header)
    row = 2
    total = 0.0
    for member in members:
        for item in structural.cut_list(member, density):
            values = [
                str(row - 1), member.Label, item.profile,
                f"={item.centerline:.2f} mm", f"={item.overall:.2f} mm",
                f"={item.angle_start:.1f} deg", f"={item.angle_end:.1f} deg",
                f"={item.mass:.3f} kg",
            ]
            for col, value in zip("ABCDEFGH", values):
                sheet.set(f"{col}{row}", value)
            total += item.mass
            row += 1
    sheet.set(f"G{row}", "Totale")
    sheet.set(f"H{row}", f"={total:.3f} kg")
    doc.recompute()
    return sheet, row - 2


class _MemberCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_StructuralMember"),
            "MenuText": "Profilato strutturale",
            "ToolTip": "Crea un profilato (IPE, HEA, HEB, tubi, angolari, piatti EN) lungo gli spigoli "
            "selezionati di uno schizzo o schizzo 3D, con taglio a mitra agli spigoli",
        }

    def IsActive(self):
        return bool(FreeCADGui.Selection.getSelection())

    def Activated(self):
        path, edges = selected_path()
        if path is None:
            return
        params = FreeCAD.ParamGet(PARAMS)
        family = params.GetString("LastProfileFamily", "Tubo quadro/rett.")
        size = params.GetString("LastProfileSize", "40x40x3")
        if family not in profiles.FAMILIES or size not in profiles.sizes(family):
            family, size = "Tubo quadro/rett.", "40x40x3"
        doc = path.Document
        doc.openTransaction("Profilato strutturale")
        try:
            obj = structural.make_member(doc, path, family, size, edges)
            doc.recompute()
        finally:
            doc.commitTransaction()
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(obj)
        FreeCAD.Console.PrintMessage(
            "Forge: profilato creato; cambiare famiglia e dimensione nelle proprietà (Family, Size).\n"
        )


class _CutListCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_CutList"),
            "MenuText": "Distinta di taglio",
            "ToolTip": "Foglio di calcolo con profilo, lunghezze, angoli di taglio e massa di ogni "
            "membro dei profilati selezionati (o di tutti)",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        members = selected_members() or [
            o for o in doc.Objects if isinstance(getattr(o, "Proxy", None), structural.StructuralMember)
        ]
        if not members:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(), "Distinta di taglio", "Non ci sono profilati strutturali."
            )
            return
        doc.openTransaction("Distinta di taglio")
        try:
            make_cut_list_sheet(doc, members)
        finally:
            doc.commitTransaction()


STRUCTURAL_COMMANDS = ["Forge_StructuralMember", "Forge_CutList"]


def register():
    FreeCADGui.addCommand("Forge_StructuralMember", _MemberCommand())
    FreeCADGui.addCommand("Forge_CutList", _CutListCommand())
