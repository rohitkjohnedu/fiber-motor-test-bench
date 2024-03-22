########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       ps_plots\VoltagePlots.py
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


class VoltagePlots(QWidget):
    def __init__(self, parent=None, plot_tittle=None, y_min=0, y_max=0):
        QWidget.__init__(self, parent=parent)

        self.layout_plot = QHBoxLayout(self)
        self.layout_plot.setSpacing(0)

        self.graphics_layout = pg.GraphicsLayoutWidget(show=False)

        # voltage plot
        self.voltage_plot = self.graphics_layout.addPlot(title=plot_tittle)
        self.voltage_plot.setLabel('bottom', 'Time', units='s')
        self.voltage_plot.setLabel('left', 'Voltage', units='V')
        self.voltage_plot.setYRange(y_min, y_max)

        # V_set // V_vm
        self.v_set_plot = self.voltage_plot.plot(pen=color[2], name="Target voltage")
        self.v_now_plot = self.voltage_plot.plot(pen=color[0], name="Output voltage")
        
        self.layout_plot.addWidget(self.graphics_layout)

    ####################################################################################################################
    def update_plot(self, t, y1):
        self.v_set_plot.setData(t, y1)  # plot
        # self.v_now_plot.setData(t, y2)

