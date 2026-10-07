# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi d'assieme di Forge: viteria ISO, serie e specchiatura di componenti (M6)."""

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib.commands import icon_path
from forgelib.features import component_pattern, fasteners


def active_container():
    """Assieme (o Part) attivo nella vista, per inserirvi i nuovi componenti."""
    gdoc = FreeCADGui.ActiveDocument
    if gdoc is None:
        return None
    try:
        return gdoc.ActiveView.getActiveObject("part")
    except Exception:
        return None


def selected_circle():
    """(spigolo circolare in coordinate globali, forma globale dell'oggetto) dalla selezione."""
    for sel in FreeCADGui.Selection.getSelectionEx("", 0):
        for sub in sel.SubObjects:
            if sub.ShapeType == "Edge" and sub.Curve.TypeId == "Part::GeomCircle":
                from forgelib import evaluate

                return sub, evaluate.global_shape(sel.Object)
    return None, None


def insert_fastener(doc, kind, size, length, edge=None, shape=None, container=None):
    placement = fasteners.placement_on_circle(edge, shape) if edge is not None else None
    obj = fasteners.make_fastener(doc, kind, size, length, placement, name=kind.replace(" ", ""))
    obj.Label = fasteners.designation(kind, size, length)
    if container is not None and hasattr(container, "addObject"):
        container.addObject(obj)
    doc.recompute()
    return obj


class FastenerDialog(QtWidgets.QDialog):
    def __init__(self, size=None, parent=None):
        super().__init__(parent or FreeCADGui.getMainWindow())
        self.setWindowTitle("Viteria ISO")
        form = QtWidgets.QFormLayout(self)
        self.kind = QtWidgets.QComboBox(self)
        for key, text in fasteners.TYPES.items():
            self.kind.addItem(f"{key} – {text}", key)
        self.size = QtWidgets.QComboBox(self)
        self.size.addItems(fasteners.SIZES)
        if size:
            self.size.setCurrentText(size)
        self.length = QtWidgets.QComboBox(self)
        self.length.addItems([f"{v}" for v in fasteners.LENGTHS])
        self.length.setCurrentText("20")
        form.addRow("Tipo", self.kind)
        form.addRow("Diametro", self.size)
        form.addRow("Lunghezza (viti)", self.length)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return self.kind.currentData(), self.size.currentText(), float(self.length.currentText())


class _FastenerCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_Fastener"),
            "MenuText": "Viteria",
            "ToolTip": "Inserisce viti, dadi e rosette ISO. Con il bordo di un foro selezionato "
            "propone il diametro adatto e posiziona l'elemento sul foro",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        edge, shape = selected_circle()
        size = fasteners.size_for_hole(2 * edge.Curve.Radius) if edge is not None else None
        dialog = FastenerDialog(size)
        if not dialog.exec():
            return
        kind, size, length = dialog.values()
        doc.openTransaction("Viteria")
        try:
            insert_fastener(doc, kind, size, length, edge, shape, active_container())
        finally:
            doc.commitTransaction()


def _selected_component():
    selection = FreeCADGui.Selection.getSelection()
    return selection[0] if selection else None


class _PatternCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_ComponentPattern"),
            "MenuText": "Serie di componenti",
            "ToolTip": "Ripete il componente selezionato in serie lineare (modificare Mode, Count, "
            "Direction, Spacing, Axis, Angle nelle proprietà); le copie seguono il seme",
        }

    def IsActive(self):
        return _selected_component() is not None

    def Activated(self):
        seed = _selected_component()
        doc = seed.Document
        try:
            from forgelib import evaluate

            spacing = max(10.0, evaluate.global_shape(seed).BoundBox.XLength * 1.5)
        except Exception:
            spacing = 50.0
        doc.openTransaction("Serie di componenti")
        try:
            obj = component_pattern.make_pattern(doc, seed, "Lineare", 3, Spacing=spacing)
            container = active_container()
            if container is not None and hasattr(container, "addObject"):
                container.addObject(obj)
            doc.recompute()
        finally:
            doc.commitTransaction()


class _MirrorCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_MirrorComponent"),
            "MenuText": "Specchia componente",
            "ToolTip": "Crea la versione opposta del componente selezionato rispetto al piano della "
            "faccia piana selezionata (secondo elemento) o al piano YZ",
        }

    def IsActive(self):
        return _selected_component() is not None

    def Activated(self):
        selection = FreeCADGui.Selection.getSelectionEx("", 0)
        component = selection[0].Object
        base, normal = FreeCAD.Vector(), FreeCAD.Vector(1, 0, 0)
        for sel in selection[1:] + selection[:1]:
            for sub in sel.SubObjects:
                if sub.ShapeType == "Face" and sub.Surface.TypeId == "Part::GeomPlane":
                    base = sub.CenterOfMass
                    u0, u1, v0, v1 = sub.ParameterRange
                    normal = sub.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
                    break
        doc = component.Document
        doc.openTransaction("Specchia componente")
        try:
            obj = component_pattern.make_mirror(doc, component, base, normal)
            container = active_container()
            if container is not None and hasattr(container, "addObject"):
                container.addObject(obj)
            doc.recompute()
        finally:
            doc.commitTransaction()


ASSEMBLY_COMMANDS = ["Forge_Fastener", "Forge_ComponentPattern", "Forge_MirrorComponent"]


def register():
    FreeCADGui.addCommand("Forge_Fastener", _FastenerCommand())
    FreeCADGui.addCommand("Forge_ComponentPattern", _PatternCommand())
    FreeCADGui.addCommand("Forge_MirrorComponent", _MirrorCommand())
