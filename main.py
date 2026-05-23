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
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QUrl
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QApplication, QPushButton,
                                QTabWidget, QScrollArea, QMessageBox, QProgressBar, QDialog, QLabel,
                                QLineEdit, QTextEdit)
from PyQt6.QtGui import QDesktopServices, QFont
from pathlib import Path
import time
import os.path
from threading import Thread

# custom packages
from PowerSupply import HvpsDevice, VoltagePlots, CurrentPlots, StaticMode, DynamicMode
from ForceSensor import FutekSensor, ForcePlot
from StandaTable import StandaTable, PositionPlot

PROGRAM_NAME = "Linear Actuator Test Bench"
PROGRAM_VERSION = "v1.0"

class LoadingWorker(QThread):
    initialization_finished = pyqtSignal(bool)
    def __init__(self, actuator, parent=None):
        super().__init__(parent)
        self.actuator = actuator
    
    def run(self):
        result = self.actuator.home_zero()
        self.initialization_finished.emit(result)

#############################################################################################################################

class InfProgressBar(QDialog):
    def __init__(self, title="InfProgressBar", message="Please wait for the end."):
        super().__init__()
    
        self.setWindowTitle(title)
        self.setFixedSize(300, 100)

        inf_label = QLabel(message)
        inf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet("font-weight: bold; font-size: 16px;")

        layout = QVBoxLayout()
        layout.addWidget(inf_label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

#############################################################################################################################

class MainWindow(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        # ************************************************************************************************************ #
        #                                               OPTIONS
        # ************************************************************************************************************ #

        # Debug options.
        self.debug = 2                      # 0: full debug OFF;        1: full debug ON;        2: comments only.
        if self.debug == 1:
            self.power_supply_debug = 0     # 0: no power supply.
            self.force_sensor_debug = 0     # 0: no force sensor.
            self.actuator_debug = 0         # 0: no actuator.
        else:
            self.power_supply_debug = 1     # 1: power supply.
            self.force_sensor_debug = 1     # 1: force sensor.
            self.actuator_debug = 1         # 1: actuator.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_voltages = 1       # 0: no voltage plot;     1: high voltage plot;    2: high + low voltage plots.
        self.display_currents = 1       # 0: no current plot;     1: current plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_force = 1          # 0: no force plot;       1: force plot.
        # ------------------------------------------------------------------------------------------------------------ #
        self.display_position = 1       # 0: no actuator plot;    1: actuator plot.

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # HIGH VOLTAGE POWER SUPPLY.
        if self.power_supply_debug == 1: # if power supply is connected
            self.power_supply = HvpsDevice()
        else:
            self.power_supply = None # else no power supply
        # ------------------------------------------------------------------------------------------------------------ #

        # FUTEK serial number fields — created before instantiation so the constructor can use them
        self.futek_sn_edit = QLineEdit("725662")
        self.futek_sn_edit.setPlaceholderText("e.g. 725662")
        self.futek_sn_edit.setFixedWidth(100)

        self.futek_sn2_edit = QLineEdit("")
        self.futek_sn2_edit.setPlaceholderText("e.g. optional")
        self.futek_sn2_edit.setFixedWidth(100)

        # FUTEK FORCE SENSOR (Load cell).
        if self.force_sensor_debug == 1: # if force sensor is connected
            self.force_sensor = FutekSensor(serial_number=self.futek_sn_edit.text().strip())
        else:
            self.force_sensor = None # else no force sensor

        # Second force sensor — only created if a serial number is specified at startup.
        self.force_sensor2 = None
        _sn2 = self.futek_sn2_edit.text().strip()
        if self.force_sensor_debug == 1 and _sn2:
            self.force_sensor2 = FutekSensor(serial_number=_sn2)

        # Read FUTEK registers once (must happen before start_recording() — DLL is not thread-safe)
        self._futek_register_text = "Not connected."
        self._futek_register2_text = "Not connected."
        if self.force_sensor_debug == 1 and self.force_sensor is not None:
            self._futek_register_text = self._read_futek_registers()
        if self.force_sensor_debug == 1 and self.force_sensor2 is not None:
            self._futek_register2_text = self._read_futek_registers(self.force_sensor2)
        # ------------------------------------------------------------------------------------------------------------ #

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
        self.force_plot = ForcePlot(self.force_sensor, self.force_sensor2)
        self.position_plot = PositionPlot(self.actuator)
        # ------------------------------------------------------------------------------------------------------------ #

        # Characterization.
        self.static = StaticMode(self.power_supply, self.force_sensor, self.actuator, self.debug, force_sensor2=self.force_sensor2)
        self.dynamic = DynamicMode(self.power_supply, self.force_sensor, self.actuator, self.debug)
        # ------------------------------------------------------------------------------------------------------------ #

        # Layouts.
        self.control_panel_layout = None
        self.monitoring_groupBox_layout = None
        # ------------------------------------------------------------------------------------------------------------ #

        # Control mode.
        self.run_btn_wdgt_static_flag = False
        self.run_btn_wdgt_dynamic_flag = False
        self.emg_stop_btn = None
        # ------------------------------------------------------------------------------------------------------------ #
        
        # Variables for the data interpolation.
        if not self.debug == 1: # if debug mode is not OFF
            self.plot_interval = 50#ms
            self.start_time = 0
            self.sample_rate = 400#Hz
            self.interpolation_stop_time = 0

            # Set a timer with the callback function which reads and displays data from the serial port.
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.plot_update_callback)
            if self.power_supply.auto_connect():
                self.timer.start(self.plot_interval)
        # ------------------------------------------------------------------------------------------------------------ #

        # Signalization about finishing the experiment.
        self.static.finished.connect(self.run_button_clicked)
        
        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #                                                             

        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        self.main_layout = QHBoxLayout(self)
        # ************************************************************************************************************ #

        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        self.control_panel_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #
        # Add the static and dynamic characterization tabs to the control panel.
        self.add_scroll_area_control() # add scroll area to the static and dynamic characterization tabs.

        # FUTEK device serial number selector (two sensors)
        futek_group = QGroupBox("FUTEK IPM650")
        futek_group.setStyleSheet("font-weight: bold;")
        futek_group_layout = QVBoxLayout(futek_group)

        sn1_row = QHBoxLayout()
        futek_sn1_label = QLabel("Sensor 1 S/N:")
        futek_sn1_label.setStyleSheet("font-weight: normal;")
        sn1_row.addWidget(futek_sn1_label)
        sn1_row.addWidget(self.futek_sn_edit)
        self.futek_apply_btn = QPushButton("Apply")
        self.futek_apply_btn.setFixedWidth(60)
        self.futek_apply_btn.setStyleSheet("font-weight: normal;")
        self.futek_apply_btn.clicked.connect(self._apply_futek_sn)
        sn1_row.addWidget(self.futek_apply_btn)
        sn1_row.addStretch()
        futek_group_layout.addLayout(sn1_row)

        sn2_row = QHBoxLayout()
        futek_sn2_label = QLabel("Sensor 2 S/N:")
        futek_sn2_label.setStyleSheet("font-weight: normal;")
        sn2_row.addWidget(futek_sn2_label)
        sn2_row.addWidget(self.futek_sn2_edit)
        self.futek_apply2_btn = QPushButton("Apply")
        self.futek_apply2_btn.setFixedWidth(60)
        self.futek_apply2_btn.setStyleSheet("font-weight: normal;")
        self.futek_apply2_btn.clicked.connect(self._apply_futek_sn2)
        sn2_row.addWidget(self.futek_apply2_btn)
        sn2_row.addStretch()
        futek_group_layout.addLayout(sn2_row)

        self.control_panel_layout.addWidget(futek_group)

        self.characterization_type = QTabWidget()
        self.characterization_type.addTab(self.scroll_area_static, 'Static Characterization')
        self.characterization_type.addTab(self.scroll_area_dynamic, 'Dynamic Characterization')

        self.control_panel_layout.addWidget(self.characterization_type)
        # ------------------------------------------------------------------------------------------------------------ #
        # RUN button
        self.run_button = QPushButton("RUN")
        if not self.debug == 1: # if debug mode is not OFF
            self.run_button.clicked.connect(self.run_button_clicked)
        self.run_button.setStyleSheet("background-color: green; "
                                        "color: white; "
                                        "font-weight: bold; "
                                        "font-size: 24px;"
                                        "position: center; ")
        self.control_panel_layout.addWidget(self.run_button)
        # ------------------------------------------------------------------------------------------------------------ #
        self.main_layout.addLayout(self.control_panel_layout) # add the control panel on the left side.

        # ************************************************************************************************************ #

        # MONITORING (Right side of the main window: force, voltage, currents and actuator position).
        self.monitoring_groupBox_layout = QVBoxLayout()

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

        # Group box for the plots.
        self.plots_groupBox = QGroupBox("Monitoring")
        self.plots_groupBox.setStyleSheet('font-weight: bold;'
                                     'background-color: white;')
        self.plots_groupBox.setLayout(all_plots_layout)
        # ------------------------------------------------------------------------------------------------------------ #

        # Add the plots to the monitoring layout.
        self.add_scroll_area_monitor() # add scroll area to the monitoring tab.
        self.monitoring_tabs = QTabWidget()
        self.monitoring_tabs.addTab(self.scroll_area_plots, "Graphs")
        self.monitoring_tabs.addTab(self._build_raw_data_tab(), "Raw Data")
        self.monitoring_groupBox_layout.addWidget(self.monitoring_tabs)
        # ------------------------------------------------------------------------------------------------------------ #
        self.main_layout.addLayout(self.monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #
        if not self.debug == 1: # if debug mode is not OFF
            if self.power_supply.sample == 10000000 - 1:
                self.power_supply.clear_buffer()
                print("Power supply buffer cleared.")
            if self.force_sensor.sample == 10000000 - 1:
                self.force_sensor.clear_buffer()
                print("Force sensor buffer cleared.")
            if self.actuator.sample == 10000000 - 1:
                self.actuator.clear_buffer()
                print("Actuator buffer cleared.")
    
    # **************************************************************************************************************** #
    #                                       FUNCTIONS FOR THE USER INTERFACE
    # **************************************************************************************************************** #  
    
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
    
    # ************************************************************************************************************ #

    def start_recording(self):
        self.start_time = time.perf_counter()
        if self.power_supply_debug == 1:
            self.power_supply.start_recording()
        if self.force_sensor_debug == 1:
            self.force_sensor.start_recording()
            if self.force_sensor2 is not None:
                self.force_sensor2.start_recording()
        if self.actuator_debug == 1:
            self.actuator.start_recording()

        # Automatic mode
        if self.characterization_type.currentIndex() == 0: # if static characterization is selected
            if self.static.auto_mode_toggle.isChecked() == True: # if automatic mode is selected
                self.running_thread = Thread(target=self.static.run_static)
                self.running_thread.start()

    def stop_recording(self):
        self.emg_stop_btn_clicked()
        if self.power_supply_debug == 1:
            self.power_supply.stop_recording()
        if self.force_sensor_debug == 1:
            self.force_sensor.stop_recording()
            if self.force_sensor2 is not None:
                self.force_sensor2.stop_recording()
        if self.actuator_debug == 1:
            self.actuator.stop_recording()

    # ************************************************************************************************************ #
        
    def run_button_clicked(self):
        if self.run_button.text() == "RUN":
            # -------------------------------------------------------------------------------------------------------- #
            print("\n[INFO] The measurement is started")
            self.run_button.setText("STOP")
            self.run_button.setStyleSheet("background-color: red; "
                                           "color: white; "
                                           "font-weight: bold; "
                                           "font-size: 24px;"
                                           "position: center; ")
            self.futek_sn_edit.setEnabled(False)
            self.futek_apply_btn.setEnabled(False)
            self.futek_sn2_edit.setEnabled(False)
            self.futek_apply2_btn.setEnabled(False)
            # -------------------------------------------------------------------------------------------------------- #
            if self.characterization_type.currentIndex() == 0: # if static characterization is selected
                self.do_static_characterization()
            elif self.characterization_type.currentIndex() == 1: # if dynamic characterization is selected
                self.do_dynamic_characterization()
        else: # STOP
            # -------------------------------------------------------------------------------------------------------- #
            print("\n[INFO] The measurement is stopped")
            self.run_button.setText("RUN")
            self.run_button.setStyleSheet("background-color: green; "
                                       "color: white; "
                                       "font-weight: bold; "
                                       "font-size: 24px;"
                                       "position: center; ")
            self.futek_sn_edit.setEnabled(True)
            self.futek_apply_btn.setEnabled(True)
            self.futek_sn2_edit.setEnabled(True)
            self.futek_apply2_btn.setEnabled(True)
            # -------------------------------------------------------------------------------------------------------- #
            if self.characterization_type.currentIndex() == 0: # if static characterization is selected
                self.stop_static_characterization()
            elif self.characterization_type.currentIndex() == 1: # if dynamic characterization is selected
                self.stop_dynamic_characterization()
            # -------------------------------------------------------------------------------------------------------- #
    
    # ************************************************************************************************************ #
    
    def do_static_characterization(self):
        # Automatic mode turn ON
        if self.static.auto_mode_toggle.isChecked() == True: # if automatic mode is selected
            self.static.stop_event.clear()
            if self.static.actuator_control.home_chckbox.isChecked(): # if homing is selected
                self.initialization() # homing the actuator
            else:
                self.start_recording()  # without homing
            self.static.disable_all_widgets(self.static.characterization_type_layout, disable=1)
        # -------------------------------------------------------------------------------------------------------- #
        # Manual mode turn ON
        elif self.static.auto_mode_toggle.isChecked() == False: # if manual mode is selected
            self.static.disable_all_widgets(self.static.control_panel_layout, disable=0)
            self.static.auto_mode_toggle.setDisabled(True)
            self.static.auto_label.setDisabled(True)
            self.static.manual_label.setDisabled(True)
            self.start_recording()
            self.static.start_indiv_rcd()
    
    # ************************************************************************************************************ #

    def stop_static_characterization(self):
        # Automatic mode turn OFF
        if self.static.auto_mode_toggle.isChecked() == True:
            # stop manually
            if self.running_thread.is_alive():
                self.static.stop_event.set()
                self.running_thread.join()
                self.stop_recording()
                self.static.disable_all_widgets(self.static.characterization_type_layout, disable=0)
                self.msg_finished("StaticCharacterization", "Auto")
            # stop automatically
            else:
                self.stop_recording()
                self.static.disable_all_widgets(self.static.characterization_type_layout, disable=0)
                if self.static.zero_step_flag == 1:
                    QMessageBox.warning(self, "Warning", "The step size is cannot be zero. Please change the step size.")
                elif self.static.out_of_range_volt_flag == 1:
                    QMessageBox.warning(self, "Warning", "The voltage is out of the range.\nPlease change the voltage in range [950; 4500].")
                elif self.static.zero_step_volt_flag == 1:
                    QMessageBox.warning(self, "Warning", "The voltage step is cannot be zero. Please change the voltage step.")
                elif self.static.out_of_range_freq_flag == 1:
                    QMessageBox.warning(self, "Warning", "The frequency is out of the range.\nPlease change the frequency in range [0; 1000].")
                elif self.static.zero_step_freq_flag == 1:
                    QMessageBox.warning(self, "Warning", "The frequency step is cannot be zero. Please change the frequency step.")
                else:
                    self.msg_finished("StaticCharacterization", "Auto")
                
        # -------------------------------------------------------------------------------------------------------- #
        # Manual mode turn OFF
        elif self.static.auto_mode_toggle.isChecked() == False:
            self.static.stop_indiv_rcd()
            self.stop_recording()
            self.static.disable_all_widgets(self.static.control_panel_layout, disable=1)
            self.static.auto_mode_toggle.setDisabled(False)
            self.static.auto_label.setDisabled(False)
            self.static.manual_label.setDisabled(False)
            time.sleep(0.1)
            if self.static.data_save_opt.isChecked() == True:
                self.static.remove_temp_files()
            self.msg_finished("StaticCharacterization", "Manual")
        
        # -------------------------------------------------------------------------------------------------------- #
        # # Clear data buffers
        # if self.power_supply_debug == 1:
        #     self.power_supply.clear_buffer()
        # if self.force_sensor_debug == 1:
        #     self.force_sensor.clear_buffer()
        # if self.actuator_debug == 1:
        #     self.actuator.clear_buffer()

    # ************************************************************************************************************ #

    def do_dynamic_characterization(self):
        # Automatic mode turn ON
        if self.dynamic.auto_mode_toggle.isChecked() == True: # if automatic mode is selected
            pass
            # self.dynamic.stop_event.clear()
            # if self.dynamic.actuator_control.home_chckbox.isChecked(): # if homing is selected
            #     self.initialization() # homing the actuator
            # else:
            #     self.start_recording()  # without homing
            # self.dynamic.disable_all_widgets(self.dynamic.characterization_type_layout, disable=1)
        # -------------------------------------------------------------------------------------------------------- #
        # Manual mode turn ON
        elif self.dynamic.auto_mode_toggle.isChecked() == False: # if manual mode is selected
            self.dynamic.disable_all_widgets(self.dynamic.control_panel_layout, disable=0)
            self.dynamic.auto_mode_toggle.setDisabled(True)
            self.dynamic.auto_label.setDisabled(True)
            self.dynamic.manual_label.setDisabled(True)
            self.start_recording()
            self.dynamic.start_indiv_rcd()
    
    # ************************************************************************************************************ #

    def stop_dynamic_characterization(self):
        # Automatic mode turn OFF
        if self.dynamic.auto_mode_toggle.isChecked() == True:
            pass
            # # stop manually
            # if self.running_thread.is_alive():
            #     self.dynamic.stop_event.set()
            #     self.running_thread.join()
            #     self.stop_recording()
            #     self.dynamic.disable_all_widgets(self.dynamic.characterization_type_layout, disable=0)
            #     self.msg_finished("Auto")
            # else:
            #     # stop automatically
            #     self.stop_recording()
            #     self.dynamic.disable_all_widgets(self.dynamic.characterization_type_layout, disable=0)
            #     if self.dynamic.zero_step_flag == 1:
            #         QMessageBox.warning(self, "Warning", "The step size is cannot be zero. Please change the step size.")
            #     else:
            #         self.msg_finished("Auto")
        # -------------------------------------------------------------------------------------------------------- #
        # Manual mode turn OFF
        elif self.dynamic.auto_mode_toggle.isChecked() == False:
            self.dynamic.stop_indiv_rcd()
            self.stop_recording()
            self.dynamic.disable_all_widgets(self.dynamic.control_panel_layout, disable=1)
            self.dynamic.auto_mode_toggle.setDisabled(False)
            self.dynamic.auto_label.setDisabled(False)
            self.dynamic.manual_label.setDisabled(False)
            time.sleep(0.1)
            if self.dynamic.data_save_opt.isChecked() == True:
                self.dynamic.remove_temp_files()
            self.msg_finished("DynamicCharacterization", "Manual")
        
        # -------------------------------------------------------------------------------------------------------- #
        # # Clear data buffers
        # if self.power_supply_debug == 1:
        #     self.power_supply.clear_buffer()
        # if self.force_sensor_debug == 1:
        #     self.force_sensor.clear_buffer()
        # if self.actuator_debug == 1:
        #     self.actuator.clear_buffer()
    
    # ************************************************************************************************************ #

    def msg_finished(self, characterization, mode):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText("The measurement is finished.")
        msg_box.setWindowTitle("Information")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        open_folder_btn = QPushButton("Open Data Folder")
        msg_box.addButton(open_folder_btn, QMessageBox.ButtonRole.ActionRole)

        msg_box.exec()

        if msg_box.clickedButton() == open_folder_btn:
            if characterization == "StaticCharacterization":
                if self.static.folder_path == "Default":
                    home_dir = str(Path.home())
                    data_folder = f"OneDrive - epfl.ch/Documents/GitHub/actuator_test_bench_software/DataFiles/{characterization}/{mode}"
                    os.makedirs(os.path.join(home_dir, data_folder), exist_ok=True)
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(home_dir, data_folder)))
                else:
                    path = os.path.join(self.static.folder_path, characterization, mode)
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            elif characterization == "DynamicCharacterization":
                if self.dynamic.folder_path == "Default":
                    home_dir = str(Path.home())
                    data_folder = f"OneDrive - epfl.ch/Documents/GitHub/actuator_test_bench_software/DataFiles/{characterization}/{mode}"
                    os.makedirs(os.path.join(home_dir, data_folder), exist_ok=True)
                    QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(home_dir, data_folder)))
                else:
                    path = os.path.join(self.dynamic.folder_path, characterization, mode)
                    QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif msg_box.clickedButton() == QMessageBox.StandardButton.Ok:
            msg_box.close()
            
    # ************************************************************************************************************ #

    def emg_stop_btn_clicked(self):
        self.power_supply.emergency_stop()
        self.actuator.stop()
    
    # ************************************************************************************************************ #

    # Initialization of the actuator.
    def initialization(self):
        self.initializator = LoadingWorker(self.actuator)
        self.initializator.initialization_finished.connect(self.initialization_finished)

        self.loading = InfProgressBar(title="Initialization", message="Please wait while the system is initializing.")
        self.loading.show()

        self.loading.progress_bar.setRange(0, 0)
        self.initializator.start()

    def initialization_finished(self, result):
        self.initializator.terminate()
        self.loading.progress_bar.setRange(0, 1)
        self.loading.progress_bar.setValue(1 if result else 0)
        time.sleep(1)
        self.loading.close()
        # -------------------------------------------------------------------------------------------------------- #
        if result:
            message = QMessageBox(self)
            message.setIcon(QMessageBox.Icon.Information)
            message.setWindowTitle('Initialization')
            message.setText('Initialization completed!')
            message.setStandardButtons(QMessageBox.StandardButton.Ok)
            QTimer.singleShot(1000, message.accept) # close message box:
            message.exec()
        # -------------------------------------------------------------------------------------------------------- #
        self.start_recording()
        return result
    
    # ************************************************************************************************************ #

    def plot_update_callback(self):
        if self.power_supply_debug == 1:
            self.voltage_plot.plot_update(self.start_time)
            self.current_plot.plot_update(self.start_time)
        if self.force_sensor_debug == 1:
            self.force_plot.plot_update(self.start_time)
        if self.actuator_debug == 1:
            self.position_plot.plot_update(self.start_time)
        if self.monitoring_tabs.currentIndex() == 1:
            self._update_raw_data_tab()

    # **************************************************************************************************************** #

    def _apply_futek_sn(self):
        if self.force_sensor_debug != 1 or self.force_sensor is None:
            return
        new_sn = self.futek_sn_edit.text().strip()
        if not new_sn:
            return
        self.futek_apply_btn.setEnabled(False)
        self.futek_apply_btn.setText("…")
        QApplication.processEvents()

        self.force_sensor.disconnect()
        self.force_sensor.connect(serial_number=new_sn)

        self._futek_register_text = self._read_futek_registers()
        self.raw_futek_display.setPlainText(self._futek_register_text)

        self.futek_apply_btn.setText("Apply")
        self.futek_apply_btn.setEnabled(True)

    def _apply_futek_sn2(self):
        if self.force_sensor_debug != 1:
            return
        new_sn = self.futek_sn2_edit.text().strip()
        if not new_sn:
            return
        self.futek_apply2_btn.setEnabled(False)
        self.futek_apply2_btn.setText("…")
        QApplication.processEvents()

        if self.force_sensor2 is not None:
            self.force_sensor2.disconnect()
            self.force_sensor2.connect(serial_number=new_sn)
        else:
            self.force_sensor2 = FutekSensor(serial_number=new_sn)
            self.force_plot.set_sensor2(self.force_sensor2)

        # Propagate the (possibly new) reference to characterization modes so
        # they tare the correct object during experiments.
        self.static.force_sensor2 = self.force_sensor2

        self._futek_register2_text = self._read_futek_registers(self.force_sensor2)

        self.futek_apply2_btn.setText("Apply")
        self.futek_apply2_btn.setEnabled(True)

    def _read_futek_registers(self, sensor=None):
        if sensor is None:
            sensor = self.force_sensor
        try:
            from ForceSensor.futek import FUTEK_UNITS_CODE
            s   = sensor
            dll = s.futek_dll
            h   = s.device_handle

            reg5_raw = dll.Get_Internal_Register(h, 5)
            reg6_raw = dll.Get_Internal_Register(h, 6)
            reg5 = int(reg5_raw)
            reg6 = int(reg6_raw)

            dp = reg6 >> 16
            uc = (reg6 & 0xFF00) >> 8
            dc = reg6 & 0xFF
            unit_name = FUTEK_UNITS_CODE[uc]["unit_name"] if uc in FUTEK_UNITS_CODE else "unknown"
            conv      = FUTEK_UNITS_CODE[uc]["conversion_to_mN"] if uc in FUTEK_UNITS_CODE else 1.0
            raw_cap   = reg5 * 10 ** (-dp)
            cap_mn    = raw_cap * conv * (1 if dc else -1)

            lines = [
                f"{'Firmware:':<14}{s.firmware_version:<12}  {'Board type:':<14}{s.board_type}",
                f"{'IPM650 S/N:':<14}{s.device_sn:<12}  {'Sensor ID:':<14}{s.sensor_id}",
                "",
                f"{'Register':<10}{'Value':>12}    Description",
                "-" * 52,
                f"{'Reg 1':<10}{s.tare_register_value:>12,.0f}    Tare register",
                f"{'Reg 2':<10}{s.offset:>12,.0f}    Zero (offset)",
                f"{'Reg 3':<10}{s.fullscale_value:>12,.0f}    Full scale",
                f"{'Reg 5':<10}{reg5:>12,}    Capacity raw value",
                f"{'Reg 6':<10}{reg6:>12,}    Capacity details:",
                f"{'':10}{'':>12}      decimal_point = {dp}  (x 10^-{dp})",
                f"{'':10}{'':>12}      unit_code     = {uc}  ({unit_name}, x{conv} mN)",
                f"{'':10}{'':>12}      direction     = {dc}  ({'positive' if dc else 'negative'})",
                "",
                f"Computed: {reg5} x 10^-{dp} x {conv} = {cap_mn:.4g} mN",
            ]
            return "\n".join(lines)
        except Exception as exc:
            return f"Error reading FUTEK registers:\n{exc}"

    def _build_raw_data_tab(self):
        mono = QFont("Courier New", 9)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)

        futek_box = QGroupBox("FUTEK IPM650")
        futek_vl = QVBoxLayout(futek_box)
        self.raw_futek_display = QTextEdit()
        self.raw_futek_display.setReadOnly(True)
        self.raw_futek_display.setFont(mono)
        self.raw_futek_display.setPlainText(self._futek_register_text)
        self.raw_futek_display.setMinimumHeight(200)
        futek_vl.addWidget(self.raw_futek_display)
        layout.addWidget(futek_box)

        standa_box = QGroupBox("Standa Translation Stage")
        standa_vl = QVBoxLayout(standa_box)
        self.raw_standa_display = QTextEdit()
        self.raw_standa_display.setReadOnly(True)
        self.raw_standa_display.setFont(mono)
        self.raw_standa_display.setPlaceholderText("No data yet — start recording.")
        self.raw_standa_display.setFixedHeight(80)
        standa_vl.addWidget(self.raw_standa_display)
        layout.addWidget(standa_box)

        hvps_box = QGroupBox("High Voltage Power Supply")
        hvps_vl = QVBoxLayout(hvps_box)
        self.raw_hvps_display = QTextEdit()
        self.raw_hvps_display.setReadOnly(True)
        self.raw_hvps_display.setFont(mono)
        self.raw_hvps_display.setPlaceholderText("No data yet — start recording.")
        self.raw_hvps_display.setFixedHeight(160)
        hvps_vl.addWidget(self.raw_hvps_display)
        layout.addWidget(hvps_box)

        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        return scroll

    def _update_raw_data_tab(self):
        if self.force_sensor_debug == 1 and self.force_sensor is not None:
            try:
                t, f = self.force_sensor.get_buffer()
                s2_line = ""
                if self.force_sensor2 is not None and self.force_sensor2.is_connected:
                    try:
                        _, f2 = self.force_sensor2.get_buffer()
                        if len(f2) > 0:
                            s2_line = f"\nSensor 2 Live Force:  {f2[-1]:+.4f} mN"
                    except Exception:
                        pass
                if len(f) > 0:
                    self.raw_futek_display.setPlainText(
                        self._futek_register_text
                        + f"\n\nSensor 1 Live Force:  {f[-1]:+.4f} mN"
                        + s2_line
                    )
            except Exception:
                pass

        if self.actuator_debug == 1 and self.actuator is not None:
            try:
                t, pos, spd = self.actuator.get_buffer()
                if len(pos) > 0:
                    lines = [
                        f"{'Position:':<14}{pos[-1]:>10.4f}  mm",
                        f"{'Speed:':<14}{spd[-1]:>10.4f}  mm/s",
                    ]
                    self.raw_standa_display.setPlainText("\n".join(lines))
            except Exception:
                pass

        if self.power_supply_debug == 1 and self.power_supply is not None:
            try:
                data = self.power_supply.get_buffer()
                if len(data) > 0:
                    r = data[-1]
                    lines = [
                        f"{'HV set:':<16}{r[2]:>10.2f}  V    {'HV measured:':<16}{r[3]:>10.2f}  V    err: {r[4]:+.2f} V",
                        f"{'LV set:':<16}{r[5]:>10.2f}  V    {'LV measured:':<16}{r[6]:>10.2f}  V    err: {r[7]:+.2f} V",
                        "",
                        f"{'Current W1:':<16}{r[8]*1000:>10.4f}  mA",
                        f"{'Current W2:':<16}{r[9]*1000:>10.4f}  mA",
                        f"{'Current W3:':<16}{r[10]*1000:>10.4f}  mA",
                    ]
                    self.raw_hvps_display.setPlainText("\n".join(lines))
            except Exception:
                pass

    # **************************************************************************************************************** #

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")
        if reply == QMessageBox.StandardButton.Yes:
            if not self.debug == 1: # if debug mode is not OFF
                self.timer.stop()
            # explicit disconnection of the devices
            if self.power_supply_debug == 1: # if power supply is connected
                self.power_supply.disconnect()
            if self.force_sensor_debug == 1: # if force sensor is connected
                self.force_sensor.disconnect()
                if self.force_sensor2 is not None:
                    self.force_sensor2.disconnect()
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
