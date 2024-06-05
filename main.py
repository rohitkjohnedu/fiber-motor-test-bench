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
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QApplication, QPushButton, QTabWidget, QMessageBox, QScrollArea
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

        # Debug options.
        self.debug = 1                  # 0: full debug OFF;        1: full debug ON.
        self.power_supply_debug = 0     # 0: no power supply;       1: power supply.
        self.force_sensor_debug = 0     # 0: no force sensor;       1: force sensor.
        self.actuator_debug = 0         # 0: no actuator;           1: actuator.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_voltages = 2       # 0: no voltage plot;       1: high voltage plot;    2: high + low voltage plots.
        self.display_currents = 1       # 0: no current plot;       1: current plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_force = 1          # 0: no force plot;         1: force plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_position = 1       # 0: no actuator plot;      1: actuator plot.

        # Variables for the data interpolation.
        if self.debug == 0: # if debug mode is OFF
            self.plot_interval = 50#ms
            self.start_time = 0
            self.sample_rate = 400#Hz
            self.interpolation_stop_time = 0

            # Set a timer with the callback function which reads and displays data from the serial port.
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.plot_update_callback)
            if self.power_supply.auto_connect():
                self.timer.start(self.plot_interval)

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # HIGH VOLTAGE POWER SUPPLY.
        if self.power_supply_debug == 1: # if power supply is connected
            self.power_supply = HvpsDevice()
        else:
            self.power_supply = None # else no power supply

        # FUTEK FORCE SENSOR (Load cell).
        if self.force_sensor_debug == 1: # if force sensor is connected
            self.force_sensor = FutekSensor()
        else:
            self.force_sensor = None # else no force sensor

        # ACTUATOR (Translation stage)
        if self.actuator_debug == 1: # if actuator is connected
            self.actuator = StandaTable()
        else:
            self.actuator = None # else no actuator
        # ------------------------------------------------------------------------------------------------------------ #
        
        # Plots.
        self.voltage_plot = VoltagePlots(self.power_supply, plot_title='Voltage', y_hv_max=4500,
                                         y_lv_max=12, display_index=self.display_voltages)
        self.current_plot = CurrentPlots(self.power_supply, plot_title='Current', y_max=0.001)
        self.force_plot = ForcePlot(self.force_sensor)
        self.position_plot = PositionPlot(self.actuator)

        # Characterization.
        self.static = StaticMode(self.power_supply, self.force_sensor, self.actuator)
        self.dynamic = DynamicMode(self.power_supply, self.force_sensor, self.actuator)

        # Layouts.
        self.control_panel_layout = None
        self.monitoring_groupBox_layout = None

        # Control mode.
        self.run_btn_wdgt_static_flag = False
        self.run_btn_wdgt_dynamic_flag = False
        self.emg_stop_btn = None
        self.static.auto_mode_toggle.stateChanged.connect(self.run_btn_wdgt_static)
        self.dynamic.auto_mode_toggle.stateChanged.connect(self.run_btn_wdgt_dynamic)
        
        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #                                                             

        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        self.main_layout = QHBoxLayout(self)
        # self.setStyleSheet("background-color: white;")
        # ************************************************************************************************************ #

        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        self.control_panel_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #
        # Add the static and dynamic characterization tabs to the control panel
        self.add_scroll_area_control() # add scroll area to the static and dynamic characterization tabs

        self.characterization_type = QTabWidget()
        self.characterization_type.addTab(self.scroll_area_static, 'Static Characterization')
        self.characterization_type.addTab(self.scroll_area_dynamic, 'Dynamic Characterization')

        self.characterization_type.currentChanged.connect(self.tab_changed)

        self.control_panel_layout.addWidget(self.characterization_type)
        # ------------------------------------------------------------------------------------------------------------ #

        self.run_btn_wdgt_static() # add the RUN button to the control panel
        # ------------------------------------------------------------------------------------------------------------ #

        self.main_layout.addLayout(self.control_panel_layout) # add the control panel on the left side.

        # ************************************************************************************************************ #

        # MONITORING (Right side of the main window: force, voltage, currents and actuator position).
        self.monitoring_groupBox_layout = QVBoxLayout()

        self.plots_groupBox = QGroupBox("Monitoring")
        self.plots_groupBox.setStyleSheet('font-weight: bold;'
                                     'background-color: white;')

        all_plots_layout = QVBoxLayout()

        # FORCE SENSOR PLOT
        if self.display_force != 0:
            self.force_plot.setMinimumHeight(200)
            force_layout = QHBoxLayout()
            force_layout.addWidget(self.force_plot)
            all_plots_layout.addLayout(force_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR PLOT
        if self.display_position != 0:
            self.position_plot.setMinimumHeight(200)
            position_layout = QHBoxLayout()
            position_layout.addWidget(self.position_plot)
            all_plots_layout.addLayout(position_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY VOLTAGE PLOT
        if self.display_voltages != 0:
            self.voltage_plot.setMinimumHeight(200)
            voltage_layout = QHBoxLayout() 
            voltage_layout.addWidget(self.voltage_plot)
            all_plots_layout.addLayout(voltage_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # POWER SUPPLY CURRENT PLOTS
        if self.display_currents != 0:
            self.current_plot.setMinimumHeight(200)
            currents_layout = QHBoxLayout()
            currents_layout.addWidget(self.current_plot)
            all_plots_layout.addLayout(currents_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        self.plots_groupBox.setLayout(all_plots_layout)
        self.add_scroll_area_monitor() # add scroll area to the monitoring tab
        self.monitoring_groupBox_layout.addWidget(self.scroll_area_plots)
        
        self.main_layout.addLayout(self.monitoring_groupBox_layout, 1) # add the monitoring on the right side.

    # ************************************************************************************************************ #
    
    # Run button widget
    def tab_changed(self):
        if self.characterization_type.currentIndex() == 0:
            self.run_btn_wdgt_static()
        elif self.characterization_type.currentIndex() == 1:
            self.run_btn_wdgt_dynamic()
    # ************************************************************************************************************ #

    def run_btn_wdgt_static(self):
        toggle_state = self.static.auto_mode_toggle.isChecked()
        if toggle_state == False and self.run_btn_wdgt_dynamic_flag == False and self.run_btn_wdgt_static_flag == False:
            # -------------------------------------------------------------------------------------------------------- #
            if self.emg_stop_btn is not None:
                self.emg_stop_btn.deleteLater()
            #--------------------------------------------------------------------------------------------------------- #
            self.run_button = QPushButton("RUN")
            if self.debug == 0: # if debug mode is OFF
                self.run_button.clicked.connect(self.run_button_clicked)
            self.run_button.setStyleSheet("background-color: green; "
                                            "color: white; "
                                            "font-weight: bold; "
                                            "font-size: 24px;"
                                            "position: center; ")
            self.control_panel_layout.addWidget(self.run_button)
            # -------------------------------------------------------------------------------------------------------- #
            self.run_btn_wdgt_static_flag = True
        # ------------------------------------------------------------------------------------------------------------ #
        elif toggle_state == False and self.run_btn_wdgt_dynamic_flag == True:
            pass
        # ------------------------------------------------------------------------------------------------------------ #
        elif toggle_state == True and self.run_btn_wdgt_dynamic_flag == False and self.run_btn_wdgt_static_flag == False:
            pass
        # ------------------------------------------------------------------------------------------------------------ #
        else:
            if self.run_button is not None:
                self.run_button.deleteLater()
            # -------------------------------------------------------------------------------------------------------- #
            self.emg_stop_btn = QPushButton("EMERGENCY STOP")
            if self.power_supply is not None:
                self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
            self.emg_stop_btn.setStyleSheet("background-color: red; "
                                            "color: white; "
                                            "font-weight: bold; "
                                            "font-size: 24px; "
                                            "position: center; ")    
            self.control_panel_layout.addWidget(self.emg_stop_btn)
            # -------------------------------------------------------------------------------------------------------- #
            self.run_btn_wdgt_static_flag = False
            self.run_btn_wdgt_dynamic_flag = False
    # ************************************************************************************************************ #

    def run_btn_wdgt_dynamic(self):
        toggle_state = self.dynamic.auto_mode_toggle.isChecked()
        if toggle_state == False and self.run_btn_wdgt_static_flag == False and self.run_btn_wdgt_dynamic_flag == False:
            # -------------------------------------------------------------------------------------------------------- #
            if self.emg_stop_btn is not None:
                self.emg_stop_btn.deleteLater()
            # -------------------------------------------------------------------------------------------------------- #
            self.run_button = QPushButton("RUN")
            if self.debug == 0: # if debug mode is OFF
                self.run_button.clicked.connect(self.run_button_clicked)
            self.run_button.setStyleSheet("background-color: green; "
                                            "color: white; "
                                            "font-weight: bold; "
                                            "font-size: 24px;"
                                            "position: center; ")
            self.control_panel_layout.addWidget(self.run_button)
            # -------------------------------------------------------------------------------------------------------- #
            self.run_btn_wdgt_dynamic_flag = True
        # ------------------------------------------------------------------------------------------------------------ #
        elif toggle_state == False and self.run_btn_wdgt_static_flag == True:
            pass
        # ------------------------------------------------------------------------------------------------------------ #
        elif toggle_state == True and self.run_btn_wdgt_static_flag == False and self.run_btn_wdgt_dynamic_flag == False:
            pass
        # ------------------------------------------------------------------------------------------------------------ #
        else:
            if self.run_button is not None:
                self.run_button.deleteLater()
            # -------------------------------------------------------------------------------------------------------- #
            self.emg_stop_btn = QPushButton("EMERGENCY STOP")
            if self.power_supply is not None:
                self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
            self.emg_stop_btn.setStyleSheet("background-color: red; "
                                            "color: white; "
                                            "font-weight: bold; "
                                            "font-size: 24px; "
                                            "position: center; ")    
            self.control_panel_layout.addWidget(self.emg_stop_btn)
            # -------------------------------------------------------------------------------------------------------- #
            self.run_btn_wdgt_static_flag = False
            self.run_btn_wdgt_dynamic_flag = False
    # ************************************************************************************************************ #
    
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    # Recursively clear nested layouts
                    self.clear_layout(item.layout())
            layout.deleteLater()

    # ************************************************************************************************************ #
    #                                          CALLBACK FOR DATA READING
    # ************************************************************************************************************ #
    
    def add_scroll_area_control(self):
        self.scroll_area_static = QScrollArea()
        self.scroll_area_static.setWidget(self.static)
        self.scroll_area_static.setWidgetResizable(True)
        self.scroll_area_static.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

        self.scroll_area_dynamic = QScrollArea()
        self.scroll_area_dynamic.setWidget(self.dynamic)
        self.scroll_area_dynamic.setWidgetResizable(True)
        self.scroll_area_dynamic.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)

    def add_scroll_area_monitor(self):
        self.scroll_area_plots = QScrollArea()
        self.scroll_area_plots.setWidget(self.plots_groupBox)
        self.scroll_area_plots.setWidgetResizable(True)
        
    def run_button_clicked(self):
        if self.run_button.text() == "RUN":
            # -------------------------------------------------------------------------------------------------------- #
            print("\n[INFO] The measurement is running")
            self.run_button.setText("STOP")
            self.run_button.setStyleSheet("background-color: red; "
                                           "color: white; "
                                           "font-weight: bold; "
                                           "font-size: 24px;"
                                           "position: center; ")
            # -------------------------------------------------------------------------------------------------------- #
            self.start_time = time.perf_counter()

            if self.power_supply_debug == 1: # if power supply is connected
                self.power_supply.start_recording()
            if self.force_sensor_debug == 1: # if force sensor is connected
                self.force_sensor.start_recording()
            if self.actuator_debug == 1: # if actuator is connected
                self.actuator.start_recording()
            # -------------------------------------------------------------------------------------------------------- #
            if self.static.characterization_type_layout.currentIndex() == 0:
                self.static.run_static(self.start_time)
            # elif self.static.characterization_type_layout.currentIndex() == 1:
            #     self.dynamic.run_dynamic()
            # -------------------------------------------------------------------------------------------------------- #

        else:
            # -------------------------------------------------------------------------------------------------------- #
            print("\n[INFO] The measurement is stopped")
            self.run_button.setText("RUN")
            self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       "font-size: 24px;"
                                       "position: center; ")
            # -------------------------------------------------------------------------------------------------------- #
            self.emg_stop_btn_clicked()
            
            if self.power_supply_debug == 1:
                self.power_supply.stop_recording()
            if self.force_sensor_debug == 1:
                self.force_sensor.stop_recording()
            if self.actuator_debug == 1:
                self.actuator.stop_recording()
            # -------------------------------------------------------------------------------------------------------- #
        
    def emg_stop_btn_clicked(self):
        self.power_supply.emergency_stop()
        self.actuator.stop()
    
    def plot_update_callback(self):
        if self.power_supply_debug == 1:
            self.voltage_plot.plot_update(self.start_time)
            self.current_plot.plot_update(self.start_time)
        if self.force_sensor_debug == 1:
            self.force_plot.plot_update(self.start_time)
        if self.actuator_debug == 1:
            self.position_plot.plot_update(self.start_time)

        if self.power_supply_debug == 1:
            new_power_supply_data = self.power_supply.get_new_data()
        if self.force_sensor_debug == 1:
            new_force_sensor_data = self.force_sensor.get_new_data()
        if self.actuator_debug == 1:
            new_actuator_data = self.actuator.get_new_data()

        if len(new_power_supply_data)>0 and len(new_force_sensor_data)>0 and len(new_actuator_data)>0:
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
            if self.debug == 0: # if debug mode is OFF
                self.timer.stop()
            # explicit disconnection of the devices
            if self.power_supply_debug == 1: # if power supply is connected
                self.power_supply.disconnect()
            if self.force_sensor_debug == 1: # if force sensor is connected
                self.force_sensor.disconnect()
            if self.actuator_debug == 1: # if actuator is connected
                self.actuator.disconnect()
            event.accept()
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
