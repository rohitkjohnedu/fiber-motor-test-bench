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

# python packages
import sys
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QApplication, QPushButton, QTabWidget, QMessageBox
import time
import numpy as np
import os.path
from datetime import datetime

# custom packages
from PowerSupply import HvpsDevice, VoltagePlots, CurrentPlots, StaticMode, DynamicMode
from ForceSensor import FutekSensor, ForcePlot
from StandaTable import StandaTable, PositionPlot

formatted_time = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')  # Get the current date and time as a string
PROGRAM_NAME = "Actuator Test Bench"
PROGRAM_VERSION = "v1.0"

class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        # ************************************************************************************************************ #
        #                                               OPTIONS
        # ************************************************************************************************************ #

        self.debug_mode = 0             # 0: no debug mode;         1: debug mode.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_voltages = 2       # 0: no voltage plot;       1: high voltage plot;    2: high + low voltage plots.
        self.display_currents = 1       # 0: no current plot;       1: current plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_force = 1          # 0: no force plot;         1: force plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_position = 1       # 0: no actuator plot;      1: actuator plot.
        # ------------------------------------------------------------------------------------------------------------ #
        static = 1                      # 0: no static mode;        1: static mode.
        dynamic = 1                     # 0: no dynamic mode;       1: dynamic mode.

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # HIGH VOLTAGE POWER SUPPLY.
        self.power_supply = HvpsDevice()
        self.voltage_plot = VoltagePlots(self.power_supply, plot_title='Voltage', y_hv_max=2200, y_lv_max=12, display_index=self.display_voltages)
        self.current_plot = CurrentPlots(self.power_supply, plot_title='Current', y_max=0.001, display_index=self.display_currents)

        # FUTEK FORCE SENSOR (Load cell).
        self.force_sensor = FutekSensor()
        self.force_plot = ForcePlot(self.force_sensor, controls=False)

        # ACTUATOR (Translation stage)
        self.actuator = StandaTable()
        self.position_plot = PositionPlot(self.actuator)

        # ------------------------------------------------------------------------------------------------------------ #
        # Modes
        self.static = StaticMode(self.power_supply, self.actuator)
        self.dynamic = DynamicMode(self.power_supply, self.actuator)
        
        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #                                                             

        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        main_layout = QHBoxLayout(self)
        # self.setStyleSheet("background-color: white;")
        # ************************************************************************************************************ #

        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        control_panel_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #

        # Type of characterization (static, dynamic, demo).
        characterization_type = QTabWidget()

        if static == 1:
            characterization_type.addTab(self.static, 'Static Characterization')

        if dynamic == 1:
            characterization_type.addTab(self.dynamic, 'Dynamic Characterization')

        control_panel_layout.addWidget(characterization_type)
        # ------------------------------------------------------------------------------------------------------------ #

        # Control buttons
        buttons_groupBox = QGroupBox("Control buttons")
        buttons_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        # buttons_groupBox.setFixedHeight(150)
        control_panel_layout.addWidget(buttons_groupBox)
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
        self.tare_button.setFixedWidth(300)
        self.tare_button.setFixedHeight(50)

        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.run_button_clicked)
        self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       'font-size: 24px;'
                                       "position: center; ")
        button_layout.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.run_button.setFixedWidth(300)
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
            all_plots_layout.addWidget(self.force_plot)
            force_layout = QHBoxLayout()
            force_layout.addWidget(self.force_plot)
            all_plots_layout.addLayout(force_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY VOLTAGE PLOT
        if self.display_voltages != 0:
            voltage_layout = QHBoxLayout() 
            voltage_layout.addWidget(self.voltage_plot)
            all_plots_layout.addLayout(voltage_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY CURRENT PLOTS
        if self.display_currents != 0:
            currents_layout = QHBoxLayout()
            currents_layout.addWidget(self.current_plot)
            all_plots_layout.addLayout(currents_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR PLOT
        if self.display_position != 0:
            position_layout = QHBoxLayout()
            position_layout.addWidget(self.position_plot)
            all_plots_layout.addLayout(position_layout)

        plots_groupBox.setLayout(all_plots_layout)
        main_layout.addLayout(monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        #                                          CALLBACK FOR DATA READING
        # ************************************************************************************************************ #

        self.plot_interval = 50#ms
        self.start_time = 0
        self.sample_rate = 400#Hz
        self.interpolation_stop_time = 0

        # Set a timer with the callback function which reads and displays data from the serial port.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.plot_update_callback)
        if self.power_supply.auto_connect():
            self.timer.start(self.plot_interval)

    def run_button_clicked(self):
        if self.run_button.text() == "Run":
            print("\n[INFO] The measurement is running")
            self.start_time = time.perf_counter()
            self.power_supply.start_recording()
            self.force_sensor.start_recording()
            self.actuator.start_recording()
            self.run_button.setText("Stop")
            self.run_button.setStyleSheet("background-color: red; "
                                           "color: white; "
                                           "font-weight: bold; "
                                           'font-size: 24px;'
                                           "position: center; ")
        else:
            print("\n[INFO] The measurement is stopped")
            self.power_supply.stop_recording()
            self.force_sensor.stop_recording()
            self.actuator.stop_recording()
            self.run_button.setText("Run")
            self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       'font-size: 24px;'
                                       "position: center; ")

    def plot_update_callback(self):
        self.voltage_plot.plot_update(self.start_time)
        self.current_plot.plot_update(self.start_time)
        self.force_plot.plot_update(self.start_time)
        self.position_plot.plot_update(self.start_time)

        new_power_supply_data = self.power_supply.get_new_data()
        new_force_sensor_data = self.force_sensor.get_new_data()
        new_actuator_data = self.actuator.get_new_data()

        if len(new_power_supply_data)>0 and len(new_force_sensor_data)>0:
            if self.interpolation_stop_time < self.start_time:
                interpolation_start_time = self.start_time
            else:
                interpolation_start_time = self.interpolation_stop_time + 1/self.sample_rate

            smallest_last_sample = min(new_power_supply_data[-1,0], new_force_sensor_data[-1,0])
            differential_time_latest_sample = smallest_last_sample - self.start_time
            interpolated_latest_sample_number = np.floor(differential_time_latest_sample/(1/self.sample_rate))
            self.interpolation_stop_time = self.start_time + interpolated_latest_sample_number*(1/self.sample_rate)

            interpolation_time = np.arange(interpolation_start_time,self.interpolation_stop_time,1/self.sample_rate)
            interpolated_force_sensor_data = np.interp(interpolation_time, new_force_sensor_data[:, 0], new_force_sensor_data[:, 1])
            interpolated_actuator_data = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 1])
            interpolated_power_supply_data = np.zeros((len(interpolation_time), 11))
            for i1 in range(2, 11):
                interpolated_power_supply_data[:, i1] = np.interp(interpolation_time, new_power_supply_data[:, 0], new_power_supply_data[:, i1])

            time_s = interpolation_time
            force_mN = interpolated_force_sensor_data
            position_mm = interpolated_actuator_data
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
                    f.write(f'Time (s), Force (mN), Position (mm), hv_set (V), hv_vm (V), hv_err (V), lv_set (V), lv_vm (V), lv_err (V), '
                            f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n')
                    
            # Save the data to the .csv file.   
            save_data = np.column_stack((time_s, force_mN, position_mm, hv_set_kV, hv_vm_kV, hv_err_V, lv_set_V, lv_vm_V, lv_err_V,
                                        cm_w1_uA, cm_w2_uA, cm_w3_uA))
            with open(file_name, 'ab') as f:
                np.savetxt(f, save_data, fmt='%.8f, %4.6f, %4.3f, %6.1f, %6.1f, % 3.1f, % 3.2f, % 3.2f, % 3.2f, % 3.1f, % 3.1f, % 3.1f')

    # **************************************************************************************************************** #

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")
        if reply == QMessageBox.StandardButton.Yes:
            self.timer.stop()
            # explicit disconnection of the devices
            self.power_supply.disconnect()
            self.force_sensor.disconnect()
            self.actuator.disconnect()
            event.accept()
            if self.debug_mode == 1:
                print("[INFO] Program closed.")
        else:
            event.ignore()

#############################################################################################################################

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)

    window = MainWindow()
    window.show()
    window.showMaximized()

    app.exec()


if __name__ == '__main__':
    main()
