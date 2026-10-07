# SPDX-License-Identifier: LGPL-2.1-or-later
"""Membri strutturali (saldature) lungo un percorso, con taglio a mitra e distinta di taglio (M5.2).

Il percorso è un insieme di spigoli (schizzo, schizzo 3D, filo): ogni spigolo rettilineo diventa
un membro con la sezione del profilato scelto, con il baricentro sull'asse. Agli spigoli in cui
due membri si incontrano il taglio è a mitra sul piano bisettore (normale = d1 + d2 normalizzata).
Volume di ogni membro = area × lunghezza dell'asse baricentrico (proprietà dei prismi a tagli
obliqui), verificato dai test. Limiti: spigoli curvi resi per sweep senza mitra; giunzioni a T e
rifilature contro altri membri non gestite (vedi PROGRESS.md).
"""

import math
from dataclasses import dataclass

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib.features import profiles

CORNERS = ["Mitra", "Nessuno"]


def _frame(direction, rotation_deg):
    """Assi (x, y, z) della sezione: z lungo il membro, y verso "l'alto" (Z globale o X)."""
    z = Vector(direction)
    z.normalize()
    up = Vector(0, 0, 1) if abs(z.z) < 0.999 else Vector(1, 0, 0)
    y = up.sub(Vector(z).multiply(up.dot(z)))
    y.normalize()
    x = y.cross(z)
    if rotation_deg:
        rot = FreeCAD.Rotation(z, rotation_deg)
        x, y = rot.multVec(x), rot.multVec(y)
    return x, y, z


def _placed_section(face, origin, direction, rotation_deg):
    x, y, z = _frame(direction, rotation_deg)
    matrix = FreeCAD.Matrix(x.x, y.x, z.x, origin.x,
                            x.y, y.y, z.y, origin.y,
                            x.z, y.z, z.z, origin.z,
                            0, 0, 0, 1)
    placed = face.copy()
    placed.transformShape(matrix)
    return placed


def _half_space(point, normal, size):
    """Grande blocco dalla parte positiva del piano (point, normal)."""
    n = Vector(normal)
    n.normalize()
    u = n.cross(Vector(0, 0, 1)) if abs(n.z) < 0.9 else n.cross(Vector(1, 0, 0))
    u.normalize()
    v = n.cross(u)
    corner = point.sub(Vector(u).multiply(size / 2)).sub(Vector(v).multiply(size / 2))
    face = Part.Face(Part.makePolygon([
        corner,
        corner.add(Vector(u).multiply(size)),
        corner.add(Vector(u).multiply(size)).add(Vector(v).multiply(size)),
        corner.add(Vector(v).multiply(size)),
        corner,
    ]))
    return face.extrude(n.multiply(size))


@dataclass
class Segment:
    start: Vector
    end: Vector
    miter_start: Vector = None  # normale del piano di mitra all'inizio (verso l'esterno del membro)
    miter_end: Vector = None

    @property
    def direction(self):
        d = self.end.sub(self.start)
        d.normalize()
        return d

    @property
    def length(self):
        return self.start.distanceToPoint(self.end)


def path_segments(edges, corners="Mitra"):
    """Segmenti rettilinei ordinati dal percorso, con i piani di mitra tra segmenti consecutivi."""
    if not edges:
        raise ValueError("Il percorso del membro strutturale è vuoto")
    sorted_edges = Part.__sortEdges__(list(edges))
    segments = []
    for edge in sorted_edges:
        if not isinstance(edge.Curve, (Part.Line, Part.LineSegment)):
            raise ValueError("Il percorso contiene spigoli curvi: usare solo segmenti rettilinei")
        a, b = edge.Vertexes[0].Point, edge.Vertexes[-1].Point
        if segments and not segments[-1].end.isEqual(a, 1e-7):
            if segments[-1].end.isEqual(b, 1e-7):
                a, b = b, a
        segments.append(Segment(a, b))
    if corners != "Mitra":
        return segments
    closed = len(segments) > 2 and segments[-1].end.isEqual(segments[0].start, 1e-7)
    pairs = list(zip(segments, segments[1:]))
    if closed:
        pairs.append((segments[-1], segments[0]))
    for first, second in pairs:
        if not first.end.isEqual(second.start, 1e-7):
            continue  # segmenti non contigui: nessuna mitra
        bisector = first.direction.add(second.direction)
        if bisector.Length < 1e-9:
            raise ValueError("Il percorso torna indietro su se stesso (angolo di 180°)")
        bisector.normalize()
        first.miter_end = bisector
        second.miter_start = Vector(bisector).multiply(-1)
    return segments


def member_solid(face, segment, rotation_deg=0.0):
    """Solido di un membro: estrusione della sezione con eventuali tagli a mitra."""
    size = face.BoundBox.DiagonalLength
    extension = 2 * size
    d = segment.direction
    start = segment.start.sub(Vector(d).multiply(extension if segment.miter_start else 0))
    length = segment.length + (extension if segment.miter_start else 0) + (
        extension if segment.miter_end else 0)
    section = _placed_section(face, start, d, rotation_deg)
    solid = section.extrude(Vector(d).multiply(length))
    big = 4 * (length + size)
    if segment.miter_end:
        solid = solid.cut(_half_space(segment.end, segment.miter_end, big))
    if segment.miter_start:
        solid = solid.cut(_half_space(segment.start, segment.miter_start, big))
    solids = solid.Solids
    if len(solids) != 1:
        raise ValueError("Il taglio a mitra non ha prodotto un solido unico")
    return solids[0]


def miter_angle(segment, at_start):
    """Angolo di taglio in gradi rispetto al taglio dritto (0 = dritto, 45 = mitra a 90°)."""
    normal = segment.miter_start if at_start else segment.miter_end
    if normal is None:
        return 0.0
    cos = abs(normal.dot(segment.direction))
    return math.degrees(math.acos(min(1.0, cos)))


class StructuralMember:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLinkSub", "Path", "Profilato", "Spigoli del percorso (vuoto = tutti)")
        obj.addProperty("App::PropertyEnumeration", "Family", "Profilato", "Famiglia del profilato")
        obj.Family = profiles.FAMILIES
        obj.addProperty("App::PropertyEnumeration", "Size", "Profilato", "Dimensione")
        obj.addProperty("App::PropertyAngle", "Rotation", "Profilato", "Rotazione attorno all'asse")
        obj.addProperty("App::PropertyEnumeration", "Corners", "Profilato", "Trattamento degli spigoli")
        obj.Corners = CORNERS
        self._update_sizes(obj)

    def _update_sizes(self, obj):
        current = obj.Size if obj.Size else None
        values = profiles.sizes(obj.Family)
        obj.Size = values
        if current in values:
            obj.Size = current

    def onChanged(self, obj, prop):
        if prop == "Family" and hasattr(obj, "Size"):
            self._update_sizes(obj)

    def edges(self, obj):
        link = obj.Path
        if not link or link[0] is None:
            raise ValueError("Membro strutturale senza percorso")
        source, subs = link
        shape = source.Shape
        if subs and any(subs):
            return [shape.getElement(s) for s in subs if s]
        return shape.Edges

    def execute(self, obj):
        face = profiles.section_face(obj.Family, obj.Size)
        segments = path_segments(self.edges(obj), obj.Corners)
        solids = [member_solid(face, seg, float(obj.Rotation)) for seg in segments]
        obj.Shape = Part.makeCompound(solids)

    def onDocumentRestored(self, obj):
        obj.Proxy = self

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_member(doc, path_obj, family="IPE", size=None, subs=(), corners="Mitra", name="Profilato"):
    obj = doc.addObject("Part::FeaturePython", name)
    StructuralMember(obj)
    obj.Family = family
    if size is not None:
        obj.Size = size
    obj.Corners = corners
    obj.Path = (path_obj, list(subs))
    if FreeCAD.GuiUp:
        obj.ViewObject.Proxy = 0
    return obj


@dataclass
class CutItem:
    index: int
    profile: str
    centerline: float  # lunghezza sull'asse baricentrico
    overall: float  # lunghezza massima (punta-punta)
    angle_start: float
    angle_end: float
    mass: float = 0.0  # kg (con densità)


def cut_list(obj, density=7.85e-6):
    """Distinta di taglio: una riga per membro (densità in kg/mm³, acciaio di default)."""
    segments = path_segments(obj.Proxy.edges(obj), obj.Corners)
    items = []
    for index, (segment, solid) in enumerate(zip(segments, obj.Shape.Solids), start=1):
        d = segment.direction
        along = [v.Point.sub(segment.start).dot(d) for v in solid.Vertexes]
        items.append(CutItem(
            index,
            f"{obj.Family} {obj.Size}",
            segment.length,
            max(along) - min(along),
            miter_angle(segment, True),
            miter_angle(segment, False),
            solid.Volume * density,
        ))
    return items
