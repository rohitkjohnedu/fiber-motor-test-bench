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
from PyQt6.QtWidgets import QWidget, QHBoxLayout
import pyqtgraph as pg
# custom packages
from PowerSupply.ps_plots import color

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)


class VoltagePlots(QWidget):
    def __init__(self, parent=None, plot_title=None, y_min=0, y_hv_max=0, y_lv_max=0, plots=None):
        QWidget.__init__(self, parent=parent)

        self.plots = plots
        self.legend = pg.LegendItem()
        
        ## Create a layout for the VoltagePlots widget:
        plot_layout = QHBoxLayout(self)
        plot_layout.setSpacing(0)

        # ------------------------------------------------------------------------------------------ #

        ## Create a plot widget:
        plot_widget = pg.PlotWidget(show=False)
        hv_plot = plot_widget.plotItem
        hv_plot.setTitle(plot_title, bold=True)
        hv_plot.setYRange(y_min, y_hv_max)
        hv_plot.setLabel('bottom', 'Time', units='s')
        hv_plot.setLabel('left', 'High Voltage', units='V')
        
        ## Creat a new viewbox for the low voltage plot:
        if self.plots is not None:
            self.lv_plot = pg.ViewBox()
            hv_plot.showAxis('right')
            hv_plot.scene().addItem(self.lv_plot)
            hv_plot.getAxis('right').linkToView(self.lv_plot)
            self.lv_plot.setXLink(hv_plot)
            hv_plot.setLabel('right', 'Low Voltage', units='V')
            self.lv_plot.setYRange(y_min, y_lv_max)
        
        # ------------------------------------------------------------------------------------------ #

            ## Handle view resizing:
            def updateViews():
                ## View has resized; update auxiliary views to match
                # self.lv_plot
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
            self.lv_set_plot = pg.PlotCurveItem(pen=color[8], name="Target low voltage")
            self.lv_plot.addItem(self.lv_set_plot)
            self.lv_now_plot = pg.PlotCurveItem(pen=color[6], name="Output low voltage")
            self.lv_plot.addItem(self.lv_now_plot)
        
        # ------------------------------------------------------------------------------------------ #

        self.legend.addItem(self.hv_set_plot, 'HV assigned')
        self.legend.addItem(self.hv_now_plot, 'HV measured')
        if self.plots is not None:
            self.legend.addItem(self.lv_set_plot, 'LV assigned')
            self.legend.addItem(self.lv_now_plot, 'LV measured')

        self.legend.setParentItem(hv_plot)
        self.legend.anchor((1.5, 0), (1, 0))
            
        plot_layout.addWidget(plot_widget)

    ####################################################################################################################
        
    def update_plot(self, t, y1, y2, y3=0, y4=0):
        self.hv_set_plot.setData(t, y1) 
        self.hv_now_plot.setData(t, y2)
        if self.plots is not None:
            self.lv_set_plot.setData(t, y3)
            self.lv_now_plot.setData(t, y4)
    
    def update_legend(self, hv_set, hv_now, lv_set=0, lv_now=0):
        for i, (variable, value)  in enumerate(zip(['HV assigned', 'HV measured'], [hv_set, hv_now])):
            self.legend.items[i][1].setText("{}: {} V".format(variable, value))

        if self.plots is not None:
            for i, (variable, value)  in enumerate(zip(['HV assigned', 'HV measured'],
                                                        [hv_set, hv_now])):
                self.legend.items[i][1].setText("{}: {} V".format(variable, value))
                
            for i, (variable, value)  in enumerate(zip(['LV assigned', 'LV measured'], [lv_set, lv_now])):
                self.legend.items[i+2][1].setText("{}: {} V".format(variable, value))