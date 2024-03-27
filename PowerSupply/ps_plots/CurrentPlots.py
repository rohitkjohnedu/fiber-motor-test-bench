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
    def __init__(self, parent=None, plot_tittle=None, plot_name=None, plot_index=None, y_min=0, y_max=0):
        QWidget.__init__(self, parent=parent)

        self.plots = 0

        plot_layout = QHBoxLayout(self)
        plot_layout.setSpacing(0)

        # ------------------------------------------------------------------------------------------ #

        ## Create a plot widget:
        plot_widget = pg.PlotWidget(show=False)
        hv_plot = plot_widget.plotItem
        hv_plot.setTitle(plot_tittle)
        hv_plot.setLabel('bottom', 'Time', units='s')
        hv_plot.setLabel('left', 'Current', units='uA')
        
        ## Creat a new viewbox for the low voltage plot:
        if self.plots is not None:
            self.lv_plot = pg.ViewBox()
            hv_plot.showAxis('right')
            hv_plot.scene().addItem(self.lv_plot)
            hv_plot.getAxis('right').linkToView(self.lv_plot)
            self.lv_plot.setXLink(hv_plot)
            hv_plot.setLabel('right', 'Low Voltage', units='V')
        
        # ------------------------------------------------------------------------------------------ #

            ## Handle view resizing:
            def updateViews():
                ## View has resized; update auxiliary views to match
                self.lv_plot
                self.lv_plot.setGeometry(hv_plot.vb.sceneBoundingRect())

                ## Need to re-update linked axes since this was called
                ## incorrectly while views had different shapes.
                self.lv_plot.linkedViewChanged(hv_plot.vb, self.lv_plot.XAxis)
            
            updateViews()
            hv_plot.vb.sigResized.connect(updateViews)

        # ------------------------------------------------------------------------------------------ #

        ## Create the plots:
        self.hv_set_plot = hv_plot.plot(pen=color[2], name="Target high voltage")
        self.hv_now_plot = hv_plot.plot(pen=color[0], name="Output high voltage")
        if self.plots is not None:
            self.lv_set_plot = pg.PlotCurveItem(pen=color[3], name="Target low voltage")
            self.lv_plot.addItem(self.lv_set_plot)
            self.lv_now_plot = pg.PlotCurveItem(pen=color[4], name="Output low voltage")
            self.lv_plot.addItem(self.lv_now_plot)
        
        # ------------------------------------------------------------------------------------------ #
            
        plot_layout.addWidget(plot_widget)

    ####################################################################################################################
        
    def update_plot(self, t, y1, y2, y3=0, y4=0):
        self.hv_set_plot.setData(t, y1) 
        self.hv_now_plot.setData(t, y2)
        if self.plots is not None:
            self.lv_set_plot.setData(t, y3)
            self.lv_now_plot.setData(t, y4)
















        # self.graphics_layout = pg.GraphicsLayoutWidget(show=False)

        # # current plot
        # self.current_plot = self.graphics_layout.addPlot(title=plot_tittle)
        # self.current_plot.setLabel('bottom', 'Time', units='s')
        # self.current_plot.setLabel('left', 'Current', units='uA')
        # self.current_plot.setYRange(y_min, y_max)

        # self.y_plot = self.current_plot.plot(pen=color[plot_index], name=plot_name)

        # self.layout_plot.addWidget(self.graphics_layout)

    ####################################################################################################################
    def update_1_plot(self, t, y):
        self.y_plot.setData(t, y)
    
