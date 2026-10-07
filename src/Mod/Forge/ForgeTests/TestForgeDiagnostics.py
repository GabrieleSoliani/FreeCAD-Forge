# SPDX-License-Identifier: LGPL-2.1-or-later
"""M3.2: diagnostica delle feature in italiano con suggerimenti calcolati."""

import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from ForgeTests import models
from forgelib import diagnostics


class DiagnosticsCase(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeDiagnostics")
        self.body = models.new_body(self.doc)
        sketch = models.add_rectangle(models.sketch_on(self.body, "Base"), 0, 0, 20, 10)
        self.pad = models.pad(self.body, sketch, 10)
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def only(self, suggest=False):
        found = diagnostics.diagnose(self.doc, suggest=suggest)
        self.assertEqual(len(found), 1, [d.text() for d in found])
        return found[0]


class TestDiagnostics(DiagnosticsCase):
    def test_healthy_model_has_no_diagnostics(self):
        self.assertEqual(diagnostics.diagnose(self.doc, suggest=True), [])

    def test_fillet_too_large_with_max_radius(self):
        fillet = self.body.newObject("PartDesign::Fillet", "Fillet")
        fillet.Base = (self.pad, [f"Edge{i}" for i in range(1, 13)])
        fillet.Radius = 6
        self.doc.recompute()
        diagnostic = self.only(suggest=True)
        self.assertEqual(diagnostic.severity, diagnostics.ERROR)
        self.assertIn("raggio", diagnostic.message)
        self.assertEqual(len(diagnostic.refs), 12)
        # il massimo teorico è appena sotto 5 (metà dello spessore di 10)
        import re

        value = float(re.search(r"circa ([0-9.]+) mm", diagnostic.suggestion).group(1))
        self.assertGreater(value, 4.5)
        self.assertLess(value, 5.0)

    def test_shell_too_thick_with_max_thickness(self):
        top = [f"Face{i + 1}" for i, f in enumerate(self.pad.Shape.Faces) if abs(f.CenterOfMass.z - 10) < 1e-6]
        shell = self.body.newObject("PartDesign::Thickness", "Thickness")
        shell.Base = (self.pad, top)
        shell.Value = 7
        self.doc.recompute()
        diagnostic = self.only(suggest=True)
        self.assertIn("parete", diagnostic.message)
        import re

        value = float(re.search(r"circa ([0-9.]+) mm", diagnostic.suggestion).group(1))
        self.assertGreater(value, 4.5)
        self.assertLess(value, 5.0)

    def test_pocket_outside_material_is_a_warning(self):
        sketch = models.add_circle(models.sketch_on(self.body, "Far", offset=Vector(0, 0, 10)), 100, 100, 2)
        models.pocket(self.body, sketch, 5)
        self.doc.recompute()
        diagnostic = self.only()
        self.assertEqual(diagnostic.severity, diagnostics.WARNING)
        self.assertIn("non rimuove materiale", diagnostic.message)

    def test_split_body_is_info(self):
        sketch = models.add_rectangle(models.sketch_on(self.body, "Cut", offset=Vector(0, 0, 10)), 9, -1, 11, 11)
        models.pocket(self.body, sketch, 20)
        self.doc.recompute()
        diagnostic = self.only()
        self.assertEqual(diagnostic.severity, diagnostics.INFO)
        self.assertIn("2 solidi", diagnostic.message)

    def test_open_profile(self):
        body = models.new_body(self.doc, "Body2")
        sketch = models.sketch_on(body, "Open")
        sketch.addGeometry(Part.LineSegment(Vector(0, 0, 0), Vector(10, 0, 0)))
        sketch.addGeometry(Part.LineSegment(Vector(10, 0, 0), Vector(10, 10, 0)))
        models.pad(body, sketch, 5, name="OpenPad")
        self.doc.recompute()
        diagnostic = self.only()
        self.assertIn("non è chiuso", diagnostic.message)
        self.assertEqual(diagnostic.raw, "Wire is not closed.")

    def test_missing_edge_reference(self):
        fillet = self.body.newObject("PartDesign::Fillet", "Fillet")
        fillet.Base = (self.pad, ["Edge99"])
        fillet.Radius = 1
        self.doc.recompute()
        self.assertIn("non esiste più", self.only().message)


class TestExplain(unittest.TestCase):
    def test_unknown_and_empty_messages(self):
        message, _ = diagnostics.explain("PartDesign::Pad", "qualcosa di strano")
        self.assertIn("qualcosa di strano", message)
        message, suggestion = diagnostics.explain("PartDesign::Pad", "")
        self.assertIn("nessun dettaglio", message)
        self.assertTrue(suggestion)

    def test_rule_specific_to_type(self):
        message, _ = diagnostics.explain("PartDesign::Chamfer", "BRep_API: command not done")
        self.assertIn("smusso", message)
        message, _ = diagnostics.explain("PartDesign::Fillet", "BRep_API: command not done")
        self.assertIn("raccordo", message)

    def test_max_feasible(self):
        self.assertAlmostEqual(diagnostics.max_feasible(lambda v: v <= 3.3, 10), 3.3, delta=0.01)
        self.assertEqual(diagnostics.max_feasible(lambda v: True, 10), 10)
        self.assertIsNone(diagnostics.max_feasible(lambda v: False, 10))
