# SPDX-License-Identifier: LGPL-2.1-or-later
"""M5: lamiera (addon SheetMetal integrato) con verifiche geometriche e tabella di piega."""

import math
import os
import tempfile
import unittest

import FreeCAD

from ForgeTests import models


def _has_sheetmetal():
    try:
        import SheetMetalCmd  # noqa: F401
    except ImportError:
        return False
    return True


@unittest.skipUnless(_has_sheetmetal(), "modulo SheetMetal non compilato")
class TestSheetMetal(unittest.TestCase):
    T = 2.0  # spessore
    R = 1.0  # raggio interno

    def setUp(self):
        from forgelib import sheetmetal

        self.sm = sheetmetal
        self.doc = FreeCAD.newDocument("ForgeSheetMetal")
        profile = self.doc.addObject("Sketcher::SketchObject", "Profilo")
        models.add_rectangle(profile, 0, 0, 100, 50)
        self.doc.recompute()
        self.base = sheetmetal.base_flange(self.doc, profile, self.T, self.R)
        self.doc.recompute()
        # spigolo superiore lungo X sul lato y=0
        self.edge = [
            f"Edge{i + 1}"
            for i, e in enumerate(self.base.Shape.Edges)
            if abs(e.CenterOfMass.y) < 1e-6 and abs(e.CenterOfMass.z - self.T) < 1e-6
        ]
        self.wall = sheetmetal.edge_flange(self.doc, self.base, self.edge, 20, self.R)
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def test_base_flange_volume(self):
        self.assertTrue(self.base.isValid(), self.base.getStatusString())
        self.assertAlmostEqual(self.base.Shape.Volume, 100 * 50 * self.T, places=6)

    def test_edge_flange_volume(self):
        self.assertEqual(len(self.edge), 1)
        self.assertTrue(self.wall.isValid(), self.wall.getStatusString())
        self.assertTrue(self.wall.Shape.isValid())
        bend = math.pi / 4 * ((self.R + self.T) ** 2 - self.R**2) * 100
        expected = 100 * 50 * self.T + 20 * self.T * 100 + bend
        self.assertAlmostEqual(self.wall.Shape.Volume, expected, places=4)

    def test_unfold_flat_length_matches_bend_table(self):
        top = [
            f"Face{i + 1}"
            for i, f in enumerate(self.wall.Shape.Faces)
            if abs(f.CenterOfMass.z - self.T) < 1e-6 and abs(f.CenterOfMass.y - 25) < 1
        ]
        flat = self.sm.unfold(self.doc, self.wall, top[0])
        self.doc.recompute()
        self.assertTrue(flat.isValid(), flat.getStatusString())
        rows = self.sm.bend_table_for_unfold(flat)
        self.assertEqual(len(rows), 1)
        bend = rows[0]
        self.assertEqual((bend.angle, bend.radius, bend.thickness), (90.0, self.R, self.T))
        self.assertAlmostEqual(bend.kfactor, self.sm.unfold_kfactor(flat), places=9)
        box = flat.Shape.BoundBox
        self.assertAlmostEqual(box.ZLength, self.T, places=6)
        # lunghezza in piano = base + ala + tolleranza di piega
        self.assertAlmostEqual(box.YLength, 50 + 20 + bend.allowance, places=3)
        self.assertAlmostEqual(
            bend.deduction, 2 * (self.R + self.T) - bend.allowance, places=9
        )
        text = self.sm.bend_table_text(rows)
        self.assertIn("Tolleranza", text.splitlines()[0])
        self.assertEqual(len(text.splitlines()), 2)

    def test_export_flat_dxf(self):
        top = [
            f"Face{i + 1}"
            for i, f in enumerate(self.wall.Shape.Faces)
            if abs(f.CenterOfMass.z - self.T) < 1e-6 and abs(f.CenterOfMass.y - 25) < 1
        ]
        flat = self.sm.unfold(self.doc, self.wall, top[0])
        self.doc.recompute()
        path = os.path.join(tempfile.mkdtemp(), "sviluppo.dxf")
        sketches = self.sm.export_flat_dxf(flat, path)
        self.assertTrue(sketches)
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        self.assertIn("ENTITIES", content)
        self.assertGreaterEqual(content.count("\nLINE"), 4)
