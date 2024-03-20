########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       ps_plots\CurrentLegend.py
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


class CurrentLegend(QWidget):
    def __init__(self, parent=None, plot_name=None, plot_index=None):
        QWidget.__init__(self, parent=parent)

        self.current_labels_layout = QVBoxLayout(self)
        self.current_labels_layout.setSpacing(0)

        # current labels
        self.y_name_label = QLabel(plot_name)
        self.y_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.y_name_label.setStyleSheet("background-color: rgb{}; color: white; ".format(color[plot_index]))
        self.y_name_label.setFixedWidth(100)

        self.y_value_label = QLabel("0 uA")
        self.y_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.y_value_label.setFixedWidth(100)

        self.current_labels_layout.addWidget(self.y_name_label)
        self.current_labels_layout.addWidget(self.y_value_label)
        self.current_labels_layout.addStretch(1)

    ####################################################################################################################
    def update_legend(self, label):
        self.y_value_label.setText("{} uA".format(label, '9f'))

    def legend_currents(self):
        return self.y_name_label
    
