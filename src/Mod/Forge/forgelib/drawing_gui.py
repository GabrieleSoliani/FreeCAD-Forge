# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comando "Tavola automatica" (M7)."""

import FreeCAD
import FreeCADGui

from forgelib import drawing
from forgelib.commands import icon_path


def drawing_sources(doc):
    """Oggetti selezionati, oppure i componenti dell'assieme attivo, oppure tutti i componenti."""
    selection = FreeCADGui.Selection.getSelection()
    if selection:
        return selection
    gdoc = FreeCADGui.getDocument(doc.Name)
    try:
        active = gdoc.ActiveView.getActiveObject("part")
    except Exception:
        active = None
    candidates = active.OutList if active is not None else doc.Objects
    return [o for o in candidates if drawing.is_component(o) and getattr(o, "Visibility", True)]


def make_auto_drawing(doc, sources):
    page, info = drawing.auto_drawing(doc, sources)
    rows = drawing.bom_rows(sources)
    main = sources[0] if len(sources) == 1 else None
    document_type = "Disegno di particolare" if len(rows) <= 1 else "Disegno d'assieme"
    drawing.fill_title_block(page, drawing.title_block_values(page, main, document_type))
    if len(rows) > 1:
        drawing.add_bom(page, rows)
        drawing.add_balloons(page, drawing.front_view(info), rows)
    doc.recompute()
    return page, info, rows


class _AutoDrawingCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_AutoDrawing"),
            "MenuText": "Tavola automatica",
            "ToolTip": "Crea una tavola A3 ISO con viste frontale, superiore, laterale (primo diedro) e "
            "assonometria, cartiglio compilato e, per gli assiemi, distinta con palloncini",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        sources = drawing_sources(doc)
        if not sources:
            FreeCAD.Console.PrintWarning("Forge: niente da mettere in tavola.\n")
            return
        doc.openTransaction("Tavola automatica")
        try:
            page, _, _ = make_auto_drawing(doc, sources)
        finally:
            doc.commitTransaction()
        page.ViewObject.doubleClicked()


def register():
    FreeCADGui.addCommand("Forge_AutoDrawing", _AutoDrawingCommand())
