# SPDX-License-Identifier: LGPL-2.1-or-later
"""M3: casi "difficili" di raccordi, smussi, gusci e sformi (FreeCADCmd -t ForgeTests.TestForgeRobustness).

Prima delle patch di Forge alcuni di questi casi davano una feature "valida" con un solido non
valido (volume negativo) o un guscio che non faceva nulla. Ogni test verifica proprietà
geometriche oggettive: validità, volume, numero di solidi, messaggio d'errore.
"""

import math
import unittest

import FreeCAD

from ForgeTests import models


class RobustnessCase(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeRobustness")
        self.body = models.new_body(self.doc)
        sketch = models.add_rectangle(models.sketch_on(self.body, "Base"), 0, 0, 20, 10)
        self.pad = models.pad(self.body, sketch, 10)
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def edges(self, predicate):
        return [
            f"Edge{i + 1}" for i, e in enumerate(self.pad.Shape.Edges) if predicate(e)
        ]

    def top_face(self):
        for i, face in enumerate(self.pad.Shape.Faces):
            if abs(face.CenterOfMass.z - 10) < 1e-6:
                return f"Face{i + 1}"
        raise AssertionError("faccia superiore non trovata")

    def assert_ok(self, feature, volume):
        self.assertTrue(feature.isValid(), feature.getStatusString())
        self.assertTrue(feature.Shape.isValid())
        self.assertEqual(len(feature.Shape.Solids), 1)
        self.assertAlmostEqual(feature.Shape.Volume, volume, delta=1e-6 * volume)

    def assert_error(self, feature, text):
        self.assertFalse(feature.isValid())
        self.assertIn(text, feature.getStatusString())
        # il corpo resta sulla forma precedente, valida
        self.assertTrue(self.body.Shape.isValid())
        self.assertGreater(self.body.Shape.Volume, 0)


class TestFillet(RobustnessCase):
    def _fillet(self, subs, radius):
        fillet = self.body.newObject("PartDesign::Fillet", "Fillet")
        fillet.Base = (self.pad, subs)
        fillet.Radius = radius
        self.doc.recompute()
        return fillet

    def test_single_edge_volume(self):
        # spigolo superiore lungo X (lunghezza 20): si toglie (r² - πr²/4)·L
        top_x = self.edges(lambda e: abs(e.CenterOfMass.z - 10) < 1e-6 and abs(e.CenterOfMass.y) < 1e-6)
        fillet = self._fillet(top_x, 2)
        self.assert_ok(fillet, 2000 - (4 - math.pi) * 20)

    def test_all_edges_valid_radius(self):
        fillet = self._fillet([f"Edge{i}" for i in range(1, 13)], 2)
        self.assertTrue(fillet.isValid(), fillet.getStatusString())
        self.assertTrue(fillet.Shape.isValid())
        self.assertLess(fillet.Shape.Volume, 2000)

    def test_radius_too_large_is_an_error_not_a_bad_solid(self):
        # prima di Forge: feature "valida" con volume negativo
        fillet = self._fillet([f"Edge{i}" for i in range(1, 13)], 6)
        self.assert_error(fillet, "radius is probably too large")


class TestChamfer(RobustnessCase):
    def test_size_too_large_is_an_error(self):
        chamfer = self.body.newObject("PartDesign::Chamfer", "Chamfer")
        chamfer.Base = (self.pad, [f"Edge{i}" for i in range(1, 13)])
        chamfer.Size = 6
        self.doc.recompute()
        self.assertFalse(chamfer.isValid())
        self.assertTrue(self.body.Shape.isValid())

    def test_single_edge_volume(self):
        top_x = self.edges(lambda e: abs(e.CenterOfMass.z - 10) < 1e-6 and abs(e.CenterOfMass.y) < 1e-6)
        chamfer = self.body.newObject("PartDesign::Chamfer", "Chamfer")
        chamfer.Base = (self.pad, top_x)
        chamfer.Size = 2
        self.doc.recompute()
        self.assert_ok(chamfer, 2000 - 0.5 * 2 * 2 * 20)


class TestThickness(RobustnessCase):
    def _fresh(self):
        self.tearDown()
        self.setUp()

    def _shell(self, value):
        shell = self.body.newObject("PartDesign::Thickness", "Thickness")
        shell.Base = (self.pad, [self.top_face()])
        shell.Value = value
        self.doc.recompute()
        return shell

    def test_valid_shell_volume(self):
        # cavità (20-2t)(10-2t)(10-t) con la faccia superiore aperta
        for t in (1, 4, 4.9):
            with self.subTest(t=t):
                self._fresh()
                shell = self._shell(t)
                self.assert_ok(shell, 2000 - (20 - 2 * t) * (10 - 2 * t) * (10 - t))

    def test_wall_too_thick_is_an_error(self):
        # prima di Forge: t=5 solido non valido, t>5 nessun effetto, entrambi "validi"
        for t, text in ((5, "not a valid solid"), (6, "had no effect"), (9, "had no effect")):
            with self.subTest(t=t):
                self._fresh()
                shell = self._shell(t)
                self.assert_error(shell, text)


class TestDraft(RobustnessCase):
    def test_failure_has_a_message(self):
        sides = [
            f"Face{i + 1}"
            for i, f in enumerate(self.pad.Shape.Faces)
            if abs(f.normalAt(0, 0).z) < 1e-6
        ]
        bottom = [
            f"Face{i + 1}"
            for i, f in enumerate(self.pad.Shape.Faces)
            if abs(f.CenterOfMass.z) < 1e-6
        ]
        draft = self.body.newObject("PartDesign::Draft", "Draft")
        draft.Base = (self.pad, sides)
        draft.NeutralPlane = (self.pad, bottom)
        draft.Angle = 60
        self.doc.recompute()
        if draft.isValid():
            self.skipTest("OCC riesce a calcolare questo sformo")
        self.assertTrue(draft.getStatusString().strip(), "messaggio d'errore vuoto")
