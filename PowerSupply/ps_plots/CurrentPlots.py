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
from PyQt6.QtWidgets import QWidget, QHBoxLayout
import pyqtgraph as pg

color = [(255, 0, 0),    #0) red
         (0, 255, 0),    #1) green
         (0, 0, 255),    #2) blue
         (127, 0, 0),    #3) brown
         (0, 127, 0),    #4) dark_green
         (0, 0, 127),    #5) dark_blue
         (255, 127, 0),  #6) orange
         (127, 0, 127),  #7) purple
         (0, 127, 255),  #8) light_blue
         (0, 0, 0)]      #9) black

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)


class CurrentPlots(QWidget):
    def __init__(self, parent=None, y_min=0, y_max=0):
        QWidget.__init__(self, parent=parent)

        plot_layout = QHBoxLayout(self)
        plot_layout.setSpacing(0)

        plot_widget = pg.PlotWidget()
        self.legend = pg.LegendItem()

        current_plot = plot_widget.plotItem
        current_plot.setTitle('Three-phase current of the Power Supply', bold=True)
        current_plot.setLabel('bottom', 'Time', units='s')
        current_plot.setLabel('left', 'Current', units='uA')
        current_plot.setYRange(y_min, y_max)

        self.y_plot = []
        for i, phase in enumerate(['A', 'B', 'C']):
            plot_item = current_plot.plot(pen=color[i+1])
            self.y_plot.append(plot_item)
            self.legend.addItem(plot_item, 'Phase {}'.format(phase))

        self.legend.setParentItem(current_plot)
        self.legend.anchor((2, 0), (1, 0))

        plot_layout.addWidget(plot_widget)

    ####################################################################################################################
    def update_plot(self, t, y1, y2, y3):
        self.y_plot[0].setData(t, y1)
        self.y_plot[1].setData(t, y2)
        self.y_plot[2].setData(t, y3)
        
    def update_legend(self, current_1, current_2, current_3):
        for i, (phase, value)  in enumerate(zip(['A', 'B', 'C'], [current_1, current_2, current_3])):
            self.legend.items[i][1].setText("Phase {}: {} uA".format(phase, value))

