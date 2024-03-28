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


class CurrentPlots(QWidget):
    def __init__(self, parent=None, plot_tittle=None, y_min=0, y_max=0):
        QWidget.__init__(self, parent=parent)

        plot_layout = QHBoxLayout(self)
        plot_layout.setSpacing(0)

        graphics_layout = pg.GraphicsLayoutWidget(show=False)

        # Current plot
        current_plot = graphics_layout.addPlot(title=plot_tittle)
        current_plot.setLabel('bottom', 'Time', units='s')
        current_plot.setLabel('left', 'Current', units='uA')
        current_plot.setYRange(y_min, y_max)

        self.y_plot = []
        for i in range(3):
            self.y_plot.append(current_plot.plot(pen=color[i+1]))

        plot_layout.addWidget(graphics_layout)

    ####################################################################################################################
    def update_plot(self, t, y1, y2, y3):
        self.y_plot[0].setData(t, y1)
        self.y_plot[1].setData(t, y2)
        self.y_plot[2].setData(t, y3)
