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
            with self.subTest(tab=tab.key):
                commands = [c for c in tab.commands if c != catalog.SEPARATOR]
                self.assertTrue(commands)
                self.assertEqual(len(commands), len(set(commands)), "comandi duplicati")
                self.assertNotEqual(tab.commands[0], catalog.SEPARATOR)
                self.assertNotEqual(tab.commands[-1], catalog.SEPARATOR)
                for a, b in zip(tab.commands, tab.commands[1:]):
                    self.assertFalse(a == b == catalog.SEPARATOR, "separatori doppi")

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
