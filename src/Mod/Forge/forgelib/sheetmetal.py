# SPDX-License-Identifier: LGPL-2.1-or-later
"""Lamiera (M5): funzioni Forge sopra l'addon SheetMetal integrato in ``src/Mod/SheetMetal``.

- creazione da script di flangia base, flangia su bordo e sviluppo (per test ed esempi);
- tabella di piega (angolo, raggio, fattore K, tolleranza e deduzione di piega);
- esportazione DXF dello sviluppo in piano.
Nessuna dipendenza dalla GUI.
"""

import math
from dataclasses import dataclass

import FreeCAD


def _sm():
    import SheetMetalBaseCmd
    import SheetMetalCmd
    import SheetMetalUnfoldCmd

    return SheetMetalBaseCmd, SheetMetalCmd, SheetMetalUnfoldCmd


def base_flange(doc, sketch, thickness, radius=1.0, name="FlangiaBase"):
    base_cmd, _, _ = _sm()
    obj = doc.addObject("Part::FeaturePython", name)
    base_cmd.SMBaseBend(obj, sketch)
    obj.Thickness = thickness
    obj.Radius = radius
    if FreeCAD.GuiUp:
        base_cmd.SMBaseViewProvider(obj.ViewObject)
    return obj


def edge_flange(doc, base, edges, length, radius=None, angle=90.0, name="Flangia"):
    _, wall_cmd, _ = _sm()
    obj = doc.addObject("Part::FeaturePython", name)
    wall_cmd.SMBendWall(obj, base, list(edges))
    obj.length = length
    obj.angle = angle
    if radius is not None:
        obj.radius = radius
    if FreeCAD.GuiUp:
        wall_cmd.SMViewProviderTree(obj.ViewObject)
    return obj


def unfold(doc, folded, stationary_face, name="Sviluppo", sketch=True):
    _, _, unfold_cmd = _sm()
    obj = doc.addObject("Part::FeaturePython", name)
    unfold_cmd.SMUnfold(obj, folded, [stationary_face])
    if hasattr(obj, "GenerateSketch"):
        obj.GenerateSketch = sketch
    return obj


@dataclass
class Bend:
    feature: str
    angle: float  # gradi
    radius: float  # raggio interno
    thickness: float
    kfactor: float

    @property
    def allowance(self):
        """Tolleranza di piega: lunghezza della fibra neutra nella piega."""
        return math.radians(self.angle) * (self.radius + self.kfactor * self.thickness)

    @property
    def deduction(self):
        """Deduzione di piega: 2·(r+t)·tan(α/2) − tolleranza (convenzione delle quote esterne)."""
        outside = 2 * (self.radius + self.thickness) * math.tan(math.radians(self.angle) / 2)
        return outside - self.allowance


def _thickness(obj):
    seen = set()
    while obj is not None and obj.Name not in seen:
        seen.add(obj.Name)
        if hasattr(obj, "Thickness"):
            return float(obj.Thickness)
        link = getattr(obj, "baseObject", None)
        obj = link[0] if isinstance(link, tuple) else link
    return None


def unfold_kfactor(unfold_obj):
    """Fattore K (convenzione ANSI) usato dallo sviluppo: in DIN K vale il doppio."""
    k = float(getattr(unfold_obj, "KFactor", 0.5))
    if str(getattr(unfold_obj, "KFactorStandard", "ansi")).lower() == "din":
        k /= 2
    return k


def bend_table_for_unfold(unfold_obj):
    """Tabella di piega coerente con lo sviluppo (stesso fattore K)."""
    folded = unfold_obj.baseObject[0]
    return bend_table(folded, kfactor=unfold_kfactor(unfold_obj))


def bend_table(folded, kfactor=0.5):
    """Pieghe della catena di feature lamiera che termina in ``folded``, dalla prima all'ultima.

    ``kfactor`` (ANSI) è quello usato per lo sviluppo: le singole flange non lo determinano.
    """
    rows = []
    obj = folded
    seen = set()
    thickness = _thickness(folded)
    while obj is not None and obj.Name not in seen:
        seen.add(obj.Name)
        if hasattr(obj, "angle") and hasattr(obj, "radius"):
            rows.append(Bend(obj.Label, float(obj.angle), float(obj.radius), thickness, kfactor))
        link = getattr(obj, "baseObject", None)
        obj = link[0] if isinstance(link, tuple) else link
    rows.reverse()
    return rows


def bend_table_text(rows):
    lines = ["Feature;Angolo [°];Raggio int. [mm];Spessore [mm];Fattore K;Tolleranza [mm];Deduzione [mm]"]
    for r in rows:
        lines.append(
            f"{r.feature};{r.angle:.2f};{r.radius:.3f};{r.thickness:.3f};{r.kfactor:.3f};"
            f"{r.allowance:.3f};{r.deduction:.3f}"
        )
    return "\n".join(lines)


def flat_sketches(unfold_obj):
    doc = unfold_obj.Document
    names = list(getattr(unfold_obj, "UnfoldSketches", []) or [])
    return [doc.getObject(n) for n in names if doc.getObject(n) is not None]


def export_flat_dxf(unfold_obj, path):
    """Esporta in DXF gli schizzi dello sviluppo (contorno, linee di piega). Restituisce gli schizzi."""
    if not getattr(unfold_obj, "GenerateSketch", True):
        unfold_obj.GenerateSketch = True
        unfold_obj.Document.recompute()
    sketches = flat_sketches(unfold_obj)
    if not sketches:
        raise RuntimeError("Lo sviluppo non ha generato schizzi da esportare")
    import importDXF

    importDXF.export(sketches, path)
    return sketches
