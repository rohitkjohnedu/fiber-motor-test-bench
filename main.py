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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QApplication, QMessageBox, QPushButton, QTabWidget
# custom packages
from PowerSupply.PS_Communication import PowerSupply
from PowerSupply.Voltage import *
from PowerSupply.Userdef import *
from ForceSensor import FutekSensor, FutekSensorPlot
from PowerSupply.ps_modes.static import StaticMode
from PowerSupply.ps_modes.dynamic import DynamicMode
from PowerSupply.ps_modes.demo import DemoMode
import time
import numpy as np
import os.path
from datetime import datetime

formatted_time = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')  # Get the current date and time as a string

class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        # ************************************************************************************************************ #
        #                               ASSIGNMENT OF VALUES TO VARIABLES FOR OPTIONS
        # ************************************************************************************************************ #

        self.debug_mode = 0             # 0: no debug mode;         1: debug mode.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_voltages = 2       # 0: no voltage plot;       1: high voltage plot;    2: high + low voltage plots.
        self.display_currents = 1       # 0: no current plot;       1: current plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_force = 1          # 0: no force plot;         1: force plot.
        # ------------------------------------------------------------------------------------------------------------ #
        static = 1                      # 0: no static mode;        1: static mode.
        dynamic = 1                     # 0: no dynamic mode;       1: dynamic mode.
        demo = 1                        # 0: no demonstration mode; 1: demonstration mode.

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # POWER SUPPLY (High voltage power supply control panel).
        board_1_port = 'COM3'
        self.power_supply = PowerSupply(port_name=board_1_port,
                                        voltage_display=self.display_voltages,
                                        currents_display=self.display_currents)
        serial = self.power_supply.ser

        # Modes
        self.static = StaticMode(ser=serial)
        self.dynamic = DynamicMode(ser=serial)
        self.demo = DemoMode(ser=serial)

        # ------------------------------------------------------------------------------------------------------------ #

        # FUTEK FORCE SENSOR (Load cell).
        self.force_sensor = FutekSensor()
        self.force_sensor_plot = FutekSensorPlot(self.force_sensor, controls=False)

        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #                                                             

        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        main_layout = QHBoxLayout(self)
        # self.setStyleSheet("background-color: white;")

        # ************************************************************************************************************ #

        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        control_panel_layout = QVBoxLayout()
        
        # Type of characterization (static, dynamic, demo).
        characterization_type = QTabWidget()

        if static == 1:
            characterization_type.addTab(self.static, 'Static Characterization')

        if dynamic == 1:
            characterization_type.addTab(self.dynamic, 'Dynamic Characterization')

        if demo == 1:
            characterization_type.addTab(self.demo, 'Performance Demonstration')

        control_panel_layout.addWidget(characterization_type)
        # ------------------------------------------------------------------------------------------------------------ #

        # Control buttons
        buttons_groupBox = QGroupBox("Control buttons")
        buttons_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        buttons_groupBox.setFixedHeight(150)
        control_panel_layout.addWidget(buttons_groupBox, stretch=0)
        control_panel_layout.addSpacing(0)
        
        button_layout = QVBoxLayout(buttons_groupBox)

        self.tare_button = QPushButton("Tare")
        self.tare_button.setStyleSheet("background-color: white; "
                                        "color: black; "
                                        "font-weight: bold; "
                                        'font-size: 24px;'
                                        "position: center; ")
        button_layout.addWidget(self.tare_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.tare_button.clicked.connect(self.force_sensor.tare)
        self.tare_button.setFixedWidth(680)
        self.tare_button.setFixedHeight(50)

        self.run_button = QPushButton("Run")
        self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       'font-size: 24px;'
                                       "position: center; ")
        button_layout.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.run_button.clicked.connect(self.run_button_clicked)
        self.run_button.setFixedWidth(680)
        self.run_button.setFixedHeight(50)

        button_layout.addStretch(1)

        # ------------------------------------------------------------------------------------------------------------ #

        main_layout.addLayout(control_panel_layout, 0) # add the control panel on the left side.

        # ************************************************************************************************************ #

        # MONITORING (Right side of the main window: plots of measured and controlled variables: force, voltage, and currents.
        # Position and speed will be added later).
        monitoring_groupBox_layout = QVBoxLayout()

        plots_groupBox = QGroupBox("Monitoring")
        plots_groupBox.setStyleSheet('font-weight: bold;'
                                     'background-color: white;')
        monitoring_groupBox_layout.addWidget(plots_groupBox)

        all_plots_layout = QVBoxLayout(plots_groupBox)
        all_plots_layout.setSpacing(0)

        # ------------------------------------------------------------------------------------------------------------ #

        # FORCE SENSOR PLOT
        if self.display_force != 0:
            all_plots_layout.addWidget(self.force_sensor_plot)
            force_sensor_layout = QHBoxLayout()
            force_sensor_layout.addWidget(self.force_sensor_plot)
            all_plots_layout.addLayout(force_sensor_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY VOLTAGE PLOT
        if self.display_voltages != 0:
            voltage_layout = QHBoxLayout()
            voltage_layout.addWidget(self.power_supply.voltage_plots)
            all_plots_layout.addLayout(voltage_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY CURRENT PLOTS
        if self.display_currents != 0:
            currents_layout = QHBoxLayout()
            currents_layout.addWidget(self.power_supply.current_plots)
            all_plots_layout.addLayout(currents_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        plots_groupBox.setLayout(all_plots_layout)
        main_layout.addLayout(monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        #                                          CALLBACK FOR DATA READING
        # ************************************************************************************************************ #

        self.plot_interval = 50#ms
        self.start_time = 0

        # Set a timer with the callback function which reads and displays data from serial port.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.plot_update_callback)
        self.timer.start(self.plot_interval)

    def run_button_clicked(self):
        if self.run_button.text() == "Run":
            self.start_time = time.perf_counter()
            self.power_supply.start_recording()
            self.force_sensor.start_recording()
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: red; "
                                           "color: white; "
                                           "font-weight: bold; "
                                           'font-size: 24px;'
                                           "position: center; ")
        else:
            self.power_supply.stop_recording()
            self.force_sensor.stop_recording()
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       'font-size: 24px;'
                                       "position: center; ")
        
    # ------------------------------------------------------------------------------------------------------------ #
        
    def plot_update_callback(self):
        if self.display_voltages !=0 or self.display_currents !=0:
            self.power_supply.plot_update(self.start_time)
        self.force_sensor_plot.plot_update(self.start_time)

        new_power_supply_data = self.power_supply.get_new_data()
        new_force_sensor_data = self.force_sensor.get_new_data()

        if len(new_power_supply_data)>0:
            interpolated_power_supply_data = np.zeros((len(new_force_sensor_data[:,0]), 11))
            for i1 in range(2, 11):
                interpolated_power_supply_data[:, i1] = np.interp(new_force_sensor_data[:, 0], new_power_supply_data[:, 0], new_power_supply_data[:, i1])

            time_s = new_force_sensor_data[:,0]
            force_mN = new_force_sensor_data[:,1]
            hv_set_kV = interpolated_power_supply_data[:,2]
            hv_vm_kV = interpolated_power_supply_data[:,3]
            hv_err_V = interpolated_power_supply_data[:,4]
            lv_set_V = interpolated_power_supply_data[:,5]
            lv_vm_V = interpolated_power_supply_data[:,6]
            lv_err_V = interpolated_power_supply_data[:,7]
            cm_w1_uA = interpolated_power_supply_data[:,8]
            cm_w2_uA = interpolated_power_supply_data[:,9]
            cm_w3_uA = interpolated_power_supply_data[:,10]

            # Create a folder to store the data files if it doesn't exist.
            folder_name = 'DataFiles'
            os.makedirs(folder_name, exist_ok=True)

            # Create a new .csv file within the folder with a file name, date and time of the experiment.
            file_name = os.path.join(folder_name, f"data_{formatted_time}.csv")
            if not os.path.isfile(file_name):
                with open(file_name, 'w') as f:
                    f.write(f'Time (s), Force (mN), hv_set (V), hv_vm (V), hv_err (V), lv_set (V), lv_vm (V), lv_err (V), '
                            f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n')
                    
            # Save the data to the .csv file.   
            save_data = np.column_stack((time_s, force_mN, hv_set_kV, hv_vm_kV, hv_err_V, lv_set_V, lv_vm_V, lv_err_V,
                                        cm_w1_uA, cm_w2_uA, cm_w3_uA))
            with open(file_name, 'ab') as f:
                np.savetxt(f, save_data, fmt='%.8f, %4.6f, %4.0f, %4.0f, %.0f, %2.1f, %2.1f, %2.1f, %2.0f, %2.0f, %2.0f')

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
