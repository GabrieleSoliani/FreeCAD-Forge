# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test di Forge che richiedono la GUI (FreeCAD -t ForgeTests.TestForgeGui)."""

import unittest

import FreeCAD
import FreeCADGui
from PySide import QtWidgets

from forgelib.ui import catalog
from forgelib.ui.command_manager import TABBAR_OBJECT_NAME


class TestForgeWorkbench(unittest.TestCase):
    def setUp(self):
        self.previous = FreeCADGui.activeWorkbench().name()
        FreeCADGui.activateWorkbench("ForgeWorkbench")
        FreeCADGui.updateGui()
        self.mw = FreeCADGui.getMainWindow()

    def tearDown(self):
        FreeCADGui.activateWorkbench(self.previous)
        FreeCADGui.updateGui()

    def _tabbar(self):
        toolbar = self.mw.findChild(QtWidgets.QToolBar, TABBAR_OBJECT_NAME)
        self.assertIsNotNone(toolbar)
        return toolbar, toolbar.findChild(QtWidgets.QTabBar)

    def test_core_commands_resolved(self):
        """Le schede che dipendono solo da moduli obbligatori devono essere complete."""
        available = set(FreeCADGui.listCommands())
        for key in ("sketch", "features", "evaluate"):
            tab = catalog.tab_by_key(key)
            _, missing = catalog.resolve_commands(tab.commands, available)
            self.assertEqual(missing, [], f"scheda {key}")

    def test_optional_tabs_resolved_when_module_built(self):
        """Un nome di comando sbagliato nel catalogo deve far fallire il test."""
        import importlib.util

        requirements = {"surfaces": "SurfaceGui", "assembly": "AssemblyGui", "drawing": "TechDrawGui"}
        available = set(FreeCADGui.listCommands())
        for key, module in requirements.items():
            with self.subTest(tab=key):
                if importlib.util.find_spec(module) is None:
                    self.skipTest(f"{module} non compilato")
                _, missing = catalog.resolve_commands(catalog.tab_by_key(key).commands, available)
                self.assertEqual(missing, [])

    def test_toolbars_created(self):
        for tab in catalog.TABS:
            with self.subTest(tab=tab.key):
                self.assertIsNotNone(self.mw.findChild(QtWidgets.QToolBar, tab.toolbar_name))

    def test_tab_switch_shows_only_one_toolbar(self):
        toolbar, tabbar = self._tabbar()
        self.assertTrue(toolbar.isVisible())
        self.assertEqual(tabbar.count(), len(catalog.TABS))
        for index, tab in enumerate(catalog.TABS):
            tabbar.setCurrentIndex(index)
            FreeCADGui.updateGui()
            visible = [
                t.key
                for t in catalog.TABS
                if self.mw.findChild(QtWidgets.QToolBar, t.toolbar_name).isVisible()
            ]
            self.assertEqual(visible, [tab.key])

    def test_command_manager_hidden_in_other_workbench(self):
        toolbar, _ = self._tabbar()
        FreeCADGui.activateWorkbench("PartDesignWorkbench")
        FreeCADGui.updateGui()
        self.assertFalse(toolbar.isVisible())
        for tab in catalog.TABS:
            self.assertFalse(self.mw.findChild(QtWidgets.QToolBar, tab.toolbar_name).isVisible())

    def test_new_document_and_body_from_features_tab(self):
        """Il comando della scheda Feature funziona dentro Forge senza cambiare workbench."""
        doc = FreeCAD.newDocument("ForgeGuiTest")
        try:
            FreeCADGui.runCommand("PartDesign_Body")
            FreeCADGui.updateGui()
            bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
            self.assertEqual(len(bodies), 1)
            self.assertEqual(FreeCADGui.activeWorkbench().name(), "ForgeWorkbench")
        finally:
            FreeCAD.closeDocument(doc.Name)
