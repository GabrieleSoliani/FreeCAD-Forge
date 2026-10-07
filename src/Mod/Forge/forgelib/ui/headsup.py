# SPDX-License-Identifier: LGPL-2.1-or-later
"""Barra "heads-up" in sovrimpressione sulla vista 3D, come in SolidWorks.

La barra è una QToolBar figlia della QMdiArea (che vive quanto la finestra principale) e non
delle singole viste: creare wrapper PySide dei widget delle viste provoca un abort all'uscita
(vedi ``command_manager.current_context``). I pulsanti eseguono comandi FreeCAD esistenti.
"""

from dataclasses import dataclass

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtGui, QtWidgets

HEADSUP_OBJECT_NAME = "ForgeHeadsUp"
TOP_MARGIN = 6


@dataclass(frozen=True)
class Item:
    """Voce di un menu della barra: testo, comando FreeCAD e indice (per i comandi di gruppo)."""

    text: str
    command: str
    index: int = 0


@dataclass(frozen=True)
class Button:
    """Pulsante della barra. Senza ``items`` esegue ``command``; con ``items`` apre un menu."""

    tooltip: str
    icon: str  # nome di un'icona di FreeCAD (FreeCADGui.getIcon) o di un comando
    command: str = ""
    items: tuple = ()


SEPARATOR = None

BUTTONS = (
    Button("Adatta alla finestra (F)", "Std_ViewFitAll", command="Std_ViewFitAll"),
    Button("Zoom finestra", "Std_ViewBoxZoom", command="Std_ViewBoxZoom"),
    SEPARATOR,
    Button(
        "Orientamento della vista",
        "Std_ViewIsometric",
        items=(
            Item("Frontale (Ctrl+1)", "Std_ViewFront"),
            Item("Posteriore (Ctrl+2)", "Std_ViewRear"),
            Item("Sinistra (Ctrl+3)", "Std_ViewLeft"),
            Item("Destra (Ctrl+4)", "Std_ViewRight"),
            Item("Superiore (Ctrl+5)", "Std_ViewTop"),
            Item("Inferiore (Ctrl+6)", "Std_ViewBottom"),
            Item("Isometrica (Ctrl+7)", "Std_ViewIsometric"),
            Item("Dimetrica", "Std_ViewDimetric"),
            Item("Trimetrica", "Std_ViewTrimetric"),
            Item("Normale a (Ctrl+8)", "Std_AlignToSelection"),
        ),
    ),
    Button(
        "Stile di visualizzazione",
        "DrawStyleFlatLines",
        items=(
            Item("Ombreggiato con spigoli", "Std_DrawStyle", 6),
            Item("Ombreggiato", "Std_DrawStyle", 5),
            Item("Linee nascoste rimosse", "Std_DrawStyle", 3),
            Item("Wireframe", "Std_DrawStyle", 2),
            Item("Come impostato nell'oggetto", "Std_DrawStyle", 0),
        ),
    ),
    SEPARATOR,
    Button("Vista in sezione", "Part_SectionCut", command="Part_SectionCut"),
    Button("Nascondi/mostra la selezione (Spazio)", "Std_ToggleVisibility",
           command="Std_ToggleVisibility"),
    Button(
        "Proiezione",
        "Std_OrthographicCamera",
        items=(
            Item("Ortogonale", "Std_OrthographicCamera"),
            Item("Prospettica", "Std_PerspectiveCamera"),
        ),
    ),
)


def referenced_commands():
    """Tutti i comandi usati dalla barra (per i test)."""
    names = []
    for button in BUTTONS:
        if button is SEPARATOR:
            continue
        if button.command:
            names.append(button.command)
        names.extend(item.command for item in button.items)
    return names


def _icon(name):
    icon = None
    try:
        icon = FreeCADGui.getIcon(name)
    except Exception:
        icon = None
    if icon is None:
        cmd = FreeCADGui.Command.get(name)
        pixmap = cmd.getInfo().get("pixmap") if cmd is not None else ""
        if pixmap:
            try:
                icon = FreeCADGui.getIcon(pixmap)
            except Exception:
                icon = None
    return icon if icon is not None else QtGui.QIcon()


def _run(command, index=0):
    if command in FreeCADGui.listCommands() and FreeCADGui.isCommandActive(command):
        FreeCADGui.runCommand(command, index)


class HeadsUpBar(QtCore.QObject):
    """Gestisce la barra: creazione, posizione e visibilità."""

    def __init__(self):
        mw = FreeCADGui.getMainWindow()
        super().__init__(mw)
        self._mdi = mw.findChild(QtWidgets.QMdiArea)
        self._wanted = False
        self._closed = False
        self._bar = QtWidgets.QToolBar(self._mdi)
        self._bar.setObjectName(HEADSUP_OBJECT_NAME)
        self._bar.setIconSize(QtCore.QSize(20, 20))
        self._bar.setMovable(False)
        self._bar.setFloatable(False)
        self._bar.setStyleSheet(
            "QToolBar#%s { background: rgba(240, 240, 240, 200); border: 1px solid "
            "rgba(120, 120, 120, 120); border-radius: 4px; padding: 1px; }" % HEADSUP_OBJECT_NAME
        )
        available = set(FreeCADGui.listCommands())
        for button in BUTTONS:
            if button is SEPARATOR:
                self._bar.addSeparator()
                continue
            self._add_button(button, available)
        self._bar.adjustSize()
        self._bar.hide()
        self._mdi.installEventFilter(self)

    def _add_button(self, button, available):
        if button.items:
            items = [item for item in button.items if item.command in available]
            if not items:
                return
            tool = QtWidgets.QToolButton(self._bar)
            tool.setIcon(_icon(button.icon))
            tool.setToolTip(button.tooltip)
            tool.setPopupMode(QtWidgets.QToolButton.InstantPopup)
            menu = QtWidgets.QMenu(tool)
            for item in items:
                action = menu.addAction(item.text)
                action.triggered.connect(
                    lambda checked=False, c=item.command, i=item.index: _run(c, i)
                )
            tool.setMenu(menu)
            self._bar.addWidget(tool)
        elif button.command in available:
            action = self._bar.addAction(_icon(button.icon), button.tooltip)
            action.triggered.connect(lambda checked=False, c=button.command: _run(c))

    # --- API ---------------------------------------------------------------------------

    def set_wanted(self, wanted):
        """Mostra la barra se ``wanted`` (Forge attivo e vista 3D attiva), altrimenti la nasconde."""
        wanted = bool(wanted) and not self._closed
        if FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Forge").GetBool(
            "ShowHeadsUp", True
        ) is False:
            wanted = False
        if wanted == self._wanted and self._bar.isVisible() == wanted:
            return
        self._wanted = wanted
        if wanted:
            self._place()
            self._bar.show()
            self._bar.raise_()
        else:
            self._bar.hide()

    def is_shown(self):
        return self._bar.isVisible()

    def bar(self):
        return self._bar

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self._mdi.removeEventFilter(self)
        self._bar.hide()

    # --- interni -----------------------------------------------------------------------

    def _place(self):
        self._bar.adjustSize()
        width = self._bar.sizeHint().width()
        x = max(0, (self._mdi.width() - width) // 2)
        self._bar.move(x, TOP_MARGIN)

    def eventFilter(self, obj, event):
        if not self._closed and event.type() == QtCore.QEvent.Resize and self._wanted:
            self._place()
            self._bar.raise_()
        return False
