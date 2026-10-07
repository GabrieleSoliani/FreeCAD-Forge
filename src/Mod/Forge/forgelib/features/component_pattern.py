# SPDX-License-Identifier: LGPL-2.1-or-later
"""Serie (lineare/circolare) e specchiatura di componenti d'assieme (M6.2).

La serie è un array di link nativo (``App::LinkPython`` con ``ElementCount``/``PlacementList``):
le copie seguono il componente seme e i parametri a ogni ricalcolo, senza creare o cancellare
oggetti durante il ricalcolo. La specchiatura usa ``Part::Mirroring`` sul componente (versione
"opposta" del pezzo). Nessuna dipendenza dalla GUI.
"""

import math

import FreeCAD
from FreeCAD import Vector

MODES = ["Lineare", "Circolare"]


def instance_placements(seed_placement, mode, count, direction=Vector(1, 0, 0), spacing=10.0,
                        axis_point=Vector(), axis=Vector(0, 0, 1), angle=360.0):
    """Posizioni delle copie (esclusa la prima, che è il seme)."""
    result = []
    if count < 2:
        return result
    if mode == "Lineare":
        d = Vector(direction)
        if d.Length < 1e-12:
            raise ValueError("Direzione della serie nulla")
        d.normalize()
        for i in range(1, count):
            p = FreeCAD.Placement(seed_placement)
            p.Base = p.Base.add(Vector(d).multiply(spacing * i))
            result.append(p)
    else:
        a = Vector(axis)
        if a.Length < 1e-12:
            raise ValueError("Asse della serie nullo")
        full = abs(abs(angle) - 360.0) < 1e-9
        step = angle / (count if full else count - 1)
        for i in range(1, count):
            rot = FreeCAD.Rotation(a, step * i)
            move = FreeCAD.Placement(Vector(), rot, axis_point)
            result.append(move.multiply(seed_placement))
    return result


class ComponentPattern:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyLink", "Seed", "Serie", "Componente da ripetere")
        obj.addProperty("App::PropertyEnumeration", "Mode", "Serie", "Lineare o circolare")
        obj.Mode = MODES
        obj.addProperty("App::PropertyInteger", "Count", "Serie", "Numero totale di istanze (seme incluso)")
        obj.Count = 3
        obj.addProperty("App::PropertyVector", "Direction", "Serie", "Direzione (serie lineare)")
        obj.Direction = Vector(1, 0, 0)
        obj.addProperty("App::PropertyLength", "Spacing", "Serie", "Passo (serie lineare)")
        obj.Spacing = 50
        obj.addProperty("App::PropertyVector", "AxisPoint", "Serie", "Punto dell'asse (serie circolare)")
        obj.addProperty("App::PropertyVector", "Axis", "Serie", "Asse (serie circolare)")
        obj.Axis = Vector(0, 0, 1)
        obj.addProperty("App::PropertyAngle", "Angle", "Serie", "Angolo totale (serie circolare)")
        obj.Angle = 360

    def execute(self, obj):
        seed = obj.Seed
        if seed is None:
            raise ValueError("Serie di componenti senza componente seme")
        target = seed.LinkedObject if seed.isDerivedFrom("App::Link") else seed
        if obj.LinkedObject != target:
            obj.LinkedObject = target
        placements = instance_placements(
            seed.Placement, obj.Mode, int(obj.Count), obj.Direction, float(obj.Spacing),
            obj.AxisPoint, obj.Axis, float(obj.Angle),
        )
        if obj.Placement != FreeCAD.Placement():
            obj.Placement = FreeCAD.Placement()
        if obj.ElementCount != len(placements):
            obj.ElementCount = len(placements)
        obj.PlacementList = placements

    def onDocumentRestored(self, obj):
        obj.Proxy = self

    def dumps(self):
        return None

    def loads(self, state):
        return None


def make_pattern(doc, seed, mode="Lineare", count=3, name="SerieComponenti", **params):
    obj = doc.addObject("App::LinkPython", name)
    ComponentPattern(obj)
    obj.Seed = seed
    obj.Mode = mode
    obj.Count = count
    for key, value in params.items():
        setattr(obj, key, value)
    obj.ShowElement = False
    return obj


def make_mirror(doc, component, base=Vector(), normal=Vector(1, 0, 0), name="Specchiato"):
    """Copia speculare (versione opposta) di un componente rispetto al piano (base, normal)."""
    obj = doc.addObject("Part::Mirroring", name)
    obj.Source = component
    obj.Base = base
    obj.Normal = normal
    obj.Label = f"{component.Label} (opposto)"
    return obj
