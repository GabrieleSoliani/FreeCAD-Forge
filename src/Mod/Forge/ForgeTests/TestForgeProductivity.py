# SPDX-License-Identifier: LGPL-2.1-or-later
"""M8: Pack and Go e libreria personale."""

import os
import tempfile
import unittest

import FreeCAD
import Part

from forgelib import productivity


class TestPackAndGo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "parti"))
        self.part_doc = FreeCAD.newDocument("ForgePackParte")
        box = self.part_doc.addObject("Part::Box", "Cubo")
        box.Length = 7
        self.part_doc.recompute()
        self.part_doc.saveAs(os.path.join(self.tmp, "parti", "cubo.FCStd"))
        self.main = FreeCAD.newDocument("ForgePackAssieme")
        self.main.saveAs(os.path.join(self.tmp, "assieme.FCStd"))  # i link esterni richiedono un file
        link = self.main.addObject("App::Link", "CuboLink")
        link.LinkedObject = box
        self.main.recompute()
        self.main.save()

    def tearDown(self):
        for name in list(FreeCAD.listDocuments()):
            if name.startswith("ForgePack") or name.startswith("assieme") or name.startswith("cubo"):
                FreeCAD.closeDocument(name)

    def test_pack_preserves_relative_links(self):
        target = os.path.join(tempfile.mkdtemp(), "pacchetto")
        result = productivity.pack_and_go(self.main, target)
        self.assertEqual(result.external, [])
        self.assertEqual(sorted(os.path.relpath(p, target) for p in result.copied),
                         sorted(["assieme.FCStd", os.path.join("parti", "cubo.FCStd")]))
        # si chiudono gli originali e si apre il pacchetto: il link deve risolversi nella copia
        FreeCAD.closeDocument(self.main.Name)
        FreeCAD.closeDocument(self.part_doc.Name)
        packed = FreeCAD.openDocument(os.path.join(target, "assieme.FCStd"))
        packed.recompute()
        link = packed.getObject("CuboLink")
        self.assertIsNotNone(link.LinkedObject)
        self.assertEqual(os.path.abspath(link.LinkedObject.Document.FileName),
                         os.path.abspath(os.path.join(target, "parti", "cubo.FCStd")))
        self.assertAlmostEqual(Part.getShape(link).Volume, 7 * 10 * 10, places=6)

    def test_unsaved_document_is_rejected(self):
        doc = FreeCAD.newDocument("ForgePackNonSalvato")
        try:
            with self.assertRaises(ValueError):
                productivity.pack_and_go(doc, tempfile.mkdtemp())
        finally:
            FreeCAD.closeDocument(doc.Name)


class TestLibrary(unittest.TestCase):
    def test_add_list_insert(self):
        directory = tempfile.mkdtemp()
        doc = FreeCAD.newDocument("ForgeLibrarySource")
        try:
            cyl = doc.addObject("Part::Cylinder", "Perno")
            cyl.Radius, cyl.Height = 3, 20
            doc.recompute()
            path = productivity.add_to_library(cyl, "Perno 6x20", directory)
            self.assertEqual(productivity.list_library(directory), [path])
            target = FreeCAD.newDocument("ForgeLibraryTarget")
            target.saveAs(os.path.join(directory, "..", "destinazione.FCStd"))
            try:
                link = productivity.insert_from_library(
                    target, path, FreeCAD.Placement(FreeCAD.Vector(50, 0, 0), FreeCAD.Rotation()))
                shape = Part.getShape(link)
                self.assertAlmostEqual(shape.Volume, 3.141592653589793 * 9 * 20, places=6)
                self.assertAlmostEqual(shape.BoundBox.XMin, 47, places=6)
                self.assertEqual(link.Label, "Perno 6x20")
                self.assertTrue(link.isDerivedFrom("App::Link"))
                unsaved = FreeCAD.newDocument("ForgeLibraryUnsaved")
                try:
                    copy = productivity.insert_from_library(unsaved, path)
                    self.assertFalse(copy.isDerivedFrom("App::Link"))
                    self.assertAlmostEqual(copy.Shape.Volume, 3.141592653589793 * 9 * 20, places=6)
                finally:
                    FreeCAD.closeDocument(unsaved.Name)
            finally:
                FreeCAD.closeDocument(target.Name)
                for name, d in list(FreeCAD.listDocuments().items()):
                    if os.path.abspath(d.FileName or "") == os.path.abspath(path):
                        FreeCAD.closeDocument(name)
        finally:
            FreeCAD.closeDocument(doc.Name)
