# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dialogo "Diagnosi schizzo" (M2)."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib import sketch_doctor
from forgelib.commands import icon_path


def target_sketch():
    """Schizzo in modifica, altrimenti il primo schizzo selezionato."""
    gdoc = FreeCADGui.ActiveDocument
    if gdoc is not None:
        vp = gdoc.getInEdit()
        if vp is not None and hasattr(vp, "Object") and vp.Object.isDerivedFrom("Sketcher::SketchObject"):
            return vp.Object
    for sel in FreeCADGui.Selection.getSelection():
        if sel.isDerivedFrom("Sketcher::SketchObject"):
            return sel
    return None


class SketchDoctorDialog(QtWidgets.QDialog):
    def __init__(self, sketch, parent=None):
        super().__init__(parent or FreeCADGui.getMainWindow())
        self.setObjectName("ForgeSketchDoctor")
        self.setWindowTitle(f"Diagnosi schizzo – {sketch.Label}")
        self.sketch = sketch
        self.fixes = []
        layout = QtWidgets.QVBoxLayout(self)
        self.summary = QtWidgets.QLabel(self)
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        layout.addWidget(QtWidgets.QLabel("Correzioni verificate (ognuna risolve il problema da sola):", self))
        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)
        buttons = QtWidgets.QHBoxLayout()
        self.apply_button = QtWidgets.QPushButton("Applica correzione", self)
        self.apply_button.clicked.connect(self.apply_selected)
        close = QtWidgets.QPushButton("Chiudi", self)
        close.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(self.apply_button)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(560, 360)
        self.refresh()

    def refresh(self):
        state, text = sketch_doctor.report(self.sketch)
        self.fixes = sketch_doctor.propose_fixes(self.sketch, state)
        self.summary.setText(text)
        self.list.clear()
        for fix in self.fixes:
            extra = "" if fix.resolves else " (restano vincoli ridondanti)"
            item = QtWidgets.QListWidgetItem(
                f"Elimina {fix.description} → gradi di libertà: {fix.dof_after}{extra}"
            )
            self.list.addItem(item)
        if self.fixes:
            self.list.setCurrentRow(0)
        self.apply_button.setEnabled(bool(self.fixes))

    def apply_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.fixes):
            sketch_doctor.apply_fix(self.sketch, self.fixes[row])
            self.refresh()


class _SketchDoctorCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_SketchDoctor"),
            "MenuText": "Diagnosi schizzo",
            "ToolTip": "Spiega vincoli in conflitto o ridondanti e propone correzioni verificate "
            "(come SketchXpert)",
        }

    def IsActive(self):
        return target_sketch() is not None

    def Activated(self):
        sketch = target_sketch()
        if sketch is None:
            return
        dialog = SketchDoctorDialog(sketch)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.open()


def register():
    FreeCADGui.addCommand("Forge_SketchDoctor", _SketchDoctorCommand())
