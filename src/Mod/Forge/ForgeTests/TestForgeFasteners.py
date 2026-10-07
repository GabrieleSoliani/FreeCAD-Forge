# SPDX-License-Identifier: LGPL-2.1-or-later
"""M6.1: toolbox di viteria ISO."""

import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib.features import fasteners


class TestFasteners(unittest.TestCase):
    def test_all_shapes_valid_with_expected_volume(self):
        for kind in fasteners.TYPES:
            for size in fasteners.SIZES:
                with self.subTest(item=f"{kind} {size}"):
                    shape = fasteners.fastener_shape(kind, size, 30)
                    self.assertTrue(shape.isValid())
                    self.assertEqual(len(shape.Solids), 1)
                    expected = fasteners.expected_volume(kind, size, 30)
                    self.assertAlmostEqual(shape.Volume, expected, delta=1e-6 * expected)

    def test_m8_socket_head_dimensions(self):
        shape = fasteners.fastener_shape("ISO 4762", "M8", 40)
        box = shape.BoundBox
        self.assertAlmostEqual(box.XLength, 13, places=6)  # dk
        self.assertAlmostEqual(box.ZMax, 8, places=6)  # k
        self.assertAlmostEqual(box.ZMin, -40, places=6)  # lunghezza sotto testa

    def test_feature_and_designation(self):
        doc = FreeCAD.newDocument("ForgeFasteners")
        try:
            screw = fasteners.make_fastener(doc, "ISO 4017", "M10", 35)
            doc.recompute()
            self.assertTrue(screw.isValid())
            self.assertEqual(screw.Designation, "ISO 4017 M10x35")
            screw.Standard = "ISO 4032"
            doc.recompute()
            self.assertEqual(screw.Designation, "ISO 4032 M10")
        finally:
            FreeCAD.closeDocument(doc.Name)

    def test_placement_on_hole_edge(self):
        plate = Part.makeBox(50, 50, 10).cut(Part.makeCylinder(3.3, 10, Vector(20, 30, 0)))
        top_edges = [e for e in plate.Edges if isinstance(e.Curve, Part.Circle)
                     and abs(e.Curve.Center.z - 10) < 1e-9]
        self.assertEqual(len(top_edges), 1)
        placement = fasteners.placement_on_circle(top_edges[0], plate)
        self.assertTrue(placement.Base.isEqual(Vector(20, 30, 10), 1e-9))
        self.assertAlmostEqual(placement.Rotation.multVec(Vector(0, 0, 1)).z, 1, places=9)
        self.assertEqual(fasteners.size_for_hole(6.6), "M6")
        screw = fasteners.fastener_shape("ISO 4762", "M6", 20)
        screw.Placement = placement
        # testa sopra la piastra, gambo Ø6 nel foro Ø6,6: nessuna compenetrazione
        self.assertLess(plate.common(screw).Volume, 1e-6)
        self.assertAlmostEqual(screw.BoundBox.ZMax, 16, places=6)
        # sulla faccia inferiore l'asse punta verso il basso
        bottom = [e for e in plate.Edges if isinstance(e.Curve, Part.Circle) and abs(e.Curve.Center.z) < 1e-9][0]
        down = fasteners.placement_on_circle(bottom, plate)
        self.assertAlmostEqual(down.Rotation.multVec(Vector(0, 0, 1)).z, -1, places=9)

    def test_size_for_hole(self):
        self.assertEqual(fasteners.size_for_hole(9), "M8")
        self.assertEqual(fasteners.size_for_hole(8.05), "M6")
        self.assertIsNone(fasteners.size_for_hole(2.5))
