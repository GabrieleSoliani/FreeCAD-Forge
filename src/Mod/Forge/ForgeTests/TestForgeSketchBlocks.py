# SPDX-License-Identifier: LGPL-2.1-or-later
"""M2.3: blocchi di schizzo (salvataggio, inserimento, rimappatura dei vincoli)."""

import os
import tempfile
import unittest

import FreeCAD
import Part
import Sketcher
from FreeCAD import Vector

from ForgeTests import models
from forgelib import sketch_blocks, sketch_doctor


class TestSketchBlocks(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeBlocks")
        body = models.new_body(self.doc)
        self.source = models.add_rectangle(models.sketch_on(body, "Sorgente"), 0, 0, 20, 10)
        add = self.source.addConstraint
        add(Sketcher.Constraint("Horizontal", 0))
        add(Sketcher.Constraint("Horizontal", 2))
        add(Sketcher.Constraint("Vertical", 1))
        add(Sketcher.Constraint("Vertical", 3))
        add(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20))
        add(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, 10))
        add(Sketcher.Constraint("Coincident", 0, 1, -1, 1))  # ancoraggio all'origine: escluso
        # una geometria estranea al blocco, con un vincolo verso il rettangolo: escluso
        self.source.addGeometry(Part.Circle(Vector(40, 0, 0), Vector(0, 0, 1), 3))
        add(Sketcher.Constraint("Coincident", 4, 3, 1, 2))
        self.source.solve()
        self.target = models.sketch_on(body, "Destinazione")
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def test_block_keeps_only_internal_constraints(self):
        data = sketch_blocks.make_block(self.source, [0, 1, 2, 3], "Rettangolo")
        self.assertEqual(len(data["geometries"]), 4)
        self.assertEqual(len(data["constraints"]), 4 + 4 + 2)

    def test_save_and_insert_with_offset(self):
        path = os.path.join(self.tmp, "rettangolo.json")
        sketch_blocks.save_block(self.source, [0, 1, 2, 3], path)
        self.assertIn(path, sketch_blocks.list_blocks(self.tmp))
        data = sketch_blocks.load_block(path)
        new_ids = sketch_blocks.insert_block(self.target, data, Vector(50, 5, 0))
        self.assertEqual(new_ids, [0, 1, 2, 3])
        self.assertEqual(self.target.ConstraintCount, 10)
        state = sketch_doctor.analyze(self.target)
        self.assertTrue(state.ok, state)
        self.assertEqual(state.dof, 2)  # solo traslazione: il blocco è rigido
        start = self.target.Geometry[0].StartPoint
        self.assertAlmostEqual(start.x, 50, places=6)
        self.assertAlmostEqual(start.y, 5, places=6)
        self.assertAlmostEqual(self.target.Geometry[0].length(), 20, places=6)

    def test_insert_twice_remaps_indices(self):
        data = sketch_blocks.make_block(self.source, [0, 1, 2, 3])
        sketch_blocks.insert_block(self.target, data)
        second = sketch_blocks.insert_block(self.target, data, Vector(0, 30, 0))
        self.assertEqual(second, [4, 5, 6, 7])
        referenced = {c.First for c in self.target.Constraints[10:]}
        self.assertTrue(referenced <= {4, 5, 6, 7})
        self.assertTrue(sketch_doctor.analyze(self.target).ok)

    def test_construction_flag_and_arcs(self):
        sketch = self.target
        sketch.addGeometry(Part.ArcOfCircle(Part.Circle(Vector(0, 0, 0), Vector(0, 0, 1), 5), 0, 1.5), True)
        data = sketch_blocks.make_block(sketch, [0])
        sketch_blocks.insert_block(sketch, data, Vector(10, 0, 0))
        self.assertTrue(sketch.getConstruction(1))
        self.assertAlmostEqual(sketch.Geometry[1].Center.x, 10, places=6)
        self.assertAlmostEqual(sketch.Geometry[1].Radius, 5, places=6)

    def test_rejects_foreign_files(self):
        path = os.path.join(self.tmp, "altro.json")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write('{"format": "altro"}')
        with self.assertRaises(ValueError):
            sketch_blocks.load_block(path)
