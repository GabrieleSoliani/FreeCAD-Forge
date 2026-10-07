# SPDX-License-Identifier: LGPL-2.1-or-later
"""Gestore unificato di equazioni e variabili globali, come le "Equazioni" di SolidWorks (M4.3).

Raccoglie in un'unica tabella tutte le espressioni del documento (``ExpressionEngine`` di ogni
oggetto) e le variabili globali (proprietà di un ``App::VarSet`` "Variabili" e alias dei fogli
di calcolo), con il valore attuale. Permette di creare variabili globali e di impostare
equazioni verificandole prima di applicarle. Nessuna dipendenza dalla GUI.
"""

from dataclasses import dataclass

import FreeCAD

VARSET_NAME = "Variabili"


@dataclass
class Equation:
    object_name: str
    label: str
    path: str  # proprietà (eventualmente con percorso, es. ".Constraints.larghezza")
    expression: str
    value: str


@dataclass
class Variable:
    owner: str  # nome dell'oggetto (VarSet o foglio)
    name: str
    value: str
    kind: str  # "variabile" o "alias foglio"


def _format(value):
    if hasattr(value, "UserString"):
        return value.UserString
    return str(value)


def list_equations(doc):
    result = []
    for obj in doc.Objects:
        for path, expression in obj.ExpressionEngine:
            try:
                value = _format(obj.evalExpression(expression))
            except Exception as err:
                value = f"errore: {err}"
            result.append(Equation(obj.Name, obj.Label, path, expression, value))
    return result


def varset(doc, create=False):
    obj = doc.getObject(VARSET_NAME)
    if obj is None and create:
        obj = doc.addObject("App::VarSet", VARSET_NAME)
    return obj


_VARSET_STATIC = {"Label", "Label2", "ExpressionEngine", "Visibility", "Exposed", "ExposedType"}


def list_variables(doc):
    """Variabili globali: proprietà aggiunte ai VarSet e alias dei fogli di calcolo."""
    result = []
    for obj in doc.Objects:
        if obj.isDerivedFrom("App::VarSet"):
            for prop in obj.PropertiesList:
                if prop in _VARSET_STATIC:
                    continue
                result.append(Variable(obj.Name, prop, _format(getattr(obj, prop)), "variabile"))
        elif obj.isDerivedFrom("Spreadsheet::Sheet"):
            for cell in obj.getUsedCells():
                alias = obj.getAlias(cell)
                if alias:
                    result.append(Variable(obj.Name, alias, _format(obj.get(alias)), "alias foglio"))
    return result


PROPERTY_TYPES = {
    "lunghezza": "App::PropertyLength",
    "distanza": "App::PropertyDistance",
    "angolo": "App::PropertyAngle",
    "numero": "App::PropertyFloat",
    "intero": "App::PropertyInteger",
}


def add_variable(doc, name, value, kind="lunghezza"):
    """Crea (o aggiorna) una variabile globale nel VarSet "Variabili"."""
    if not name.isidentifier():
        raise ValueError(f"Nome di variabile non valido: {name}")
    vs = varset(doc, create=True)
    if name not in vs.PropertiesList:
        vs.addProperty(PROPERTY_TYPES[kind], name, "Variabili", "Variabile globale Forge")
    if isinstance(value, str):
        value = FreeCAD.Units.Quantity(value) if kind in ("lunghezza", "distanza", "angolo") else float(value)
    setattr(vs, name, value)
    doc.recompute()
    return vs


def check_expression(obj, expression):
    """Valuta l'espressione nel contesto dell'oggetto. Restituisce il valore o solleva ValueError."""
    try:
        return obj.evalExpression(expression)
    except Exception as err:
        raise ValueError(f"Equazione non valida \"{expression}\": {err}") from None


def set_equation(obj, path, expression):
    """Imposta (o rimuove con espressione vuota) l'equazione di una proprietà, dopo averla verificata."""
    if expression.strip():
        check_expression(obj, expression)
        obj.setExpression(path, expression)
    else:
        obj.setExpression(path, None)
    obj.Document.recompute()
