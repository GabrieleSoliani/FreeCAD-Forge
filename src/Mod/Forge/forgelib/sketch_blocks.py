# SPDX-License-Identifier: LGPL-2.1-or-later
"""Blocchi di schizzo riutilizzabili, come i blocchi di SolidWorks (M2.3).

Un blocco è un insieme di geometrie con i vincoli *interni* (che collegano solo geometrie del
blocco), salvato in un file JSON che usa la serializzazione nativa di FreeCAD
(``dumpContent``/``restoreContent``, in base64) per geometrie e vincoli. All'inserimento le geometrie vengono
traslate e gli indici dei vincoli rimappati. I vincoli verso assi o geometria esterna non fanno
parte del blocco: così il blocco resta rigido ma libero di essere posizionato (3 gradi di
libertà se è completamente vincolato al suo interno). Nessuna dipendenza dalla GUI.
"""

import base64
import json
import os

import FreeCAD
import Part
import Sketcher

FORMAT = "forge-sketch-block"
VERSION = 1

# numero di campi (First, Second, Third) che possono riferirsi a geometrie
_GEO_FIELDS = ("First", "Second", "Third")
_UNUSED = -2000  # GeoEnum::GeoUndef


def blocks_dir():
    path = os.path.join(FreeCAD.getUserAppDataDir(), "Forge", "Blocchi")
    os.makedirs(path, exist_ok=True)
    return path


def _encode(persistent):
    return base64.b64encode(bytes(persistent.dumpContent())).decode("ascii")


def _decode(text):
    return base64.b64decode(text.encode("ascii"))


def _referenced(constraint):
    return [getattr(constraint, f) for f in _GEO_FIELDS if getattr(constraint, f) != _UNUSED]


def make_block(sketch, geo_ids, name="Blocco"):
    """Dati del blocco formato dalle geometrie ``geo_ids`` (base 0) dello schizzo."""
    geo_ids = sorted(set(geo_ids))
    if not geo_ids:
        raise ValueError("Nessuna geometria selezionata per il blocco")
    remap = {old: new for new, old in enumerate(geo_ids)}
    geometries = []
    for old in geo_ids:
        geometry = sketch.Geometry[old]
        geometries.append(
            {
                "type": geometry.TypeId,
                "content": _encode(geometry),
                "construction": bool(sketch.getConstruction(old)),
            }
        )
    constraints = []
    for constraint in sketch.Constraints:
        refs = _referenced(constraint)
        if not refs or any(r not in remap for r in refs):
            continue  # vincoli verso assi, esterni o fuori blocco: non fanno parte del blocco
        constraints.append(_encode(constraint))
    # gli indici restano quelli dello schizzo di origine: si rimappano all'inserimento
    return {
        "format": FORMAT,
        "version": VERSION,
        "name": name,
        "source_ids": geo_ids,
        "geometries": geometries,
        "constraints": constraints,
    }


def save_block(sketch, geo_ids, path, name=None):
    data = make_block(sketch, geo_ids, name or os.path.splitext(os.path.basename(path))[0])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    return data


def load_block(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("format") != FORMAT:
        raise ValueError(f"{path}: non è un blocco di schizzo Forge")
    return data


def _new_geometry(type_id):
    constructors = {
        "Part::GeomLineSegment": Part.LineSegment,
        "Part::GeomCircle": Part.Circle,
        "Part::GeomArcOfCircle": lambda: Part.ArcOfCircle(Part.Circle(), 0, 1),
        "Part::GeomPoint": lambda: Part.Point(FreeCAD.Vector()),
        "Part::GeomEllipse": Part.Ellipse,
        "Part::GeomArcOfEllipse": lambda: Part.ArcOfEllipse(Part.Ellipse(), 0, 1),
        "Part::GeomBSplineCurve": Part.BSplineCurve,
    }
    if type_id not in constructors:
        raise ValueError(f"Tipo di geometria non supportato nei blocchi: {type_id}")
    return constructors[type_id]()


def insert_block(sketch, data, offset=FreeCAD.Vector()):
    """Inserisce il blocco nello schizzo traslato di ``offset``. Restituisce i nuovi geo id."""
    source_ids = data["source_ids"]
    first_new = sketch.GeometryCount
    remap = {old: first_new + i for i, old in enumerate(source_ids)}
    new_ids = []
    for item in data["geometries"]:
        geometry = _new_geometry(item["type"])
        geometry.restoreContent(_decode(item["content"]))
        geometry.translate(offset)
        new_ids.append(sketch.addGeometry(geometry, item["construction"]))
    constraints = []
    for content in data["constraints"]:
        constraint = Sketcher.Constraint("Horizontal", 0)
        constraint.restoreContent(_decode(content))
        for field_name in _GEO_FIELDS:
            value = getattr(constraint, field_name)
            if value != _UNUSED:
                setattr(constraint, field_name, remap[value])
        constraints.append(constraint)
    if constraints:
        sketch.addConstraint(constraints)
    sketch.solve()
    return new_ids


def list_blocks(directory=None):
    directory = directory or blocks_dir()
    return sorted(
        os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(".json")
    )
