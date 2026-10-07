# SPDX-License-Identifier: LGPL-2.1-or-later
"""Test di Forge eseguibili senza GUI (FreeCADCmd -t ForgeTests.TestForgeApp)."""

import unittest

from forgelib.ui import catalog
from forgelib.ui.context import Context, TabFollower, choose_tab


class TestCatalog(unittest.TestCase):
    def test_tab_keys_and_toolbars_unique(self):
        keys = [tab.key for tab in catalog.TABS]
        self.assertEqual(len(keys), len(set(keys)))
        names = [tab.toolbar_name for tab in catalog.TABS]
        self.assertEqual(len(names), len(set(names)))

    def test_expected_tabs(self):
        keys = {tab.key for tab in catalog.TABS}
        self.assertEqual(
            keys, {"sketch", "features", "surfaces", "evaluate", "assembly", "drawing"}
        )
        self.assertIsNotNone(catalog.tab_by_key(catalog.DEFAULT_TAB))
        self.assertIsNone(catalog.tab_by_key("inesistente"))

    def test_tabs_well_formed(self):
        for tab in catalog.TABS:
            for name, group in tab.all_toolbars():
                with self.subTest(toolbar=name):
                    commands = [c for c in group if c != catalog.SEPARATOR]
                    self.assertTrue(commands)
                    self.assertEqual(len(commands), len(set(commands)), "comandi duplicati")
                    self.assertNotEqual(group[0], catalog.SEPARATOR)
                    self.assertNotEqual(group[-1], catalog.SEPARATOR)
                    for a, b in zip(group, group[1:]):
                        self.assertFalse(a == b == catalog.SEPARATOR, "separatori doppi")

    def test_all_toolbar_names_unique(self):
        names = [name for tab in catalog.TABS for name, _ in tab.all_toolbars()]
        self.assertEqual(len(names), len(set(names)))

    def test_sketch_tab_has_edit_toolbars(self):
        tab = catalog.tab_by_key("sketch")
        self.assertEqual(tab.edit_toolbar_names(), ["Forge Schizzo - Disegno", "Forge Schizzo - Vincoli"])
        edit_commands = {c for _, group in tab.edit_groups for c in group}
        # uscita dallo schizzo e quota intelligente devono essere sempre a portata di mano
        self.assertIn("Sketcher_LeaveSketch", edit_commands)
        self.assertIn("Sketcher_CompDimensionTools", edit_commands)
        for other in catalog.TABS:
            if other.key != "sketch":
                self.assertEqual(other.edit_groups, ())

    def test_resolve_commands(self):
        sep = catalog.SEPARATOR
        commands = ["A", sep, "B", "C", sep, "D", sep, "E"]
        resolved, missing = catalog.resolve_commands(commands, {"A", "C", "E"})
        self.assertEqual(resolved, ["A", sep, "C", sep, "E"])
        self.assertEqual(missing, ["B", "D"])

    def test_resolve_commands_drops_dangling_separators(self):
        sep = catalog.SEPARATOR
        resolved, missing = catalog.resolve_commands([sep, "A", sep, "B", sep], {"A"})
        self.assertEqual(resolved, ["A"])
        self.assertEqual(missing, ["B"])
        self.assertEqual(catalog.resolve_commands(["X", sep, "Y"], set()), ([], ["X", "Y"]))


class TestContext(unittest.TestCase):
    def test_choose_tab_priority(self):
        self.assertIsNone(choose_tab(Context()))
        self.assertEqual(choose_tab(Context(sketch_in_edit=True)), "sketch")
        self.assertEqual(choose_tab(Context(assembly_active=True)), "assembly")
        self.assertEqual(
            choose_tab(Context(sketch_in_edit=True, assembly_active=True)), "sketch"
        )
        self.assertEqual(
            choose_tab(Context(drawing_page_active=True, sketch_in_edit=True)), "drawing"
        )

    def test_follower_enters_and_restores(self):
        follower = TabFollower()
        free = Context()
        sketch = Context(sketch_in_edit=True)
        self.assertIsNone(follower.update(free, "surfaces"))
        self.assertEqual(follower.update(sketch, "surfaces"), "sketch")
        # nessun nuovo cambio finché il contesto non cambia, anche se l'utente cambia scheda
        self.assertIsNone(follower.update(sketch, "evaluate"))
        # uscendo dallo schizzo si torna alla scheda di partenza
        self.assertEqual(follower.update(free, "evaluate"), "surfaces")
        self.assertIsNone(follower.update(free, "surfaces"))

    def test_follower_nested_contexts_restore_first_tab(self):
        follower = TabFollower()
        follower.update(Context(), "features")
        self.assertEqual(follower.update(Context(assembly_active=True), "features"), "assembly")
        self.assertEqual(
            follower.update(Context(assembly_active=True, sketch_in_edit=True), "assembly"),
            "sketch",
        )
        self.assertEqual(follower.update(Context(assembly_active=True), "sketch"), "assembly")
        self.assertEqual(follower.update(Context(), "assembly"), "features")

    def test_follower_no_switch_when_already_there(self):
        follower = TabFollower()
        self.assertIsNone(follower.update(Context(drawing_page_active=True), "drawing"))
        self.assertIsNone(follower.update(Context(), "drawing"))
