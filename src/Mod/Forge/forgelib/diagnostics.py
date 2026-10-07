# SPDX-License-Identifier: LGPL-2.1-or-later
"""Diagnostica delle feature PartDesign: messaggi comprensibili e suggerimenti (M3).

``diagnose(doc)`` esamina le feature di un documento e restituisce una lista di ``Diagnostic``:
- errori delle feature (stato non valido), con il messaggio grezzo tradotto in una spiegazione;
- fallimenti silenziosi: feature "valida" con solido non valido;
- feature che non hanno effetto (es. una tasca che non interseca il materiale);
- risultati divisi in più solidi.
Con ``suggest=True`` calcola anche suggerimenti numerici (raggio o spessore massimo applicabile),
provando l'operazione sulla forma di partenza con una bisezione. Nessuna dipendenza dalla GUI.
"""

import re
from dataclasses import dataclass, field

ERROR = "errore"
WARNING = "avviso"
INFO = "info"

SUBTRACTIVE_TYPES = (
    "PartDesign::Pocket",
    "PartDesign::Groove",
    "PartDesign::Hole",
    "PartDesign::SubtractiveLoft",
    "PartDesign::SubtractivePipe",
    "PartDesign::SubtractiveHelix",
)
ADDITIVE_TYPES = (
    "PartDesign::Pad",
    "PartDesign::Revolution",
    "PartDesign::AdditiveLoft",
    "PartDesign::AdditivePipe",
    "PartDesign::AdditiveHelix",
)


@dataclass
class Diagnostic:
    name: str  # nome interno dell'oggetto
    label: str  # etichetta mostrata all'utente
    severity: str  # ERROR, WARNING o INFO
    message: str  # spiegazione in italiano
    suggestion: str = ""  # cosa fare
    raw: str = ""  # messaggio originale di FreeCAD/OCC
    refs: list = field(default_factory=list)  # [(oggetto, sotto-elemento)] da evidenziare

    def text(self):
        out = f"{self.label}: {self.message}"
        if self.suggestion:
            out += f" Suggerimento: {self.suggestion}"
        return out


# (espressione sul messaggio grezzo, prefisso del TypeId o "", spiegazione, suggerimento)
RULES = (
    (r"radius is probably too large|BRep_API: command not done|Fillet operation failed",
     "PartDesign::Fillet",
     "Il raccordo non si può costruire con questo raggio: è troppo grande rispetto alle facce "
     "adiacenti agli spigoli scelti.",
     "Riduci il raggio oppure raccorda gli spigoli in più feature separate."),
    (r"size is probably too large|BRep_API: command not done|Failed to create chamfer",
     "PartDesign::Chamfer",
     "Lo smusso non si può costruire con questa dimensione: è troppo grande rispetto alle facce "
     "adiacenti.",
     "Riduci la dimensione dello smusso oppure smussa gli spigoli in più feature."),
    (r"wall is probably too thick|Failed to make thick solid",
     "PartDesign::Thickness",
     "Il guscio non si può costruire: la parete è troppo spessa per la parte.",
     "Riduci lo spessore della parete."),
    (r"Draft failed", "PartDesign::Draft",
     "Lo sformo non si può calcolare: l'angolo è troppo grande per le facce scelte oppure il "
     "piano neutro non è adatto.",
     "Riduci l'angolo o scegli come piano neutro una faccia perpendicolare alla direzione di "
     "estrazione."),
    (r"Wire is not closed", "",
     "Il profilo dello schizzo non è chiuso.",
     "Apri lo schizzo e usa \"Valida schizzo\" per trovare le estremità che non coincidono."),
    (r"Linked shape object is empty|No profile linked|shape is empty", "",
     "Lo schizzo usato come profilo è vuoto.",
     "Disegna il profilo nello schizzo oppure scegli un altro schizzo."),
    (r"Invalid (edge|face) link|Invalid face reference|Invalid edge reference", "",
     "La feature si riferisce a uno spigolo o a una faccia che non esiste più (la geometria a "
     "monte è cambiata).",
     "Modifica la feature e riseleziona gli spigoli o le facce."),
    (r"total length of zero|Length too small", "",
     "La lunghezza dell'estrusione è zero.",
     "Imposta una lunghezza maggiore di zero."),
    (r"Revolve axis intersects the sketch", "",
     "L'asse di rivoluzione attraversa il profilo: il solido si intersecherebbe con se stesso.",
     "Sposta il profilo tutto da un lato dell'asse o scegli un altro asse."),
    (r"multiple solids", "",
     "Il risultato è diviso in più solidi separati.",
     "Modifica la feature in modo che il corpo resti un solido unico, oppure attiva "
     "\"Allow Compound\" nelle proprietà del corpo."),
    (r"not a solid|Resulting shape is null|Result is not a solid", "",
     "L'operazione non ha prodotto un solido.",
     "Controlla il profilo e le dimensioni; usa Valuta → Verifica geometria sulla feature "
     "precedente."),
    (r"does not intersect|no intersection|did not intersect", "",
     "Il profilo non interseca il solido.",
     "Sposta il profilo o cambia direzione e lunghezza dell'estrusione."),
)


def explain(type_id, raw):
    """Spiegazione e suggerimento per un messaggio d'errore grezzo."""
    for pattern, type_prefix, message, suggestion in RULES:
        if type_prefix and not type_id.startswith(type_prefix):
            continue
        if re.search(pattern, raw or "", re.IGNORECASE):
            return message, suggestion
    if not (raw or "").strip():
        return ("La feature non si può calcolare (nessun dettaglio dal kernel geometrico).",
                "Prova a modificare le dimensioni o i riferimenti della feature.")
    return (f"La feature non si può calcolare: {raw}",
            "Usa Valuta → Verifica geometria sulla feature precedente per cercare difetti.")


def _base_feature(feature):
    base = getattr(feature, "BaseFeature", None)
    return base if base is not None and not base.Shape.isNull() else None


def _volume(shape):
    return 0.0 if shape is None or shape.isNull() else shape.Volume


def _dressup_refs(feature):
    base = getattr(feature, "Base", None)
    if not base or not isinstance(base, tuple) or base[0] is None:
        return None, []
    return base[0], list(base[1])


def max_feasible(trial, upper, iterations=14):
    """Massimo valore in (0, upper] per cui ``trial(v)`` riesce, per bisezione.

    ``trial`` restituisce True se l'operazione con il valore dato produce un solido valido.
    Restituisce None se nemmeno l'1% di ``upper`` funziona.
    """
    lo = upper * 0.01
    if not trial(lo):
        return None
    hi = upper
    if trial(hi):
        return hi
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if trial(mid):
            lo = mid
        else:
            hi = mid
    return lo


def _fillet_trial(shape, edges, kind):
    base_volume = shape.Volume

    def trial(value):
        try:
            if kind == "fillet":
                result = shape.makeFillet(value, edges)
            else:
                result = shape.makeChamfer(value, edges)
        except Exception:
            return False
        return (not result.isNull() and result.isValid() and len(result.Solids) == 1
                and 0 < result.Volume < base_volume * 1.5)

    return trial


def _thickness_trial(shape, faces):
    base_volume = shape.Volume

    def trial(value):
        try:
            result = shape.makeThickness(faces, -value, 1e-3)
        except Exception:
            return False
        return (not result.isNull() and result.isValid() and len(result.Solids) == 1
                and 0 < result.Volume < base_volume * (1 - 1e-9))

    return trial


def _round_down(value):
    """Arrotonda per difetto a un valore "da quota" (2 cifre significative circa)."""
    if value >= 10:
        step = 0.5
    elif value >= 1:
        step = 0.05
    else:
        step = 0.005
    rounded = int(value / step) * step
    return round(rounded if rounded > 0 else value, 3)


def numeric_suggestion(feature):
    """Suggerimento numerico per raccordi, smussi e gusci falliti, oppure ""."""
    base, subs = _dressup_refs(feature)
    if base is None or base.Shape.isNull() or not subs:
        return ""
    shape = base.Shape.copy()
    shape.Placement = FreeCAD_identity()
    try:
        elements = [shape.getElement(sub) for sub in subs]
    except Exception:
        return ""
    type_id = feature.TypeId
    if type_id == "PartDesign::Fillet":
        value = max_feasible(_fillet_trial(shape, elements, "fillet"), float(feature.Radius))
        what = "raggio"
    elif type_id == "PartDesign::Chamfer":
        value = max_feasible(_fillet_trial(shape, elements, "chamfer"), float(feature.Size))
        what = "dimensione"
    elif type_id == "PartDesign::Thickness":
        value = max_feasible(_thickness_trial(shape, elements), float(feature.Value))
        what = "spessore"
    else:
        return ""
    if value is None:
        return f"Nessun valore di {what} funziona con questi riferimenti: prova a cambiarli."
    return f"Il {what} massimo applicabile è circa {_round_down(value):g} mm."


def FreeCAD_identity():
    import FreeCAD

    return FreeCAD.Placement()


def _is_partdesign_feature(obj):
    return obj.isDerivedFrom("PartDesign::Feature") and not obj.isDerivedFrom(
        "PartDesign::FeatureBase"
    )


def diagnose_object(obj, suggest=False):
    """Diagnostica di una singola feature, oppure None se non c'è nulla da segnalare."""
    if not _is_partdesign_feature(obj):
        return None
    type_id = obj.TypeId
    refs = []
    base, subs = _dressup_refs(obj)
    if base is not None:
        refs = [(base.Name, sub) for sub in subs]

    if not obj.isValid():
        raw = obj.getStatusString()
        if raw == "Valid":
            raw = ""
        message, suggestion = explain(type_id, raw)
        if suggest:
            numeric = numeric_suggestion(obj)
            if numeric:
                suggestion = f"{numeric} {suggestion}"
        return Diagnostic(obj.Name, obj.Label, ERROR, message, suggestion, raw, refs)

    shape = obj.Shape
    if shape.isNull():
        return None
    if not shape.isValid():
        return Diagnostic(obj.Name, obj.Label, ERROR,
                          "La feature ha prodotto un solido non valido.",
                          "Le feature successive potrebbero fallire: modifica le dimensioni di "
                          "questa feature.", "", refs)

    base_feature = _base_feature(obj)
    if base_feature is not None and type_id.startswith(SUBTRACTIVE_TYPES + ADDITIVE_TYPES):
        before = _volume(base_feature.Shape)
        after = _volume(shape)
        if abs(after - before) <= 1e-9 * max(1.0, abs(before)):
            verb = "rimuove" if type_id in SUBTRACTIVE_TYPES else "aggiunge"
            return Diagnostic(obj.Name, obj.Label, WARNING,
                              f"La feature non {verb} materiale: il profilo non interseca il "
                              "solido.",
                              "Controlla posizione dello schizzo, direzione e lunghezza.", "", refs)

    if len(shape.Solids) > 1:
        return Diagnostic(obj.Name, obj.Label, INFO,
                          f"Il corpo è diviso in {len(shape.Solids)} solidi separati.",
                          "Se non è voluto, modifica la feature in modo che il corpo resti "
                          "unico.", "", refs)
    return None


def diagnose(doc, suggest=False):
    """Diagnostica di tutte le feature PartDesign del documento, nell'ordine del documento."""
    results = []
    for obj in doc.Objects:
        diagnostic = diagnose_object(obj, suggest=suggest)
        if diagnostic is not None:
            results.append(diagnostic)
    return results
