# SPDX-License-Identifier: LGPL-2.1-or-later
"""M4.3: gestore unificato di equazioni e variabili globali."""

import math
import unittest

import FreeCAD

from ForgeTests import models
from forgelib import equations


class TestEquations(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeEquations")
        self.body, self.pad, self.pocket = models.block_with_hole(self.doc)

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def test_global_variable_drives_feature(self):
        equations.add_variable(self.doc, "spessore", "8 mm")
        equations.set_equation(self.pad, "Length", "Variabili.spessore * 2")
        self.assertAlmostEqual(float(self.pad.Length), 16, places=9)
        self.assertAlmostEqual(self.body.Shape.Volume, 20 * 10 * 16 - 20 * math.pi, places=6)
        # cambiando la variabile cambia il pezzo
        equations.add_variable(self.doc, "spessore", "6 mm")
        self.assertAlmostEqual(float(self.pad.Length), 12, places=9)

    def test_listing(self):
        equations.add_variable(self.doc, "foro", "5 mm")
        equations.set_equation(self.pocket, "Length", "Variabili.foro")
        listed = equations.list_equations(self.doc)
        self.assertEqual([(e.object_name, e.path, e.expression) for e in listed],
                         [("Pocket", "Length", "Variabili.foro")])
        self.assertIn("5", listed[0].value)
        variables = equations.list_variables(self.doc)
        self.assertEqual([(v.name, v.kind) for v in variables], [("foro", "variabile")])

    def test_spreadsheet_alias_is_a_variable(self):
        sheet = self.doc.addObject("Spreadsheet::Sheet", "Parametri")
        sheet.set("A1", "12")
        sheet.setAlias("A1", "lunghezza")
        self.doc.recompute()
        names = [(v.owner, v.name) for v in equations.list_variables(self.doc)]
        self.assertIn(("Parametri", "lunghezza"), names)

    def test_invalid_equation_is_rejected_without_changes(self):
        with self.assertRaises(ValueError) as ctx:
            equations.set_equation(self.pad, "Length", "Inesistente.valore + 1")
        self.assertIn("non valida", str(ctx.exception))
        self.assertEqual(list(self.pad.ExpressionEngine), [])

    def test_remove_equation(self):
        equations.set_equation(self.pad, "Length", "15 mm")
        equations.set_equation(self.pad, "Length", "")
        self.assertEqual(list(self.pad.ExpressionEngine), [])
        self.assertAlmostEqual(float(self.pad.Length), 15, places=9)

    def test_bad_variable_name(self):
        with self.assertRaises(ValueError):
            equations.add_variable(self.doc, "2nome", "1 mm")
