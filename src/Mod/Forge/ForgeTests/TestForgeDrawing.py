# SPDX-License-Identifier: LGPL-2.1-or-later
"""M7: tavola automatica, distinta con palloncini, cartiglio."""

import unittest

import FreeCAD
from FreeCAD import Vector

from forgelib import drawing
from forgelib.features import fasteners


class TestScale(unittest.TestCase):
    def test_choose_scale(self):
        self.assertEqual(drawing.choose_scale(20, 10, 10), 5)
        self.assertEqual(drawing.choose_scale(100, 60, 40), 1)
        self.assertEqual(drawing.choose_scale(400, 150, 100), 0.4)  # 1:2,5
        self.assertEqual(drawing.scale_text(0.4), "1:2.5")
        self.assertEqual(drawing.scale_text(2), "2:1")


class TestDrawing(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeDrawing")
        self.plate = self.doc.addObject("Part::Box", "Piastra")
        self.plate.Length, self.plate.Width, self.plate.Height = 120, 80, 10
        self.screws = []
        for i, x in enumerate((20, 100)):
            placement = FreeCAD.Placement(Vector(x, 40, 10), FreeCAD.Rotation())
            screw = fasteners.make_fastener(self.doc, "ISO 4762", "M8", 25, placement, name=f"Vite{i}")
            self.screws.append(screw)
        self.nut = fasteners.make_fastener(self.doc, "ISO 4032", "M8", name="Dado")
        self.nut.Placement.Base = Vector(60, 40, -10)
        self.doc.recompute()

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def test_auto_drawing_views(self):
        page, info = drawing.auto_drawing(self.doc, [self.plate])
        self.assertTrue(page.isValid(), page.getStatusString())
        self.assertEqual(page.Scale, 1)
        types = sorted(v.Type for v in info["group"].Views)
        self.assertEqual(types, ["Front", "Right", "Top"])
        self.assertEqual(info["group"].ProjectionType, "First angle")
        for view in list(info["group"].Views) + [info["iso"]]:
            self.assertTrue(view.isValid(), view.getStatusString())
            self.assertGreater(len(view.getVisibleEdges()), 0)
        front = drawing.front_view(info)
        self.assertEqual(front.Type, "Front")

    def test_bom_groups_identical_components(self):
        rows = drawing.bom_rows(self.doc.Objects)
        summary = {r.name: r.quantity for r in rows}
        self.assertEqual(summary, {"Piastra": 1, "ISO 4762 M8x25": 2, "ISO 4032 M8": 1})
        self.assertEqual([r.item for r in rows], [1, 2, 3])

    def test_bom_and_balloons_on_page(self):
        sources = [self.plate] + self.screws + [self.nut]
        page, info = drawing.auto_drawing(self.doc, sources)
        rows = drawing.bom_rows(self.doc.Objects)
        sheet, bom_view = drawing.add_bom(page, rows)
        self.assertEqual(sheet.get("B3"), "ISO 4762 M8x25")
        self.assertEqual(int(sheet.get("C3")), 2)
        self.assertTrue(bom_view.isValid(), bom_view.getStatusString())
        front = drawing.front_view(info)
        balloons = drawing.add_balloons(page, front, rows)
        self.assertEqual([b.Text for b in balloons], ["1", "2", "3"])
        half_w = (120 + 30) / 2
        for balloon in balloons:
            self.assertTrue(balloon.isValid(), balloon.getStatusString())
            self.assertLessEqual(abs(float(balloon.OriginX)), half_w)

    def test_title_block(self):
        page, _ = drawing.auto_drawing(self.doc, [self.plate])
        values = drawing.title_block_values(page, self.plate)
        written = drawing.fill_title_block(page, values)
        texts = page.Template.EditableTexts
        self.assertEqual(texts["title"], "Piastra")
        self.assertEqual(texts["scale"], "1:1")
        self.assertEqual(texts["general_tolerances"], "ISO 2768-m")
        self.assertIn("date_of_issue", written)

    def test_mirrored_source_not_counted_twice(self):
        from forgelib.features import component_pattern

        mirror = component_pattern.make_mirror(self.doc, self.plate, Vector(0, 0, 0), Vector(1, 0, 0))
        self.doc.recompute()
        names = [r.name for r in drawing.bom_rows(self.doc.Objects)]
        self.assertIn(mirror.Label, names)
        self.assertNotIn("Piastra", names)  # la sorgente è usata dalla specchiatura
