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


class VoltagePlots(QWidget):
    def __init__(self, device=None, parent=None, plot_title=None, y_min=0, y_hv_max=0, y_lv_max=0, display_index=None):
        QWidget.__init__(self, parent=parent)

        self.device = device
        self.display_index = display_index
        
        self.plotHistoryLength = 10#seconds
        self.maxPlotHistoryLength = 100000#samples
        
        # Create a layout for the VoltagePlots widget:
        plot_layout = QHBoxLayout(self)

        # Create a plot widget:
        plot_widget = pg.PlotWidget(self)
        self.legend = pg.LegendItem()

        # Create the plots:
        hv_plot = plot_widget.plotItem
        hv_plot.setTitle(plot_title, bold=True)
        hv_plot.setLabel('left', 'High Voltage', units='V')
        hv_plot.setLabel('bottom', 'Time', units='s')
        hv_plot.setYRange(y_min, y_hv_max)
        
        # Creat a new viewbox for the low voltage plot:
        if self.display_index == 2:
            self.lv_plot = pg.ViewBox()
            hv_plot.showAxis('right')
            hv_plot.scene().addItem(self.lv_plot)
            hv_plot.getAxis('right').linkToView(self.lv_plot)
            self.lv_plot.setXLink(hv_plot)
            hv_plot.setLabel('right', 'Low Voltage', units='V')
            self.lv_plot.setYRange(y_min, y_lv_max)
        # ------------------------------------------------------------------------------------------ #

            # Handle view resizing:
            def updateViews():
                # View has resized; update auxiliary views to match self.lv_plot
                self.lv_plot.setGeometry(hv_plot.vb.sceneBoundingRect())

                # Need to re-update linked axes since this was called
                # incorrectly while views had different shapes.
                self.lv_plot.linkedViewChanged(hv_plot.vb, self.lv_plot.XAxis)
            
            updateViews()
            hv_plot.vb.sigResized.connect(updateViews)
        # ------------------------------------------------------------------------------------------ #

        # Create the plots:
        self.hv_set_plot = hv_plot.plot(pen=color[2], name="Target high voltage")
        self.hv_now_plot = hv_plot.plot(pen=color[0], name="Output high voltage")
        if self.display_index == 2:
            self.lv_set_plot = pg.PlotCurveItem(pen=color[8], name="Target low voltage")
            self.lv_plot.addItem(self.lv_set_plot)
            self.lv_now_plot = pg.PlotCurveItem(pen=color[6], name="Output low voltage")
            self.lv_plot.addItem(self.lv_now_plot)
        # ------------------------------------------------------------------------------------------ #

        self.legend.addItem(self.hv_set_plot, 'HV assigned')
        self.legend.addItem(self.hv_now_plot, 'HV measured')
        if self.display_index == 2:
            self.legend.addItem(self.lv_set_plot, 'LV assigned')
            self.legend.addItem(self.lv_now_plot, 'LV measured')

        self.legend.setParentItem(hv_plot)
        self.legend.anchor((1.5, 0), (1, 0))
            
        plot_layout.addWidget(plot_widget)

    ####################################################################################################################
    
    def plot_update(self, start_time):
        all_data = self.device.get_buffer()
        data = all_data
        hv_vm = data[:, 3]

        if self.display_index != 0:
            epoch_time = data[:, 0]
            tplot = epoch_time - start_time

            if len(tplot) > self.maxPlotHistoryLength:
                tplot = tplot[-self.maxPlotHistoryLength:]

            hv_set = data[:, 2]
            if len(tplot) > self.maxPlotHistoryLength:
                                hv_set = hv_set[-self.maxPlotHistoryLength:]
                                hv_vm = hv_vm[-self.maxPlotHistoryLength:]
            
            if self.display_index == 1:
                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use])
                    self.update_legend(hv_set[-1], hv_vm[-1])

            if self.display_index == 2:
                lv_set = data[:, 5]
                lv_vm = data[:, 6]
                
                if len(tplot) > self.maxPlotHistoryLength:
                    lv_set = lv_set[-self.maxPlotHistoryLength:]
                    lv_vm = lv_vm[-self.maxPlotHistoryLength:]

                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use],
                                                    y3=lv_set[use], y4=lv_vm[use])
                    self.update_legend(hv_set[-1], hv_vm[-1], lv_set[-1], lv_vm[-1])
    # ------------------------------------------------------------------------------------------------------------------ #

    def update_plot(self, t, y1, y2, y3=0, y4=0):
        self.hv_set_plot.setData(t, y1) 
        self.hv_now_plot.setData(t, y2)
        if self.display_index == 2:
            self.lv_set_plot.setData(t, y3)
            self.lv_now_plot.setData(t, y4)
    # ------------------------------------------------------------------------------------------------------------------ #
    
    def update_legend(self, hv_set, hv_now, lv_set=0, lv_now=0):
        for i, (variable, value)  in enumerate(zip(['HV assigned', 'HV measured'], [hv_set, hv_now])):
            self.legend.items[i][1].setText("{}: {} V".format(variable, value))

        if self.display_index is not None:
            for i, (variable, value)  in enumerate(zip(['HV assigned', 'HV measured'],
                                                        [hv_set, hv_now])):
                self.legend.items[i][1].setText("{}: {} V".format(variable, value))
            if self.display_index == 2:    
                for i, (variable, value)  in enumerate(zip(['LV assigned', 'LV measured'], [lv_set, lv_now])):
                    self.legend.items[i+2][1].setText("{}: {} V".format(variable, value))