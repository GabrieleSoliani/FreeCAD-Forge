# SPDX-License-Identifier: LGPL-2.1-or-later
"""M8 (GUI): comandi Rileva interferenze e Analisi di sformo."""

import unittest

import FreeCAD
import FreeCADGui
from FreeCAD import Vector

from forgelib import evaluate, evaluate_gui


def setUpModule():
    # i comandi Forge si registrano all'inizializzazione del workbench
    previous = FreeCADGui.activeWorkbench().name()
    FreeCADGui.activateWorkbench("ForgeWorkbench")
    FreeCADGui.activateWorkbench(previous)


class TestEvaluateGui(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeEvaluateGui")
        self.a = self.doc.addObject("Part::Box", "A")
        self.b = self.doc.addObject("Part::Box", "B")
        self.b.Placement.Base = Vector(8, 0, 0)
        self.c = self.doc.addObject("Part::Cone", "C")
        self.c.Radius1, self.c.Radius2, self.c.Height = 10, 8, 10
        self.c.Placement.Base = Vector(100, 0, 0)
        self.doc.recompute()
        FreeCADGui.Selection.clearSelection()

    def tearDown(self):
        FreeCADGui.Selection.clearSelection()
        FreeCAD.closeDocument(self.doc.Name)

    def test_interference_on_visible_solids(self):
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual([(f.first, f.second, f.kind) for f in found], [("A", "B", "interferenza")])
        group = self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP)
        self.assertIsNotNone(group)
        self.assertEqual(len(group.Group), 1)
        self.assertAlmostEqual(group.Group[0].Shape.Volume, 200, places=6)
        # una seconda esecuzione sostituisce i risultati e non conta i solidi rossi
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual(len(found), 1)
        self.assertEqual(len(self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP).Group), 1)

    def test_interference_on_selection_only(self):
        FreeCADGui.Selection.addSelection(self.a)
        FreeCADGui.Selection.addSelection(self.c)
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual(found, [])
        self.assertIsNone(self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP))

    def test_draft_analysis_colors_and_clear(self):
        result, faces = evaluate_gui.run_draft_analysis(self.c, Vector(0, 0, 1), min_angle=1)
        self.assertEqual(len(result.ViewObject.DiffuseColor), len(self.c.Shape.Faces))
        self.assertFalse(self.c.Visibility)
        counts = evaluate.summarize_draft(faces)
        self.assertEqual(counts[evaluate.POSITIVE], 2)
        colors = [tuple(round(x, 2) for x in c[:3]) for c in result.ViewObject.DiffuseColor]
        self.assertIn(tuple(round(x, 2) for x in evaluate.DRAFT_COLORS[evaluate.NEGATIVE]), colors)
        self.assertEqual(evaluate_gui.clear_draft_analysis(self.doc), 1)
        self.assertTrue(self.c.Visibility)
        self.assertIsNone(self.doc.getObject(evaluate_gui.DRAFT_OBJECT))

    def test_commands_registered(self):
        for name in evaluate_gui.EVALUATE_COMMANDS:
            self.assertIn(name, FreeCADGui.listCommands())
