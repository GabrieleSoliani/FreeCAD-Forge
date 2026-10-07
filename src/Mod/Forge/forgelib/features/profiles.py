# SPDX-License-Identifier: LGPL-2.1-or-later
"""Libreria di profilati strutturali (EN) e costruzione delle sezioni (M5.2).

Dimensioni in mm. Fonti: EN 10365 (IPE, HEA, HEB), EN 10219 (tubi formati a freddo),
EN 10056-1 (angolari a lati uguali). Semplificazioni dichiarate:
- tubi quadri/rettangolari: raggio esterno 2·t e interno t (EN 10219 per t ≤ 6 mm);
- angolari: raggi di raccordo al piede r1 come da norma, raccordo di punta r2 = r1/2;
- i profili UPN (ali rastremate) non sono inclusi per non introdurre sezioni approssimate.
Le sezioni sono facce nel piano XY con il baricentro nell'origine (salvo dove indicato).
"""

import math

import Part
from FreeCAD import Vector

# h, b, tw, tf, r
I_SECTIONS = {
    "IPE": {
        "80": (80, 46, 3.8, 5.2, 5), "100": (100, 55, 4.1, 5.7, 7), "120": (120, 64, 4.4, 6.3, 7),
        "140": (140, 73, 4.7, 6.9, 7), "160": (160, 82, 5.0, 7.4, 9), "180": (180, 91, 5.3, 8.0, 9),
        "200": (200, 100, 5.6, 8.5, 12), "220": (220, 110, 5.9, 9.2, 12),
        "240": (240, 120, 6.2, 9.8, 15), "270": (270, 135, 6.6, 10.2, 15),
        "300": (300, 150, 7.1, 10.7, 15),
    },
    "HEA": {
        "100": (96, 100, 5.0, 8.0, 12), "120": (114, 120, 5.0, 8.0, 12), "140": (133, 140, 5.5, 8.5, 12),
        "160": (152, 160, 6.0, 9.0, 15), "180": (171, 180, 6.0, 9.5, 15), "200": (190, 200, 6.5, 10.0, 18),
        "220": (210, 220, 7.0, 11.0, 18), "240": (230, 240, 7.5, 12.0, 21),
    },
    "HEB": {
        "100": (100, 100, 6.0, 10.0, 12), "120": (120, 120, 6.5, 11.0, 12), "140": (140, 140, 7.0, 12.0, 12),
        "160": (160, 160, 8.0, 13.0, 15), "180": (180, 180, 8.5, 14.0, 15), "200": (200, 200, 9.0, 15.0, 18),
    },
}

# tubi rettangolari/quadri: (h, b, t)
RHS = {
    f"{h}x{b}x{t:g}": (h, b, t)
    for h, b, t in (
        (20, 20, 2), (30, 30, 2), (30, 30, 3), (40, 40, 2), (40, 40, 3), (40, 40, 4), (50, 50, 3),
        (50, 50, 4), (60, 60, 3), (60, 60, 4), (80, 80, 4), (80, 80, 5), (100, 100, 4), (100, 100, 5),
        (40, 20, 2), (50, 30, 3), (60, 40, 3), (80, 40, 3), (100, 50, 4), (120, 60, 4),
    )
}
# tubi tondi: (d, t)
CHS = {f"{d:g}x{t:g}": (d, t) for d, t in (
    (21.3, 2), (26.9, 2), (33.7, 2.6), (42.4, 2.6), (48.3, 3.2), (60.3, 3.2), (76.1, 3.2), (88.9, 4), (114.3, 4))}
# angolari a lati uguali: (a, t, r1)
ANGLES = {f"{a}x{t}": (a, t, r) for a, t, r in (
    (20, 3, 3.5), (25, 3, 3.5), (30, 3, 5), (40, 4, 6), (50, 5, 7), (60, 6, 8), (70, 7, 9), (80, 8, 10),
    (100, 10, 12))}
# piatti: (b, t)
FLATS = {f"{b}x{t}": (b, t) for b, t in ((20, 5), (30, 5), (40, 5), (50, 5), (50, 10), (60, 8), (80, 10), (100, 10))}

FAMILIES = ["IPE", "HEA", "HEB", "Tubo quadro/rett.", "Tubo tondo", "Angolare", "Piatto"]


def sizes(family):
    if family in I_SECTIONS:
        return list(I_SECTIONS[family])
    return list({"Tubo quadro/rett.": RHS, "Tubo tondo": CHS, "Angolare": ANGLES, "Piatto": FLATS}[family])


def _arc(center, radius, start_deg, end_deg):
    """Arco di circonferenza nel piano XY da start_deg a end_deg (gradi, senso antiorario)."""
    cx, cy = center
    pts = []
    for deg in (start_deg, (start_deg + end_deg) / 2, end_deg):
        rad = math.radians(deg)
        pts.append(Vector(cx + radius * math.cos(rad), cy + radius * math.sin(rad), 0))
    return Part.Arc(*pts).toShape()


def _line(p, q):
    return Part.LineSegment(Vector(p[0], p[1], 0), Vector(q[0], q[1], 0)).toShape()


def _rounded_rect_face(w, h, r):
    """Rettangolo w×h centrato nell'origine con spigoli raccordati di raggio r (r = 0: vivi)."""
    x, y = w / 2, h / 2
    if r <= 0:
        return Part.Face(Part.makePolygon([Vector(-x, -y, 0), Vector(x, -y, 0), Vector(x, y, 0),
                                           Vector(-x, y, 0), Vector(-x, -y, 0)]))
    edges = [
        _line((-x + r, -y), (x - r, -y)),
        _arc((x - r, -y + r), r, -90, 0),
        _line((x, -y + r), (x, y - r)),
        _arc((x - r, y - r), r, 0, 90),
        _line((x - r, y), (-x + r, y)),
        _arc((-x + r, y - r), r, 90, 180),
        _line((-x, y - r), (-x, -y + r)),
        _arc((-x + r, -y + r), r, 180, 270),
    ]
    return Part.Face(Part.Wire(edges))


def _i_section(h, b, tw, tf, r):
    """Profilo a I/H con raccordi anima-ali di raggio r (area esatta: 2·b·tf + (h−2tf)·tw + (4−π)·r²)."""
    x, y = b / 2, h / 2
    w = tw / 2
    yi = y - tf  # filo interno delle ali
    edges = [
        _line((-x, -y), (x, -y)),
        _line((x, -y), (x, -yi)),
        _line((x, -yi), (w + r, -yi)),
        _arc((w + r, -yi + r), r, -90, -180),
        _line((w, -yi + r), (w, yi - r)),
        _arc((w + r, yi - r), r, 180, 90),
        _line((w + r, yi), (x, yi)),
        _line((x, yi), (x, y)),
        _line((x, y), (-x, y)),
        _line((-x, y), (-x, yi)),
        _line((-x, yi), (-w - r, yi)),
        _arc((-w - r, yi - r), r, 90, 0),
        _line((-w, yi - r), (-w, -yi + r)),
        _arc((-w - r, -yi + r), r, 0, -90),
        _line((-w - r, -yi), (-x, -yi)),
        _line((-x, -yi), (-x, -y)),
    ]
    return Part.Face(Part.Wire(edges))


def _angle_section(a, t, r1):
    """Angolare a lati uguali con raccordo interno r1 e di punta r2 = r1/2; baricentro nell'origine."""
    r2 = r1 / 2
    outline = Part.Face(Part.makePolygon([Vector(0, 0, 0), Vector(a, 0, 0), Vector(a, t, 0),
                                          Vector(t, t, 0), Vector(t, a, 0), Vector(0, a, 0),
                                          Vector(0, 0, 0)]))
    solid = outline.extrude(Vector(0, 0, 1))
    # raccordo interno (aggiunge materiale) e raccordi di punta (tolgono materiale)
    corner = Part.makeBox(r1, r1, 1, Vector(t, t, 0)).cut(Part.makeCylinder(r1, 1, Vector(t + r1, t + r1, 0)))
    solid = solid.fuse(corner)
    for cx, cy, bx, by in ((a - r2, t - r2, a - r2, t - r2), (t - r2, a - r2, t - r2, a - r2)):
        tip = Part.makeBox(r2, r2, 1, Vector(bx, by, 0)).cut(Part.makeCylinder(r2, 1, Vector(cx, cy, 0)))
        solid = solid.cut(tip)
    solid = solid.removeSplitter()
    face = [f for f in solid.Faces if abs(f.CenterOfMass.z) < 1e-9][0]
    return Part.Face(face.OuterWire)


def section_face(family, size):
    """Faccia della sezione nel piano XY, con il baricentro nell'origine."""
    if family in I_SECTIONS:
        face = _i_section(*I_SECTIONS[family][size])
    elif family == "Tubo quadro/rett.":
        h, b, t = RHS[size]
        outer = _rounded_rect_face(b, h, 2 * t)
        inner = _rounded_rect_face(b - 2 * t, h - 2 * t, t)
        face = outer.cut(inner).Faces[0]
    elif family == "Tubo tondo":
        d, t = CHS[size]
        outer = Part.Face(Part.Wire(Part.makeCircle(d / 2)))
        inner = Part.Face(Part.Wire(Part.makeCircle(d / 2 - t)))
        face = outer.cut(inner).Faces[0]
    elif family == "Angolare":
        face = _angle_section(*ANGLES[size])
    elif family == "Piatto":
        b, t = FLATS[size]
        face = _rounded_rect_face(b, t, 0)
    else:
        raise ValueError(f"Famiglia di profilati sconosciuta: {family}")
    center = face.CenterOfMass
    face.translate(Vector(-center.x, -center.y, 0))
    return face


def nominal_area(family, size):
    """Area teorica della sezione (mm²) dalle formule della norma, per verifica."""
    if family in I_SECTIONS:
        h, b, tw, tf, r = I_SECTIONS[family][size]
        return 2 * b * tf + (h - 2 * tf) * tw + (4 - math.pi) * r * r
    if family == "Tubo tondo":
        d, t = CHS[size]
        return math.pi / 4 * (d * d - (d - 2 * t) ** 2)
    if family == "Piatto":
        b, t = FLATS[size]
        return b * t
    if family == "Tubo quadro/rett.":
        h, b, t = RHS[size]
        ro, ri = 2 * t, t
        return (b * h - (4 - math.pi) * ro * ro) - ((b - 2 * t) * (h - 2 * t) - (4 - math.pi) * ri * ri)
    if family == "Angolare":
        a, t, r1 = ANGLES[size]
        r2 = r1 / 2
        return t * (2 * a - t) + (1 - math.pi / 4) * (r1 * r1 - 2 * r2 * r2)
    raise ValueError(family)
