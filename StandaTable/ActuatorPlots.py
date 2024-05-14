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


class ActuatorPlots(QWidget):
    def __init__(self, actuator, parent=None):
        QWidget.__init__(self, parent=parent)

        self.actuator = actuator
        self.legend = pg.LegendItem()

        self.display_position = 1
        self.plotHistoryLength = 10#seconds
        self.maxPlotHistoryLength = 100000#samples
        
        # Create a layout for the VoltagePlots widget:
        plot_layout = QHBoxLayout(self)
        plot_layout.setSpacing(0)

        # ------------------------------------------------------------------------------------------ #

        # Create a plot widget:
        plot_widget = pg.PlotWidget(self, title="<b>Force Sensor Reading</b>")
        # plot_widget.setMinimumWidth(600)
        plot_widget.setMinimumHeight(300)
        plot_widget.setLabel('bottom', 'Time', units='s')
        plot_widget.setLabel('left', 'Position', units='mm')
        self.plot_position = self.plot_widget.plot()
        plot_layout.addWidget(self.plot_widget)

        # ------------------------------------------------------------------------------------------ #

        # Create the plots:
        # self.hv_set_plot = pos_plot.plot(pen=color[2], name="Target high voltage")
        # self.hv_now_plot = pos_plot.plot(pen=color[0], name="Output high voltage")
        
        # ------------------------------------------------------------------------------------------ #

            
        # plot_layout.addWidget(plot_widget)

    ####################################################################################################################
    def plot_update(self, start_time):
        if self.actuator.is_connected:
            epoch_time_force, force = self.actuator.get_buffer()
            tplot = epoch_time_force - start_time

            if len(tplot) > self.maxPlotHistoryLength:
                    tplot = tplot[-self.maxPlotHistoryLength:]
                    position = force[-self.maxPlotHistoryLength:]

            if len(tplot)>0:
                use = tplot>tplot[-1]-self.plotHistoryLength
                self.position.setData(tplot[use], position[use])

    def set_plot_history(self, history_length):
        self.plotHistoryLength = history_length

    # def update_plot(self, t, y1, y2, y3=0, y4=0):
    #     self.hv_set_plot.setData(t, y1) 
    #     self.hv_now_plot.setData(t, y2)
    #     if self.plots is not None:
    #         self.lv_set_plot.setData(t, y3)
    #         self.lv_now_plot.setData(t, y4)
    