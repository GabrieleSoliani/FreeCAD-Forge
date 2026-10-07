# SPDX-License-Identifier: LGPL-2.1-or-later
"""M6.2: serie e specchiatura di componenti."""

import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib import evaluate
from forgelib.features import component_pattern as cp


class TestComponentPattern(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeComponents")
        self.part = self.doc.addObject("Part::Box", "Blocchetto")
        self.part.Length, self.part.Width, self.part.Height = 10, 20, 5
        self.seed = self.doc.addObject("App::Link", "Componente")
        self.seed.LinkedObject = self.part
        self.seed.Placement.Base = Vector(100, 0, 0)
        self.part.Visibility = False
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def shapes(self, pattern):
        return [(f"{pattern.Name}{i}", s) for i, s in enumerate(Part.getShape(pattern).Solids)]

    def test_linear_pattern(self):
        pattern = cp.make_pattern(self.doc, self.seed, "Lineare", 4, Direction=Vector(0, 1, 0), Spacing=30)
        self.doc.recompute()
        self.assertTrue(pattern.isValid(), pattern.getStatusString())
        solids = Part.getShape(pattern).Solids
        self.assertEqual(len(solids), 3)
        ys = sorted(round(s.BoundBox.YMin, 6) for s in solids)
        self.assertEqual(ys, [30, 60, 90])
        self.assertTrue(all(abs(s.BoundBox.XMin - 100) < 1e-9 for s in solids))
        self.assertAlmostEqual(sum(s.Volume for s in solids), 3 * 1000, places=6)

    def test_pattern_follows_seed_and_parameters(self):
        pattern = cp.make_pattern(self.doc, self.seed, "Lineare", 2, Direction=Vector(1, 0, 0), Spacing=50)
        self.doc.recompute()
        self.seed.Placement.Base = Vector(0, 0, 0)
        pattern.Count = 3
        self.doc.recompute()
        xs = sorted(round(s.BoundBox.XMin, 6) for s in Part.getShape(pattern).Solids)
        self.assertEqual(xs, [50, 100])

    def test_circular_pattern_no_overlaps(self):
        pattern = cp.make_pattern(self.doc, self.seed, "Circolare", 6, Axis=Vector(0, 0, 1), Angle=360)
        self.doc.recompute()
        items = self.shapes(pattern) + [("seme", Part.getShape(self.seed))]
        self.assertEqual(len(items), 6)
        overlaps = [f for f in evaluate.check_pairs(items) if f.kind == "interferenza"]
        self.assertEqual(overlaps, [])
        # tutte le istanze alla stessa distanza dall'asse
        radii = {round(Vector(s.CenterOfMass.x, s.CenterOfMass.y, 0).Length, 6) for _, s in items}
        self.assertEqual(len(radii), 1)

    def test_partial_arc_includes_both_ends(self):
        placements = cp.instance_placements(FreeCAD.Placement(Vector(10, 0, 0), FreeCAD.Rotation()),
                                            "Circolare", 3, angle=90)
        self.assertTrue(placements[-1].Base.isEqual(Vector(0, 10, 0), 1e-9))

    def test_mirror_component(self):
        mirrored = cp.make_mirror(self.doc, self.seed, Vector(0, 0, 0), Vector(1, 0, 0))
        self.doc.recompute()
        self.assertTrue(mirrored.isValid(), mirrored.getStatusString())
        self.assertAlmostEqual(mirrored.Shape.Volume, 1000, places=6)
        self.assertAlmostEqual(mirrored.Shape.BoundBox.XMax, -100, places=6)
        self.assertIn("opposto", mirrored.Label)

    def test_save_and_reopen(self):
        import os
        import tempfile

        cp.make_pattern(self.doc, self.seed, "Lineare", 3, Spacing=40)
        self.doc.recompute()
        path = os.path.join(tempfile.mkdtemp(), "serie.FCStd")
        self.doc.saveAs(path)
        FreeCAD.closeDocument(self.doc.Name)
        self.doc = FreeCAD.openDocument(path)
        pattern = self.doc.getObject("SerieComponenti")
        pattern.touch()
        self.doc.recompute()
        self.assertTrue(pattern.isValid())
        self.assertEqual(len(Part.getShape(pattern).Solids), 2)
