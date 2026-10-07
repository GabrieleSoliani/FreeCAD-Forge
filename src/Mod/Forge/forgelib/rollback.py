# SPDX-License-Identifier: LGPL-2.1-or-later
"""Rollback di un corpo PartDesign, come la rollback bar di SolidWorks.

La posizione di rollback è un intero da 0 a N (N = numero di feature solide del corpo):
- 0 = prima di tutte le feature (``Tip`` = feature base del corpo, se c'è, altrimenti nessuno);
- k = dopo la k-esima feature (``Tip`` = k-esima feature).
FreeCAD calcola la forma del corpo fino al ``Tip``: è lo stesso meccanismo di
``PartDesign_MoveTip``, qui reso navigabile a passi. Nessuna dipendenza dalla GUI.
"""

import FreeCAD


def is_body(obj):
    return obj is not None and obj.isDerivedFrom("PartDesign::Body")


def solid_features(body):
    """Feature solide del corpo nell'ordine dell'albero, esclusa la feature base."""
    base = body.BaseFeature
    return [
        obj
        for obj in body.Group
        if obj.isDerivedFrom("PartDesign::Feature") and obj is not base
    ]


def position(body):
    """Posizione di rollback attuale (0..N)."""
    features = solid_features(body)
    tip = body.Tip
    if tip is None or tip is body.BaseFeature:
        return 0
    for index, feature in enumerate(features):
        if feature is tip:
            return index + 1
    return len(features)


def feature_at(body, pos):
    """Feature che diventa il ``Tip`` alla posizione data (None per la posizione 0 senza base)."""
    features = solid_features(body)
    pos = max(0, min(pos, len(features)))
    return features[pos - 1] if pos > 0 else body.BaseFeature


def set_position(body, pos, recompute=True):
    """Porta il rollback alla posizione ``pos`` (limitata a 0..N). Restituisce la posizione."""
    features = solid_features(body)
    pos = max(0, min(int(pos), len(features)))
    if pos == position(body):
        return pos
    new_tip = feature_at(body, pos)
    doc = body.Document
    doc.openTransaction("Rollback")
    try:
        body.Tip = new_tip
        if new_tip is not None:
            new_tip.Visibility = True  # come PartDesign_MoveTip
        if recompute:
            doc.recompute()
    finally:
        doc.commitTransaction()
    return pos


def step(body, delta):
    return set_position(body, position(body) + delta)


def to_end(body):
    return set_position(body, len(solid_features(body)))


def is_rolled_back(body):
    return position(body) < len(solid_features(body))


def describe(body):
    """Testo breve per l'interfaccia: "3/5 – Pocket001"."""
    features = solid_features(body)
    pos = position(body)
    if pos == 0:
        name = "inizio"
    else:
        name = features[pos - 1].Label
    return f"{pos}/{len(features)} – {name}"


def active_body():
    """Corpo attivo nella vista (solo con GUI), altrimenti None."""
    if not FreeCAD.GuiUp:
        return None
    import FreeCADGui

    gdoc = FreeCADGui.ActiveDocument
    if gdoc is None:
        return None
    try:
        body = gdoc.ActiveView.getActiveObject("pdbody")
    except Exception:
        return None
    return body if is_body(body) else None
