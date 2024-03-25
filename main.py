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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QApplication, QMessageBox, QPushButton
# custom packages
from PowerSupply.PS_Widget import PowerSupply
from PowerSupply.Userdef import *
from ForceSensor import FutekSensor, FutekSensorPlot, FutekSensorControl
import time

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

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # POWER SUPPLY (High voltage power supply control panel).
        board_1_port = 'COM3'
        self.power_supply = PowerSupply(port_name=board_1_port,
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

        # Power supply control panel.
        self.power_supply_groupBox = QGroupBox(self.power_supply.board_name)
        self.power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.power_supply_groupBox, stretch=1)

        self.power_supply_groupBox_layout = QFormLayout(self.power_supply_groupBox)
        self.power_supply_groupBox_layout.addRow(self.power_supply)
        self.power_supply_groupBox.setLayout(self.power_supply_groupBox_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel). Plan to make two tabs for the linear stage
        # and the linear actuator.
        self.actuator_groupBox = QGroupBox("Actuator")
        self.actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.

        # ------------------------------------------------------------------------------------------------------------ #

        # Unified controller
        self.uni_groupBox = QGroupBox("Uni controller")
        self.uni_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.uni_groupBox, stretch=1)

        # Here will be the code for the unified controller
        self.button_layout = QVBoxLayout(self.uni_groupBox)
        self.run_button = QPushButton("Run")
        self.button_layout.addWidget(self.run_button)
        self.run_button.clicked.connect(self.run_button_clicked)
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
                self.voltage_layout.addWidget(self.power_supply.hv_plots)
                self.voltage_labels_layout.addWidget(self.power_supply.voltage_legend)

            if self.display_voltages == 2:
                self.voltage_layout.addWidget(self.power_supply.lv_plots)
                self.voltage_labels_layout.addWidget(self.power_supply.voltage_legend)

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
                self.currents_layout.addWidget(self.power_supply.hb_cm_plots[plots_row])
                self.current_labels_layout.addWidget(self.power_supply.current_legend[plots_row])

            self.current_labels_layout.addStretch(1)
            self.currents_layout.addLayout(self.current_labels_layout)
            self.all_plots_layout.addLayout(self.currents_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        self.plots_groupBox.setLayout(self.all_plots_layout)
        self.main_layout.addLayout(self.monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        #                                          CALLBACK FOR DATA READING
        # ************************************************************************************************************ #

        self.plot_interval = 10#ms
        self.start_time = 0

        # Set a timer with the callback function which reads and displays data from serial port.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.plot_update_callback)
        self.timer.start(self.plot_interval)

        # self.start_time = time.perf_counter()

    def run_button_clicked(self):
        if self.run_button.text() == "Run":
            self.start_time = time.perf_counter()
            self.power_supply.start_recording()
            self.force_sensor.start_recording()
            self.run_button.setText("Stop")
        else:
            self.power_supply.stop_recording()
            self.force_sensor.stop_recording()
            self.run_button.setText("Run")
        
    # ------------------------------------------------------------------------------------------------------------ #
        
    def plot_update_callback(self):
        self.power_supply.plot_update(self.start_time)
        self.force_sensor_plot.plot_update(self.start_time)


        #save and plot futek data 

    # **************************************************************************************************************** #
            
    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")

        if reply == QMessageBox.StandardButton.Yes:
            self.power_supply.stop_comm()

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
