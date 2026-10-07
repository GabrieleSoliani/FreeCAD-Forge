# SPDX-License-Identifier: LGPL-2.1-or-later
"""M3.3: i modelli di riferimento si costruiscono senza errori e con il volume atteso."""

import time
import unittest

import FreeCAD

from ForgeTests import examples
from forgelib import diagnostics


class TestForgeExamples(unittest.TestCase):
    timings = {}

    def _check(self, key):
        doc = FreeCAD.newDocument("ForgeExample_" + key)
        try:
            result = examples.EXAMPLES[key](doc)
            start = time.perf_counter()
            for obj in doc.Objects:
                obj.touch()
            doc.recompute()
            TestForgeExamples.timings[key] = time.perf_counter() - start
            body = result["body"]
            invalid = [o.Name for o in doc.Objects if not o.isValid()]
            self.assertEqual(invalid, [])
            self.assertEqual(diagnostics.diagnose(doc), [])
            shape = body.Shape
            self.assertTrue(shape.isValid())
            self.assertEqual(len(shape.Solids), result.get("solids", 1))
            if result["volume"] is not None:
                tolerance = result.get("tolerance", 1e-6)
                self.assertAlmostEqual(shape.Volume, result["volume"], delta=tolerance * result["volume"])
        finally:
            FreeCAD.closeDocument(doc.Name)

    def test_flangia(self):
        self._check("flangia")

    def test_staffa_a_L(self):
        self._check("staffa_a_L")

    def test_albero_a_gradini(self):
        self._check("albero_a_gradini")

    def test_scatola_con_guscio(self):
        self._check("scatola_con_guscio")

    def test_molla(self):
        self._check("molla")

    def test_telaio_saldato(self):
        self._check("telaio_saldato")

    def test_staffa_lamiera(self):
        try:
            import SheetMetalCmd  # noqa: F401
        except ImportError:
            self.skipTest("SheetMetal non compilato")
        self._check("staffa_lamiera")

    @classmethod
    def tearDownClass(cls):
        if cls.timings:
            text = ", ".join(f"{k} {v * 1000:.0f} ms" for k, v in sorted(cls.timings.items()))
            FreeCAD.Console.PrintMessage(f"Forge: tempi di ricalcolo completo: {text}\n")
