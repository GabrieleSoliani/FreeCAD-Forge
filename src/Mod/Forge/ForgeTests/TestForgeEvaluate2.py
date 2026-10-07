# SPDX-License-Identifier: LGPL-2.1-or-later
"""M8: analisi di spessore e confronto tra versioni."""

import unittest

import Part
from FreeCAD import Vector

from forgelib import evaluate


class TestThickness(unittest.TestCase):
    def setUp(self):
        # piastra 60×40×10 con una costola alta 20 e spessa 1 sopra
        plate = Part.makeBox(60, 40, 10)
        rib = Part.makeBox(1, 40, 20, Vector(30, 0, 10))
        self.shape = plate.fuse(rib).removeSplitter()

    def test_local_thickness_of_plate(self):
        t = evaluate.local_thickness(self.shape, Vector(10, 20, 10), Vector(0, 0, 1), 200)
        self.assertAlmostEqual(t, 10, places=6)

    def test_thin_rib_faces_flagged(self):
        faces = evaluate.thickness_analysis(self.shape, minimum=2)
        thin = [f for f in faces if f.kind == evaluate.THIN]
        # le due facce laterali grandi della costola (spessore 1) sono sottili
        self.assertGreaterEqual(len(thin), 2)
        for face in thin:
            self.assertLess(face.minimum, 2)
        def is_rib_side(face):
            u0, u1, v0, v1 = face.ParameterRange
            normal = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
            return abs(abs(normal.x) - 1) < 1e-9 and 29.9 < face.CenterOfMass.x < 31.1

        rib_sides = [f for f in faces if is_rib_side(self.shape.Faces[f.index - 1])]
        self.assertEqual(len(rib_sides), 2)
        for face in rib_sides:
            self.assertEqual(face.kind, evaluate.THIN)
            self.assertAlmostEqual(face.minimum, 1, places=6)

    def test_thick_block_has_no_thin_faces(self):
        faces = evaluate.thickness_analysis(Part.makeBox(30, 30, 30), minimum=2)
        self.assertEqual({f.kind for f in faces}, {evaluate.THICK})
        self.assertEqual(len(faces), 6)


class TestCompare(unittest.TestCase):
    def test_added_and_removed_material(self):
        old = Part.makeBox(20, 10, 10)
        new = Part.makeBox(20, 10, 10).cut(Part.makeCylinder(2, 10, Vector(10, 5, 0)))
        new = new.fuse(Part.makeBox(5, 10, 10, Vector(20, 0, 0)))
        result = evaluate.compare_shapes(old, new)
        self.assertAlmostEqual(result.added_volume, 500, places=6)
        self.assertAlmostEqual(result.removed_volume, 3.141592653589793 * 4 * 10, places=6)
        self.assertFalse(result.identical)

    def test_identical(self):
        self.assertTrue(evaluate.compare_shapes(Part.makeBox(5, 5, 5), Part.makeBox(5, 5, 5)).identical)
