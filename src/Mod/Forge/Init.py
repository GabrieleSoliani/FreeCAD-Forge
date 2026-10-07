# SPDX-License-Identifier: LGPL-2.1-or-later
# FreeCAD Forge: inizializzazione headless (nessuna dipendenza dalla GUI).

import FreeCAD

FreeCAD.__unit_test__ += [
    "ForgeTests.TestForgeApp",
    "ForgeTests.TestForgeRobustness",
    "ForgeTests.TestForgeDiagnostics",
    "ForgeTests.TestForgeExamples",
]
