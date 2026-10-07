# SPDX-License-Identifier: LGPL-2.1-or-later
"""Produttività (M8): Pack and Go e libreria personale di componenti.

Pack and Go: copia il documento e i documenti collegati che si trovano nella sua cartella (o in
sottocartelle) in una nuova cartella, mantenendo la struttura relativa: i collegamenti
(``App::Link`` verso altri file) restano validi perché FreeCAD li memorizza con percorso relativo.
Le dipendenze fuori dalla cartella del documento vengono elencate e non copiate (limite).

Libreria personale: componenti salvati come file .FCStd in ``<dati utente>/Forge/Libreria`` e
inseriti come link. Nessuna dipendenza dalla GUI.
"""

import os
import shutil
from dataclasses import dataclass, field

import FreeCAD


@dataclass
class PackResult:
    copied: list = field(default_factory=list)  # percorsi dei file creati
    external: list = field(default_factory=list)  # dipendenze non copiate (fuori cartella)


def dependencies(doc):
    """Documenti da cui ``doc`` dipende (escluso ``doc``)."""
    deps = []
    for other in doc.getDependentDocuments():
        if other is not doc and other.FileName:
            deps.append(other)
    return deps


def pack_and_go(doc, target_dir, save_first=True):
    if not doc.FileName:
        raise ValueError("Salvare il documento prima di usare Pack and Go")
    if save_first:
        for other in [doc] + dependencies(doc):
            if other.isTouched() or other.FileName == "":
                other.save()
    root = os.path.dirname(os.path.abspath(doc.FileName))
    os.makedirs(target_dir, exist_ok=True)
    result = PackResult()
    for other in [doc] + dependencies(doc):
        source = os.path.abspath(other.FileName)
        rel = os.path.relpath(source, root)
        if rel.startswith(".."):
            result.external.append(source)
            continue
        destination = os.path.join(target_dir, rel)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(source, destination)
        result.copied.append(destination)
    return result


# --- libreria personale ------------------------------------------------------------------------


def library_dir():
    path = os.path.join(FreeCAD.getUserAppDataDir(), "Forge", "Libreria")
    os.makedirs(path, exist_ok=True)
    return path


def add_to_library(obj, name=None, directory=None):
    """Salva una copia dell'oggetto (con le dipendenze) come componente di libreria."""
    directory = directory or library_dir()
    name = name or obj.Label
    safe = "".join(c for c in name if c.isalnum() or c in " -_").strip() or "componente"
    path = os.path.join(directory, safe + ".FCStd")
    target = FreeCAD.newDocument("ForgeLibreria", hidden=True)
    try:
        target.copyObject(obj, True)
        target.recompute()
        target.saveAs(path)
    finally:
        FreeCAD.closeDocument(target.Name)
    return path


def list_library(directory=None):
    directory = directory or library_dir()
    return sorted(os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith(".fcstd"))


def _root_component(doc):
    # oggetti non usati da altri oggetti dello stesso documento (RootObjects esclude anche quelli
    # collegati da altri documenti, ad esempio da un inserimento precedente)
    roots = [o for o in doc.Objects if not any(p.Document is doc for p in o.InList)]
    for obj in roots:
        if hasattr(obj, "Shape") and not obj.Shape.isNull() and obj.Shape.Solids:
            return obj
    raise ValueError(f"{doc.FileName}: nessun solido da inserire")


def insert_from_library(doc, path, placement=None):
    """Inserisce un componente di libreria.

    Se il documento è già salvato il componente è un link al file di libreria (condiviso:
    modifiche alla libreria si propagano); altrimenti FreeCAD non permette link esterni e il
    componente viene copiato nel documento.
    """
    source = None
    for open_doc in FreeCAD.listDocuments().values():
        if os.path.abspath(open_doc.FileName or "") == os.path.abspath(path):
            source = open_doc
    if source is None:
        source = FreeCAD.openDocument(path, hidden=True)
    component = _root_component(source)
    label = os.path.splitext(os.path.basename(path))[0]
    if not doc.FileName:
        link = doc.copyObject(component, True)
        link.Label = label
        if placement is not None:
            link.Placement = placement
        doc.recompute()
        return link
    link = doc.addObject("App::Link", "Libreria")
    link.LinkedObject = component
    link.Label = label
    if placement is not None:
        link.Placement = placement
    doc.recompute()
    return link
