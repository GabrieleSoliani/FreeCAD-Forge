# SPDX-License-Identifier: LGPL-2.1-or-later
"""M4.1: configurazioni con parametri e soppressione."""

import math
import os
import tempfile
import unittest

import FreeCAD

from ForgeTests import models
from forgelib.features import configurations as cf

HOLE = 20 * math.pi  # foro Ø4 profondo 5


class TestConfigurations(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeConfigurations")
        self.body, self.pad, self.pocket = models.block_with_hole(self.doc)
        self.cfg = cf.make_configurations(self.doc)
        cf.add_parameter(self.cfg, "Pad.Length")
        cf.add_parameter(self.cfg, "Pocket.Suppressed")
        cf.add_configuration(self.cfg, "Senza foro")
        cf.set_value(self.cfg, "Senza foro", "Pocket.Suppressed", True)
        cf.add_configuration(self.cfg, "Alto", copy_from="Standard")
        cf.set_value(self.cfg, "Alto", "Pad.Length", "20 mm")

    def tearDown(self):
        if self.doc.Name in FreeCAD.listDocuments():
            FreeCAD.closeDocument(self.doc.Name)

    def volume(self):
        return self.body.Shape.Volume

    def test_switching_configurations(self):
        self.assertEqual(self.cfg.getEnumerationsOfProperty("ActiveConfiguration"),
                         ["Standard", "Senza foro", "Alto"])
        self.assertEqual(cf.apply_configuration(self.cfg, "Senza foro", recompute=True), [])
        self.assertTrue(self.pocket.Suppressed)
        self.assertAlmostEqual(self.volume(), 2000, places=6)
        cf.apply_configuration(self.cfg, "Alto", recompute=True)
        self.assertFalse(self.pocket.Suppressed)
        self.assertAlmostEqual(self.volume(), 4000 - HOLE, places=6)
        cf.apply_configuration(self.cfg, "Standard", recompute=True)
        self.assertAlmostEqual(self.volume(), 2000 - HOLE, places=6)
        self.assertEqual(self.cfg.ActiveConfiguration, "Standard")

    def test_setting_active_property_applies(self):
        self.cfg.ActiveConfiguration = "Senza foro"
        self.doc.recompute()
        self.assertAlmostEqual(self.volume(), 2000, places=6)

    def test_capture_current_values(self):
        cf.apply_configuration(self.cfg, "Alto")
        self.pad.Length = 30
        cf.capture(self.cfg, "Alto")
        cf.apply_configuration(self.cfg, "Standard")
        self.assertAlmostEqual(float(self.pad.Length), 10, places=9)
        cf.apply_configuration(self.cfg, "Alto")
        self.assertAlmostEqual(float(self.pad.Length), 30, places=9)

    def test_expression_bound_parameter_is_reported(self):
        self.pad.setExpression("Length", "12 mm")
        errors = cf.apply_configuration(self.cfg, "Alto")
        self.assertEqual(len(errors), 1)
        self.assertIn("espressione", errors[0])

    def test_design_table_from_spreadsheet(self):
        sheet = self.doc.addObject("Spreadsheet::Sheet", "TabellaDati")
        sheet.set("B1", "Pad.Length")
        sheet.set("C1", "Pocket.Suppressed")
        sheet.set("A2", "Basso")
        sheet.set("B2", "5")
        sheet.set("C2", "true")
        self.doc.recompute()
        cf.import_design_table(self.cfg, sheet)
        cf.apply_configuration(self.cfg, "Basso", recompute=True)
        self.assertAlmostEqual(self.volume(), 1000, places=6)

    def test_errors_for_bad_parameters(self):
        with self.assertRaises(ValueError):
            cf.add_parameter(self.cfg, "Inesistente.Length")
        with self.assertRaises(ValueError):
            cf.add_parameter(self.cfg, "Pad.NonEsiste")
        with self.assertRaises(ValueError):
            cf.add_configuration(self.cfg, "Alto")

    def test_save_and_reopen_keeps_table_and_active(self):
        cf.apply_configuration(self.cfg, "Senza foro", recompute=True)
        path = os.path.join(tempfile.mkdtemp(), "configurazioni.FCStd")
        self.doc.saveAs(path)
        FreeCAD.closeDocument(self.doc.Name)
        self.doc = FreeCAD.openDocument(path)
        cfg = self.doc.getObject("Configurazioni")
        self.assertEqual(cfg.ActiveConfiguration, "Senza foro")
        self.assertTrue(self.doc.getObject("Pocket").Suppressed)
        cf.apply_configuration(cfg, "Standard", recompute=True)
        body = self.doc.getObject("Body")
        self.assertAlmostEqual(body.Shape.Volume, 2000 - HOLE, places=6)
