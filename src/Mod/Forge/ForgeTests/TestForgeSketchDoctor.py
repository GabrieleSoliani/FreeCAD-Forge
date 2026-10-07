# SPDX-License-Identifier: LGPL-2.1-or-later
"""M2: diagnosi degli schizzi con proposta di soluzioni."""

import unittest

import FreeCAD
import Sketcher

from ForgeTests import models
from forgelib import sketch_doctor


class SketchCase(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeSketchDoctor")
        body = models.new_body(self.doc)
        # rettangolo: 4 linee + 4 coincidenti (vincoli 1..4)
        self.sketch = models.add_rectangle(models.sketch_on(body, "S"), 0, 0, 20, 10)
        add = self.sketch.addConstraint
        add(Sketcher.Constraint("Horizontal", 0))  # 5
        add(Sketcher.Constraint("Horizontal", 2))  # 6
        add(Sketcher.Constraint("Vertical", 1))  # 7
        add(Sketcher.Constraint("Vertical", 3))  # 8

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def add(self, constraint):
        return self.sketch.addConstraint(constraint) + 1  # base 1


class TestSketchDoctor(SketchCase):
    def test_underconstrained_report(self):
        state, text = sketch_doctor.report(self.sketch)
        self.assertTrue(state.ok)
        self.assertEqual(state.dof, 4)
        self.assertIn("4 gradi di libertà", text)
        self.assertEqual(sketch_doctor.propose_fixes(self.sketch), [])

    def test_fully_constrained(self):
        self.add(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20))
        self.add(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, 10))
        self.add(Sketcher.Constraint("Coincident", 0, 1, -1, 1))
        state, text = sketch_doctor.report(self.sketch)
        self.assertTrue(state.fully_constrained)
        self.assertIn("completamente vincolato", text)

    def test_conflicting_dimensions_propose_removing_one_of_them(self):
        first = self.add(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20))
        second = self.add(Sketcher.Constraint("DistanceX", 2, 2, 2, 1, 25))
        state = sketch_doctor.analyze(self.sketch)
        self.assertIn(second, state.conflicting)
        fixes = sketch_doctor.propose_fixes(self.sketch, state)
        proposed = [f.constraint for f in fixes]
        # le quote vengono proposte per prime
        self.assertEqual(proposed[:2], sorted([first, second]))
        for fix in fixes:
            self.assertTrue(fix.resolves)
        self.assertIn("Distanza orizzontale", fixes[0].description)
        self.assertIn("mm", fixes[0].description)
        # lo schizzo non è stato modificato dalla ricerca
        self.assertEqual(self.sketch.ConstraintCount, 10)
        self.assertTrue(all(c.IsActive for c in self.sketch.Constraints))
        self.assertEqual(sketch_doctor.analyze(self.sketch).conflicting, state.conflicting)

    def test_apply_fix_resolves(self):
        self.add(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20))
        self.add(Sketcher.Constraint("DistanceX", 2, 2, 2, 1, 25))
        fix = sketch_doctor.propose_fixes(self.sketch)[0]
        sketch_doctor.apply_fix(self.sketch, fix)
        state = sketch_doctor.analyze(self.sketch)
        self.assertTrue(state.ok)
        self.assertEqual(state.dof, fix.dof_after)

    def test_redundant_constraint(self):
        duplicate = self.add(Sketcher.Constraint("Horizontal", 0))
        state = sketch_doctor.analyze(self.sketch)
        self.assertEqual(state.redundant, [duplicate])
        fixes = sketch_doctor.propose_fixes(self.sketch, state)
        self.assertEqual([f.constraint for f in fixes], [duplicate])
        self.assertIn("Orizzontale", fixes[0].description)
        self.assertIn("Linea 1", fixes[0].description)

    def test_describe_angle_and_axes(self):
        index = self.add(Sketcher.Constraint("Coincident", 0, 1, -1, 1))
        self.assertIn("asse orizzontale", sketch_doctor.describe(self.sketch, index))
        import math

        angle = self.add(Sketcher.Constraint("Angle", 0, math.radians(30)))
        self.assertIn("30°", sketch_doctor.describe(self.sketch, angle))
