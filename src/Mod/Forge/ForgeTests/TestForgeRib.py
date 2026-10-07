# SPDX-License-Identifier: LGPL-2.1-or-later
"""M4.2: nervatura da profilo aperto."""

import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from ForgeTests import examples, models
from forgelib.features import rib


class TestRib(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeRib")
        # staffa a L senza fori né raccordi: base y 0..40 z 0..5, ala y 0..5 z 0..40, lunga 60 in X
        self.body = models.new_body(self.doc)
        profile = examples._polygon(
            models.sketch_on(self.body, "ProfiloL", plane="YZ_Plane"),
            [(0, 0), (40, 0), (40, 5), (5, 5), (5, 40), (0, 40)],
        )
        self.pad = models.pad(self.body, profile, 60)
        self.doc.recompute()
        self.base_volume = self.pad.Shape.Volume

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def rib_sketch(self, a, b, x=30):
        sketch = models.sketch_on(self.body, "ProfiloNervatura", plane="YZ_Plane", offset=Vector(0, 0, x))
        sketch.addGeometry(Part.LineSegment(Vector(*a, 0), Vector(*b, 0)))
        self.doc.recompute()
        return sketch

    def test_gusset_volume(self):
        sketch = self.rib_sketch((30, 5), (5, 30))
        feature = rib.make_rib(self.body, sketch, 4)
        self.doc.recompute()
        self.assertTrue(feature.isValid(), feature.getStatusString())
        self.assertTrue(self.body.Shape.isValid())
        self.assertEqual(len(self.body.Shape.Solids), 1)
        # triangolo rettangolo 25 × 25 per 4 mm di spessore
        self.assertAlmostEqual(self.body.Shape.Volume - self.base_volume, 0.5 * 25 * 25 * 4, places=4)
        box = feature.Shape.BoundBox
        self.assertAlmostEqual(box.XLength, 60, places=6)

    def test_short_profile_is_extended_to_material(self):
        # profilo che non tocca il pezzo: prolungato fino alle facce interne
        sketch = self.rib_sketch((25, 10), (10, 25))
        feature = rib.make_rib(self.body, sketch, 2)
        self.doc.recompute()
        self.assertTrue(feature.isValid(), feature.getStatusString())
        # retta y + z = 35 tra y=5 e z=5: triangolo con cateti 25
        self.assertAlmostEqual(self.body.Shape.Volume - self.base_volume, 0.5 * 25 * 25 * 2, places=4)

    def test_closed_profile_is_rejected(self):
        sketch = models.add_rectangle(models.sketch_on(self.body, "Chiuso", plane="YZ_Plane", offset=Vector(0, 0, 30)), 10, 10, 20, 20)
        feature = rib.make_rib(self.body, sketch, 2)
        self.doc.recompute()
        self.assertFalse(feature.isValid())
        self.assertIn("aperto", feature.getStatusString())

    def test_profile_without_closure(self):
        # linea parallela alla base, sopra il pezzo: non chiude alcuna regione
        sketch = self.rib_sketch((50, 50), (60, 50))
        feature = rib.make_rib(self.body, sketch, 2)
        self.doc.recompute()
        self.assertFalse(feature.isValid())
