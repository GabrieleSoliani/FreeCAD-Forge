# SPDX-License-Identifier: LGPL-2.1-or-later
"""M8: interferenze/giochi e analisi di sformo."""

import math
import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib import evaluate


def box(x, y, z, dx=10, dy=10, dz=10):
    return Part.makeBox(dx, dy, dz, Vector(x, y, z))


class TestInterference(unittest.TestCase):
    def test_overlap_contact_and_clearance(self):
        items = [
            ("A", box(0, 0, 0)),
            ("B", box(8, 0, 0)),  # compenetra A per 2×10×10
            ("C", box(0, 10, 0)),  # tocca A sulla faccia y=10
            ("D", box(0, 0, 10.3)),  # sopra A a 0,3 mm
            ("E", box(100, 100, 100)),  # lontano
        ]
        found = evaluate.check_pairs(items, clearance=0.5)
        summary = [(f.first, f.second, f.kind) for f in found]
        self.assertEqual(summary[0], ("A", "B", "interferenza"))
        self.assertAlmostEqual(found[0].volume, 200, places=6)
        self.assertIn(("A", "D", "gioco"), summary)
        self.assertIn(("A", "C", "contatto"), summary)
        self.assertNotIn("E", {n for f in found for n in (f.first, f.second)})
        gap = [f for f in found if f.kind == "gioco" and {f.first, f.second} == {"A", "D"}][0]
        self.assertAlmostEqual(gap.distance, 0.3, places=6)

    def test_no_clearance_check_by_default(self):
        found = evaluate.check_pairs([("A", box(0, 0, 0)), ("D", box(0, 0, 10.3))])
        self.assertEqual(found, [])

    def test_links_use_global_placement(self):
        doc = FreeCAD.newDocument("ForgeInterference")
        try:
            part = doc.addObject("Part::Box", "Cubo")
            first = doc.addObject("App::Link", "Primo")
            first.LinkedObject = part
            second = doc.addObject("App::Link", "Secondo")
            second.LinkedObject = part
            second.Placement.Base = Vector(5, 0, 0)
            part.Visibility = False
            doc.recompute()
            items = [(o.Label, evaluate.global_shape(o)) for o in (first, second)]
            found = evaluate.check_pairs(items)
            self.assertEqual(len(found), 1)
            self.assertAlmostEqual(found[0].volume, 500, places=6)
        finally:
            FreeCAD.closeDocument(doc.Name)


class TestDraftAnalysis(unittest.TestCase):
    def kinds(self, shape, direction=(0, 0, 1), min_angle=1.0):
        return {f.index: f for f in evaluate.draft_analysis(shape, Vector(*direction), min_angle)}

    def test_cone_side_has_positive_draft(self):
        cone = Part.makeCone(10, 8, 10)
        faces = self.kinds(cone)
        side = [f for f in faces.values() if abs(f.min_angle) < 89][0]
        self.assertEqual(side.kind, evaluate.POSITIVE)
        self.assertAlmostEqual(side.min_angle, math.degrees(math.atan(2 / 10)), places=4)
        self.assertEqual(evaluate.summarize_draft(faces.values())[evaluate.POSITIVE], 2)  # lato + cima
        self.assertEqual(evaluate.summarize_draft(faces.values())[evaluate.NEGATIVE], 1)  # base

    def test_cube_vertical_faces_need_draft(self):
        counts = evaluate.summarize_draft(self.kinds(box(0, 0, 0)).values())
        self.assertEqual(counts, {evaluate.INSUFFICIENT: 4, evaluate.POSITIVE: 1, evaluate.NEGATIVE: 1})

    def test_threshold(self):
        cone = Part.makeCone(10, 8, 10)  # lato a 11,31°
        counts = evaluate.summarize_draft(self.kinds(cone, min_angle=15).values())
        self.assertEqual(counts[evaluate.INSUFFICIENT], 1)

    def test_sphere_straddles(self):
        sphere = Part.makeSphere(5)
        kinds = {f.kind for f in self.kinds(sphere).values()}
        self.assertEqual(kinds, {evaluate.STRADDLE})

    def test_reversed_direction_swaps_sign(self):
        cone = Part.makeCone(10, 8, 10)
        side = [f for f in self.kinds(cone, direction=(0, 0, -1)).values() if abs(f.min_angle) < 89][0]
        self.assertEqual(side.kind, evaluate.NEGATIVE)
