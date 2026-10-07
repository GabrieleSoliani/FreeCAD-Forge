# SPDX-License-Identifier: LGPL-2.1-or-later
"""M5.2: profilati strutturali (sezioni EN, membri con mitra, distinta di taglio)."""

import math
import unittest

import FreeCAD
import Part
from FreeCAD import Vector

from forgelib import evaluate
from forgelib.features import profiles, sketch3d, structural


class TestProfiles(unittest.TestCase):
    def test_all_sections_match_nominal_area_and_are_centered(self):
        for family in profiles.FAMILIES:
            for size in profiles.sizes(family):
                with self.subTest(profile=f"{family} {size}"):
                    face = profiles.section_face(family, size)
                    self.assertTrue(face.isValid())
                    nominal = profiles.nominal_area(family, size)
                    self.assertAlmostEqual(face.Area, nominal, delta=1e-6 * nominal)
                    self.assertAlmostEqual(face.CenterOfMass.x, 0, places=7)
                    self.assertAlmostEqual(face.CenterOfMass.y, 0, places=7)

    def test_ipe200_matches_en_table(self):
        # EN 10365: IPE 200, A = 28,5 cm²
        self.assertAlmostEqual(profiles.nominal_area("IPE", "200") / 100, 28.5, delta=0.05)
        # HEB 200: A = 78,1 cm²
        self.assertAlmostEqual(profiles.nominal_area("HEB", "200") / 100, 78.1, delta=0.05)


class TestMembers(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeStructural")

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def path(self, points, closed=False):
        obj = sketch3d.make_sketch3d(self.doc, points, closed=closed, name="Percorso")
        self.doc.recompute()
        return obj

    def member(self, path, family="IPE", size="100", **kw):
        obj = structural.make_member(self.doc, path, family, size, **kw)
        self.doc.recompute()
        self.assertTrue(obj.isValid(), obj.getStatusString())
        return obj

    def test_straight_member_volume(self):
        path = self.path([(0, 0, 0), (1000, 0, 0)])
        obj = self.member(path, "IPE", "200")
        area = profiles.nominal_area("IPE", "200")
        self.assertAlmostEqual(obj.Shape.Volume, area * 1000, delta=1e-6 * area * 1000)
        # anima verticale: altezza 200 lungo Z
        self.assertAlmostEqual(obj.Shape.BoundBox.ZLength, 200, places=6)

    def test_mitered_rectangular_frame(self):
        path = self.path([(0, 0, 0), (1000, 0, 0), (1000, 600, 0), (0, 600, 0)], closed=True)
        obj = self.member(path, "Tubo quadro/rett.", "40x40x3")
        area = profiles.nominal_area("Tubo quadro/rett.", "40x40x3")
        self.assertEqual(len(obj.Shape.Solids), 4)
        self.assertAlmostEqual(obj.Shape.Volume, area * 3200, delta=1e-6 * area * 3200)
        items = [(f"m{i}", s) for i, s in enumerate(obj.Shape.Solids)]
        overlaps = [f for f in evaluate.check_pairs(items) if f.kind == "interferenza"]
        self.assertEqual(overlaps, [])
        cuts = structural.cut_list(obj)
        self.assertEqual(sorted(round(c.centerline) for c in cuts), [600, 600, 1000, 1000])
        for item in cuts:
            self.assertAlmostEqual(item.angle_start, 45, places=6)
            self.assertAlmostEqual(item.angle_end, 45, places=6)
            # punta-punta = asse + 2 × metà larghezza del tubo (tan 45° = 1)
            self.assertAlmostEqual(item.overall, item.centerline + 40, places=6)

    def test_open_l_path_has_square_ends(self):
        path = self.path([(0, 0, 0), (500, 0, 0), (500, 300, 0)])
        obj = self.member(path, "Angolare", "50x5")
        area = profiles.nominal_area("Angolare", "50x5")
        self.assertAlmostEqual(obj.Shape.Volume, area * 800, delta=1e-6 * area * 800)
        cuts = structural.cut_list(obj)
        self.assertEqual(len(cuts), 2)
        self.assertEqual(cuts[0].angle_start, 0.0)
        self.assertAlmostEqual(cuts[0].angle_end, 45, places=6)
        self.assertEqual(cuts[1].angle_end, 0.0)

    def test_non_planar_corner(self):
        path = self.path([(0, 0, 0), (400, 0, 0), (400, 300, 200)])
        obj = self.member(path, "Tubo tondo", "48.3x3.2")
        area = profiles.nominal_area("Tubo tondo", "48.3x3.2")
        length = 400 + math.hypot(300, 200)
        self.assertAlmostEqual(obj.Shape.Volume, area * length, delta=1e-6 * area * length)

    def test_rotation_and_mass(self):
        path = self.path([(0, 0, 0), (1000, 0, 0)])
        obj = self.member(path, "IPE", "100")
        obj.Rotation = 90
        self.doc.recompute()
        self.assertAlmostEqual(obj.Shape.BoundBox.YLength, 100, places=6)  # anima ruotata in orizzontale
        mass = structural.cut_list(obj)[0].mass
        # IPE 100: 8,1 kg/m
        self.assertAlmostEqual(mass, 8.1, delta=0.1)

    def test_family_change_updates_sizes(self):
        path = self.path([(0, 0, 0), (100, 0, 0)])
        obj = self.member(path, "IPE", "100")
        obj.Family = "HEB"
        self.assertIn(obj.Size, profiles.sizes("HEB"))
        self.doc.recompute()
        self.assertTrue(obj.isValid())

    def test_curved_path_is_reported(self):
        arc = self.doc.addObject("Part::Feature", "Arco")
        arc.Shape = Part.makeCircle(100, Vector(0, 0, 0), Vector(0, 0, 1), 0, 90)
        obj = structural.make_member(self.doc, arc, "IPE", "100")
        self.doc.recompute()
        self.assertFalse(obj.isValid())
        self.assertIn("curvi", obj.getStatusString())
