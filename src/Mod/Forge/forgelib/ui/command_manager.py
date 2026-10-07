# SPDX-License-Identifier: LGPL-2.1-or-later
"""Command manager a schede di Forge.

Una riga di linguette (QTabBar dentro una QToolBar propria) sopra le toolbar delle schede.
Le toolbar delle schede sono toolbar standard create dal workbench Forge: il command manager
si limita a mostrare quella della scheda scelta e a nascondere le altre.
"""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib.ui import catalog
from forgelib.ui.context import Context, TabFollower

PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/Forge"
TABBAR_OBJECT_NAME = "ForgeCommandManager"
POLL_INTERVAL_MS = 300


def _params():
    return FreeCAD.ParamGet(PARAM_PATH)


def current_context():
    """Legge dalla GUI lo stato che guida il cambio automatico di scheda."""
    drawing = False
    mdi = FreeCADGui.getMainWindow().findChild(QtWidgets.QMdiArea)
    if mdi is not None:
        sub = mdi.activeSubWindow()
        widget = sub.widget() if sub is not None else None
        if widget is not None:
            drawing = widget.metaObject().className() == "TechDrawGui::MDIViewPage"

    sketch = False
    assembly = False
    gdoc = FreeCADGui.ActiveDocument
    if gdoc is not None:
        vp = gdoc.getInEdit()
        if vp is not None and hasattr(vp, "Object"):
            sketch = vp.Object.isDerivedFrom("Sketcher::SketchObject")
        if not drawing:
            try:
                active = gdoc.ActiveView.getActiveObject("part")
            except Exception:
                active = None
            assembly = active is not None and active.isDerivedFrom("Assembly::AssemblyObject")

    return Context(drawing_page_active=drawing, sketch_in_edit=sketch, assembly_active=assembly)


class CommandManager(QtCore.QObject):
    """Barra a schede che alterna le toolbar "Forge <scheda>"."""

    def __init__(self, tabs):
        super().__init__(FreeCADGui.getMainWindow())
        self._tabs = list(tabs)
        self._follower = TabFollower()
        self._laid_out = False
        self._editing = False  # uno schizzo è in modifica

        mw = FreeCADGui.getMainWindow()
        self._toolbar = QtWidgets.QToolBar("Forge Command Manager", mw)
        self._toolbar.setObjectName(TABBAR_OBJECT_NAME)
        self._toolbar.setMovable(False)
        self._toolbar.toggleViewAction().setVisible(False)

        self._tabbar = QtWidgets.QTabBar(self._toolbar)
        self._tabbar.setDrawBase(False)
        self._tabbar.setExpanding(False)
        for tab in self._tabs:
            self._tabbar.addTab(tab.label)
        self._toolbar.addWidget(self._tabbar)
        self._tabbar.currentChanged.connect(self._apply)
        # si ricorda solo la scheda scelta a mano, non quelle imposte dal contesto
        self._tabbar.tabBarClicked.connect(self._remember)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._follow_context)

        mw.addToolBar(QtCore.Qt.TopToolBarArea, self._toolbar)
        self._toolbar.hide()

    # --- API ---------------------------------------------------------------------------

    def current_key(self):
        index = self._tabbar.currentIndex()
        return self._tabs[index].key if 0 <= index < len(self._tabs) else None

    def set_current(self, key):
        for index, tab in enumerate(self._tabs):
            if tab.key == key:
                if index == self._tabbar.currentIndex():
                    self._apply(index)
                else:
                    self._tabbar.setCurrentIndex(index)  # chiama _apply
                return True
        return False

    def activate(self):
        """Mostra il command manager (all'attivazione del workbench Forge)."""
        self._layout_once()
        self._toolbar.show()
        key = _params().GetString("LastTab", catalog.DEFAULT_TAB)
        if not self.set_current(key):
            self.set_current(catalog.DEFAULT_TAB)
        self._follow_context()
        self._timer.start()

    def deactivate(self):
        """Nasconde il command manager (alla disattivazione del workbench Forge)."""
        self._timer.stop()
        self._toolbar.hide()

    def toolbar(self, name):
        return FreeCADGui.getMainWindow().findChild(QtWidgets.QToolBar, name)

    def visible_toolbars(self, tab):
        """Nomi delle toolbar da mostrare per la scheda nello stato attuale."""
        if self._editing and tab.edit_groups:
            return tab.edit_toolbar_names()
        return [tab.toolbar_name]

    # --- interni -----------------------------------------------------------------------

    def _layout_once(self):
        """Mette le linguette su una riga propria e le toolbar delle schede sotto."""
        if self._laid_out:
            return
        mw = FreeCADGui.getMainWindow()
        area = QtCore.Qt.TopToolBarArea
        mw.addToolBarBreak(area)
        mw.addToolBar(area, self._toolbar)
        mw.addToolBarBreak(area)
        for tab in self._tabs:
            for name, _ in tab.all_toolbars():
                toolbar = self.toolbar(name)
                if toolbar is not None:
                    mw.addToolBar(area, toolbar)
        self._laid_out = True

    def _remember(self, index):
        if 0 <= index < len(self._tabs):
            _params().SetString("LastTab", self._tabs[index].key)

    def _apply(self, index):
        shown = set()
        if 0 <= index < len(self._tabs):
            shown = set(self.visible_toolbars(self._tabs[index]))
        for tab in self._tabs:
            for name, _ in tab.all_toolbars():
                toolbar = self.toolbar(name)
                if toolbar is not None:
                    toolbar.setVisible(name in shown)

    def _follow_context(self):
        try:
            context = current_context()
        except Exception as err:  # la GUI può essere in uno stato transitorio
            FreeCAD.Console.PrintLog(f"Forge: contesto non leggibile: {err}\n")
            return
        key = None
        if _params().GetBool("AutoSwitchTabs", True):
            key = self._follower.update(context, self.current_key())
        if context.sketch_in_edit != self._editing:
            self._editing = context.sketch_in_edit
            if key is None:
                self._apply(self._tabbar.currentIndex())
        if key is not None:
            self.set_current(key)
