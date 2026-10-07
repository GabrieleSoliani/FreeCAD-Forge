# SPDX-License-Identifier: LGPL-2.1-or-later
"""Genera i modelli di riferimento di Forge come file .FCStd in questa cartella.

Uso (dalla radice del repository):
    pixi run build/relWithDebInfo/bin/FreeCADCmd.exe forge_examples/genera_esempi.py
"""

import os

import FreeCAD

from ForgeTests import examples

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if not os.path.isfile(os.path.join(HERE, "genera_esempi.py")):
    HERE = os.path.join(os.getcwd(), "forge_examples")

for key, build in examples.EXAMPLES.items():
    doc = FreeCAD.newDocument(key)
    result = build(doc)
    shape = result["body"].Shape
    status = "ok" if shape.isValid() and all(o.isValid() for o in doc.Objects) else "ERRORE"
    path = os.path.join(HERE, key + ".FCStd")
    doc.saveAs(path)
    FreeCAD.Console.PrintMessage(f"{key}: {status}, volume {shape.Volume:.2f} mm3 -> {path}\n")
    FreeCAD.closeDocument(doc.Name)
