# SPDX-License-Identifier: LGPL-2.1-or-later
"""Costruzione di modelli PartDesign di prova, senza GUI."""

import FreeCAD
import Part
from FreeCAD import Vector


def origin_feature(body, role):
    for feature in body.Origin.OriginFeatures:
        if feature.Role == role:
            return feature
    raise LookupError(role)


def sketch_on(body, name, plane="XY_Plane", offset=None):
    sketch = body.newObject("Sketcher::SketchObject", name)
    sketch.AttachmentSupport = (origin_feature(body, plane), [""])
    sketch.MapMode = "FlatFace"
    if offset is not None:
        sketch.AttachmentOffset = FreeCAD.Placement(offset, FreeCAD.Rotation())
    return sketch


def add_rectangle(sketch, x0, y0, x1, y1):
    points = [Vector(x0, y0, 0), Vector(x1, y0, 0), Vector(x1, y1, 0), Vector(x0, y1, 0)]
    first = sketch.GeometryCount
    for i in range(4):
        sketch.addGeometry(Part.LineSegment(points[i], points[(i + 1) % 4]))
    import Sketcher

    for i in range(4):
        sketch.addConstraint(Sketcher.Constraint("Coincident", first + i, 2, first + (i + 1) % 4, 1))
    return sketch


def add_circle(sketch, cx, cy, r):
    sketch.addGeometry(Part.Circle(Vector(cx, cy, 0), Vector(0, 0, 1), r))
    return sketch


def new_body(doc, name="Body"):
    return doc.addObject("PartDesign::Body", name)


def pad(body, sketch, length, name="Pad"):
    feature = body.newObject("PartDesign::Pad", name)
    feature.Profile = sketch
    feature.Length = length
    return feature


def pocket(body, sketch, length, name="Pocket"):
    feature = body.newObject("PartDesign::Pocket", name)
    feature.Profile = sketch
    feature.Length = length
    return feature


def block_with_hole(doc):
    """Blocco 20x10x10 con foro cieco Ø4 profondo 5 dalla faccia superiore.

    Restituisce (body, pad, pocket). Volume finale: 2000 - 20π.
    """
    body = new_body(doc)
    base = add_rectangle(sketch_on(body, "BaseSketch"), 0, 0, 20, 10)
    pad_feature = pad(body, base, 10)
    top = add_circle(sketch_on(body, "HoleSketch", offset=Vector(0, 0, 10)), 10, 5, 2)
    pocket_feature = pocket(body, top, 5)
    doc.recompute()
    return body, pad_feature, pocket_feature
