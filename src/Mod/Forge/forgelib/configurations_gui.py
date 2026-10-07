# SPDX-License-Identifier: LGPL-2.1-or-later
"""Dialogo "Configurazioni" (M4.1)."""

import FreeCAD
import FreeCADGui
from PySide import QtCore, QtWidgets

from forgelib.commands import icon_path
from forgelib.features import configurations as cf


class ConfigurationsDialog(QtWidgets.QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent or FreeCADGui.getMainWindow())
        self.setObjectName("ForgeConfigurations")
        self.setWindowTitle("Configurazioni")
        self.cfg = cfg
        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Configurazione attiva:", self))
        self.active = QtWidgets.QComboBox(self)
        top.addWidget(self.active, 1)
        activate = QtWidgets.QPushButton("Attiva", self)
        activate.clicked.connect(self.activate_selected)
        top.addWidget(activate)
        layout.addLayout(top)
        self.table = QtWidgets.QTableWidget(self)
        layout.addWidget(self.table, 1)
        buttons = QtWidgets.QHBoxLayout()
        for text, slot in (
            ("Nuova configurazione…", self.new_configuration),
            ("Aggiungi parametro…", self.new_parameter),
            ("Cattura valori correnti", self.capture_current),
            ("Importa tabella dati", self.import_table),
        ):
            button = QtWidgets.QPushButton(text, self)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.messages = QtWidgets.QLabel("", self)
        self.messages.setWordWrap(True)
        layout.addWidget(self.messages)
        close = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close, parent=self)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.resize(640, 380)
        self.refresh()

    def refresh(self):
        data = cf.Configurations.data(self.cfg)
        self.active.clear()
        self.active.addItems(data["configs"])
        self.active.setCurrentText(self.cfg.ActiveConfiguration)
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setColumnCount(len(data["configs"]))
        self.table.setRowCount(len(data["params"]))
        self.table.setHorizontalHeaderLabels(data["configs"])
        self.table.setVerticalHeaderLabels(data["params"])
        for r, param in enumerate(data["params"]):
            for c, config in enumerate(data["configs"]):
                value = data["values"].get(config, {}).get(param, "")
                self.table.setItem(r, c, QtWidgets.QTableWidgetItem(str(value)))
        self.table.blockSignals(False)
        try:
            self.table.itemChanged.disconnect(self.cell_changed)
        except (RuntimeError, TypeError):
            pass
        self.table.itemChanged.connect(self.cell_changed)

    def cell_changed(self, item):
        data = cf.Configurations.data(self.cfg)
        config = data["configs"][item.column()]
        param = data["params"][item.row()]
        cf.set_value(self.cfg, config, param, item.text())

    def activate_selected(self):
        doc = self.cfg.Document
        doc.openTransaction("Configurazione")
        try:
            errors = cf.apply_configuration(self.cfg, self.active.currentText(), recompute=True)
        finally:
            doc.commitTransaction()
        self.messages.setText("\n".join(errors) if errors else
                              f"Configurazione \"{self.cfg.ActiveConfiguration}\" attiva.")

    def new_configuration(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Nuova configurazione", "Nome:")
        if ok and name.strip():
            try:
                cf.add_configuration(self.cfg, name.strip())
            except ValueError as err:
                self.messages.setText(str(err))
            self.refresh()

    def new_parameter(self):
        suggestion = ""
        selection = FreeCADGui.Selection.getSelection()
        if selection:
            suggestion = selection[0].Name + ".Suppressed"
        param, ok = QtWidgets.QInputDialog.getText(
            self, "Aggiungi parametro", "Parametro (Oggetto.Proprietà, es. Pad.Length):",
            QtWidgets.QLineEdit.Normal, suggestion)
        if ok and param.strip():
            try:
                cf.add_parameter(self.cfg, param.strip())
            except ValueError as err:
                self.messages.setText(str(err))
            self.refresh()

    def capture_current(self):
        cf.capture(self.cfg, self.active.currentText())
        self.refresh()

    def import_table(self):
        sheets = [o for o in FreeCADGui.Selection.getSelection() if o.isDerivedFrom("Spreadsheet::Sheet")]
        if not sheets:
            self.messages.setText("Selezionare prima un foglio di calcolo con la tabella dati.")
            return
        cf.import_design_table(self.cfg, sheets[0])
        self.refresh()


class _ConfigurationsCommand:
    def GetResources(self):
        return {
            "Pixmap": icon_path("Forge_Configurations"),
            "MenuText": "Configurazioni",
            "ToolTip": "Gestisce le configurazioni del documento: valori dei parametri e "
            "soppressione delle feature per configurazione, tabella dati da foglio di calcolo",
        }

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

    def Activated(self):
        doc = FreeCAD.ActiveDocument
        cfg = cf.make_configurations(doc)
        dialog = ConfigurationsDialog(cfg)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        dialog.open()


def register():
    FreeCADGui.addCommand("Forge_Configurations", _ConfigurationsCommand())
