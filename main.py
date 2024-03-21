########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       main.py
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

import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QApplication, QMessageBox
# custom packages
from PowerSupply.PS_Widget import PowerSupply
from PowerSupply.Userdef import *
from ForceSensor import FutekSensor, FutekSensorPlot, FutekSensorControl


class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        # ************************************************************************************************************ #
        #                               ASSIGNMENT OF VALUES TO VARIABLES FOR OPTIONS
        # ************************************************************************************************************ #

        self.debug_mode = 0             # 0: no debug mode;         1: debug mode.
        display_cmd = 0                 # 0: no data display;       1: data display.
        record_data = 0                 # 0: no data record;        1: data record.
        self.display_currents = 0       # 0: no current plot;       1: current plot.
        self.display_voltages = 1       # 0: no voltage plot;       1: high voltage plot;       2: low voltage plot.
        self.display_force = 1          # 0: no force plot;         1: force plot.

        # ------------------------------------------------------------------------------------------------------------ #

        # Estimation of data rate transmission used for nice beginning of plot and not totally inaccurate time basis on
        # plots.

        self.plot_interval = 1#ms
        self.estimateRate = 0.005

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # POWER SUPPLY (High voltage power supply control panel).
        board_1_port = 'COM3'
        self.board_1 = PowerSupply(port_name=board_1_port,
                                        estimate_rate=self.estimateRate,
                                        currents_display=self.display_currents,
                                        voltage_display=self.display_voltages,
                                        debug_mode=self.debug_mode,
                                        rcv_data=display_cmd,
                                        record_data=record_data)

        # ------------------------------------------------------------------------------------------------------------ #

        # FUTEK FORCE SENSOR (Load cell).
        self.force_sensor = FutekSensor()
        self.force_sensor_plot = FutekSensorPlot(self.force_sensor, controls=False)
        self.force_sensor_control = FutekSensorControl(self.force_sensor_plot)

        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #                                                             

        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        self.main_layout = QHBoxLayout(self)
        # self.setStyleSheet("background-color: white;")

        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        self.control_panel_layout = QVBoxLayout()

        # ------------------------------------------------------------------------------------------------------------ #

        # BOARD #1 (Power supply control panel).
        self.board_1_groupBox = QGroupBox(self.board_1.board_name)
        self.board_1_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.board_1_groupBox, stretch=1)

        self.board_1_groupBox_layout = QFormLayout(self.board_1_groupBox)
        self.board_1_groupBox_layout.addRow(self.board_1)
        self.board_1_groupBox.setLayout(self.board_1_groupBox_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel). Plan to make two tabs for the linear stage
        # and the linear actuator.
        self.actuator_groupBox = QGroupBox("Actuator")
        self.actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.

        # ------------------------------------------------------------------------------------------------------------ #

        self.main_layout.addLayout(self.control_panel_layout, 0) # add the control panel on the left side.

        # ************************************************************************************************************ #

        # MONITORING (Right side of the main window: plots of measured and controlled variables: force, voltage, and currents.
        # Position and speed will be added later).
        self.monitoring_groupBox_layout = QVBoxLayout()

        self.plots_groupBox = QGroupBox("Monitoring")
        self.plots_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.monitoring_groupBox_layout.addWidget(self.plots_groupBox)

        self.all_plots_layout = QVBoxLayout(self.plots_groupBox)
        self.all_plots_layout.setSpacing(0)

        # ------------------------------------------------------------------------------------------------------------ #

        # FORCE SENSOR PLOT
        if self.display_force != 0:
            self.all_plots_layout.addWidget(self.force_sensor_plot)

            self.force_sensor_layout = QHBoxLayout()
            self.force_sensor_layout.addWidget(self.force_sensor_plot)
            self.force_sensor_layout.addWidget(self.force_sensor_control)

            self.all_plots_layout.addLayout(self.force_sensor_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY VOLTAGE PLOT
        if self.display_voltages != 0:
            self.voltage_layout = QHBoxLayout()
            self.voltage_labels_layout = QVBoxLayout()
            self.voltage_labels_layout.setContentsMargins(0, 10, 0, 10)

            if self.display_voltages == 1:
                self.voltage_layout.addWidget(self.board_1.hv_plots)
                self.voltage_labels_layout.addWidget(self.board_1.voltage_legend)

            if self.display_voltages == 2:
                self.voltage_layout.addWidget(self.board_1.lv_plots)
                self.voltage_labels_layout.addWidget(self.board_1.voltage_legend)

            self.voltage_labels_layout.addStretch(1)
            self.voltage_layout.addLayout(self.voltage_labels_layout)
            self.all_plots_layout.addLayout(self.voltage_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY CURRENT PLOTS
        if self.display_currents != 0:
            self.currents_layout = QHBoxLayout()
            self.currents_layout.setSpacing(0)
            self.current_labels_layout = QVBoxLayout()
            self.current_labels_layout.setContentsMargins(0, 10, 0, 10)

            for plots_row in range(3):  # three phases means 3 current plots.
                self.currents_layout.addWidget(self.board_1.hb_cm_plots[plots_row])
                self.current_labels_layout.addWidget(self.board_1.current_legend[plots_row])

            self.current_labels_layout.addStretch(1)
            self.currents_layout.addLayout(self.current_labels_layout)
            self.all_plots_layout.addLayout(self.currents_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        self.plots_groupBox.setLayout(self.all_plots_layout)
        self.main_layout.addLayout(self.monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        #                                          CALLBACK FOR DATA READING
        # ************************************************************************************************************ #
        
        # Set a timer with the callback function which reads data from serial port and plot.
        # Period is 30ms => 33Hz, if enough data sent by the board.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_reader_callback)
        self.timer.start(self.plot_interval)

    # ------------------------------------------------------------------------------------------------------------ #
        
    def data_reader_callback(self):
        self.board_1.data_reader_callback()
        self.board_1.plot_data()
        # self.force_sensor_plot.plot_update()
        #save and plot futek data 

    # **************************************************************************************************************** #
            
    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")

        if reply == QMessageBox.StandardButton.Yes:
            self.board_1.stop_comm()

            event.accept()
            if self.debug_mode == 1:
                print("[INFO] Program closed.")

        else:
            event.ignore()

    # ************************************************************************************************************ #

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)

    window = MainWindow()
    window.show()
    window.showMaximized()

    app.exec()


if __name__ == '__main__':
    main()
