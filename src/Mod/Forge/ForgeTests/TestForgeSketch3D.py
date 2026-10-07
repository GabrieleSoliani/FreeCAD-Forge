# SPDX-License-Identifier: LGPL-2.1-or-later
"""M2.4: schizzo 3D ridotto (polilinea/spline 3D come percorso)."""

import math
import os
import tempfile
import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib.features import sketch3d


class TestSketch3D(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeSketch3D")

    def tearDown(self):
        if self.doc.Name in FreeCAD.listDocuments():
            FreeCAD.closeDocument(self.doc.Name)

    def make(self, points, **kw):
        obj = sketch3d.make_sketch3d(self.doc, points, **kw)
        self.doc.recompute()
        return obj

    def test_open_polyline_length(self):
        obj = self.make([(0, 0, 0), (10, 0, 0), (10, 10, 5)])
        self.assertTrue(obj.isValid())
        self.assertAlmostEqual(obj.Shape.Length, 10 + math.hypot(10, 5), places=9)
        self.assertFalse(obj.Shape.isClosed())

    def test_closed_square(self):
        obj = self.make([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], closed=True)
        self.assertTrue(obj.Shape.isClosed())
        self.assertAlmostEqual(obj.Shape.Length, 40, places=9)

    def test_bend_radius(self):
        obj = self.make([(0, 0, 0), (10, 0, 0), (10, 10, 0)], bend_radius=2)
        self.assertAlmostEqual(obj.Shape.Length, 16 + math.pi, places=9)
        self.assertEqual(len(obj.Shape.Edges), 3)

    def test_bend_radius_on_closed_3d_path(self):
        points = [(0, 0, 0), (20, 0, 0), (20, 20, 10), (0, 20, 10)]
        obj = self.make(points, closed=True, bend_radius=3)
        self.assertTrue(obj.isValid(), obj.getStatusString())
        self.assertTrue(obj.Shape.isClosed())
        self.assertEqual(len(obj.Shape.Edges), 8)

    def test_bend_radius_too_large_is_an_error(self):
        obj = self.make([(0, 0, 0), (2, 0, 0), (2, 2, 0)], bend_radius=5)
        self.assertFalse(obj.isValid())
        self.assertIn("Raggio di raccordo troppo grande", obj.getStatusString())

    def test_spline_passes_through_points(self):
        points = [(0, 0, 0), (10, 5, 2), (20, 0, 8), (30, -5, 0)]
        obj = self.make(points, mode="Spline")
        for p in points:
            self.assertLess(obj.Shape.distToShape(Part.Vertex(Vector(*p)))[0], 1e-7)

    def test_too_few_points(self):
        obj = self.make([(0, 0, 0)])
        self.assertFalse(obj.isValid())
        self.assertIn("almeno 2 punti", obj.getStatusString())

    def test_sweep_along_bent_path(self):
        obj = self.make([(0, 0, 0), (30, 0, 0), (30, 30, 0)], bend_radius=5)
        path = obj.Shape
        circle = Part.Wire([Part.makeCircle(1, Vector(0, 0, 0), Vector(1, 0, 0))])
        sweep = path.makePipeShell([circle], True, True)
        self.assertTrue(sweep.isValid())
        # Pappus: volume = area della sezione × lunghezza del percorso (anche sull'arco)
        self.assertAlmostEqual(sweep.Volume, math.pi * path.Length, delta=1e-3 * sweep.Volume)

    def test_save_and_reopen(self):
        self.make([(0, 0, 0), (10, 0, 0), (10, 10, 5)], mode="Spline")
        path = os.path.join(tempfile.mkdtemp(), "schizzo3d.FCStd")
        self.doc.saveAs(path)
        FreeCAD.closeDocument(self.doc.Name)
        self.doc = FreeCAD.openDocument(path)
        obj = self.doc.getObject("Schizzo3D")
        obj.touch()
        self.doc.recompute()
        self.assertTrue(obj.isValid())
        self.assertEqual(len(obj.Points), 3)
        self.assertEqual(obj.Mode, "Spline")
