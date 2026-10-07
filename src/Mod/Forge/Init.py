# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: inizializzazione headless (nessuna dipendenza dalla GUI).

import FreeCAD

FreeCAD.__unit_test__ += [
    "ForgeTests.TestForgeApp",
    "ForgeTests.TestForgeRobustness",
    "ForgeTests.TestForgeDiagnostics",
    "ForgeTests.TestForgeExamples",
    "ForgeTests.TestForgeEvaluate",
    "ForgeTests.TestForgeSketchDoctor",
    "ForgeTests.TestForgeSketchBlocks",
    "ForgeTests.TestForgeSketch3D",
    "ForgeTests.TestForgeSheetMetal",
    "ForgeTests.TestForgeStructural",
    "ForgeTests.TestForgeFasteners",
    "ForgeTests.TestForgeComponents",
    "ForgeTests.TestForgeDrawing",
    "ForgeTests.TestForgeConfigurations",
    "ForgeTests.TestForgeRib",
    "ForgeTests.TestForgeEquations",
    "ForgeTests.TestForgeEvaluate2",
    "ForgeTests.TestForgeProductivity",
]
