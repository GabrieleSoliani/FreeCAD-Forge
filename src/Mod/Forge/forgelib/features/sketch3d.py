# SPDX-License-Identifier: LGPL-2.1-or-later
"""Schizzo 3D in versione ridotta (M2.4).

Feature parametrica con una lista di punti 3D che genera una polilinea (con raccordi opzionali
agli spigoli) oppure una spline interpolante, aperta o chiusa. Serve come percorso per sweep e
profilati. Limite rispetto a SolidWorks: niente vincoli 3D tra entità; i punti si modificano
nelle proprietà (anche con espressioni) o si ricavano da vertici selezionati.
"""

import FreeCAD
import Part

MODES = ["Polilinea", "Spline"]


class Sketch3D:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyVectorList", "Points", "Schizzo3D", "Punti del percorso")
        obj.addProperty("App::PropertyEnumeration", "Mode", "Schizzo3D", "Polilinea o spline")
        obj.Mode = MODES
        obj.addProperty("App::PropertyBool", "Closed", "Schizzo3D", "Percorso chiuso")
        obj.addProperty(
            "App::PropertyLength", "BendRadius", "Schizzo3D",
            "Raggio di raccordo agli spigoli della polilinea (0 = spigoli vivi)",
        )

    def execute(self, obj):
        obj.Shape = build_wire(list(obj.Points), obj.Mode, obj.Closed, float(obj.BendRadius))

    def onDocumentRestored(self, obj):
        obj.Proxy = self

    def dumps(self):
        return None

    def loads(self, state):
        return None


def build_wire(points, mode="Polilinea", closed=False, bend_radius=0.0):
    """Filo 3D dai punti. Solleva ValueError con un messaggio comprensibile se non è possibile."""
    if len(points) < 2:
        raise ValueError("Lo schizzo 3D richiede almeno 2 punti")
    for a, b in zip(points, points[1:]):
        if a.isEqual(b, 1e-9):
            raise ValueError("Lo schizzo 3D contiene due punti consecutivi coincidenti")
    if mode == "Spline":
        curve = Part.BSplineCurve()
        if closed:
            if len(points) < 3:
                raise ValueError("Una spline chiusa richiede almeno 3 punti")
            curve.interpolate(points, PeriodicFlag=True)
        else:
            curve.interpolate(points)
        return Part.Wire([curve.toShape()])
    polygon = list(points) + ([points[0]] if closed else [])
    wire = Part.makePolygon(polygon)
    if bend_radius > 0 and len(polygon) > 2:
        try:
            wire = _fillet_polyline(polygon, bend_radius, closed)
        except Exception as err:
            raise ValueError(f"Raggio di raccordo troppo grande per i segmenti: {err}")
    return wire


def _corner_arc(prev_p, p, next_p, radius):
    """(inizio, medio, fine) dell'arco tangente allo spigolo ``p``, oppure None se allineato."""
    import math

    d1 = prev_p.sub(p)
    d2 = next_p.sub(p)
    d1.normalize()
    d2.normalize()
    angle = d1.getAngle(d2)
    if angle < 1e-6 or abs(angle - math.pi) < 1e-6:
        return None
    setback = radius / math.tan(angle / 2)
    if setback > p.distanceToPoint(prev_p) / 2 + 1e-9 or setback > p.distanceToPoint(next_p) / 2 + 1e-9:
        raise ValueError("raggio troppo grande per la lunghezza dei segmenti")
    bisector = d1.add(d2)
    bisector.normalize()
    start = p.add(FreeCAD.Vector(d1).multiply(setback))
    end = p.add(FreeCAD.Vector(d2).multiply(setback))
    middle = p.add(bisector.multiply(radius / math.sin(angle / 2) - radius))
    return start, middle, end


def _fillet_polyline(polygon, radius, closed):
    """Polilinea 3D con archi tangenti agli spigoli interni (``polygon`` chiuso se ``closed``)."""
    points = polygon[:-1] if closed else polygon
    n = len(points)
    corner_ids = range(n) if closed else range(1, n - 1)
    arcs = {i: _corner_arc(points[i - 1], points[i], points[(i + 1) % n], radius) for i in corner_ids}

    def leaving(i):  # punto da cui parte il tratto rettilineo dopo il vertice i
        return arcs[i][2] if arcs.get(i) else points[i]

    def arriving(i):  # punto in cui arriva il tratto rettilineo nel vertice i
        return arcs[i][0] if arcs.get(i) else points[i]

    edges = []
    segments = n if closed else n - 1
    for i in range(segments):
        j = (i + 1) % n
        a, b = leaving(i), arriving(j)
        if not a.isEqual(b, 1e-9):
            edges.append(Part.LineSegment(a, b).toShape())
        if arcs.get(j) and (closed or j < n - 1):
            edges.append(Part.Arc(*arcs[j]).toShape())
    return Part.Wire(Part.__sortEdges__(edges))


def make_sketch3d(doc, points, mode="Polilinea", closed=False, bend_radius=0.0, name="Schizzo3D"):
    obj = doc.addObject("Part::FeaturePython", name)
    Sketch3D(obj)
    obj.Points = [FreeCAD.Vector(p) for p in points]
    obj.Mode = mode
    obj.Closed = closed
    obj.BendRadius = bend_radius
    if FreeCAD.GuiUp:
        obj.ViewObject.Proxy = 0
        obj.ViewObject.LineWidth = 3
    return obj


# --- GUI -------------------------------------------------------------------------------------


def selected_vertex_points():
    """Punti dei vertici selezionati, nell'ordine di selezione (coordinate globali)."""
    import FreeCADGui

    points = []
    for sel in FreeCADGui.Selection.getSelectionEx("", 0):
        for sub in sel.SubObjects:
            if sub.ShapeType == "Vertex":
                points.append(sub.Point)
    return points


class _Sketch3DCommand:
    def GetResources(self):
        from forgelib.commands import icon_path

        return {
            "Pixmap": icon_path("Forge_Sketch3D"),
            "MenuText": "Schizzo 3D",
            "ToolTip": "Crea una polilinea 3D dai vertici selezionati (nell'ordine di selezione); "
            "senza selezione crea un percorso di esempio da modificare nelle proprietà "
            "(Points, Mode, Closed, BendRadius)",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        points = selected_vertex_points()
        if len(points) < 2:
            points = [FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(50, 0, 0), FreeCAD.Vector(50, 50, 25)]
        doc.openTransaction("Schizzo 3D")
        try:
            make_sketch3d(doc, points)
            doc.recompute()
        finally:
            doc.commitTransaction()


def register():
    import FreeCADGui

    FreeCADGui.addCommand("Forge_Sketch3D", _Sketch3DCommand())
