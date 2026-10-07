# SPDX-License-Identifier: LGPL-2.1-or-later
"""Scelta automatica della scheda in base al contesto di lavoro.

La decisione è separata dalla raccolta dello stato (che richiede la GUI) per poterla testare
senza interfaccia: ``choose_tab`` riceve un ``Context`` e restituisce la chiave della scheda,
oppure None se il contesto non impone una scheda.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Context:
    """Stato dell'interfaccia rilevante per il cambio di scheda."""

    drawing_page_active: bool = False  # la vista attiva è una pagina TechDraw
    sketch_in_edit: bool = False  # uno schizzo è in modifica
    assembly_active: bool = False  # un assieme è l'oggetto attivo del documento


def choose_tab(context):
    """Restituisce la chiave della scheda adatta al contesto, oppure None."""
    if context.drawing_page_active:
        return "drawing"
    if context.sketch_in_edit:
        return "sketch"
    if context.assembly_active:
        return "assembly"
    return None


class TabFollower:
    """Decide quando cambiare scheda, come fa SolidWorks.

    - La scheda cambia solo quando cambia il contesto, quindi una scheda scelta a mano resta
      attiva finché il contesto non cambia.
    - Quando si esce da un contesto (per esempio si chiude lo schizzo) si torna alla scheda
      che l'utente aveva prima di entrarci.
    """

    def __init__(self):
        self._context_tab = None
        self._restore = None

    def update(self, context, current):
        """Restituisce la chiave della scheda da attivare, oppure None per non fare nulla.

        ``current`` è la chiave della scheda attualmente visibile.
        """
        wanted = choose_tab(context)
        if wanted == self._context_tab:
            return None
        entering_from_free = self._context_tab is None
        self._context_tab = wanted
        if wanted is None:
            restore, self._restore = self._restore, None
            return restore if restore != current else None
        if entering_from_free:
            self._restore = current
        return wanted if wanted != current else None
