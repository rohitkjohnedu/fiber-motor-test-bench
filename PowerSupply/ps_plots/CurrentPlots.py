########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       ps_plots\CurrentPlots.py
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


class Current1Plots(QWidget):
    def __init__(self, parent=None, plot_tittle=None, plot_name=None, plot_index=None, y_min=0, y_max=0):
        QWidget.__init__(self, parent=parent)

        self.layout_plot = QHBoxLayout(self)
        self.layout_plot.setSpacing(0)

        self.graphics_layout = pg.GraphicsLayoutWidget(show=False)

        # current plot
        self.current_plot = self.graphics_layout.addPlot(title=plot_tittle)
        self.current_plot.setLabel('bottom', 'Time', units='s')
        self.current_plot.setLabel('left', 'Current', units='uA')
        self.current_plot.setYRange(y_min, y_max)

        self.y_plot = self.current_plot.plot(pen=color[plot_index], name=plot_name)

        self.layout_plot.addWidget(self.graphics_layout)

    ####################################################################################################################
    def update_1_plot(self, t, y):
        self.y_plot.setData(t, y)
    
