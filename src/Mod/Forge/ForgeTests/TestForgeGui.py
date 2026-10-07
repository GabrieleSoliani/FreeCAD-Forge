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
        # niente timer durante i test: il contesto si aggiorna solo con _follow_context() esplicito
        FreeCADGui.getWorkbench("ForgeWorkbench")._manager._timer.stop()

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
            for name, commands in catalog.tab_by_key(key).all_toolbars():
                _, missing = catalog.resolve_commands(commands, available)
                self.assertEqual(missing, [], name)

    def test_optional_tabs_resolved_when_module_built(self):
        """Un nome di comando sbagliato nel catalogo deve far fallire il test."""
        import importlib.util

        requirements = {
            "surfaces": "SurfaceGui",
            "assembly": "AssemblyGui",
            "drawing": "TechDrawGui",
            "sheetmetal": "SheetMetalCmd",
        }
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

    def _visible_forge_toolbars(self):
        return [
            name
            for tab in catalog.TABS
            for name, _ in tab.all_toolbars()
            if self.mw.findChild(QtWidgets.QToolBar, name).isVisible()
        ]

    def _make_sketch(self, doc):
        body = doc.addObject("PartDesign::Body", "Body")
        sketch = body.newObject("Sketcher::SketchObject", "Sketch")
        doc.recompute()
        return sketch

    def test_sketch_edit_stays_in_forge(self):
        """Modificare uno schizzo da Forge non cambia workbench e mostra le toolbar di modifica."""
        manager = FreeCADGui.getWorkbench("ForgeWorkbench")._manager
        doc = FreeCAD.newDocument("ForgeSketchEdit")
        try:
            sketch = self._make_sketch(doc)
            manager.set_current("evaluate")
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
            FreeCADGui.updateGui()
            manager._follow_context()
            self.assertEqual(FreeCADGui.activeWorkbench().name(), "ForgeWorkbench")
            self.assertEqual(manager.current_key(), "sketch")
            self.assertEqual(
                sorted(self._visible_forge_toolbars()),
                sorted(catalog.tab_by_key("sketch").edit_toolbar_names()),
            )
            FreeCADGui.ActiveDocument.resetEdit()
            FreeCADGui.updateGui()
            manager._follow_context()
            self.assertEqual(FreeCADGui.activeWorkbench().name(), "ForgeWorkbench")
            self.assertEqual(manager.current_key(), "evaluate")
            self.assertEqual(self._visible_forge_toolbars(), ["Forge Valuta"])
        finally:
            FreeCAD.closeDocument(doc.Name)

    def test_drawing_page_switches_to_drawing_tab(self):
        if "TechDraw_PageDefault" not in FreeCADGui.listCommands():
            self.skipTest("TechDraw non compilato")
        manager = FreeCADGui.getWorkbench("ForgeWorkbench")._manager
        doc = FreeCAD.newDocument("ForgeDrawingTab")
        try:
            manager.set_current("features")
            manager._follow_context()
            FreeCADGui.runCommand("TechDraw_PageDefault")
            FreeCADGui.updateGui()
            manager._follow_context()
            self.assertEqual(manager.current_key(), "drawing")
            self.assertEqual(self._visible_forge_toolbars(), ["Forge Tavola"])
        finally:
            FreeCAD.closeDocument(doc.Name)
            FreeCADGui.updateGui()
            manager._follow_context()

    def test_headsup_commands_exist(self):
        from forgelib.ui import headsup

        available = set(FreeCADGui.listCommands())
        missing = [c for c in headsup.referenced_commands() if c not in available]
        self.assertEqual(missing, [])

    def test_headsup_follows_3d_view(self):
        manager = FreeCADGui.getWorkbench("ForgeWorkbench")._manager
        doc = FreeCAD.newDocument("ForgeHeadsUp")
        try:
            FreeCADGui.updateGui()
            manager._follow_context()
            self.assertTrue(manager.headsup.is_shown())
            bar = manager.headsup.bar()
            self.assertGreaterEqual(bar.x(), 0)
            self.assertLessEqual(bar.x() + bar.width(), bar.parentWidget().width() + 1)
            FreeCADGui.activateWorkbench("PartDesignWorkbench")
            self.assertFalse(manager.headsup.is_shown())
        finally:
            FreeCAD.closeDocument(doc.Name)
        FreeCADGui.activateWorkbench("ForgeWorkbench")
        FreeCADGui.updateGui()
        manager._timer.stop()
        if FreeCADGui.ActiveDocument is None:
            manager._follow_context()
            self.assertFalse(manager.headsup.is_shown())

    def test_rollback_slider_and_commands(self):
        from ForgeTests import models
        from forgelib import rollback

        manager = FreeCADGui.getWorkbench("ForgeWorkbench")._manager
        doc = FreeCAD.newDocument("ForgeRollbackGui")
        try:
            body, pad, pocket = models.block_with_hole(doc)
            FreeCADGui.ActiveDocument.ActiveView.setActiveObject("pdbody", body)
            FreeCADGui.updateGui()
            manager._follow_context()
            slider = self.mw.findChild(QtWidgets.QSlider, "ForgeRollbackSlider")
            label = self.mw.findChild(QtWidgets.QLabel, "ForgeRollbackLabel")
            self.assertEqual((slider.minimum(), slider.maximum(), slider.value()), (0, 2, 2))
            self.assertTrue(manager.rollback_shown())

            slider.setValue(1)  # come un rilascio del cursore
            self.assertIs(body.Tip, pad)
            self.assertAlmostEqual(body.Shape.Volume, 2000, places=6)
            self.assertEqual(label.text(), "1/2 – Pad")

            FreeCADGui.runCommand("Forge_RollbackPrevious")
            self.assertEqual(rollback.position(body), 0)
            self.assertFalse(FreeCADGui.isCommandActive("Forge_RollbackPrevious"))
            FreeCADGui.runCommand("Forge_RollbackNext")
            self.assertEqual(rollback.position(body), 1)
            FreeCADGui.runCommand("Forge_RollbackToEnd")
            self.assertIs(body.Tip, pocket)
            manager._follow_context()
            self.assertEqual(slider.value(), 2)
        finally:
            FreeCAD.closeDocument(doc.Name)
        FreeCADGui.updateGui()
        manager._follow_context()
        self.assertFalse(manager.rollback_shown())

    def test_sketch_edit_outside_forge_unchanged(self):
        """Fuori da Forge la modifica dello schizzo passa ancora allo Sketcher (comportamento upstream)."""
        doc = FreeCAD.newDocument("ForgeSketchEditPD")
        try:
            sketch = self._make_sketch(doc)
            FreeCADGui.activateWorkbench("PartDesignWorkbench")
            FreeCADGui.ActiveDocument.setEdit(sketch.Name)
            FreeCADGui.updateGui()
            self.assertEqual(FreeCADGui.activeWorkbench().name(), "SketcherWorkbench")
            FreeCADGui.ActiveDocument.resetEdit()
            FreeCADGui.updateGui()
            self.assertEqual(FreeCADGui.activeWorkbench().name(), "PartDesignWorkbench")
        finally:
            FreeCAD.closeDocument(doc.Name)

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


class TestForgeSettings(unittest.TestCase):
    def _snapshot(self):
        from forgelib import settings

        params = {(g, n): FreeCAD.ParamGet(g).GetContents() for g, _, n, _ in settings.PARAMETERS}
        shortcuts = FreeCAD.ParamGet(settings.SHORTCUT_PARAMS).GetContents()
        return params, sorted(shortcuts or [])

    def test_apply_and_revert_restore_exact_state(self):
        from forgelib import settings

        if settings.is_applied():
            self.skipTest("impostazioni Forge già applicate dall'utente")
        before = self._snapshot()
        try:
            self.assertTrue(settings.apply())
            self.assertFalse(settings.apply(), "una seconda applicazione non deve fare nulla")
            view = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/View")
            self.assertEqual(view.GetString("NavigationStyle"), "Gui::SolidWorksNavigationStyle")
            for cmd, key in settings.SHORTCUTS.items():
                if FreeCADGui.Command.get(cmd) is None:
                    continue
                self.assertEqual(FreeCADGui.Command.get(cmd).getShortcut(), key)
                owners = [
                    name
                    for name in FreeCADGui.Command.listAll()
                    if FreeCADGui.Command.get(name).getShortcut().replace(" ", "").lower()
                    == key.lower()
                ]
                self.assertEqual(owners, [cmd], f"conflitto su {key}")
        finally:
            settings.revert()
        self.assertFalse(settings.is_applied())
        self.assertEqual(self._snapshot(), before)


def tearDownModule():
    # In modalità test FreeCAD esce con SystemExit senza chiudere la finestra principale, quindi
    # mainWindowClosed/aboutToQuit non arrivano: si spegne il command manager come all'uscita reale.
    manager = getattr(FreeCADGui.getWorkbench("ForgeWorkbench"), "_manager", None)
    if manager is not None:
        manager.shutdown()


class TestForgeRadial(unittest.TestCase):
    def setUp(self):
        self.previous = FreeCADGui.activeWorkbench().name()
        FreeCADGui.activateWorkbench("ForgeWorkbench")
        FreeCADGui.getWorkbench("ForgeWorkbench")._manager._timer.stop()

    def tearDown(self):
        FreeCADGui.activateWorkbench(self.previous)

    def test_radial_items_exist(self):
        from forgelib.ui.radial import RADIAL_ITEMS

        available = set(FreeCADGui.listCommands())
        for key in ("sketch", "part"):
            missing = [c for c in RADIAL_ITEMS[key] if c not in available]
            self.assertEqual(missing, [], key)

    def test_radial_menu_opens_with_part_commands(self):
        from forgelib.ui.radial import RADIAL_ITEMS, show_radial_menu

        doc = FreeCAD.newDocument("ForgeRadial")
        try:
            FreeCADGui.updateGui()
            menu = show_radial_menu()
            FreeCADGui.updateGui()
            names = [b.objectName() for b in menu.findChildren(QtWidgets.QToolButton)]
            self.assertEqual(names, list(RADIAL_ITEMS["part"]))
            self.assertTrue(menu.isVisible())
            menu.close()
            FreeCADGui.updateGui()
        finally:
            FreeCAD.closeDocument(doc.Name)


class TestForgeDiagnosticsGui(unittest.TestCase):
    def setUp(self):
        self.previous = FreeCADGui.activeWorkbench().name()
        FreeCADGui.activateWorkbench("ForgeWorkbench")
        FreeCADGui.getWorkbench("ForgeWorkbench")._manager._timer.stop()
        from ForgeTests import models

        self.doc = FreeCAD.newDocument("ForgeDiagGui")
        body = models.new_body(self.doc)
        pad = models.pad(body, models.add_rectangle(models.sketch_on(body, "S"), 0, 0, 20, 10), 10)
        self.doc.recompute()
        self.fillet = body.newObject("PartDesign::Fillet", "Fillet")
        self.fillet.Base = (pad, ["Edge1", "Edge2"])
        self.fillet.Radius = 30
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)
        FreeCADGui.activateWorkbench(self.previous)

    def test_reporter_records_new_problems(self):
        from forgelib import commands

        self.assertIsNotNone(commands.reporter)
        commands.reporter.slotRecomputedDocument(self.doc)
        self.assertIn("Fillet", {name for name, _ in commands.reporter._reported[self.doc.Name]})

    def test_show_diagnostics_selects_geometry(self):
        from forgelib import commands, diagnostics

        found = diagnostics.diagnose(self.doc, suggest=True)
        self.assertEqual(len(found), 1)
        box = commands.show_diagnostics(found)
        FreeCADGui.updateGui()
        selected = FreeCADGui.Selection.getSelectionEx()
        self.assertEqual(len(selected), 1)
        self.assertEqual(sorted(selected[0].SubElementNames), ["Edge1", "Edge2"])
        box.close()
