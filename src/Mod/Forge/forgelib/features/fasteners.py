# SPDX-License-Identifier: LGPL-2.1-or-later
"""Toolbox di viteria ISO (M6.1).

Viti a testa cilindrica con esagono incassato (ISO 4762), viti a testa esagonale (ISO 4017),
dadi esagonali (ISO 4032) e rosette piane (ISO 7089), da M3 a M20, con le dimensioni nominali
delle norme. Semplificazioni dichiarate: filettatura non modellata (gambo al diametro nominale,
come la filettatura cosmetica), smussi e raccordi di testa omessi, dado senza foro filettato
(foro al diametro nominale). I volumi sono quindi calcolabili esattamente (vedi test).
"""

import math

import FreeCAD
import Part
from FreeCAD import Vector

SIZES = ["M3", "M4", "M5", "M6", "M8", "M10", "M12", "M16", "M20"]
NOMINAL = {"M3": 3, "M4": 4, "M5": 5, "M6": 6, "M8": 8, "M10": 10, "M12": 12, "M16": 16, "M20": 20}

# ISO 4762: dk (diametro testa), k (altezza testa), s (chiave esagono), t (profondità esagono)
ISO4762 = {
    "M3": (5.5, 3, 2.5, 1.3), "M4": (7, 4, 3, 2), "M5": (8.5, 5, 4, 2.5), "M6": (10, 6, 5, 3),
    "M8": (13, 8, 6, 4), "M10": (16, 10, 8, 5), "M12": (18, 12, 10, 6), "M16": (24, 16, 14, 8),
    "M20": (30, 20, 17, 10),
}
# ISO 4017: s (chiave), k (altezza testa)
ISO4017 = {
    "M3": (5.5, 2), "M4": (7, 2.8), "M5": (8, 3.5), "M6": (10, 4), "M8": (13, 5.3), "M10": (16, 6.4),
    "M12": (18, 7.5), "M16": (24, 10), "M20": (30, 12.5),
}
# ISO 4032: s (chiave), m (altezza)
ISO4032 = {
    "M3": (5.5, 2.4), "M4": (7, 3.2), "M5": (8, 4.7), "M6": (10, 5.2), "M8": (13, 6.8),
    "M10": (16, 8.4), "M12": (18, 10.8), "M16": (24, 14.8), "M20": (30, 18),
}
# ISO 7089: d1 (foro), d2 (esterno), h (spessore)
ISO7089 = {
    "M3": (3.2, 7, 0.5), "M4": (4.3, 9, 0.8), "M5": (5.3, 10, 1), "M6": (6.4, 12, 1.6),
    "M8": (8.4, 16, 1.6), "M10": (10.5, 20, 2), "M12": (13, 24, 2.5), "M16": (17, 30, 3),
    "M20": (21, 37, 3),
}
# lunghezze unificate più comuni (mm)
LENGTHS = [6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100, 110, 120]

TYPES = {
    "ISO 4762": "Vite TCEI (testa cilindrica, esagono incassato)",
    "ISO 4017": "Vite TE (testa esagonale)",
    "ISO 4032": "Dado esagonale",
    "ISO 7089": "Rosetta piana",
}


def _hexagon_prism(s, height, z0=0.0):
    """Prisma esagonale con chiave s (distanza tra le facce), da z0 a z0+height."""
    r = s / math.sqrt(3)  # raggio del cerchio circoscritto
    pts = [Vector(r * math.cos(math.radians(30 + 60 * i)), r * math.sin(math.radians(30 + 60 * i)), z0)
           for i in range(6)]
    face = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return face.extrude(Vector(0, 0, height))


def hexagon_area(s):
    return math.sqrt(3) / 2 * s * s


def fastener_shape(kind, size, length=20.0):
    """Forma nel sistema locale: asse lungo Z, sottotesta (o faccia d'appoggio) a z = 0, gambo verso -Z."""
    d = NOMINAL[size]
    if kind == "ISO 4762":
        dk, k, s, t = ISO4762[size]
        head = Part.makeCylinder(dk / 2, k, Vector(0, 0, 0))
        head = head.cut(_hexagon_prism(s, t, k - t))
        shank = Part.makeCylinder(d / 2, length, Vector(0, 0, -length))
        return head.fuse(shank).removeSplitter()
    if kind == "ISO 4017":
        s, k = ISO4017[size]
        head = _hexagon_prism(s, k)
        shank = Part.makeCylinder(d / 2, length, Vector(0, 0, -length))
        return head.fuse(shank).removeSplitter()
    if kind == "ISO 4032":
        s, m = ISO4032[size]
        return _hexagon_prism(s, m).cut(Part.makeCylinder(d / 2, m, Vector(0, 0, 0)))
    if kind == "ISO 7089":
        d1, d2, h = ISO7089[size]
        return Part.makeCylinder(d2 / 2, h).cut(Part.makeCylinder(d1 / 2, h))
    raise ValueError(f"Tipo di elemento di fissaggio sconosciuto: {kind}")


def expected_volume(kind, size, length=20.0):
    """Volume teorico (mm³) con le stesse semplificazioni della forma."""
    d = NOMINAL[size]
    shank = math.pi * d * d / 4 * length
    if kind == "ISO 4762":
        dk, k, s, t = ISO4762[size]
        return math.pi * dk * dk / 4 * k - hexagon_area(s) * t + shank
    if kind == "ISO 4017":
        s, k = ISO4017[size]
        return hexagon_area(s) * k + shank
    if kind == "ISO 4032":
        s, m = ISO4032[size]
        return (hexagon_area(s) - math.pi * d * d / 4) * m
    if kind == "ISO 7089":
        d1, d2, h = ISO7089[size]
        return math.pi / 4 * (d2 * d2 - d1 * d1) * h
    raise ValueError(kind)


def designation(kind, size, length):
    if kind in ("ISO 4762", "ISO 4017"):
        return f"{kind} {size}x{length:g}"
    return f"{kind} {size}"


class Fastener:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyEnumeration", "Standard", "Viteria", "Norma")
        obj.Standard = list(TYPES)
        obj.addProperty("App::PropertyEnumeration", "Size", "Viteria", "Diametro nominale")
        obj.Size = SIZES
        obj.addProperty("App::PropertyLength", "Length", "Viteria", "Lunghezza del gambo (viti)")
        obj.Length = 20
        obj.addProperty("App::PropertyString", "Designation", "Viteria", "Designazione per la distinta")
        obj.setEditorMode("Designation", 1)

    def execute(self, obj):
        obj.Shape = fastener_shape(obj.Standard, obj.Size, float(obj.Length))
        obj.Designation = designation(obj.Standard, obj.Size, float(obj.Length))

    def onDocumentRestored(self, obj):
        obj.Proxy = self

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_fastener(doc, kind="ISO 4762", size="M6", length=20.0, placement=None, name="Vite"):
    obj = doc.addObject("Part::FeaturePython", name)
    Fastener(obj)
    obj.Standard = kind
    obj.Size = size
    obj.Length = length
    if placement is not None:
        obj.Placement = placement
    if FreeCAD.GuiUp:
        obj.ViewObject.Proxy = 0
        obj.ViewObject.ShapeColor = (0.55, 0.57, 0.6)
    return obj


def outward_axis(shape, edge):
    """Normale uscente della faccia piana del solido che contiene il bordo, oppure None."""
    circle = edge.Curve
    for face in shape.ancestorsOfType(edge, Part.Face):
        if not isinstance(face.Surface, Part.Plane):
            continue
        u0, u1, v0, v1 = face.ParameterRange
        normal = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        if abs(abs(normal.dot(circle.Axis)) - 1) < 1e-6:
            return normal
    return None


def placement_on_circle(edge, shape=None, flip=False):
    """Posizione per un elemento sul bordo circolare di un foro: origine al centro, asse sulla normale.

    Con ``shape`` (il solido forato) l'asse è la normale uscente della faccia d'appoggio, così la
    testa resta fuori e il gambo entra nel foro; ``flip`` la inverte.
    """
    circle = edge.Curve
    if not isinstance(circle, Part.Circle):
        raise ValueError("Selezionare il bordo circolare di un foro")
    axis = outward_axis(shape, edge) if shape is not None else None
    axis = Vector(circle.Axis) if axis is None else Vector(axis)
    if flip:
        axis = axis.multiply(-1)
    rotation = FreeCAD.Rotation(Vector(0, 0, 1), axis)
    return FreeCAD.Placement(circle.Center, rotation)


def size_for_hole(diameter):
    """Diametro nominale più grande che entra nel foro (gioco minimo 0,1 mm)."""
    best = None
    for size in SIZES:
        if NOMINAL[size] <= diameter - 0.1 + 1e-9:
            best = size
    return best
