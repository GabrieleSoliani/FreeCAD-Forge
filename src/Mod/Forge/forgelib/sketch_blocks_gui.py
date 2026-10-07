# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi "Salva blocco" e "Inserisci blocco" per lo schizzo in modifica (M2.3)."""

import os
import re

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib import sketch_blocks
from forgelib.commands import icon_path


def sketch_in_edit():
    gdoc = FreeCADGui.ActiveDocument
    if gdoc is None:
        return None
    vp = gdoc.getInEdit()
    if vp is not None and hasattr(vp, "Object") and vp.Object.isDerivedFrom("Sketcher::SketchObject"):
        return vp.Object
    return None


def selected_geometry_ids(sketch):
    """Geo id (base 0) degli spigoli selezionati nello schizzo ("Edge3" → 2)."""
    ids = []
    for sel in FreeCADGui.Selection.getSelectionEx():
        if sel.Object is not sketch:
            continue
        for sub in sel.SubElementNames:
            match = re.fullmatch(r"Edge(\d+)", sub)
            if match:
                ids.append(int(match.group(1)) - 1)
    return sorted(set(ids))


def safe_file_name(name):
    cleaned = re.sub(r"[^\w\- ]+", "", name, flags=re.UNICODE).strip()
    return cleaned or "blocco"


class _SaveBlockCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_SketchBlock"),
            "MenuText": "Salva blocco",
            "ToolTip": "Salva le geometrie selezionate dello schizzo, con i loro vincoli interni, "
            "come blocco riutilizzabile",
        }

    def IsActive(self):
        sketch = sketch_in_edit()
        return sketch is not None and bool(selected_geometry_ids(sketch))

    def Activated(self):
        sketch = sketch_in_edit()
        ids = selected_geometry_ids(sketch)
        name, ok = QtWidgets.QInputDialog.getText(
            FreeCADGui.getMainWindow(), "Salva blocco", "Nome del blocco:"
        )
        if not ok or not name.strip():
            return
        path = os.path.join(sketch_blocks.blocks_dir(), safe_file_name(name) + ".json")
        data = sketch_blocks.save_block(sketch, ids, path, name.strip())
        FreeCAD.Console.PrintMessage(
            f"Forge: blocco \"{name}\" salvato ({len(data['geometries'])} geometrie, "
            f"{len(data['constraints'])} vincoli) in {path}\n"
        )


class _InsertBlockCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_SketchBlockInsert"),
            "MenuText": "Inserisci blocco",
            "ToolTip": "Inserisce nello schizzo un blocco salvato (nell'origine: poi trascinalo o "
            "vincolalo dove serve)",
        }

    def IsActive(self):
        return sketch_in_edit() is not None

    def Activated(self):
        sketch = sketch_in_edit()
        paths = sketch_blocks.list_blocks()
        if not paths:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Inserisci blocco",
                "Non ci sono blocchi salvati. Seleziona delle geometrie e usa \"Salva blocco\".",
            )
            return
        names = [os.path.splitext(os.path.basename(p))[0] for p in paths]
        name, ok = QtWidgets.QInputDialog.getItem(
            FreeCADGui.getMainWindow(), "Inserisci blocco", "Blocco:", names, 0, False
        )
        if not ok:
            return
        data = sketch_blocks.load_block(paths[names.index(name)])
        doc = sketch.Document
        doc.openTransaction("Inserisci blocco")
        try:
            sketch_blocks.insert_block(sketch, data)
        finally:
            doc.commitTransaction()
        doc.recompute()


BLOCK_COMMANDS = ["Forge_SaveSketchBlock", "Forge_InsertSketchBlock"]


def register():
    FreeCADGui.addCommand("Forge_SaveSketchBlock", _SaveBlockCommand())
    FreeCADGui.addCommand("Forge_InsertSketchBlock", _InsertBlockCommand())
