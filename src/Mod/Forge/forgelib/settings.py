# SPDX-License-Identifier: LGPL-2.1-or-later
"""Impostazioni "stile SolidWorks" di Forge, con backup e ripristino.

FreeCAD non offre un'API Python per applicare i preference pack e non cerca i pack nei moduli
di sistema, quindi Forge applica direttamente i parametri. Prima di cambiare qualcosa salva lo
stato precedente (parametri e scorciatoie) in ``Mod/Forge/SettingsBackup`` come JSON, così
``revert`` riporta tutto esattamente com'era.

Le funzioni pure (pianificazione e serializzazione) sono separate dall'accesso a FreeCAD per
poterle testare senza GUI.
"""

import json

FORGE_PARAMS = "User parameter:BaseApp/Preferences/Mod/Forge"
SHORTCUT_PARAMS = "User parameter:BaseApp/Preferences/Shortcut"
BACKUP_KEY = "SettingsBackup"

# (gruppo, tipo, nome, valore). Tipi: "String", "Bool", "Int".
PARAMETERS = (
    ("User parameter:BaseApp/Preferences/View", "String", "NavigationStyle",
     "Gui::SolidWorksNavigationStyle"),
    ("User parameter:BaseApp/Preferences/View", "Bool", "ZoomAtCursor", True),
    ("User parameter:BaseApp/Preferences/General", "String", "AutoloadModule", "ForgeWorkbench"),
)

# Scorciatoie predefinite di SolidWorks riprodotte con i comandi equivalenti di FreeCAD.
SHORTCUTS = {
    "Std_ViewFitAll": "F",
    "Std_ViewFront": "Ctrl+1",
    "Std_ViewRear": "Ctrl+2",
    "Std_ViewLeft": "Ctrl+3",
    "Std_ViewRight": "Ctrl+4",
    "Std_ViewTop": "Ctrl+5",
    "Std_ViewBottom": "Ctrl+6",
    "Std_ViewIsometric": "Ctrl+7",
    "Std_AlignToSelection": "Ctrl+8",  # "Normale a"
    "Std_Refresh": "Ctrl+B",  # "Ricostruisci"
}


def _norm(key):
    return key.replace(" ", "").lower()


def plan_shortcuts(current, wanted):
    """Calcola le scorciatoie da impostare.

    ``current``: {comando: scorciatoia attuale} di tutti i comandi registrati.
    ``wanted``: {comando: scorciatoia desiderata}; i comandi assenti in ``current`` sono ignorati.
    Restituisce {comando: nuova scorciatoia}: le scorciatoie desiderate più la rimozione ("")
    delle stesse scorciatoie da altri comandi, per evitare conflitti.
    """
    changes = {}
    taken = {_norm(k): cmd for cmd, k in wanted.items() if cmd in current}
    for cmd, key in wanted.items():
        if cmd in current and _norm(current[cmd]) != _norm(key):
            changes[cmd] = key
    for cmd, key in current.items():
        if cmd in wanted or not key:
            continue
        if _norm(key) in taken:
            changes[cmd] = ""
    return changes


def encode_backup(params, shortcuts):
    """Serializza il backup.

    ``params``: lista di (gruppo, tipo, nome, valore precedente o None se assente).
    ``shortcuts``: {comando: valore personalizzato precedente o None se era quello predefinito}.
    """
    return json.dumps({"params": [list(p) for p in params], "shortcuts": shortcuts})


def decode_backup(text):
    data = json.loads(text)
    return [tuple(p) for p in data["params"]], dict(data["shortcuts"])


# --- accesso a FreeCAD ---------------------------------------------------------------------


def _get(group, kind, name):
    """Valore del parametro, oppure None se non è impostato."""
    import FreeCAD

    content_kind = {"String": "String", "Bool": "Boolean", "Int": "Integer"}[kind]
    for entry_kind, entry_name, value in FreeCAD.ParamGet(group).GetContents() or []:
        if entry_name == name and entry_kind == content_kind:
            return value
    return None


def _set(group, kind, name, value):
    import FreeCAD

    grp = FreeCAD.ParamGet(group)
    if value is None:
        getattr(grp, "Rem" + kind)(name)
    else:
        getattr(grp, "Set" + kind)(name, value)


def is_applied():
    import FreeCAD

    return bool(FreeCAD.ParamGet(FORGE_PARAMS).GetString(BACKUP_KEY, ""))


def apply():
    """Applica le impostazioni. Restituisce False se erano già applicate."""
    import FreeCAD
    import FreeCADGui

    if is_applied():
        return False

    param_backup = [(g, k, n, _get(g, k, n)) for g, k, n, _ in PARAMETERS]

    current = {}
    for name in FreeCADGui.Command.listAll():
        cmd = FreeCADGui.Command.get(name)
        if cmd is not None:
            current[name] = cmd.getShortcut()
    changes = plan_shortcuts(current, SHORTCUTS)
    shortcut_backup = {cmd: _get(SHORTCUT_PARAMS, "String", cmd) for cmd in changes}

    # il backup si scrive prima di toccare qualunque cosa
    FreeCAD.ParamGet(FORGE_PARAMS).SetString(
        BACKUP_KEY, encode_backup(param_backup, shortcut_backup)
    )
    for group, kind, name, value in PARAMETERS:
        _set(group, kind, name, value)
    for cmd, key in changes.items():
        FreeCADGui.Command.get(cmd).setShortcut(key)
    return True


def revert():
    """Ripristina lo stato precedente ad ``apply``. Restituisce False se non c'era nulla."""
    import FreeCAD
    import FreeCADGui

    grp = FreeCAD.ParamGet(FORGE_PARAMS)
    text = grp.GetString(BACKUP_KEY, "")
    if not text:
        return False
    params, shortcuts = decode_backup(text)
    for group, kind, name, value in params:
        _set(group, kind, name, value)
    for name, value in shortcuts.items():
        cmd = FreeCADGui.Command.get(name)
        if cmd is None:
            continue
        if value is None:
            cmd.resetShortcut()
        else:
            cmd.setShortcut(value)
    grp.RemString(BACKUP_KEY)
    return True
