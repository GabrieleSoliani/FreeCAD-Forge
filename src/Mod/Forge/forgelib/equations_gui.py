# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dialogo "Equazioni" (M4.3): tutte le espressioni e le variabili globali in un'unica finestra."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib import equations
from forgelib.commands import icon_path


class EquationsDialog(QtWidgets.QDialog):
    def __init__(self, doc, parent=None):
        super().__init__(parent or FreeCADGui.getMainWindow())
        self.setObjectName("ForgeEquations")
        self.setWindowTitle("Equazioni e variabili globali")
        self.doc = doc
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Variabili globali", self))
        self.variables = QtWidgets.QTableWidget(0, 3, self)
        self.variables.setHorizontalHeaderLabels(["Nome", "Valore", "Tipo"])
        self.variables.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.variables)
        add_var = QtWidgets.QPushButton("Nuova variabile globale…", self)
        add_var.clicked.connect(self.new_variable)
        layout.addWidget(add_var)
        layout.addWidget(QtWidgets.QLabel("Equazioni (modificare la colonna Equazione; vuota = rimuove)", self))
        self.table = QtWidgets.QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Oggetto", "Proprietà", "Equazione", "Valore"])
        layout.addWidget(self.table, 1)
        self.messages = QtWidgets.QLabel("", self)
        self.messages.setWordWrap(True)
        layout.addWidget(self.messages)
        close = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, parent=self)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.resize(680, 480)
        self.table.itemChanged.connect(self.equation_changed)
        self.refresh()

    def refresh(self):
        self.table.blockSignals(True)
        self.rows = equations.list_equations(self.doc)
        self.table.setRowCount(len(self.rows))
        for r, eq in enumerate(self.rows):
            for c, text in enumerate((eq.label, eq.path, eq.expression, eq.value)):
                item = QtWidgets.QTableWidgetItem(text)
                if c != 2:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.blockSignals(False)
        variables = equations.list_variables(self.doc)
        self.variables.setRowCount(len(variables))
        for r, var in enumerate(variables):
            for c, text in enumerate((var.name, var.value, var.kind)):
                self.variables.setItem(r, c, QtWidgets.QTableWidgetItem(text))

    def equation_changed(self, item):
        if item.column() != 2:
            return
        eq = self.rows[item.row()]
        obj = self.doc.getObject(eq.object_name)
        self.doc.openTransaction("Equazione")
        try:
            equations.set_equation(obj, eq.path, item.text())
            self.messages.setText(f"{eq.label}.{eq.path} aggiornata.")
        except ValueError as err:
            self.messages.setText(str(err))
        finally:
            self.doc.commitTransaction()
        QtCore.QTimer.singleShot(0, self.refresh)

    def new_variable(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Nuova variabile", "Nome (senza spazi):")
        if not ok or not name.strip():
            return
        value, ok = QtWidgets.QInputDialog.getText(self, "Nuova variabile", "Valore (es. 10 mm):")
        if not ok:
            return
        try:
            equations.add_variable(self.doc, name.strip(), value.strip() or "0 mm")
            self.messages.setText(f"Usare nelle equazioni: Variabili.{name.strip()}")
        except (ValueError, Exception) as err:
            self.messages.setText(str(err))
        self.refresh()


class _EquationsCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_Equations"),
            "MenuText": "Equazioni",
            "ToolTip": "Tutte le equazioni del documento e le variabili globali in un'unica tabella",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        dialog = EquationsDialog(FreeCAD.ActiveDocument)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.open()


def register():
    FreeCADGui.addCommand("Forge_Equations", _EquationsCommand())
