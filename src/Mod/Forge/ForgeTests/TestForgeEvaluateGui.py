# SPDX-License-Identifier: LGPL-2.1-or-later
"""M8 (GUI): comandi Rileva interferenze e Analisi di sformo."""

import unittest

import FreeCAD
import FreeCADGui
from FreeCAD import Vector

from forgelib import evaluate, evaluate_gui


def setUpModule():
    # i comandi Forge si registrano all'inizializzazione del workbench
    previous = FreeCADGui.activeWorkbench().name()
    FreeCADGui.activateWorkbench("ForgeWorkbench")
    FreeCADGui.activateWorkbench(previous)


class TestEvaluateGui(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("ForgeEvaluateGui")
        self.a = self.doc.addObject("Part::Box", "A")
        self.b = self.doc.addObject("Part::Box", "B")
        self.b.Placement.Base = Vector(8, 0, 0)
        self.c = self.doc.addObject("Part::Cone", "C")
        self.c.Radius1, self.c.Radius2, self.c.Height = 10, 8, 10
        self.c.Placement.Base = Vector(100, 0, 0)
        self.doc.recompute()
        FreeCADGui.Selection.clearSelection()

    def tearDown(self):
        FreeCADGui.Selection.clearSelection()
        FreeCAD.closeDocument(self.doc.Name)

    def test_interference_on_visible_solids(self):
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual([(f.first, f.second, f.kind) for f in found], [("A", "B", "interferenza")])
        group = self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP)
        self.assertIsNotNone(group)
        self.assertEqual(len(group.Group), 1)
        self.assertAlmostEqual(group.Group[0].Shape.Volume, 200, places=6)
        # una seconda esecuzione sostituisce i risultati e non conta i solidi rossi
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual(len(found), 1)
        self.assertEqual(len(self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP).Group), 1)

    def test_interference_on_selection_only(self):
        FreeCADGui.Selection.addSelection(self.a)
        FreeCADGui.Selection.addSelection(self.c)
        found = evaluate_gui.run_interference(self.doc, clearance=0)
        self.assertEqual(found, [])
        self.assertIsNone(self.doc.getObject(evaluate_gui.INTERFERENCE_GROUP))

    def test_draft_analysis_colors_and_clear(self):
        result, faces = evaluate_gui.run_draft_analysis(self.c, Vector(0, 0, 1), min_angle=1)
        self.assertEqual(len(result.ViewObject.DiffuseColor), len(self.c.Shape.Faces))
        self.assertFalse(self.c.Visibility)
        counts = evaluate.summarize_draft(faces)
        self.assertEqual(counts[evaluate.POSITIVE], 2)
        colors = [tuple(round(x, 2) for x in c[:3]) for c in result.ViewObject.DiffuseColor]
        self.assertIn(tuple(round(x, 2) for x in evaluate.DRAFT_COLORS[evaluate.NEGATIVE]), colors)
        self.assertEqual(evaluate_gui.clear_draft_analysis(self.doc), 1)
        self.assertTrue(self.c.Visibility)
        self.assertIsNone(self.doc.getObject(evaluate_gui.DRAFT_OBJECT))

    def test_commands_registered(self):
        for name in evaluate_gui.EVALUATE_COMMANDS:
            self.assertIn(name, FreeCADGui.listCommands())


class TestSketchDoctorGui(unittest.TestCase):
    def setUp(self):
        import Sketcher

        from ForgeTests import models

        self.doc = FreeCAD.newDocument("ForgeSketchDoctorGui")
        body = models.new_body(self.doc)
        self.sketch = models.add_rectangle(models.sketch_on(body, "S"), 0, 0, 20, 10)
        self.sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
        self.sketch.addConstraint(Sketcher.Constraint("Horizontal", 2))
        self.sketch.addConstraint(Sketcher.Constraint("Vertical", 1))
        self.sketch.addConstraint(Sketcher.Constraint("Vertical", 3))
        self.sketch.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 20))
        self.sketch.addConstraint(Sketcher.Constraint("DistanceX", 2, 2, 2, 1, 25))
        self.doc.recompute()
        FreeCADGui.Selection.clearSelection()
        FreeCADGui.Selection.addSelection(self.sketch)

    def tearDown(self):
        FreeCADGui.Selection.clearSelection()
        FreeCAD.closeDocument(self.doc.Name)

    def test_dialog_lists_and_applies_fix(self):
        from forgelib import sketch_doctor, sketch_doctor_gui

        self.assertIs(sketch_doctor_gui.target_sketch(), self.sketch)
        self.assertTrue(FreeCADGui.isCommandActive("Forge_SketchDoctor"))
        dialog = sketch_doctor_gui.SketchDoctorDialog(self.sketch)
        try:
            self.assertGreaterEqual(dialog.list.count(), 2)
            self.assertIn("conflitto", dialog.summary.text())
            dialog.apply_selected()
            self.assertTrue(sketch_doctor.analyze(self.sketch).ok)
            self.assertEqual(dialog.list.count(), 0)
            self.assertFalse(dialog.apply_button.isEnabled())
        finally:
            dialog.close()
            dialog.deleteLater()


class TestSketchBlocksGui(unittest.TestCase):
    def test_selection_to_geometry_ids_and_names(self):
        from ForgeTests import models
        from forgelib import sketch_blocks_gui

        doc = FreeCAD.newDocument("ForgeBlocksGui")
        try:
            body = models.new_body(doc)
            sketch = models.add_rectangle(models.sketch_on(body, "S"), 0, 0, 20, 10)
            doc.recompute()
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(sketch, ["Edge3", "Edge1", "Vertex2"])
            self.assertEqual(sketch_blocks_gui.selected_geometry_ids(sketch), [0, 2])
            self.assertEqual(sketch_blocks_gui.safe_file_name("Asola: 10/5"), "Asola 105")
            for name in sketch_blocks_gui.BLOCK_COMMANDS:
                self.assertIn(name, FreeCADGui.listCommands())
        finally:
            FreeCADGui.Selection.clearSelection()
            FreeCAD.closeDocument(doc.Name)


class TestSheetMetalGui(unittest.TestCase):
    def test_bend_table_sheet(self):
        try:
            import SheetMetalCmd  # noqa: F401
        except ImportError:
            self.skipTest("SheetMetal non compilato")
        from ForgeTests import models
        from forgelib import sheetmetal, sheetmetal_gui

        doc = FreeCAD.newDocument("ForgeSheetMetalGui")
        try:
            profile = doc.addObject("Sketcher::SketchObject", "Profilo")
            models.add_rectangle(profile, 0, 0, 100, 50)
            doc.recompute()
            base = sheetmetal.base_flange(doc, profile, 2, 1)
            doc.recompute()
            edge = [f"Edge{i + 1}" for i, e in enumerate(base.Shape.Edges)
                    if abs(e.CenterOfMass.y) < 1e-6 and abs(e.CenterOfMass.z - 2) < 1e-6]
            wall = sheetmetal.edge_flange(doc, base, edge, 20, 1)
            doc.recompute()
            top = [f"Face{i + 1}" for i, f in enumerate(wall.Shape.Faces)
                   if abs(f.CenterOfMass.z - 2) < 1e-6 and abs(f.CenterOfMass.y - 25) < 1]
            flat = sheetmetal.unfold(doc, wall, top[0])
            doc.recompute()
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(flat)
            self.assertIs(sheetmetal_gui.selected_unfold(), flat)
            self.assertTrue(FreeCADGui.isCommandActive("Forge_BendTable"))
            sheet, rows = sheetmetal_gui.make_bend_table_sheet(flat)
            self.assertEqual(sheet.get("A1"), "Feature")
            self.assertAlmostEqual(float(sheet.get("F2")), rows[0].allowance, places=3)
        finally:
            FreeCADGui.Selection.clearSelection()
            FreeCAD.closeDocument(doc.Name)


class TestStructuralGui(unittest.TestCase):
    def test_cut_list_sheet(self):
        from forgelib import structural_gui
        from forgelib.features import sketch3d, structural

        doc = FreeCAD.newDocument("ForgeStructuralGui")
        try:
            path = sketch3d.make_sketch3d(
                doc, [(0, 0, 0), (1000, 0, 0), (1000, 600, 0), (0, 600, 0)], closed=True
            )
            doc.recompute()
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(path, ["Edge1", "Edge2"])
            obj, edges = structural_gui.selected_path()
            self.assertEqual((obj, edges), (path, ["Edge1", "Edge2"]))
            member = structural.make_member(doc, path, "IPE", "100")
            doc.recompute()
            sheet, rows = structural_gui.make_cut_list_sheet(doc, [member])
            self.assertEqual(rows, 4)
            self.assertEqual(sheet.get("C2"), "IPE 100")
            total = float(sheet.get("H6"))
            self.assertAlmostEqual(total, 8.1 * 3.2, delta=0.4)
        finally:
            FreeCADGui.Selection.clearSelection()
            FreeCAD.closeDocument(doc.Name)


class TestAssemblyGui(unittest.TestCase):
    def test_insert_fastener_on_selected_hole(self):
        from forgelib import assembly_gui

        doc = FreeCAD.newDocument("ForgeAssemblyGui")
        try:
            plate = doc.addObject("Part::Feature", "Piastra")
            import Part

            plate.Shape = Part.makeBox(50, 50, 10).cut(Part.makeCylinder(4.5, 10, Vector(25, 25, 0)))
            doc.recompute()
            top = [f"Edge{i + 1}" for i, e in enumerate(plate.Shape.Edges)
                   if e.Curve.TypeId == "Part::GeomCircle" and abs(e.Curve.Center.z - 10) < 1e-9]
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(plate, top)
            edge, shape = assembly_gui.selected_circle()
            self.assertIsNotNone(edge)
            from forgelib.features import fasteners

            self.assertEqual(fasteners.size_for_hole(2 * edge.Curve.Radius), "M8")
            screw = assembly_gui.insert_fastener(doc, "ISO 4762", "M8", 30, edge, shape)
            self.assertEqual(screw.Label, "ISO 4762 M8x30")
            self.assertLess(plate.Shape.common(screw.Shape).Volume, 1e-6)
            self.assertAlmostEqual(screw.Shape.BoundBox.ZMax, 18, places=6)
            for name in assembly_gui.ASSEMBLY_COMMANDS:
                self.assertIn(name, FreeCADGui.listCommands())
        finally:
            FreeCADGui.Selection.clearSelection()
            FreeCAD.closeDocument(doc.Name)


class TestDrawingGui(unittest.TestCase):
    def test_auto_drawing_for_selection(self):
        from forgelib import drawing_gui
        from forgelib.features import fasteners

        doc = FreeCAD.newDocument("ForgeDrawingGui")
        try:
            plate = doc.addObject("Part::Box", "Piastra")
            screw = fasteners.make_fastener(doc, "ISO 4017", "M6", 20,
                                            FreeCAD.Placement(Vector(5, 5, 10), FreeCAD.Rotation()))
            doc.recompute()
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(plate)
            FreeCADGui.Selection.addSelection(screw)
            sources = drawing_gui.drawing_sources(doc)
            self.assertEqual(sources, [plate, screw])
            page, info, rows = drawing_gui.make_auto_drawing(doc, sources)
            self.assertEqual(len(rows), 2)
            balloons = [o for o in page.Views if o.TypeId == "TechDraw::DrawViewBalloon"]
            self.assertEqual(len(balloons), 2)
            self.assertEqual(page.Template.EditableTexts["document_type"], "Disegno d'assieme")
        finally:
            FreeCADGui.Selection.clearSelection()
            FreeCAD.closeDocument(doc.Name)


class TestConfigurationsGui(unittest.TestCase):
    def test_dialog_edit_and_activate(self):
        from ForgeTests import models
        from forgelib import configurations_gui
        from forgelib.features import configurations as cf

        doc = FreeCAD.newDocument("ForgeConfigurationsGui")
        try:
            body, pad, pocket = models.block_with_hole(doc)
            cfg = cf.make_configurations(doc)
            cf.add_parameter(cfg, "Pocket.Suppressed")
            cf.add_configuration(cfg, "Senza foro")
            dialog = configurations_gui.ConfigurationsDialog(cfg)
            try:
                self.assertEqual(dialog.table.rowCount(), 1)
                self.assertEqual(dialog.table.columnCount(), 2)
                dialog.table.item(0, 1).setText("true")  # salva nella tabella
                dialog.active.setCurrentText("Senza foro")
                dialog.activate_selected()
                self.assertTrue(pocket.Suppressed)
                self.assertAlmostEqual(body.Shape.Volume, 2000, places=6)
                self.assertIn("Senza foro", dialog.messages.text())
            finally:
                dialog.close()
                dialog.deleteLater()
        finally:
            FreeCAD.closeDocument(doc.Name)
