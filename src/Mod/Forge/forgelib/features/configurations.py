# SPDX-License-Identifier: LGPL-2.1-or-later
"""Configurazioni con parametri e soppressione delle feature, come in SolidWorks (M4.1).

Un oggetto ``Configurazioni`` per documento contiene una tabella: righe = configurazioni,
colonne = parametri nella forma ``Oggetto.Proprietà`` (es. ``Pad.Length``,
``Pocket.Suppressed``). Attivare una configurazione scrive i valori nelle proprietà e
sopprime/riattiva le feature. La tabella si può importare da un foglio di calcolo (tabella dati:
prima colonna = nomi delle configurazioni, prima riga = parametri). Nessuna dipendenza dalla GUI.
Limite: un parametro legato a un'espressione non viene sovrascritto (si segnala l'errore).
"""

import json

import FreeCAD

DEFAULT_NAME = "Standard"


def _parse(value):
    """Valore memorizzato nella tabella → valore da assegnare alla proprietà."""
    if isinstance(value, (int, float)):  # bool compreso
        return value
    text = str(value).strip()
    if text.lower() in ("true", "vero", "sì", "si", "soppressa", "soppresso"):
        return True
    if text.lower() in ("false", "falso", "no", "attiva", "attivo"):
        return False
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return FreeCAD.Units.Quantity(text)
    except Exception:
        return text


def _store(value):
    """Valore di una proprietà → valore serializzabile in JSON."""
    if isinstance(value, (int, float, str)):  # bool compreso
        return value
    if hasattr(value, "UserString"):
        return value.UserString
    return str(value)


class Configurations:
    def __init__(self, obj):
        obj.Proxy = self
        obj.addProperty("App::PropertyEnumeration", "ActiveConfiguration", "Configurazioni",
                        "Configurazione attiva")
        obj.addProperty("App::PropertyString", "Table", "Configurazioni", "Tabella (JSON)")
        obj.setEditorMode("Table", 2)
        obj.Table = json.dumps({"configs": [DEFAULT_NAME], "params": [], "values": {DEFAULT_NAME: {}}})
        obj.ActiveConfiguration = [DEFAULT_NAME]
        self._applying = False

    # --- tabella --------------------------------------------------------------------------

    @staticmethod
    def data(obj):
        return json.loads(obj.Table)

    def save(self, obj, data):
        obj.Table = json.dumps(data)
        active = obj.ActiveConfiguration
        self._applying = True
        try:
            obj.ActiveConfiguration = data["configs"]
            if active in data["configs"]:
                obj.ActiveConfiguration = active
        finally:
            self._applying = False

    # --- applicazione ----------------------------------------------------------------------

    def onChanged(self, obj, prop):
        if prop != "ActiveConfiguration" or getattr(self, "_applying", False):
            return
        if "Restore" in obj.State:  # durante il caricamento i valori sono già quelli salvati
            return
        apply_configuration(obj, obj.ActiveConfiguration)

    def execute(self, obj):
        pass

    def onDocumentRestored(self, obj):
        obj.Proxy = self
        self._applying = False

    def dumps(self):
        return None

    def loads(self, state):
        return None


def _split(param):
    if "." not in param:
        raise ValueError(f"Parametro non valido (atteso Oggetto.Proprietà): {param}")
    name, prop = param.split(".", 1)
    return name, prop


def _resolve(doc, name):
    obj = doc.getObject(name)
    if obj is None:
        matches = doc.getObjectsByLabel(name)
        obj = matches[0] if matches else None
    if obj is None:
        raise ValueError(f"Oggetto non trovato: {name}")
    return obj


def apply_configuration(cfg, name, recompute=False):
    """Applica la configurazione ``name``. Restituisce l'elenco degli errori (stringhe)."""
    data = Configurations.data(cfg)
    if name not in data["configs"]:
        raise ValueError(f"Configurazione sconosciuta: {name}")
    doc = cfg.Document
    errors = []
    values = data["values"].get(name, {})
    for param in data["params"]:
        if param not in values:
            continue
        try:
            obj_name, prop = _split(param)
            obj = _resolve(doc, obj_name)
            if any(path == prop for path, _ in obj.ExpressionEngine):
                raise ValueError(f"{param} è legato a un'espressione")
            setattr(obj, prop, _parse(values[param]))
        except Exception as err:
            errors.append(f"{param}: {err}")
    if cfg.ActiveConfiguration != name:
        proxy = cfg.Proxy
        proxy._applying = True
        try:
            cfg.ActiveConfiguration = name
        finally:
            proxy._applying = False
    if recompute:
        doc.recompute()
    return errors


def make_configurations(doc, name="Configurazioni"):
    existing = [o for o in doc.Objects if isinstance(getattr(o, "Proxy", None), Configurations)]
    if existing:
        return existing[0]
    obj = doc.addObject("App::FeaturePython", name)
    Configurations(obj)
    if FreeCAD.GuiUp:
        obj.ViewObject.Proxy = 0
    return obj


def add_parameter(cfg, param):
    """Aggiunge un parametro e ne cattura il valore attuale in tutte le configurazioni."""
    obj_name, prop = _split(param)
    obj = _resolve(cfg.Document, obj_name)
    if prop not in obj.PropertiesList:
        raise ValueError(f"{obj_name} non ha la proprietà {prop}")
    data = Configurations.data(cfg)
    if param not in data["params"]:
        data["params"].append(param)
        current = _store(getattr(obj, prop))
        for config in data["configs"]:
            data["values"].setdefault(config, {})[param] = current
    cfg.Proxy.save(cfg, data)


def add_configuration(cfg, name, copy_from=None):
    data = Configurations.data(cfg)
    if name in data["configs"]:
        raise ValueError(f"La configurazione {name} esiste già")
    source = copy_from or cfg.ActiveConfiguration
    data["configs"].append(name)
    data["values"][name] = dict(data["values"].get(source, {}))
    cfg.Proxy.save(cfg, data)


def set_value(cfg, config, param, value):
    data = Configurations.data(cfg)
    if config not in data["configs"]:
        raise ValueError(f"Configurazione sconosciuta: {config}")
    if param not in data["params"]:
        raise ValueError(f"Parametro non presente nella tabella: {param}")
    data["values"][config][param] = _store(value)
    cfg.Proxy.save(cfg, data)


def capture(cfg, config=None):
    """Salva nella configurazione i valori attuali di tutti i parametri."""
    config = config or cfg.ActiveConfiguration
    data = Configurations.data(cfg)
    for param in data["params"]:
        obj_name, prop = _split(param)
        data["values"][config][param] = _store(getattr(_resolve(cfg.Document, obj_name), prop))
    cfg.Proxy.save(cfg, data)


def import_design_table(cfg, sheet):
    """Importa una tabella dati da un foglio di calcolo (A1 vuota, riga 1 parametri, colonna A configurazioni)."""
    import re

    cells = [c for c in sheet.getUsedCells()]
    if not cells:
        raise ValueError("Il foglio è vuoto")
    def split(cell):
        m = re.fullmatch(r"([A-Z]+)(\d+)", cell)
        return m.group(1), int(m.group(2))
    columns = sorted({split(c)[0] for c in cells}, key=lambda c: (len(c), c))
    rows = sorted({split(c)[1] for c in cells})
    params = [str(sheet.get(f"{col}1")) for col in columns[1:] if f"{col}1" in cells]
    data = Configurations.data(cfg)
    for param in params:
        _split(param)
        if param not in data["params"]:
            data["params"].append(param)
    for row in rows[1:]:
        if f"A{row}" not in cells:
            continue
        name = str(sheet.get(f"A{row}"))
        if name not in data["configs"]:
            data["configs"].append(name)
            data["values"][name] = {}
        for col, param in zip(columns[1:], params):
            cell = f"{col}{row}"
            if cell in cells:
                data["values"][name][param] = _store(sheet.get(cell))
    cfg.Proxy.save(cfg, data)
    return data
