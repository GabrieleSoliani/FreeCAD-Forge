# SPDX-License-Identifier: LGPL-2.1-or-later
"""Menu radiale contestuale (tasto S), ispirato alla "shortcut bar" di SolidWorks.

I comandi mostrati dipendono dal contesto (schizzo in modifica, tavola, assieme, parte).
La parte dati e la geometria dell'anello sono funzioni pure, testabili senza GUI.
"""

import math

from forgelib.ui.context import choose_tab

# Comandi per contesto, in senso orario a partire dall'alto.
RADIAL_ITEMS = {
    "sketch": (
        "Sketcher_CompDimensionTools",
        "Sketcher_CompLine",
        "Sketcher_CompCreateRectangles",
        "Sketcher_CompCreateArc",
        "Sketcher_CompCurveEdition",
        "Sketcher_ToggleConstruction",
        "Sketcher_ConstrainCoincidentUnified",
        "Sketcher_LeaveSketch",
    ),
    "part": (
        "PartDesign_NewSketch",
        "PartDesign_Pad",
        "PartDesign_Pocket",
        "PartDesign_Hole",
        "PartDesign_Fillet",
        "PartDesign_Chamfer",
        "Std_Measure",
        "Std_AlignToSelection",
    ),
    "assembly": (
        "Assembly_Insert",
        "Assembly_CreateJointFixed",
        "Assembly_CreateJointRevolute",
        "Assembly_CreateJointSlider",
        "Assembly_CreateJointDistance",
        "Assembly_ToggleGrounded",
        "Std_Measure",
        "Assembly_SolveAssembly",
    ),
    "drawing": (
        "TechDraw_View",
        "TechDraw_Dimension",
        "TechDraw_Balloon",
        "TechDraw_SectionGroup",
        "TechDraw_DetailView",
        "TechDraw_CenterLineGroup",
        "TechDraw_LeaderLine",
        "TechDraw_RichTextAnnotation",
    ),
}


def radial_context(context):
    """Chiave di RADIAL_ITEMS per il contesto dato."""
    tab = choose_tab(context)
    return tab if tab in RADIAL_ITEMS else "part"


def ring_positions(count, radius):
    """Centri (x, y) dei pulsanti su un anello, il primo in alto, poi in senso orario.

    Coordinate relative al centro, con y verso il basso (convenzione Qt).
    """
    positions = []
    for i in range(count):
        angle = -math.pi / 2 + 2 * math.pi * i / count
        positions.append((round(radius * math.cos(angle)), round(radius * math.sin(angle))))
    return positions


def available_items(key, available):
    return [name for name in RADIAL_ITEMS[key] if name in available]


RADIUS = 78
BUTTON = 40


def _make_widget_class():
    """Classe del widget creata solo con la GUI (PySide non è disponibile in FreeCADCmd)."""
    import FreeCADGui
    from PySide import QtCore, QtGui, QtWidgets

    from forgelib.ui.headsup import _icon

    class RadialMenu(QtWidgets.QWidget):
        """Popup circolare: ogni pulsante esegue un comando FreeCAD e chiude il menu."""

        def __init__(self, commands, parent=None):
            super().__init__(parent, QtCore.Qt.Popup | QtCore.Qt.FramelessWindowHint)
            self.setObjectName("ForgeRadialMenu")
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            side = 2 * (RADIUS + BUTTON)
            self.setFixedSize(side, side)
            self.commands = list(commands)
            center = side // 2
            for name, (dx, dy) in zip(self.commands, ring_positions(len(self.commands), RADIUS)):
                cmd = FreeCADGui.Command.get(name)
                info = cmd.getInfo() if cmd is not None else {}
                button = QtWidgets.QToolButton(self)
                button.setObjectName(name)
                button.setIcon(_icon(info.get("pixmap") or name))
                button.setIconSize(QtCore.QSize(26, 26))
                button.setToolTip(info.get("menuText", name).replace("&", ""))
                button.setFixedSize(BUTTON, BUTTON)
                button.move(center + dx - BUTTON // 2, center + dy - BUTTON // 2)
                button.setEnabled(FreeCADGui.isCommandActive(name))
                button.clicked.connect(lambda checked=False, n=name: self._run(n))

        def _run(self, name):
            self.close()
            QtCore.QTimer.singleShot(0, lambda: FreeCADGui.runCommand(name))

        def paintEvent(self, event):
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            center = QtCore.QPointF(self.width() / 2, self.height() / 2)
            outer = RADIUS + BUTTON / 2 + 6
            inner = RADIUS - BUTTON / 2 - 6
            path = QtGui.QPainterPath()
            path.addEllipse(center, outer, outer)
            path.addEllipse(center, inner, inner)
            painter.fillPath(path, QtGui.QColor(245, 245, 245, 215))
            painter.setPen(QtGui.QPen(QtGui.QColor(110, 110, 110, 160), 1))
            painter.drawPath(path)

        def keyPressEvent(self, event):
            if event.key() in (QtCore.Qt.Key_Escape, QtCore.Qt.Key_S):
                self.close()
            else:
                super().keyPressEvent(event)

    return RadialMenu


_widget_class = None


def show_radial_menu():
    """Apre il menu radiale centrato sul cursore. Restituisce il widget (per i test)."""
    import FreeCADGui
    from PySide import QtGui

    from forgelib.ui.command_manager import current_context

    global _widget_class
    if _widget_class is None:
        _widget_class = _make_widget_class()
    key = radial_context(current_context())
    commands = available_items(key, set(FreeCADGui.listCommands()))
    menu = _widget_class(commands, FreeCADGui.getMainWindow())
    pos = QtGui.QCursor.pos()
    menu.move(pos.x() - menu.width() // 2, pos.y() - menu.height() // 2)
    menu.show()
    return menu
