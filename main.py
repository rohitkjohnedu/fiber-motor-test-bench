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
from PyQt6.QtCore import Qt, QTimer 
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QApplication, QMessageBox, QPushButton, QTabWidget, QComboBox
import time
import numpy as np
import os.path
from datetime import datetime

# custom packages
# from PowerSupply.PS_Communication import PowerSupply
# from ForceSensor import FutekSensor, FutekSensorPlot
from PowerSupply.ps_modes.static import StaticMode
# from PowerSupply.ps_modes.dynamic import DynamicMode
# from PowerSupply.ps_modes.demo import DemoMode

# custom packages from a new software version
from PowerSupply.device import HvpsDevice
from PowerSupply.ps_modes.voltage_widget import VoltageWidget
from PowerSupply.ps_modes.voltage_plots import VoltagePlots
from PowerSupply.ps_modes.mode_1_widget import Mode1Widget
from PowerSupply.ps_modes.mode_5_widget import Mode5Widget

# formatted_time = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')  # Get the current date and time as a string
PROGRAM_NAME = "Actuator Test Bench"
PROGRAM_VERSION = "v1.0"

PLOT_UPDATE_RATE = 50 # new

class MainWindow(QWidget):
    def __init__(self, device = HvpsDevice(), parent=None): # new
        QWidget.__init__(self, parent=parent)

        # ************************************************************************************************************ #
        #                               ASSIGNMENT OF VALUES TO VARIABLES FOR OPTIONS
        # ************************************************************************************************************ #

        # self.debug_mode = 0             # 0: no debug mode;         1: debug mode.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_voltages = 1       # 0: no voltage plot;       1: high voltage plot;    2: high + low voltage plots.
        # self.display_currents = 0       # 0: no current plot;       1: current plot.
        # ------------------------------------------------------------------------------------------------------------ #
        # self.display_force = 0          # 0: no force plot;         1: force plot.
        # ------------------------------------------------------------------------------------------------------------ #
        static = 1                      # 0: no static mode;        1: static mode.
        # dynamic = 1                     # 0: no dynamic mode;       1: dynamic mode.
        # demo = 1                        # 0: no demonstration mode; 1: demonstration mode.

        # ************************************************************************************************************ #
        # NEW
        self.device = device
        self.available_boards = []

        # ************************************************************************************************************ #

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # New Interface Widgets

        # self.voltage = VoltageWidget(self.device)
        # self.mode1 = Mode1Widget(self.device)
        # self.mode5 = Mode5Widget(self.device)
        self.high_voltage_plot = VoltagePlots(title="High Voltage Monitor", y_max=2200)

        # POWER SUPPLY (High voltage power supply control panel).
        # board_1_port = 'COM3'
        # self.power_supply = PowerSupply(port_name=board_1_port,
        #                                 voltage_display=self.display_voltages,
        #                                 currents_display=self.display_currents)
        # serial = self.power_supply.ser

        # Modes
        self.static = StaticMode(self.device)
        # self.dynamic = DynamicMode()
        # self.demo = DemoMode()

        # ------------------------------------------------------------------------------------------------------------ #

        # FUTEK FORCE SENSOR (Load cell).
        # self.force_sensor = FutekSensor()
        # self.force_sensor_plot = FutekSensorPlot(self.force_sensor, controls=False)

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
        # NEW
        connection_layout = QHBoxLayout()
        self.board_select = QComboBox()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_available_boards)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._connect)
        clear_buffer_button = QPushButton("Clear Buffer")
        clear_buffer_button.clicked.connect(self.device.clear_buffer)
        save_buffer_button = QPushButton("Save Buffer")
        save_buffer_button.clicked.connect(lambda: self.device.save_buffer())
        
        connection_layout.addWidget(self.board_select)
        connection_layout.addWidget(refresh_button)
        connection_layout.addWidget(self.connect_button)
        connection_layout.addWidget(clear_buffer_button)
        connection_layout.addWidget(save_buffer_button)

        control_panel_layout.addLayout(connection_layout)

        # control_panel_layout.addWidget(self.voltage)

        # tabs = QTabWidget()
        # tabs.addTab(self.mode1, "Mode 1")
        # tabs.addTab(self.mode5, "Mode 5")
        # control_panel_layout.addWidget(tabs)

        # ------------------------------------------------------------------------------------------------------------ #

        # Type of characterization (static, dynamic, demo).
        characterization_type = QTabWidget()

        if static == 1:
            characterization_type.addTab(self.static, 'Static Characterization')

        # if dynamic == 1:
        #     characterization_type.addTab(self.dynamic, 'Dynamic Characterization')

        # if demo == 1:
        #     characterization_type.addTab(self.demo, 'Performance Demonstration')

        control_panel_layout.addWidget(characterization_type)
        # ------------------------------------------------------------------------------------------------------------ #

        # Control buttons
        # buttons_groupBox = QGroupBox("Control buttons")
        # buttons_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        # # buttons_groupBox.setFixedHeight(150)
        # control_panel_layout.addWidget(buttons_groupBox)
        # control_panel_layout.addSpacing(0)
        
        # button_layout = QVBoxLayout(buttons_groupBox)

        # self.emg_stop_btn = QPushButton("EMERGENCY STOP")
        # self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
        # self.emg_stop_btn.setStyleSheet("background-color: red; "
        #                                 "color: white; "
        #                                 "font-weight: bold; "
        #                                 'font-size: 24px;'
        #                                 "position: center; "
        #                                 "border: 1px solid black;")
        # button_layout.addWidget(self.emg_stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.emg_stop_btn.setFixedWidth(680)
        # self.emg_stop_btn.setFixedHeight(50)

        # self.tare_button = QPushButton("Tare")
        # self.tare_button.setStyleSheet("background-color: white; "
        #                                 "color: black; "
        #                                 "font-weight: bold; "
        #                                 'font-size: 24px;'
        #                                 "position: center; ")
        # button_layout.addWidget(self.tare_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.tare_button.clicked.connect(self.force_sensor.tare)
        # self.tare_button.setFixedWidth(680)
        # self.tare_button.setFixedHeight(50)

        # self.run_button = QPushButton("Run")
        # self.run_button.clicked.connect(self.run_button_clicked)
        # self.run_button.setStyleSheet("background-color: green; "
        #                                "color: white; "
        #                                "font-weight: bold; "
        #                                'font-size: 24px;'
        #                                "position: center; ")
        # button_layout.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignCenter)
        # self.run_button.setFixedWidth(680)
        # self.run_button.setFixedHeight(50)

        # button_layout.addStretch(1)

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
        # if self.display_force != 0:
        #     all_plots_layout.addWidget(self.force_sensor_plot)
        #     force_sensor_layout = QHBoxLayout()
        #     force_sensor_layout.addWidget(self.force_sensor_plot)
        #     all_plots_layout.addLayout(force_sensor_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY VOLTAGE PLOT
        if self.display_voltages != 0:
            voltage_layout = QHBoxLayout() 
            voltage_layout.addWidget(self.high_voltage_plot)
            all_plots_layout.addLayout(voltage_layout)

        # if self.display_voltages != 0:
        #     voltage_layout = QHBoxLayout()
        #     voltage_layout.addWidget(self.power_supply.voltage_plots)
        #     all_plots_layout.addLayout(voltage_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY CURRENT PLOTS
        # if self.display_currents != 0:
        #     currents_layout = QHBoxLayout()
        #     currents_layout.addWidget(self.power_supply.current_plots)
        #     all_plots_layout.addLayout(currents_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        plots_groupBox.setLayout(all_plots_layout)
        main_layout.addLayout(monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        #                                          CALLBACK FOR DATA READING
        # ************************************************************************************************************ #

        # self.plot_interval = 50#ms
        # self.start_time = 0
        # self.sample_rate = 400#Hz
        # self.interpolation_stop_time = 0

        # Set a timer with the callback function which reads and displays data from serial port.
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.plot_update_callback)
        # self.timer.start(self.plot_interval)

    # def attach_serial(self, serial):
    #     self.ser = serial

    # def send_command(self,ser, command):
    #     to_send = bytearray(command, encoding="utf-8")
    #     ser.write(to_send)

    # def emg_stop_btn_clicked(self):
    #     # send through the serial port
    #     to_send = "\r\nEStop\r\n"
    #     self.send_command(self.ser, to_send)
    #     # display information message
    #     print("[INFO] Emergency stop")

    # def run_button_clicked(self):
    #     if self.run_button.text() == "Run":
    #         self.start_time = time.perf_counter()
    #         # self.power_supply.start_recording()
    #         self.force_sensor.start_recording()
    #         self.run_button.setText("Stop")
    #         self.run_button.setStyleSheet("background-color: red; "
    #                                        "color: white; "
    #                                        "font-weight: bold; "
    #                                        'font-size: 24px;'
    #                                        "position: center; ")
    #     else:
    #         # self.power_supply.stop_recording()
    #         self.force_sensor.stop_recording()
    #         self.run_button.setText("Run")
    #         self.run_button.setStyleSheet("background-color: green; "
    #                                    "color: white; "
    #                                    "font-weight: bold; "
    #                                    'font-size: 24px;'
    #                                    "position: center; ")
        
    # ------------------------------------------------------------------------------------------------------------ #

        self._refresh_available_boards()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_plots)

    def _update_plots(self):
        data = self.device.get_buffer(clear_buffer=False)
        if data.shape[0] == 0:
            return
        # only take the last 50 values
        length = min(100, data.shape[0])
        data = data[-length:]
        time = (data[:, 1] - data[-1, 1])/1e3
        v_target = data[:, 2]
        v_monitor = data[:, 5]
        # self.voltage.update_label(v_monitor[-1])
        self.high_voltage_plot.update_plot(time,
                                           [v_target, v_monitor, v_monitor-v_target],
                                           [v_target[-1], v_monitor[-1], v_monitor[-1]-v_target[-1]])
        # currents = [data[:, i]/1e6 for i in range(6, 14)]
        # self.current_plot.update_plot(time, currents, [c[-1] for c in currents])

    def _refresh_available_boards(self):
        self.available_boards = self.device.detect()
        self.board_select.clear()
        self.board_select.addItems([f"Board {b['name']}" for b in self.available_boards])
        self.connect_button.setText("Connect")


    # def plot_update_callback(self):
        # if self.display_voltages !=0 or self.display_currents !=0:
        #     # self.power_supply.plot_update(self.start_time)
        # self.force_sensor_plot.plot_update(self.start_time)

        # new_power_supply_data = self.power_supply.get_new_data()
        # new_force_sensor_data = self.force_sensor.get_new_data()


        # if len(new_power_supply_data)>0 and len(new_force_sensor_data)>0:
        #     if self.interpolation_stop_time < self.start_time:
        #         interpolation_start_time = self.start_time
        #     else:
        #         interpolation_start_time = self.interpolation_stop_time + 1/self.sample_rate

        #     smallest_last_sample = min(new_power_supply_data[-1,0],new_force_sensor_data[-1,0])
        #     differential_time_latest_sample = smallest_last_sample - self.start_time
        #     interpolated_latest_sample_number = np.floor(differential_time_latest_sample/(1/self.sample_rate))
        #     self.interpolation_stop_time = self.start_time + interpolated_latest_sample_number*(1/self.sample_rate)

        #     interpolation_time = np.arange(interpolation_start_time,self.interpolation_stop_time,1/self.sample_rate)
        #     interpolated_force_sensor_data = np.interp(interpolation_time, new_force_sensor_data[:, 0], new_force_sensor_data[:, 1])
        #     interpolated_power_supply_data = np.zeros((len(interpolation_time), 11))
        #     for i1 in range(2, 11):
        #         interpolated_power_supply_data[:, i1] = np.interp(interpolation_time, new_power_supply_data[:, 0], new_power_supply_data[:, i1])

        #     time_s = interpolation_time
        #     force_mN = interpolated_force_sensor_data
        #     hv_set_kV = interpolated_power_supply_data[:,2]
        #     hv_vm_kV = interpolated_power_supply_data[:,3]
        #     hv_err_V = interpolated_power_supply_data[:,4]
        #     lv_set_V = interpolated_power_supply_data[:,5]
        #     lv_vm_V = interpolated_power_supply_data[:,6]
        #     lv_err_V = interpolated_power_supply_data[:,7]
        #     cm_w1_uA = interpolated_power_supply_data[:,8]
        #     cm_w2_uA = interpolated_power_supply_data[:,9]
        #     cm_w3_uA = interpolated_power_supply_data[:,10]

        #     # Create a folder to store the data files if it doesn't exist.
        #     folder_name = 'DataFiles'
        #     os.makedirs(folder_name, exist_ok=True)

        #     # Create a new .csv file within the folder with a file name, date and time of the experiment.
        #     file_name = os.path.join(folder_name, f"data_{formatted_time}.csv")
        #     if not os.path.isfile(file_name):
        #         with open(file_name, 'w') as f:
        #             f.write(f'Time (s), Force (mN), hv_set (V), hv_vm (V), hv_err (V), lv_set (V), lv_vm (V), lv_err (V), '
        #                     f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n')
                    
        #     # Save the data to the .csv file.   
        #     save_data = np.column_stack((time_s, force_mN, hv_set_kV, hv_vm_kV, hv_err_V, lv_set_V, lv_vm_V, lv_err_V,
        #                                 cm_w1_uA, cm_w2_uA, cm_w3_uA))
        #     with open(file_name, 'ab') as f:
        #         np.savetxt(f, save_data, fmt='%.8f, %4.6f, %4.0f, %4.0f, %.0f, %2.2f, %2.2f, %2.2f, %2.0f, %2.0f, %2.0f')

    # **************************************************************************************************************** #
            
    # def closeEvent(self, event):
    #     reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")

    #     if reply == QMessageBox.StandardButton.Yes:
    #         self.power_supply.stop_comm()

    #         event.accept()
    #         if self.debug_mode == 1:
    #             print("[INFO] Program closed.")

    #     else:
    #         event.ignore()

    # ************************************************************************************************************ #
    
    def _connect(self):
        if self.device.is_open:
            self.timer.stop()
            self.device.disconnect()
            self.connect_button.setText("Connect")
        else:
            index = self.board_select.currentIndex()
            if index == -1:
                return
            board = self.available_boards[index]
            if self.device.connect(board['device']):
                self.timer.start(PLOT_UPDATE_RATE)
                self.connect_button.setText("Disconnect")

    def closeEvent(self, event):
        self.timer.stop()
        self.device.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)

    window = MainWindow()
    window.show()
    window.showMaximized()

    app.exec()


if __name__ == '__main__':
    main()
