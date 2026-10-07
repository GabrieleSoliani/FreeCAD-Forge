# SPDX-License-Identifier: LGPL-2.1-or-later
"""Nervatura (rib) da profilo aperto, come in SolidWorks (M4.2).

Il profilo (uno schizzo con un filo aperto) giace in un piano che attraversa il pezzo. Nel piano
il profilo viene prolungato fino al materiale; la regione chiusa delimitata dal profilo e dalla
sezione del pezzo diventa la nervatura, estrusa simmetricamente rispetto al piano per lo spessore
dato. Se le regioni chiuse sono due (una per lato), ``Reversed`` sceglie l'altra.
Feature ``PartDesign::FeaturePython``: si inserisce nel corpo come le altre feature.
"""

import FreeCAD
import Part
from FreeCAD import Vector


def _plane_frame(sketch):
    placement = sketch.getGlobalPlacement()
    normal = placement.Rotation.multVec(Vector(0, 0, 1))
    return placement.Base, normal


def _open_wire(sketch):
    edges = [e for e in sketch.Shape.Edges]
    if not edges:
        raise ValueError("Lo schizzo della nervatura è vuoto")
    wires = Part.__sortEdges__(edges)
    wire = Part.Wire(wires)
    if wire.isClosed():
        raise ValueError("Il profilo della nervatura deve essere aperto (una linea o una spezzata)")
    return wire


def _extended(wire, length):
    """Filo prolungato alle estremità lungo le tangenti."""
    edges = list(wire.OrderedEdges)
    first, last = edges[0], edges[-1]
    start = wire.OrderedVertexes[0].Point
    end = wire.OrderedVertexes[-1].Point
    t0 = first.tangentAt(first.FirstParameter if first.Vertexes[0].Point.isEqual(start, 1e-7) else first.LastParameter)
    if not first.Vertexes[0].Point.isEqual(start, 1e-7):
        t0 = t0.multiply(-1)
    t1 = last.tangentAt(last.LastParameter if last.Vertexes[-1].Point.isEqual(end, 1e-7) else last.FirstParameter)
    if not last.Vertexes[-1].Point.isEqual(end, 1e-7):
        t1 = t1.multiply(-1)
    t0.normalize()
    t1.normalize()
    head = Part.LineSegment(start.sub(Vector(t0).multiply(length)), start).toShape()
    tail = Part.LineSegment(end, end.add(Vector(t1).multiply(length))).toShape()
    return Part.Wire(Part.__sortEdges__([head] + edges + [tail]))


def rib_face(solid, sketch, reversed_side=False):
    """Faccia piana della nervatura nel piano dello schizzo."""
    origin, normal = _plane_frame(sketch)
    wire = _open_wire(sketch)
    size = solid.BoundBox.DiagonalLength + wire.BoundBox.DiagonalLength
    # sezione del pezzo nel piano dello schizzo
    slab = Part.makePlane(4 * size, 4 * size, Vector(-2 * size, -2 * size, 0))
    slab.Placement = sketch.getGlobalPlacement()
    material = slab.common(solid)
    if material.isNull() or not material.Faces:
        raise ValueError("Il piano dello schizzo non attraversa il pezzo")
    # piano diviso dal profilo prolungato, tolto il materiale
    from BOPTools import SplitAPI

    pieces = SplitAPI.slice(slab, [_extended(wire, 2 * size)], "Split")
    free = pieces.cut(material)
    outer = slab.OuterWire
    candidates = []
    for face in free.Faces:
        touches_profile = face.distToShape(wire)[0] < 1e-6
        bounded = face.distToShape(outer)[0] > 1e-6
        if touches_profile and bounded:
            candidates.append(face)
    if not candidates:
        raise ValueError("Il profilo non chiude una regione con il pezzo: prolungalo fino al materiale")
    if len(candidates) > 1:
        # una regione per lato: si sceglie con il verso della normale del piano × direzione del profilo
        direction = wire.OrderedVertexes[-1].Point.sub(wire.OrderedVertexes[0].Point)
        side = normal.cross(direction)
        candidates.sort(key=lambda f: f.CenterOfMass.sub(origin).dot(side), reverse=not reversed_side)
    return candidates[0]


def rib_solid(solid, sketch, thickness, reversed_side=False):
    if thickness <= 0:
        raise ValueError("Lo spessore della nervatura deve essere maggiore di zero")
    face = rib_face(solid, sketch, reversed_side)
    _, normal = _plane_frame(sketch)
    n = Vector(normal)
    n.normalize()
    face = face.copy()
    face.translate(Vector(n).multiply(-thickness / 2))
    return face.extrude(Vector(n).multiply(thickness))


class Rib:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink", "Profile", "Nervatura", "Schizzo con il profilo aperto")
        obj.addProperty("App::PropertyLength", "Thickness", "Nervatura", "Spessore (simmetrico al piano)")
        obj.Thickness = 3
        obj.addProperty("App::PropertyBool", "Reversed", "Nervatura", "Riempie l'altro lato del profilo")

    def execute(self, obj):
        base = obj.BaseFeature
        if base is None or base.Shape.isNull():
            raise ValueError("La nervatura richiede un solido precedente nel corpo")
        solid = base.Shape.copy()
        rib = rib_solid(solid, obj.Profile, float(obj.Thickness), obj.Reversed)
        result = solid.fuse(rib).removeSplitter()
        if len(result.Solids) != 1:
            raise ValueError("La nervatura non si collega al pezzo")
        obj.Shape = result

    def onDocumentRestored(self, obj):
        obj.Proxy = self

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_rib(body, sketch, thickness=3.0, name="Nervatura"):
    obj = body.newObject("PartDesign::FeaturePython", name)
    Rib(obj)
    obj.Profile = sketch
    obj.Thickness = thickness
    if FreeCAD.GuiUp:
        obj.ViewObject.Proxy = 0
        sketch.ViewObject.Visibility = False
    return obj


# --- GUI -------------------------------------------------------------------------------------


class _RibCommand:
    def GetResources(self):
        from forgelib.commands import icon_path

        return {
            "Pixmap": icon_path("Forge_Rib"),
            "MenuText": "Nervatura",
            "ToolTip": "Crea una nervatura da uno schizzo con un profilo aperto che attraversa il "
            "pezzo: il profilo viene prolungato fino al materiale e ispessito simmetricamente",
        }

    def _sketch(self):
        import FreeCADGui

        for obj in FreeCADGui.Selection.getSelection():
            if obj.isDerivedFrom("Sketcher::SketchObject"):
                return obj
        return None

    def IsActive(self):
        sketch = self._sketch()
        return sketch is not None and any(p.isDerivedFrom("PartDesign::Body") for p in sketch.InList)

    def Activated(self):
        sketch = self._sketch()
        body = [p for p in sketch.InList if p.isDerivedFrom("PartDesign::Body")][0]
        doc = body.Document
        doc.openTransaction("Nervatura")
        try:
            make_rib(body, sketch)
            doc.recompute()
        finally:
            doc.commitTransaction()


def register():
    import FreeCADGui

    FreeCADGui.addCommand("Forge_Rib", _RibCommand())
