# SPDX-License-Identifier: LGPL-2.1-or-later
"""Modelli di riferimento in stile esercizi dei tutorial SolidWorks (M3.3).

Ogni funzione costruisce un modello PartDesign in un documento e restituisce un dizionario con
il corpo e il volume atteso (None se non esiste una formula semplice). Usate dai test
(``TestForgeExamples``) e da ``forge_examples/genera_esempi.py`` per salvare i file .FCStd.
"""

import math

import FreeCAD
import Part
from FreeCAD import Vector

from ForgeTests import models


def _polygon(sketch, points):
    import Sketcher

    first = sketch.GeometryCount
    n = len(points)
    for i in range(n):
        a, b = points[i], points[(i + 1) % n]
        sketch.addGeometry(Part.LineSegment(Vector(a[0], a[1], 0), Vector(b[0], b[1], 0)))
    for i in range(n):
        sketch.addConstraint(Sketcher.Constraint("Coincident", first + i, 2, first + (i + 1) % n, 1))
    return sketch


def _through_all(pocket):
    pocket.Type = "ThroughAll"
    pocket.SideType = "Symmetric"
    return pocket


def _edges(feature, predicate):
    return [f"Edge{i + 1}" for i, e in enumerate(feature.Shape.Edges) if predicate(e)]


def flange(doc):
    """Flangia: disco Ø80×10, mozzo Ø40×20, foro centrale Ø20, 6 fori Ø8 su Ø60 (serie polare)."""
    body = models.new_body(doc, "Flangia")
    disk = models.pad(body, models.add_circle(models.sketch_on(body, "Disco"), 0, 0, 40), 10, "Disco")
    hub_sketch = models.add_circle(models.sketch_on(body, "SchizzoMozzo", offset=Vector(0, 0, 10)), 0, 0, 20)
    models.pad(body, hub_sketch, 20, "Mozzo")
    bore = _through_all(models.pocket(body, models.add_circle(models.sketch_on(body, "SchizzoForo"), 0, 0, 10), 1, "ForoCentrale"))
    hole = _through_all(models.pocket(body, models.add_circle(models.sketch_on(body, "SchizzoFori"), 30, 0, 4), 1, "Foro"))
    pattern = body.newObject("PartDesign::PolarPattern", "SerieFori")
    pattern.Originals = [hole]
    pattern.Axis = (models.origin_feature(body, "Z_Axis"), [""])
    pattern.Angle = 360
    pattern.Occurrences = 6
    # creata da script senza Originals, la serie non diventa Tip da sola (il comando GUI lo fa)
    body.Tip = pattern
    doc.recompute()
    expected = math.pi * (40**2 * 10 + 20**2 * 20 - 10**2 * 30 - 6 * 4**2 * 10)
    return {"body": body, "volume": expected, "features": [disk, bore, hole, pattern]}


def l_bracket(doc):
    """Staffa a L 60 mm, spessore 5, ali 40: due fori Ø6 sulla base e raccordo interno r=3."""
    body = models.new_body(doc, "Staffa")
    profile = _polygon(
        models.sketch_on(body, "ProfiloL", plane="YZ_Plane"),
        [(0, 0), (40, 0), (40, 5), (5, 5), (5, 40), (0, 40)],
    )
    base = models.pad(body, profile, 60, "Staffa")
    holes = models.sketch_on(body, "SchizzoFori")
    models.add_circle(holes, 15, 25, 3)
    models.add_circle(holes, 45, 25, 3)
    _through_all(models.pocket(body, holes, 1, "Fori"))
    doc.recompute()
    pocket = body.Tip
    inner = _edges(
        pocket,
        lambda e: abs(e.CenterOfMass.y - 5) < 1e-6 and abs(e.CenterOfMass.z - 5) < 1e-6,
    )
    fillet = body.newObject("PartDesign::Fillet", "RaccordoInterno")
    fillet.Base = (pocket, inner)
    fillet.Radius = 3
    doc.recompute()
    expected = (40 * 5 + 5 * 35) * 60 - 2 * math.pi * 9 * 5 + (9 - 2.25 * math.pi) * 60
    return {"body": body, "volume": expected, "features": [base, pocket, fillet]}


def stepped_shaft(doc):
    """Albero a gradini per rivoluzione (Ø20/Ø30/Ø20, lungo 100) con smussi 1 mm alle estremità."""
    body = models.new_body(doc, "Albero")
    profile = _polygon(
        models.sketch_on(body, "Profilo", plane="XZ_Plane"),
        [(0, 0), (10, 0), (10, 40), (15, 40), (15, 70), (10, 70), (10, 100), (0, 100)],
    )
    revolution = body.newObject("PartDesign::Revolution", "Rivoluzione")
    revolution.Profile = profile
    revolution.ReferenceAxis = (profile, ["V_Axis"])
    revolution.Angle = 360
    doc.recompute()
    ends = _edges(
        revolution,
        lambda e: isinstance(e.Curve, Part.Circle)
        and abs(e.Curve.Radius - 10) < 1e-6
        and (abs(e.CenterOfMass.z) < 1e-6 or abs(e.CenterOfMass.z - 100) < 1e-6),
    )
    chamfer = body.newObject("PartDesign::Chamfer", "Smussi")
    chamfer.Base = (revolution, ends)
    chamfer.Size = 1
    doc.recompute()
    # Pappus: anello triangolare di area 0,5 con baricentro a raggio 10 - 1/3, per due estremità
    expected = math.pi * (100 * 40 + 225 * 30 + 100 * 30) - 2 * (2 * math.pi * (10 - 1 / 3) * 0.5)
    return {"body": body, "volume": expected, "features": [revolution, chamfer]}


def shelled_box(doc):
    """Scatola 60×40×30 con spigoli verticali raccordati r=5 e guscio di 2 mm aperto in alto."""
    body = models.new_body(doc, "Scatola")
    block = models.pad(body, models.add_rectangle(models.sketch_on(body, "Base"), 0, 0, 60, 40), 30, "Blocco")
    doc.recompute()
    vertical = _edges(block, lambda e: abs(e.tangentAt(e.FirstParameter).z) > 0.999)
    fillet = body.newObject("PartDesign::Fillet", "RaccordiVerticali")
    fillet.Base = (block, vertical)
    fillet.Radius = 5
    doc.recompute()
    top = [f"Face{i + 1}" for i, f in enumerate(fillet.Shape.Faces) if abs(f.CenterOfMass.z - 30) < 1e-6]
    shell = body.newObject("PartDesign::Thickness", "Guscio")
    shell.Base = (fillet, top)
    shell.Value = 2
    doc.recompute()
    # pianta esterna: rettangolo raccordato r=5; interna: offset di 2 → r=3, 56×36; cavità alta 28
    outer = 60 * 40 - (4 - math.pi) * 25
    inner = 56 * 36 - (4 - math.pi) * 9
    expected = outer * 30 - inner * 28
    return {"body": body, "volume": expected, "features": [block, fillet, shell]}


def spring(doc):
    """Molla: sezione circolare r=1 a raggio 10, passo 5, altezza 30 (elica additiva)."""
    body = models.new_body(doc, "Molla")
    section = models.add_circle(models.sketch_on(body, "Sezione", plane="XZ_Plane"), 10, 0, 1)
    helix = body.newObject("PartDesign::AdditiveHelix", "Elica")
    helix.Profile = section
    helix.ReferenceAxis = (section, ["V_Axis"])
    helix.Pitch = 5
    helix.Height = 30
    doc.recompute()
    turns = 30 / 5
    length = turns * math.hypot(2 * math.pi * 10, 5)
    # la sezione è nel piano dell'asse, non perpendicolare all'elica: l'area efficace è π·r²
    # proiettata; si usa una tolleranza più larga nei test
    expected = math.pi * 1**2 * length * math.cos(math.atan2(5, 2 * math.pi * 10))
    return {"body": body, "volume": expected, "features": [helix], "tolerance": 0.03}


EXAMPLES = {
    "flangia": flange,
    "staffa_a_L": l_bracket,
    "albero_a_gradini": stepped_shaft,
    "scatola_con_guscio": shelled_box,
    "molla": spring,
}
