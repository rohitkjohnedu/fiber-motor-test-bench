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
    def __init__(self, parent=None, plot_tittle=None, y_min=0, y_hv_max=0, y_lv_max=0, plots=None):
        QWidget.__init__(self, parent=parent)

        self.plots = plots

        layout_plot = QHBoxLayout(self)
        layout_plot.setSpacing(0)

        # self.plot_widget = pg.PlotWidget()
        # layout_plot.addWidget(self.plot_widget)

        self.graphics_layout = pg.GraphicsLayoutWidget(show=False)

        self.voltage_plot = self.graphics_layout.addPlot(title=plot_tittle)
        self.voltage_plot.setYRange(y_min, y_hv_max)

        self.hv_set_plot = self.voltage_plot.plot(pen=color[2], name="Target voltage")
        self.hv_now_plot = self.voltage_plot.plot(pen=color[0], name="Output voltage")

        if self.plots == "HV + LV":
            self.lv_plot = pg.ViewBox()
            self.voltage_plot.showAxis('right')
            self.voltage_plot.scene().addItem(self.lv_plot)
            self.voltage_plot.getAxis('right').linkToView(self.lv_plot)
            self.lv_plot.setXLink(self.voltage_plot)
            self.voltage_plot.setLabel('right', 'Low Voltage', units='V')
            self.lv_plot.setYRange(y_min, y_lv_max)

            self.lv_set_plot = pg.PlotCurveItem(pen=color[3], name="Target low voltage")
            self.lv_plot.addItem(self.lv_set_plot)
            self.lv_now_plot = pg.PlotCurveItem(pen=color[4], name="Output low voltage")
            self.lv_plot.addItem(self.lv_now_plot)

        # self.lv_set_plot = self.voltage_plot.plot(pen=color[3], name="kTarget voltage")
        # self.lv_now_plot = self.voltage_plot.plot(pen=color[4], name="kOutput voltage")

        layout_plot.addWidget(self.graphics_layout)

        # if self.plots == "HV + LV":
        #     self.lv_plot = pg.ViewBox()
        #     self.plot_widget.showAxis('right')
        #     self.plot_widget.scene().addItem(self.lv_plot)
        #     self.plot_widget.getAxis('right').linkToView(self.lv_plot)
        #     self.lv_plot.setXLink(self.plot_widget)
        #     self.plot_widget.setLabel('right', 'Low Voltage', units='V')
        #     # self.lv_plot.setYRange(y_min, y_lv_max)
            
        #     self.lv_set_plot = pg.PlotCurveItem(pen=color[3], name="Target low voltage")
        #     self.lv_plot.addItem(self.lv_set_plot)
        #     self.lv_now_plot = pg.PlotCurveItem(pen=color[4], name="Output low voltage")
        #     self.lv_plot.addItem(self.lv_now_plot)

        # self.plot_widget.setLabel('bottom', 'Time', units='s')
        # self.plot_widget.setTitle(plot_tittle)

        # self.plot_widget.addLegend()

    ####################################################################################################################
    def update_plot(self, t, y1, y2, y3=None, y4=None):
        self.hv_set_plot.setData(t, y1) 
        self.hv_now_plot.setData(t, y2)
        # if self.plots == "HV + LV":
        self.lv_set_plot.setData(t, y3)
        self.lv_now_plot.setData(t, y4)





        # self.graphics_layout = pg.GraphicsLayoutWidget(show=False)
        # # ************************************************************************************************************ #
        # # voltage plot
        # self.voltage_plot_1 = self.graphics_layout.addPlot(title=plot_tittle)
        # self.voltage_plot_2 = self.graphics_layout.addPlot(title=plot_tittle)
        # # self.voltage_plot.setLabel('bottom', 'Time', units='s')
        # # self.voltage_plot.setLabel('left', 'Voltage', units='V')
        # self.voltage_plot_1.setYRange(y_min, y_hv_max)
        # self.voltage_plot_2.setYRange(y_min, y_lv_max)
        # # ------------------------------------------------------------------------------------------------------------ #
        # # V_set // V_vm
        # self.hv_set_plot = self.voltage_plot_1.plot(pen=color[2], name="Target voltage")
        # self.hv_now_plot = self.voltage_plot_1.plot(pen=color[0], name="Output voltage")

        # self.lv_set_plot = self.voltage_plot_2.plot(pen=color[2], name="Target voltage")
        # self.lv_now_plot = self.voltage_plot_2.plot(pen=color[0], name="Output voltage")

        # layout_plot.addWidget(self.graphics_layout)