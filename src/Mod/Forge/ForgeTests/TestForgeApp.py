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
            keys,
            {"sketch", "features", "surfaces", "sheetmetal", "weldments", "evaluate", "assembly",
             "drawing"},
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


class TestSettings(unittest.TestCase):
    def test_plan_sets_wanted_and_clears_conflicts(self):
        from forgelib.settings import plan_shortcuts

        current = {"Fit": "V, F", "Other": "F", "Front": "1", "Free": "Ctrl+1", "Same": "Ctrl+B"}
        wanted = {"Fit": "F", "Front": "Ctrl+1", "Same": "Ctrl+B", "Missing": "Ctrl+9"}
        changes = plan_shortcuts(current, wanted)
        self.assertEqual(
            changes, {"Fit": "F", "Front": "Ctrl+1", "Other": "", "Free": ""}
        )

    def test_plan_ignores_spacing_and_case(self):
        from forgelib.settings import plan_shortcuts

        self.assertEqual(plan_shortcuts({"A": "ctrl+b", "B": "Ctrl + B"}, {"A": "Ctrl+B"}), {"B": ""})

    def test_backup_roundtrip(self):
        from forgelib.settings import decode_backup, encode_backup

        params = [("G", "String", "N", None), ("G", "Bool", "B", True), ("H", "Int", "I", 3)]
        shortcuts = {"Cmd": None, "Cmd2": "Ctrl+K"}
        self.assertEqual(decode_backup(encode_backup(params, shortcuts)), (params, shortcuts))

    def test_shortcut_table_has_unique_keys(self):
        from forgelib.settings import SHORTCUTS

        keys = [k.lower() for k in SHORTCUTS.values()]
        self.assertEqual(len(keys), len(set(keys)))


class TestRollback(unittest.TestCase):
    def setUp(self):
        import FreeCAD

        from ForgeTests import models

        self.doc = FreeCAD.newDocument("ForgeRollback")
        self.body, self.pad, self.pocket = models.block_with_hole(self.doc)

    def tearDown(self):
        import FreeCAD

        FreeCAD.closeDocument(self.doc.Name)

    def _volume(self):
        shape = self.body.Shape
        return 0.0 if shape.isNull() else shape.Volume

    def test_model_is_valid(self):
        import math

        self.assertTrue(self.body.Shape.isValid())
        self.assertAlmostEqual(self._volume(), 2000 - 20 * math.pi, places=6)

    def test_positions_and_volumes(self):
        import math

        from forgelib import rollback

        self.assertEqual(rollback.solid_features(self.body), [self.pad, self.pocket])
        self.assertEqual(rollback.position(self.body), 2)
        self.assertFalse(rollback.is_rolled_back(self.body))

        self.assertEqual(rollback.step(self.body, -1), 1)
        self.assertIs(self.body.Tip, self.pad)
        self.assertTrue(rollback.is_rolled_back(self.body))
        self.assertAlmostEqual(self._volume(), 2000, places=6)
        self.assertEqual(rollback.describe(self.body), "1/2 – Pad")

        self.assertEqual(rollback.set_position(self.body, 0), 0)
        self.assertIsNone(self.body.Tip)
        self.assertEqual(self._volume(), 0.0)
        self.assertEqual(rollback.describe(self.body), "0/2 – inizio")

        self.assertEqual(rollback.to_end(self.body), 2)
        self.assertIs(self.body.Tip, self.pocket)
        self.assertAlmostEqual(self._volume(), 2000 - 20 * math.pi, places=6)

    def test_positions_are_clamped(self):
        from forgelib import rollback

        self.assertEqual(rollback.set_position(self.body, 99), 2)
        self.assertEqual(rollback.set_position(self.body, -5), 0)
        self.assertEqual(rollback.step(self.body, -1), 0)

    def test_rollback_is_undoable(self):
        from forgelib import rollback

        self.doc.UndoMode = 1
        rollback.set_position(self.body, 1)
        self.assertIs(self.body.Tip, self.pad)
        self.doc.undo()
        self.assertIs(self.body.Tip, self.pocket)


class TestRadial(unittest.TestCase):
    def test_ring_positions(self):
        from forgelib.ui.radial import ring_positions

        self.assertEqual(ring_positions(4, 10), [(0, -10), (10, 0), (0, 10), (-10, 0)])
        for x, y in ring_positions(8, 78):
            self.assertAlmostEqual((x * x + y * y) ** 0.5, 78, delta=1)

    def test_context_mapping(self):
        from forgelib.ui.radial import RADIAL_ITEMS, radial_context

        self.assertEqual(radial_context(Context()), "part")
        self.assertEqual(radial_context(Context(sketch_in_edit=True)), "sketch")
        self.assertEqual(radial_context(Context(drawing_page_active=True)), "drawing")
        self.assertEqual(radial_context(Context(assembly_active=True)), "assembly")
        for key, items in RADIAL_ITEMS.items():
            self.assertEqual(len(items), len(set(items)), key)
            self.assertLessEqual(len(items), 8, key)
