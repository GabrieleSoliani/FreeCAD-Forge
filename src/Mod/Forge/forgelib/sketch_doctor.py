# SPDX-License-Identifier: LGPL-2.1-or-later
"""Diagnosi degli schizzi con proposta di soluzioni, come SketchXpert di SolidWorks (M2).

``analyze(sketch)`` risolve lo schizzo e riporta gradi di libertà, vincoli in conflitto,
ridondanti e malformati. ``propose_fixes(sketch)`` prova a disattivare uno alla volta i vincoli
sospetti (riattivandoli subito dopo) e restituisce solo le correzioni che risolvono davvero il
problema, con i gradi di libertà che resterebbero. Nessuna dipendenza dalla GUI.

Convenzione: gli indici dei vincoli esposti all'utente sono in base 1, come nei messaggi del
solutore di FreeCAD (``ConflictingConstraints`` ecc.).
"""

import math
from dataclasses import dataclass, field

TYPE_NAMES = {
    "Coincident": "Coincidente",
    "Horizontal": "Orizzontale",
    "Vertical": "Verticale",
    "Parallel": "Parallelo",
    "Perpendicular": "Perpendicolare",
    "Tangent": "Tangente",
    "Equal": "Uguale",
    "Symmetric": "Simmetrico",
    "Block": "Blocco",
    "Distance": "Distanza",
    "DistanceX": "Distanza orizzontale",
    "DistanceY": "Distanza verticale",
    "Radius": "Raggio",
    "Diameter": "Diametro",
    "Angle": "Angolo",
    "PointOnObject": "Punto su oggetto",
    "InternalAlignment": "Allineamento interno",
    "SnellsLaw": "Legge di Snell",
    "Weight": "Peso",
}
DIMENSIONAL = {"Distance", "DistanceX", "DistanceY", "Radius", "Diameter", "Angle", "Weight"}

GEOMETRY_NAMES = {
    "Part::GeomLineSegment": "Linea",
    "Part::GeomArcOfCircle": "Arco",
    "Part::GeomCircle": "Cerchio",
    "Part::GeomPoint": "Punto",
    "Part::GeomEllipse": "Ellisse",
    "Part::GeomArcOfEllipse": "Arco di ellisse",
    "Part::GeomArcOfHyperbola": "Arco di iperbole",
    "Part::GeomArcOfParabola": "Arco di parabola",
    "Part::GeomBSplineCurve": "B-spline",
}


@dataclass
class SketchState:
    status: int  # risultato di solve(): 0 ok, <0 errore
    dof: int
    conflicting: list = field(default_factory=list)  # base 1
    redundant: list = field(default_factory=list)
    partially_redundant: list = field(default_factory=list)
    malformed: list = field(default_factory=list)

    @property
    def fully_constrained(self):
        return self.ok and self.dof == 0

    @property
    def ok(self):
        return not (self.conflicting or self.redundant or self.malformed) and self.status == 0


@dataclass
class Fix:
    constraint: int  # base 1
    description: str
    action: str  # "elimina"
    dof_after: int
    resolves: bool


def geometry_name(sketch, geo_id):
    if geo_id == -1:
        return "asse orizzontale"
    if geo_id == -2:
        return "asse verticale"
    if geo_id <= -3:
        return f"geometria esterna {-geo_id - 2}"
    if geo_id < 0 or geo_id >= sketch.GeometryCount:
        return "?"
    geometry = sketch.Geometry[geo_id]
    name = GEOMETRY_NAMES.get(geometry.TypeId, "Elemento")
    if sketch.getConstruction(geo_id):
        name += " di costruzione"
    return f"{name} {geo_id + 1}"


def describe(sketch, index):
    """Descrizione in italiano del vincolo ``index`` (base 1)."""
    constraint = sketch.Constraints[index - 1]
    kind = TYPE_NAMES.get(constraint.Type, constraint.Type)
    parts = [geometry_name(sketch, constraint.First)]
    if constraint.Second not in (-2000, None) and constraint.Type not in ("Horizontal", "Vertical"):
        if constraint.Second != constraint.First:
            parts.append(geometry_name(sketch, constraint.Second))
    text = f"#{index} {kind}"
    if constraint.Name:
        text += f" \"{constraint.Name}\""
    if constraint.Type in DIMENSIONAL and constraint.Type != "Weight":
        if constraint.Type == "Angle":
            text += f" {math.degrees(constraint.Value):.4g}°"
        else:
            text += f" {constraint.Value:.4g} mm"
    if not constraint.Driving:
        text += " (di riferimento)"
    return f"{text} ({' / '.join(parts)})"


def analyze(sketch):
    status = sketch.solve()
    return SketchState(
        status=status,
        dof=sketch.DoF,
        conflicting=list(sketch.ConflictingConstraints),
        redundant=list(sketch.RedundantConstraints),
        partially_redundant=list(sketch.PartiallyRedundantConstraints),
        malformed=list(sketch.MalformedConstraints),
    )


def _try_without(sketch, index):
    """Stato dello schizzo con il vincolo ``index`` (base 1) disattivato; poi lo riattiva."""
    was_active = sketch.Constraints[index - 1].IsActive
    sketch.setActive(index - 1, False)
    try:
        return analyze(sketch)
    finally:
        sketch.setActive(index - 1, was_active)
        sketch.solve()


def _candidate_order(sketch, indices):
    """Prima i vincoli dimensionali, poi quelli geometrici, per ultimi i coincidenti."""

    def rank(index):
        kind = sketch.Constraints[index - 1].Type
        if kind in DIMENSIONAL:
            return 0
        if kind in ("Coincident", "InternalAlignment"):
            return 2
        return 1

    return sorted(indices, key=lambda i: (rank(i), i))


def propose_fixes(sketch, state=None):
    """Correzioni che risolvono conflitti o ridondanze, verificate una per una."""
    if state is None:
        state = analyze(sketch)
    fixes = []
    if state.conflicting:
        for index in _candidate_order(sketch, state.conflicting):
            after = _try_without(sketch, index)
            if not after.conflicting:
                fixes.append(Fix(index, describe(sketch, index), "elimina", after.dof,
                                 not after.redundant))
    elif state.redundant:
        for index in state.redundant:
            after = _try_without(sketch, index)
            if not after.redundant and not after.conflicting:
                fixes.append(Fix(index, describe(sketch, index), "elimina", after.dof, True))
    return fixes


def report(sketch):
    """Testo di sintesi in italiano dello stato dello schizzo."""
    state = analyze(sketch)
    lines = []
    if state.malformed:
        lines.append("Vincoli malformati (riferimenti non validi): "
                     + ", ".join(describe(sketch, i) for i in state.malformed))
    if state.conflicting:
        lines.append("Vincoli in conflitto: " + ", ".join(describe(sketch, i) for i in state.conflicting))
    if state.redundant:
        lines.append("Vincoli ridondanti: " + ", ".join(describe(sketch, i) for i in state.redundant))
    if not lines:
        if state.dof == 0:
            lines.append("Lo schizzo è completamente vincolato.")
        else:
            lines.append(f"Lo schizzo è sotto-vincolato: {state.dof} gradi di libertà.")
    return state, "\n".join(lines)


def apply_fix(sketch, fix):
    """Elimina il vincolo proposto (in una transazione annullabile)."""
    doc = sketch.Document
    doc.openTransaction("Diagnosi schizzo")
    try:
        sketch.delConstraint(fix.constraint - 1)
        sketch.solve()
    finally:
        doc.commitTransaction()
