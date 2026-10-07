# SPDX-License-Identifier: LGPL-2.1-or-later
"""Messa in tavola rapida (M7): tavola automatica, distinta con palloncini, cartiglio compilato.

- ``auto_drawing``: pagina A3 ISO 5457 con viste frontale/superiore/laterale (metodo europeo,
  primo diedro) e assonometria, a scala unificata scelta automaticamente;
- ``bom_rows`` / ``add_bom``: distinta raggruppata per componente con quantità, materiale, massa;
  foglio di calcolo collegato e posizionato sulla tavola;
- ``add_balloons``: un palloncino per voce di distinta, ancorato al baricentro del componente;
- ``fill_title_block``: campi del cartiglio da proprietà del documento e dell'oggetto.
Nessuna dipendenza dalla GUI (la pagina si apre a parte).
"""

import datetime
import os
from dataclasses import dataclass

import FreeCAD
from FreeCAD import Vector

TEMPLATE = "A3_Landscape_ISO5457_advanced.svg"
SHEET_W, SHEET_H = 420.0, 297.0
# area utile per le tre viste ortogonali (sinistra della tavola, sopra il cartiglio)
VIEWS_W, VIEWS_H = 250.0, 170.0
GAP = 25.0
STANDARD_SCALES = [10, 5, 2, 1, 1 / 2, 1 / 2.5, 1 / 5, 1 / 10, 1 / 20, 1 / 50, 1 / 100]


def template_path(name=TEMPLATE):
    candidates = [
        os.path.join(FreeCAD.getResourceDir(), "Mod", "TechDraw", "Templates", "ISO", name),
        os.path.join(FreeCAD.getHomePath(), "Mod", "TechDraw", "Templates", "ISO", name),
        os.path.join(FreeCAD.getHomePath(), "data", "Mod", "TechDraw", "Templates", "ISO", name),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(f"Template TechDraw non trovato: {name}")


def scale_text(scale):
    if scale >= 1:
        return f"{scale:g}:1"
    return f"1:{1 / scale:g}"


def choose_scale(size_x, size_y, size_z):
    """Scala unificata più grande con cui le tre viste (fronte, sopra, lato) entrano nell'area utile."""
    width = size_x + size_y
    height = size_z + size_y
    for scale in STANDARD_SCALES:
        if width * scale + GAP <= VIEWS_W and height * scale + GAP <= VIEWS_H:
            return scale
    return STANDARD_SCALES[-1]


def _sources_shape(sources):
    import Part

    shapes = [Part.getShape(o, "", needSubElement=False, transform=True) for o in sources]
    shapes = [s for s in shapes if not s.isNull()]
    return Part.makeCompound(shapes)


def auto_drawing(doc, sources, name="Tavola"):
    """Crea la tavola con le viste standard degli oggetti ``sources``. Restituisce (pagina, viste)."""
    sources = list(sources)
    shape = _sources_shape(sources)
    box = shape.BoundBox
    scale = choose_scale(box.XLength, box.YLength, box.ZLength)

    page = doc.addObject("TechDraw::DrawPage", name)
    template = doc.addObject("TechDraw::DrawSVGTemplate", name + "Template")
    template.Template = template_path()
    page.Template = template
    page.Scale = scale

    group = doc.addObject("TechDraw::DrawProjGroup", name + "Viste")
    page.addView(group)
    group.Source = sources
    group.ProjectionType = "First angle"
    group.ScaleType = "Page"
    group.addProjection("Front")
    group.addProjection("Top")
    group.addProjection("Right")
    group.X = 30 + VIEWS_W / 2
    group.Y = 75 + VIEWS_H / 2

    iso = doc.addObject("TechDraw::DrawViewPart", name + "Iso")
    page.addView(iso)
    iso.Source = sources
    iso.Direction = Vector(1, -1, 1)
    iso.XDirection = Vector(1, 1, 0)
    iso.ScaleType = "Custom"
    iso.Scale = scale * 0.6
    iso.X = 345
    iso.Y = 150
    doc.recompute()
    return page, {"group": group, "iso": iso, "scale": scale}


def front_view(info):
    group = info["group"]
    for view in group.Views:
        if getattr(view, "Type", "") == "Front":
            return view
    return group.Views[0]


# --- distinta ----------------------------------------------------------------------------------


@dataclass
class BomRow:
    item: int
    name: str
    quantity: int
    material: str
    instances: list  # oggetti del documento


def _component_key(obj):
    target = obj.LinkedObject if obj.isDerivedFrom("App::Link") and obj.LinkedObject else obj
    designation = getattr(target, "Designation", "") or getattr(obj, "Designation", "")
    return target, designation or target.Label


def _material(target):
    material = getattr(target, "ShapeMaterial", None)
    name = getattr(material, "Name", "") if material is not None else ""
    return "" if name in ("", "Default") else name


def is_component(obj):
    """Componenti da contare in distinta: solidi di primo livello, link, viteria, serie."""
    if obj.isDerivedFrom("App::DocumentObjectGroup") or obj.TypeId.startswith("TechDraw::"):
        return False
    if obj.TypeId.startswith(("Assembly::", "Spreadsheet::", "Sketcher::")):
        return False
    if any(p.isDerivedFrom("PartDesign::Body") for p in obj.InList):
        return False
    if obj.isDerivedFrom("App::Link") or obj.isDerivedFrom("PartDesign::Body"):
        return True
    if obj.isDerivedFrom("Part::Feature"):
        # le forme usate da altri oggetti (es. sorgenti di una specchiatura) non sono componenti
        users = [p for p in obj.InList if not p.TypeId.startswith(("TechDraw::", "Assembly::", "App::Part"))]
        return not users and not obj.Shape.isNull() and len(obj.Shape.Solids) > 0
    return False


def bom_rows(objects):
    rows = {}
    order = []
    for obj in objects:
        if not is_component(obj):
            continue
        target, name = _component_key(obj)
        count = 1
        element_count = getattr(obj, "ElementCount", 0) if obj.isDerivedFrom("App::Link") else 0
        if element_count:
            count = element_count
        if name not in rows:
            rows[name] = BomRow(0, name, 0, _material(target), [])
            order.append(name)
        rows[name].quantity += count
        rows[name].instances.append(obj)
    result = []
    for item, name in enumerate(order, start=1):
        row = rows[name]
        row.item = item
        result.append(row)
    return result


def add_bom(page, rows, name="Distinta"):
    doc = page.Document
    sheet = doc.addObject("Spreadsheet::Sheet", name)
    for col, header in zip("ABCD", ("Pos.", "Denominazione", "Q.tà", "Materiale")):
        sheet.set(f"{col}1", header)
    for i, row in enumerate(rows, start=2):
        sheet.set(f"A{i}", str(row.item))
        sheet.set(f"B{i}", row.name)
        sheet.set(f"C{i}", str(row.quantity))
        sheet.set(f"D{i}", row.material)
    doc.recompute()
    view = doc.addObject("TechDraw::DrawViewSpreadsheet", name + "Vista")
    view.Source = sheet
    view.CellEnd = f"D{len(rows) + 1}"
    page.addView(view)
    view.X = 330
    view.Y = 260
    doc.recompute()
    return sheet, view


def add_balloons(page, view, rows):
    """Un palloncino per voce, ancorato al baricentro della prima istanza del componente."""
    import Part

    doc = page.Document
    sources = list(view.Source) or list(getattr(view, "XSource", []))
    centre = _sources_shape(sources).BoundBox.Center
    balloons = []
    for row in rows:
        shape = Part.getShape(row.instances[0], "", needSubElement=False, transform=True)
        anchor = view.projectPoint(shape.BoundBox.Center.sub(centre))
        balloon = doc.addObject("TechDraw::DrawViewBalloon", f"Palloncino{row.item:03d}")
        balloon.SourceView = view
        balloon.OriginX = anchor.x
        balloon.OriginY = anchor.y
        length = max(anchor.Length, 1e-6)
        offset = 25.0 / max(view.getScale(), 1e-9)
        balloon.X = anchor.x + anchor.x / length * offset
        balloon.Y = anchor.y + anchor.y / length * offset
        balloon.Text = str(row.item)
        page.addView(balloon)
        balloons.append(balloon)
    doc.recompute()
    return balloons


# --- cartiglio ---------------------------------------------------------------------------------


def author():
    return FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Document").GetString("prefAuthor", "")


def title_block_values(page, main_object=None, document_type="Disegno di particolare"):
    doc = page.Document
    values = {
        "title": main_object.Label if main_object is not None else doc.Label,
        "creator": doc.CreatedBy or author(),
        "date_of_issue": datetime.date.today().isoformat(),
        "scale": scale_text(page.Scale),
        "drawing_number": doc.Label,
        "sheet_number": "1/1",
        "language_code": "it",
        "general_tolerances": "ISO 2768-m",
        "document_type": document_type,
        "revision_index": "A",
    }
    if main_object is not None:
        target, _ = _component_key(main_object)
        material = _material(target)
        if material:
            values["part_material"] = material
    return values


def fill_title_block(page, values):
    """Compila i campi del cartiglio presenti nel template. Restituisce i campi effettivamente scritti."""
    template = page.Template
    texts = dict(template.EditableTexts)
    written = {k: v for k, v in values.items() if k in texts}
    texts.update(written)
    template.EditableTexts = texts
    return written
