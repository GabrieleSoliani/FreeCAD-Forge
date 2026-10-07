# SPDX-License-Identifier: LGPL-2.1-or-later
"""Comandi GUI di valutazione: interferenze e analisi di sformo (M8)."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib import evaluate
from forgelib.commands import icon_path

PARAMS = "User parameter:BaseApp/Preferences/Mod/Forge"
INTERFERENCE_GROUP = "Interferenze"
DRAFT_OBJECT = "AnalisiSformo"


def _params():
    return FreeCAD.ParamGet(PARAMS)


def _in_body(obj):
    return any(p.isDerivedFrom("PartDesign::Body") for p in obj.InList)


def _is_forge_result(obj):
    if obj.Name.startswith(DRAFT_OBJECT) or obj.Name.startswith(INTERFERENCE_GROUP):
        return True
    return any(p.Name.startswith(INTERFERENCE_GROUP) for p in obj.InList)


def candidate_items(doc):
    """Oggetti da controllare: selezione (≥2), assieme attivo oppure solidi visibili di primo livello."""
    selection = [s.Object for s in FreeCADGui.Selection.getSelectionEx(doc.Name)]
    if len(selection) >= 2:
        return [(o.Label, evaluate.global_shape(o)) for o in selection]
    view = FreeCADGui.ActiveDocument.ActiveView if FreeCADGui.ActiveDocument else None
    try:
        active = view.getActiveObject("part") if view is not None else None
    except Exception:
        active = None
    if active is not None and active.isDerivedFrom("Assembly::AssemblyObject"):
        return evaluate.assembly_components(active)
    items = []
    for obj in doc.Objects:
        if _is_forge_result(obj):
            continue
        if not obj.isDerivedFrom("Part::Feature") and not obj.isDerivedFrom("App::Link"):
            continue
        if _in_body(obj) or obj.isDerivedFrom("Sketcher::SketchObject"):
            continue
        if not getattr(obj, "Visibility", False):
            continue
        try:
            shape = evaluate.global_shape(obj)
        except Exception:
            continue
        if shape.Solids:
            items.append((obj.Label, shape))
    return items


def run_interference(doc, clearance=None):
    """Esegue il controllo e crea il gruppo con i solidi d'interferenza. Restituisce i risultati."""
    if clearance is None:
        clearance = _params().GetFloat("Clearance", 0.0)
    old = doc.getObject(INTERFERENCE_GROUP)
    doc.openTransaction("Interferenze")
    try:
        if old is not None:
            old.removeObjectsFromDocument()
            doc.removeObject(old.Name)
        found = evaluate.check_pairs(candidate_items(doc), clearance=clearance)
        overlaps = [f for f in found if f.kind == "interferenza"]
        if overlaps:
            group = doc.addObject("App::DocumentObjectGroup", INTERFERENCE_GROUP)
            for number, item in enumerate(overlaps, start=1):
                obj = doc.addObject("Part::Feature", f"Interferenza{number:03d}")
                obj.Label = f"Interferenza {item.first} / {item.second}"
                obj.Shape = item.shape
                group.addObject(obj)
                if obj.ViewObject is not None:
                    obj.ViewObject.ShapeColor = (0.85, 0.1, 0.1)
                    obj.ViewObject.Transparency = 20
        doc.recompute()
    finally:
        doc.commitTransaction()
    return found


def report_text(found):
    if not found:
        return "Nessuna interferenza."
    lines = []
    for item in found:
        if item.kind == "interferenza":
            lines.append(f"Interferenza tra {item.first} e {item.second}: {item.volume:.3f} mm³")
        elif item.kind == "gioco":
            lines.append(
                f"Gioco insufficiente tra {item.first} e {item.second}: {item.distance:.3f} mm"
            )
        else:
            lines.append(f"Contatto tra {item.first} e {item.second}")
    return "\n".join(lines)


class _InterferenceCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_Interference"),
            "MenuText": "Rileva interferenze",
            "ToolTip": "Controlla le compenetrazioni tra i componenti selezionati, dell'assieme "
            "attivo o tra tutti i solidi visibili; le interferenze diventano solidi rossi nel "
            'gruppo "Interferenze"',
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        found = run_interference(FreeCAD.ActiveDocument)
        overlaps = sum(1 for f in found if f.kind == "interferenza")
        box = QtWidgets.QMessageBox(FreeCADGui.getMainWindow())
        box.setWindowTitle("Interferenze")
        box.setIcon(
            QtWidgets.QMessageBox.Warning if overlaps else QtWidgets.QMessageBox.Information
        )
        box.setText(f"Interferenze: {overlaps}. Coppie segnalate: {len(found)}.")
        box.setInformativeText(report_text(found))
        box.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        box.open()


def _pull_direction_and_object():
    """Direzione di estrazione dalla faccia selezionata (normale) oppure +Z."""
    selection = FreeCADGui.Selection.getSelectionEx()
    if not selection:
        return None, None
    sel = selection[0]
    direction = FreeCAD.Vector(0, 0, 1)
    for sub in sel.SubObjects:
        if sub.ShapeType == "Face":
            u0, u1, v0, v1 = sub.ParameterRange
            direction = sub.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            break
    return sel.Object, direction


def run_draft_analysis(obj, direction, min_angle=None):
    """Crea l'oggetto colorato dell'analisi di sformo per ``obj``. Restituisce (oggetto, facce)."""
    if min_angle is None:
        min_angle = _params().GetFloat("MinDraftAngle", 1.0)
    doc = obj.Document
    shape = evaluate.global_shape(obj)
    faces = evaluate.draft_analysis(shape, direction, min_angle)
    doc.openTransaction("Analisi di sformo")
    try:
        result = doc.addObject("Part::Feature", DRAFT_OBJECT)
        result.Label = f"Analisi sformo {obj.Label} ({min_angle:g}°)"
        result.Shape = shape
        result.addProperty("App::PropertyLink", "AnalysedObject", "Forge", "Oggetto analizzato")
        result.AnalysedObject = obj
        doc.recompute()
        if result.ViewObject is not None:
            colors = [(0.6, 0.6, 0.6)] * len(shape.Faces)
            for face in faces:
                colors[face.index - 1] = evaluate.DRAFT_COLORS[face.kind]
            result.ViewObject.DiffuseColor = colors
            obj.Visibility = False
    finally:
        doc.commitTransaction()
    return result, faces


def clear_draft_analysis(doc):
    """Rimuove le analisi di sformo e rende di nuovo visibili gli oggetti analizzati."""
    removed = 0
    for obj in list(doc.Objects):
        if obj.Name.startswith(DRAFT_OBJECT):
            target = getattr(obj, "AnalysedObject", None)
            if target is not None:
                target.Visibility = True
            doc.removeObject(obj.Name)
            removed += 1
    return removed


class _DraftAnalysisCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_DraftAnalysis"),
            "MenuText": "Analisi di sformo",
            "ToolTip": "Colora le facce in base all'angolo di sformo rispetto alla direzione di "
            "estrazione (normale della faccia selezionata, altrimenti +Z). Verde positivo, "
            "rosso negativo, giallo insufficiente, blu a cavallo. Rieseguire per togliere "
            "l'analisi.",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if clear_draft_analysis(doc):
            doc.recompute()
            return
        obj, direction = _pull_direction_and_object()
        if obj is None:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Analisi di sformo",
                "Seleziona un corpo o un solido (e, se vuoi, una sua faccia piana come direzione "
                "di estrazione).",
            )
            return
        _, faces = run_draft_analysis(obj, direction)
        counts = evaluate.summarize_draft(faces)
        text = ", ".join(f"{k}: {v}" for k, v in counts.items())
        FreeCAD.Console.PrintMessage(f"Forge: analisi di sformo di {obj.Label}: {text}\n")


EVALUATE_COMMANDS = ["Forge_Interference", "Forge_DraftAnalysis"]


def register():
    FreeCADGui.addCommand("Forge_Interference", _InterferenceCommand())
    FreeCADGui.addCommand("Forge_DraftAnalysis", _DraftAnalysisCommand())
    FreeCADGui.addCommand("Forge_ThicknessAnalysis", _ThicknessCommand())
    FreeCADGui.addCommand("Forge_Compare", _CompareCommand())


# --- analisi di spessore e confronto (M8) -------------------------------------------------------

THICKNESS_OBJECT = "AnalisiSpessore"
COMPARE_GROUP = "Confronto"


def run_thickness_analysis(obj, minimum=None):
    """Copia colorata: rosso le facce più sottili di ``minimum``, verde le altre."""
    if minimum is None:
        minimum = _params().GetFloat("MinThickness", 1.0)
    doc = obj.Document
    shape = evaluate.global_shape(obj)
    faces = evaluate.thickness_analysis(shape, minimum)
    doc.openTransaction("Analisi di spessore")
    try:
        result = doc.addObject("Part::Feature", THICKNESS_OBJECT)
        result.Label = f"Analisi spessore {obj.Label} (min {minimum:g} mm)"
        result.Shape = shape
        result.addProperty("App::PropertyLink", "AnalysedObject", "Forge", "Oggetto analizzato")
        result.AnalysedObject = obj
        doc.recompute()
        if result.ViewObject is not None:
            colors = [(0.6, 0.6, 0.6)] * len(shape.Faces)
            for face in faces:
                colors[face.index - 1] = evaluate.THICKNESS_COLORS[face.kind]
            result.ViewObject.DiffuseColor = colors
            obj.Visibility = False
    finally:
        doc.commitTransaction()
    return result, faces


def clear_thickness_analysis(doc):
    removed = 0
    for obj in list(doc.Objects):
        if obj.Name.startswith(THICKNESS_OBJECT):
            target = getattr(obj, "AnalysedObject", None)
            if target is not None:
                target.Visibility = True
            doc.removeObject(obj.Name)
            removed += 1
    return removed


def run_compare(old_obj, new_obj):
    """Gruppo "Confronto" con il materiale aggiunto (verde) e tolto (rosso) dalla nuova versione."""
    doc = new_obj.Document
    result = evaluate.compare_shapes(evaluate.global_shape(old_obj), evaluate.global_shape(new_obj))
    doc.openTransaction("Confronta versioni")
    try:
        old_group = doc.getObject(COMPARE_GROUP)
        if old_group is not None:
            old_group.removeObjectsFromDocument()
            doc.removeObject(old_group.Name)
        group = doc.addObject("App::DocumentObjectGroup", COMPARE_GROUP)
        for name, shape, volume, color in (
            ("Aggiunto", result.added, result.added_volume, (0.2, 0.75, 0.25)),
            ("Tolto", result.removed, result.removed_volume, (0.85, 0.2, 0.2)),
        ):
            if volume > 1e-6:
                part = doc.addObject("Part::Feature", name)
                part.Shape = shape
                part.Label = f"{name} ({volume:.1f} mm³)"
                group.addObject(part)
                if part.ViewObject is not None:
                    part.ViewObject.ShapeColor = color
        doc.recompute()
    finally:
        doc.commitTransaction()
    return result


class _ThicknessCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_ThicknessAnalysis"),
            "MenuText": "Analisi di spessore",
            "ToolTip": "Colora in rosso le facce dove lo spessore è sotto il minimo (parametro "
            "MinThickness, mm). Rieseguire per togliere l'analisi.",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        if clear_thickness_analysis(doc):
            doc.recompute()
            return
        selection = FreeCADGui.Selection.getSelection()
        if not selection:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(), "Analisi di spessore", "Seleziona un corpo o un solido.")
            return
        minimum = _params().GetFloat("MinThickness", 1.0)
        value, ok = QtWidgets.QInputDialog.getDouble(
            FreeCADGui.getMainWindow(), "Analisi di spessore", "Spessore minimo (mm):",
            minimum, 0.01, 1e6, 2)
        if not ok:
            return
        _params().SetFloat("MinThickness", value)
        _, faces = run_thickness_analysis(selection[0], value)
        thin = [f for f in faces if f.kind == evaluate.THIN]
        detail = f" (minimo {min(f.minimum for f in thin):.3f} mm)" if thin else ""
        FreeCAD.Console.PrintMessage(f"Forge: facce sotto {value:g} mm: {len(thin)}{detail}\n")


class _CompareCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_Compare"),
            "MenuText": "Confronta versioni",
            "ToolTip": "Seleziona la versione vecchia e poi la nuova: mostra in verde il materiale "
            "aggiunto e in rosso quello tolto, con i volumi",
        }

    def IsActive(self):
        return len(FreeCADGui.Selection.getSelection()) == 2

    def Activated(self):
        old_obj, new_obj = FreeCADGui.Selection.getSelection()
        result = run_compare(old_obj, new_obj)
        if result.identical:
            text = "Le due versioni sono identiche."
        else:
            text = f"Aggiunto {result.added_volume:.2f} mm³, tolto {result.removed_volume:.2f} mm³."
        QtWidgets.QMessageBox.information(FreeCADGui.getMainWindow(), "Confronta versioni", text)


EVALUATE_COMMANDS += ["Forge_ThicknessAnalysis", "Forge_Compare"]
