# SPDX-License-Identifier: LGPL-2.1-or-later
"""Strumenti di valutazione (M8): interferenze/giochi e analisi di sformo.

Solo geometria (Part/OCC), nessuna dipendenza dalla GUI.
"""

import math
from dataclasses import dataclass

from FreeCAD import Vector

# --- interferenze e giochi -------------------------------------------------------------------


@dataclass
class Interference:
    first: str
    second: str
    volume: float  # volume comune (mm³); 0 per contatto o gioco
    distance: float  # distanza minima (0 se si toccano o si compenetrano)
    kind: str  # "interferenza", "contatto" o "gioco"
    shape: object = None  # solido comune (solo per le interferenze)


def _solid_shape(shape):
    return shape is not None and not shape.isNull() and len(shape.Solids) > 0


def check_pairs(items, clearance=0.0, volume_tol=1e-6):
    """Controlla ogni coppia di forme.

    ``items``: lista di (nome, forma) con le forme già nella posizione globale.
    ``clearance``: se > 0 segnala anche le coppie a distanza minore di questo valore ("gioco").
    Restituisce le coppie con interferenza, contatto o gioco insufficiente, in ordine di gravità.
    """
    found = []
    shapes = [(name, shape) for name, shape in items if _solid_shape(shape)]
    for i in range(len(shapes)):
        name_a, a = shapes[i]
        box_a = a.BoundBox
        for j in range(i + 1, len(shapes)):
            name_b, b = shapes[j]
            box_b = b.BoundBox
            grown = box_a.__class__(box_a)
            grown.enlarge(max(clearance, 1e-7))
            if not grown.intersect(box_b):
                continue
            common = a.common(b)
            volume = common.Volume if not common.isNull() else 0.0
            if volume > volume_tol:
                found.append(Interference(name_a, name_b, volume, 0.0, "interferenza", common))
                continue
            distance = a.distToShape(b)[0]
            if distance <= 1e-7:
                found.append(Interference(name_a, name_b, 0.0, 0.0, "contatto"))
            elif clearance > 0 and distance < clearance:
                found.append(Interference(name_a, name_b, 0.0, distance, "gioco"))
    order = {"interferenza": 0, "gioco": 1, "contatto": 2}
    found.sort(key=lambda f: (order[f.kind], -f.volume, f.distance))
    return found


def global_shape(obj):
    """Forma di un oggetto nella posizione globale (gestisce Link e assiemi annidati)."""
    import Part

    return Part.getShape(obj, "", needSubElement=False, transform=True)


def assembly_components(assembly):
    """Componenti di un assieme come (etichetta, forma globale), esclusi giunti e gruppi."""
    items = []
    for obj in assembly.OutList:
        if obj.isDerivedFrom("App::DocumentObjectGroup") or obj.TypeId.startswith("Assembly::"):
            if not obj.isDerivedFrom("Assembly::AssemblyLink"):
                continue
        try:
            shape = global_shape(obj)
        except Exception:
            continue
        if _solid_shape(shape):
            items.append((obj.Label, shape))
    return items


# --- analisi di sformo -------------------------------------------------------------------------

POSITIVE = "sformo positivo"
NEGATIVE = "sformo negativo"
INSUFFICIENT = "sformo insufficiente"
STRADDLE = "a cavallo"


@dataclass
class FaceDraft:
    index: int  # 1-based, come "FaceN"
    kind: str
    min_angle: float  # gradi
    max_angle: float


def _face_angles(face, direction, samples):
    """Angoli di sformo (gradi) campionati sulla faccia: 90° - angolo(normale, direzione)."""
    u0, u1, v0, v1 = face.ParameterRange
    angles = []
    for i in range(samples):
        for j in range(samples):
            u = u0 + (u1 - u0) * (i + 0.5) / samples
            v = v0 + (v1 - v0) * (j + 0.5) / samples
            try:
                if not face.isInside(face.valueAt(u, v), 1e-6, True):
                    continue
                normal = face.normalAt(u, v)
            except Exception:
                continue
            cos = max(-1.0, min(1.0, normal.dot(direction)))
            angles.append(90.0 - math.degrees(math.acos(cos)))
    return angles


def draft_analysis(shape, direction, min_angle=1.0, samples=4):
    """Classifica le facce di un solido rispetto alla direzione di estrazione.

    - sformo positivo: tutta la faccia guarda verso la direzione con almeno ``min_angle``;
    - sformo negativo: tutta la faccia guarda in verso opposto con almeno ``min_angle``;
    - sformo insufficiente: l'angolo resta sotto ``min_angle`` in valore assoluto;
    - a cavallo: la faccia ha zone positive e negative (va divisa con una linea di divisione).
    """
    d = Vector(direction)
    d.normalize()
    result = []
    for index, face in enumerate(shape.Faces, start=1):
        angles = _face_angles(face, d, samples if face.Surface.TypeId != "Part::GeomPlane" else 1)
        if not angles:
            continue
        lo, hi = min(angles), max(angles)
        if lo >= min_angle:
            kind = POSITIVE
        elif hi <= -min_angle:
            kind = NEGATIVE
        elif lo > -min_angle and hi < min_angle:
            kind = INSUFFICIENT
        elif lo <= -min_angle and hi >= min_angle:
            kind = STRADDLE
        else:
            kind = INSUFFICIENT
        result.append(FaceDraft(index, kind, lo, hi))
    return result


DRAFT_COLORS = {
    POSITIVE: (0.20, 0.70, 0.25),
    NEGATIVE: (0.85, 0.20, 0.20),
    INSUFFICIENT: (0.95, 0.80, 0.10),
    STRADDLE: (0.25, 0.45, 0.90),
}


def summarize_draft(faces):
    counts = {}
    for face in faces:
        counts[face.kind] = counts.get(face.kind, 0) + 1
    return counts
