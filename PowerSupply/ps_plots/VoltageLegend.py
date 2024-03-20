########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       ps_plots\VoltageLegend.py
# @brief      Author:             MBE
#             Institute:          EPFL
#             Laboratory:         LMTS
#             Software version:   v1.09 (SYLVAIN/MARTIJN/MYKHAILO)
#             Created on:         11.03.2024
#             Last modifications: 11.03.2024
#
# Copyright 2021/2024 EPFL-LMTS
# All rights reserved.
# NO HELP WILL BE GIVEN IF YOU MODIFY THIS CODE !!!
########################################################################################################################

# python packages
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import pyqtgraph as pg
# custom packages
from PowerSupply.ps_plots import *

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)


class VoltageLegend(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.voltage_labels_layout = QVBoxLayout(self)
        self.voltage_labels_layout.setSpacing(0)

        # Voltage labels
        # ------------------------------------------------------------------------------------------------------------ #
        # Vhv_set
        self.hv_set_name_label = QLabel("Target")
        self.hv_set_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_set_name_label.setStyleSheet("background-color: rgb{}; color: white" .format(color[2]))
        self.hv_set_name_label.setFixedWidth(100)

        self.hv_set_value_label = QLabel("0 V")
        self.hv_set_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_set_value_label.setFixedWidth(100)
        # ------------------------------------------------------------------------------------------------------------ #
        # Vhv_vm
        self.hv_vm_name_label = QLabel("Monitor")
        self.hv_vm_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_vm_name_label.setStyleSheet("background-color: rgb{}; color: white" .format(color[0]))
        self.hv_vm_name_label.setFixedWidth(100)

        self.hv_vm_value_label = QLabel("0 V")
        self.hv_vm_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_vm_value_label.setFixedWidth(100)
        # ------------------------------------------------------------------------------------------------------------ #
        # Vhv_err
        self.hv_err_name_label = QLabel("Error")
        self.hv_err_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_err_name_label.setStyleSheet("background-color: rgb{}; color: white" .format(color[9]))
        self.hv_err_name_label.setFixedWidth(100)

        self.hv_err_value_label = QLabel("0 V")
        self.hv_err_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hv_err_value_label.setFixedWidth(100)        
        # ------------------------------------------------------------------------------------------------------------ #

        self.voltage_labels_layout.addWidget(self.hv_set_name_label)
        self.voltage_labels_layout.addWidget(self.hv_set_value_label)

        self.voltage_labels_layout.addWidget(self.hv_vm_name_label)
        self.voltage_labels_layout.addWidget(self.hv_vm_value_label)

        self.voltage_labels_layout.addWidget(self.hv_err_name_label)
        self.voltage_labels_layout.addWidget(self.hv_err_value_label)

        self.voltage_labels_layout.addStretch(1)

    ####################################################################################################################
    def update_label(self, label1, label2, label3):
        self.hv_set_value_label.setText("{} V".format(label1, '4.2f'))
        self.hv_vm_value_label.setText("{} V".format(label2, '4.2f'))
        self.hv_err_value_label.setText("{} V".format(label3, '4.2f'))
