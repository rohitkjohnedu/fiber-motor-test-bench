import datetime
import json
import logging
import os
import sys
from pathlib import Path

from PyQt6 import QtCore, QtWidgets, QtGui


class DictDialog(QtWidgets.QDialog):
    def __init__(self, user_fields=[], parent = None, auto_save_file=None):
        super(DictDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.button_groups = dict({})
        self.widgets = []
        self.user_fields = user_fields
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.main_widget = SettingsWidget(parent=self.scroll_area, user_fields=self.user_fields, auto_save_file=auto_save_file)
        self.scroll_area.setWidget(self.main_widget)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.scroll_area)
        self.main_widget.show()
        save_load_layout = QtWidgets.QHBoxLayout()
        save_button = QtWidgets.QPushButton('Save')
        save_button.clicked.connect(self._save_button_callback)
        load_button = QtWidgets.QPushButton('Load')
        load_button.clicked.connect(self._load_button_callback)
        save_load_layout.addWidget(save_button)
        save_load_layout.addWidget(load_button)
        self.main_layout.addLayout(save_load_layout)

        ok_button = QtWidgets.QPushButton('&Ok')
        ok_button.clicked.connect(self.accept)
        cancel_button = QtWidgets.QPushButton('&Cancel')
        cancel_button.clicked.connect(self.reject)
        ok_cancel_layout = QtWidgets.QHBoxLayout()
        ok_cancel_layout.addWidget(ok_button)
        ok_cancel_layout.addWidget(cancel_button)
        self.main_layout.addLayout(ok_cancel_layout)

    def _save_button_callback(self):
        file = QtWidgets.QFileDialog.getSaveFileName(self, caption="Save values", directory=os.getcwd())
        if file[0]:
            self.main_widget.save_values(file[0])

    def _load_button_callback(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, caption="Load values", directory=os.getcwd())
        if file[0]:
            self.main_widget.load_values(file[0])

    def generate_dialog(self):
        self.main_widget.generate()

    def clear_dialog(self):
        self.main_widget.clear_widget()

    def save_dialog(self, filename, updated_values=False):
        self.main_widget.save_widget(filename, updated_values)

    def load_dialog(self, filename):
        self.clear_dialog()
        self.user_fields = json.load(open(filename, "r"))
        self.generate_dialog()

    def accept(self):
        super(DictDialog, self).accept()

    def reject(self):
        super(DictDialog, self).reject()

    def get_input(self):
        return self.main_widget.get_values()

    def set_fields_values(self, values_dict):
        self.main_widget.set_fields_values(values_dict)
        self.clear_dialog()
        self.generate_dialog()

    def save_input(self, filename):
        self.main_widget.save_values(filename)


class SettingsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, user_fields=[], auto_save_file=None):
        super(SettingsWidget, self).__init__(parent)
        self.button_groups = dict({})
        self.widgets = []
        self.user_fields = user_fields
        self.main_layout = QtWidgets.QFormLayout(self)
        if auto_save_file:
            self.auto_load_file = Path(auto_save_file)
            if self.auto_load_file.exists():
                self.load_values(str(self.auto_load_file))
        else:
            self.auto_load_file = None

    def generate(self):
        self.clear_widget()
        self.widgets = []
        self.button_groups = dict({})
        for i, field in enumerate(self.user_fields):
            if isinstance(field, dict):
                if "value" in field:
                    if field["value"] is None:
                        field["value"] = ""
                    if type(field["value"]) is float:
                        field["value"] = "%.4f" % field["value"]
                    if type(field["value"]) is int:
                        field["value"] = "%d" % field["value"]
                if field["type"] == "date":
                    date_edit = QtWidgets.QDateEdit()
                    if "value" in field:
                        date_edit.setDate(datetime.datetime.strptime(field["value"], "%d/%m/%Y"))
                    self.widgets.append(date_edit)
                elif field["type"] == "line_edit":
                    line_edit = QtWidgets.QLineEdit()
                    if "placeholder" in field:
                        line_edit.setPlaceholderText(field["placeholder"])
                    if "value" in field:
                        line_edit.setText(field["value"])
                    self.widgets.append(line_edit)
                elif field["type"] == "text_edit":
                    text_edit = QtWidgets.QTextEdit()
                    if "placeholder" in field:
                        text_edit.setPlaceholderText(field["placeholder"])
                    if "value" in field:
                        text_edit.setText(field["value"])
                    self.widgets.append(text_edit)
                elif field["type"] == "radio":
                    button_name = field["options"].split(",")
                    hlayout = QtWidgets.QHBoxLayout()
                    self.button_groups[field["name"]] = QtWidgets.QButtonGroup(self)
                    for j in range(len(button_name)):
                        button = QtWidgets.QRadioButton(button_name[j])
                        self.button_groups[field["name"]].addButton(button)
                        hlayout.addWidget(button)
                    self.widgets.append(hlayout)
                elif field["type"] == "grade_question":
                    slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
                    if "tooltip" in field:
                        slider.setToolTip(field["tooltip"])
                    slider.setMinimum(0)
                    slider.setMaximum(10)
                    if "value" in field:
                        slider.setValue(int(field["value"]))
                    slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
                    if "slider_label" in field:
                        slider_layout = QtWidgets.QHBoxLayout()
                        slider_layout.addWidget(QtWidgets.QLabel(field["slider_label"][0]))
                        slider_layout.addWidget(slider)
                        slider_layout.addWidget(QtWidgets.QLabel(field["slider_label"][1]))
                        self.widgets.append(slider_layout)

                    else:
                        self.widgets.append(slider)
                elif field["type"] == "checkbox":
                    checkbox = QtWidgets.QCheckBox()
                    checkbox.setChecked(field["value"])
                    self.widgets.append(checkbox)
                elif field["type"] == "folder":
                    browse_layout = QtWidgets.QHBoxLayout()
                    path_edit = QtWidgets.QLineEdit(field["value"])
                    browse_layout.addWidget(path_edit)
                    browse_button = QtWidgets.QPushButton("")
                    browse_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                    browse_button.clicked.connect(self._browse_button_callback)
                    browse_layout.addWidget(browse_button)
                    self.widgets.append(browse_layout)
                elif field["type"] == "combobox":
                    selections = field["options"].split(",")
                    widget = QtWidgets.QComboBox()
                    widget.addItems(selections)
                    widget.setCurrentText(field["value"])
                    self.widgets.append(widget)

                if "tooltip" in field and not field["type"] in ["grade_question", "radio"]:
                    self.widgets[i].setToolTip(field["tooltip"])
                self.main_layout.addRow(field["label"], self.widgets[i])
            else:
                self.main_layout.addRow(field)

    def _browse_button_callback(self):
        widget = self.sender()
        for wid in self.widgets:
            if isinstance(wid, QtWidgets.QHBoxLayout):
                if wid.itemAt(1).widget() == widget:
                    folder_edit = wid.itemAt(0).widget()
                    break
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder", folder_edit.text())
        if folder:
            folder_edit.setText(folder)

    def clear_widget(self):
        for i in reversed(range(self.main_layout.count())):
            if isinstance(self.main_layout.itemAt(i), QtWidgets.QHBoxLayout):
                for j in reversed(range(self.main_layout.itemAt(i).count())):
                    self.main_layout.itemAt(i).itemAt(j).widget().setParent(None)
                self.main_layout.itemAt(i).setParent(None)
            else:
                self.main_layout.itemAt(i).widget().setParent(None)

    def save_widget(self, filename, updated_values=False):
        if updated_values:
            results = self.get_values()
            for i, field in enumerate(self.user_fields):
                field["value"] = results["value"]
        json.dump(self.user_fields, open(filename, "w"), indent=4)

    def load_widget(self, filename):
        self.clear_widget()
        self.user_fields = json.load(open(filename, "r"))
        self.generate()

    def get_values(self):
        results = dict({})
        for i, field in enumerate(self.user_fields):
            if isinstance(field, dict):
                if field["type"] == "date":
                    date = self.widgets[i].date()
                    py_date = date.toPyDate()
                    results[field["name"]] = py_date.strftime("%d/%m/%Y")
                elif field["type"] == "line_edit":
                    results[field["name"]] = self.widgets[i].text()
                elif field["type"] == "text_edit":
                    results[field["name"]] = self.widgets[i].toPlainText()
                elif field["type"] == "radio":
                    checked_button = self.button_groups[field["name"]].checkedButton()
                    if checked_button:
                        results[field["name"]] = checked_button.text()
                    else:
                        results[field["name"]] = None
                elif field["type"] == "grade_question":
                    if "slider_label" in field:
                        results[field["name"]] = self.widgets[i].itemAt(1).widget().value()
                    else:
                        results[field["name"]] = self.widgets[i].value()
                elif field["type"] == "checkbox":
                    results[field["name"]] = self.widgets[i].isChecked()
                elif field["type"] == "folder":
                    results[field["name"]] = self.widgets[i].itemAt(0).widget().text()
                elif field["type"] == "combobox":
                    results[field["name"]] = self.widgets[i].currentText()
        return results

    def set_fields_values(self, values_dict):
        for value_name in values_dict.keys():
            for i, field in enumerate(self.user_fields):
                if isinstance(field, dict):
                    if field["name"] == value_name:
                        field["value"] = values_dict[value_name]
        self.clear_widget()
        self.generate()

    def load_values(self, filename):
        values = json.load(open(filename, "r"))
        self.set_fields_values(values)

    def save_values(self, filename):
        results = self.get_values()
        json.dump(results, open(filename, "w"), indent=4)

    def hideEvent(self, e):
        if self.auto_load_file is not None:
            self.save_values(self.auto_load_file)
        e.accept()


def get_application_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.getcwd()
    return application_path


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS).joinpath(relative_path).resolve().absolute().as_posix()
    return Path(__file__).parent.joinpath(relative_path).resolve().absolute().as_posix()


def create_qt_app_from_widget(app, widget, appname="LMTS app"):
    app.aboutToQuit.connect(app.deleteLater)
    app.setApplicationName(appname)
    app.setWindowIcon(QtGui.QIcon(resource_path("../../assets/EPFL_icon.ico")))
    widget.setWindowTitle(appname)
    widget.setWindowIcon(QtGui.QIcon(resource_path("../../assets/EPFL_icon.ico")))
    widget.show()
    sys.exit(app.exec())
    return app

class QPlainTextEditLogger(logging.Handler):
    """
    Class to redirect logging output to QtWidget.
    """

    def __init__(self, parent=None):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


if __name__ == '__main__':
    DIALOG_PARAMETERS = [{
        "name": "name",
        "label": "Experiment Name",
        "type": "line_edit",
        "value": "Experiment"
        }, {
        "name": "amplitudes",
        "label": "Voltages",
        "type": "line_edit",
        "value": "100,200,300"
        }, {
        "name": "amplitudes_for_mod",
        "label": "Voltages for modulation",
        "type": "line_edit",
        "value": "100,200,300"
        }, {
        "name": "frequencies",
        "label": "Switching frequencies",
        "type": "line_edit",
        "value": "200"
        }, {
        "name": "base_frequency",
        "label": "Main frequency",
        "type": "line_edit",
        "value": "200"
        }, {
        "name": "modulation_frequencies",
        "label": "Modulation frequencies",
        "type": "line_edit",
        "value": "1,2,10,20"
        }, {
        "name": "time_point",
        "label": "Time (s)",
        "type": "line_edit",
        "value": "10"
        }, {
        "name": "time_before_after",
        "label": "Time before/after (s)",
        "type": "line_edit",
        "value": "5"
        }, {
        "name": "n_repetitions",
        "label": "Number of repetitions",
        "type": "line_edit",
        "value": "3"
        }, {
        "name": "n_sig_repetitions",
        "label": "Number of signal activation",
        "type": "line_edit",
        "value": "3"
        }, {
        "name": "stiffness_interval",
        "label": "Stiffness mesurement interval",
        "type": "line_edit",
        "value": "5"
        }, {
        "name": "indentation_force",
        "label": "Indentation force",
        "type": "line_edit",
        "value": "3"
        }, {
        "name": "indentation_range",
        "label": "Indentation range",
        "type": "line_edit",
        "value": "0.5"
        }, {
        "name": "indentation_speed",
        "label": "Indentation speed",
        "type": "line_edit",
        "value": "0.05"
        }, {
        "name": "voltage_indentation",
        "label": "Voltages for indentation",
        "type": "line_edit",
        "value": "1000"
        }, {
        "name": "record_video",
        "label": "Capture video",
        "type": "checkbox",
        "value": True
        }, {
        "name": "pressure",
        "label": "Pressure",
        "type": "line_edit",
        "value": "10"
        }, {
        "name": "information",
        "label": "Information",
        "type": "text_edit",
        "value": "Do: ,Di: , Seal, Dielectric, Top Mylar, Top PDMS, Pressure"
        }, {
        "name": "saving_folder",
        "label": "Saving folder",
        "type": "folder",
        "value": ""
        }]
    APP = QtWidgets.QApplication([])
    dialog = DictDialog(user_fields=DIALOG_PARAMETERS)
    dialog.generate_dialog()
    dialog.exec_()
    APP.exec_()
