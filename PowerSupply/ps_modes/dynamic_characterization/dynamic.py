# python packages
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QGroupBox, QFormLayout, QLabel, QPushButton, QComboBox,
                             QVBoxLayout, QLineEdit, QHBoxLayout, QFrame, QCheckBox)
import numpy as np
import time
import threading
from datetime import datetime
import os.path
# custom packages
from PowerSupply.ps_modes.dynamic_characterization.dynamic_ps import Dynamic_PS
from StandaTable.standa_table import StandaTableWidget
from tools.gui_tools.py_toggle import PyToggle

class DynamicMode(QWidget):
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    finished = pyqtSignal()
    zero_step_size = pyqtSignal()

    def __init__(self, power_supply=None, force_sensor=None, actuator=None, debug=1, parent=None):
        QWidget.__init__(self, parent=parent)

        # Event to stop the data recording.
        self.stop_event = threading.Event()

        # Components.
        self.power_supply = power_supply
        self.force_sensor = force_sensor
        self.actuator = actuator

        # Debugging flags.
        self.debug = debug
        if self.debug == 0:
            self.power_supply_debug = 1
            self.force_sensor_debug = 1
            self.actuator_debug = 1
        else:
            self.power_supply_debug = 0
            self.force_sensor_debug = 0
            self.actuator_debug = 0 

        # Variables.
        if self.debug == 0:
            self.start_time = 0
            self.plot_interval = 50#ms
            self.sample_rate = 400#Hz
            self.interpolation_stop_time = 0

            # Timer for the data interpolation.
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.indiv_data_rcd)

            # Signals.
            self.start_recording.connect(self.start_indiv_rcd)
            self.stop_recording.connect(self.stop_indiv_rcd)
            self.zero_step_size.connect(self.zero_step_size_msg)

    # ************************************************************************************************************ #
    #                                     DYNAMIC CHARACTERIZATION INTERFACE                                       #
    # ************************************************************************************************************ #

        self.characterization_type_layout = QVBoxLayout(self)

        self.auto_mode_toggle = PyToggle()
        self.auto_mode_toggle.setChecked(True)

        self.auto_label = QLabel("Auto")
        self.auto_label.setStyleSheet("font-weight: bold;" "font-size: 22px")
        self.auto_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.manual_label = QLabel("Manual")
        self.manual_label.setStyleSheet("font-weight: normal;" "font-size: 22px")
        self.manual_label.setCursor(Qt.CursorShape.PointingHandCursor)

        self.auto_mode_layout = QHBoxLayout()
        self.auto_mode_layout.addWidget(self.auto_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.auto_mode_layout.addWidget(self.auto_mode_toggle, alignment=Qt.AlignmentFlag.AlignCenter)
        self.auto_mode_layout.addWidget(self.manual_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.characterization_type_layout.addLayout(self.auto_mode_layout)

        self.bottom_frame = QFrame()
        self.bottom_frame.setFrameShape(QFrame.Shape.HLine)
        self.bottom_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.characterization_type_layout.addWidget(self.bottom_frame)

        self.auto_mode_toggle.stateChanged.connect(self.auto_mode_changed)

        self.init_ui('auto')
        # -------------------------------------------------------------------------------------------------------- #

    def init_ui(self, mode):

        self.control_panel_layout = QVBoxLayout()

        if mode == 'auto':
            # Type of experiment.
            experiment_type_layout = QFormLayout()
            experiment_type_label = QLabel("Experiment:")
            self.experiment_type = QComboBox()
            experiments = ['Force vs. Speed', 'Force vs. Voltage and Speed', 'Force vs. Frequency and Speed']
            for experiment in experiments:
                self.experiment_type.addItem(experiment)
            experiment_type_layout.addRow(experiment_type_label, self.experiment_type)
            self.experiment_type.currentIndexChanged.connect(self.experiment_type_widgets)
            self.control_panel_layout.addLayout(experiment_type_layout)
  
            self.components_control_widgets(mode, exp_type=self.experiment_type.currentText())
            self.characterization_type_layout.addLayout(self.control_panel_layout)
        # -------------------------------------------------------------------------------------------------------- #

        if mode == 'manual':
            self.upper_control_layout = QVBoxLayout()
            # Data save option.
            data_save_opt_layout = QHBoxLayout()
            self.data_save_lbl = QLabel("Save data:")
            self.data_save_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.data_save_lbl.setFixedWidth(175)
            self.data_save_opt = QCheckBox()
            self.data_save_opt.setChecked(True)
            data_save_opt_layout.addWidget(self.data_save_lbl)
            data_save_opt_layout.addWidget(self.data_save_opt)
            self.upper_control_layout.addLayout(data_save_opt_layout)

            # Force sensor "Tare" button.
            tare_btn = QPushButton("TARE FORCE")
            if self.force_sensor is not None:
                tare_btn.clicked.connect(self.force_sensor.tare)
            tare_btn.setStyleSheet("background-color: white; "
                                    "color: black; "
                                    "font-weight: bold; "
                                    "font-size: 24px; "
                                    "position: center; ")
            self.control_panel_layout.addWidget(tare_btn)
        
            self.components_control_widgets(mode)
            self.disable_all_widgets(self.control_panel_layout, disable=1)

            self.upper_control_layout.addLayout(self.control_panel_layout)
            self.characterization_type_layout.addLayout(self.upper_control_layout)

    # ************************************************************************************************************ #
    
    # Change control interface based on the mode selected.
    def auto_mode_changed(self, auto):
        if auto:
            self.auto_mode_interface()
        else:
            self.manual_mode_interface()

    def manual_mode_interface(self):
        self.auto_mode_toggle.setChecked(False)
        self.auto_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.clear_layout(self.control_panel_layout)
        self.init_ui('manual')

    def auto_mode_interface(self):
        self.auto_mode_toggle.setChecked(True)
        self.auto_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.clear_layout(self.upper_control_layout)
        self.init_ui('auto')

    def mousePressEvent(self, event):
        if self.auto_label.underMouse():
            self.auto_mode_changed(auto=True)
        elif self.manual_label.underMouse():
            self.auto_mode_changed(auto=False)

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

    # Widgets for the control panel.
    def components_control_widgets(self, mode, exp_type=None):
        self.widgets_layout = QVBoxLayout()

        # Actuator control panel.
        self.actuator_control = StandaTableWidget(self.actuator, mode=mode, exp_type=exp_type)

        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(actuator_groupBox)

        self.actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        self.actuator_groupBox_layout.addRow(self.actuator_control)
        # -------------------------------------------------------------------------------------------------------- #
        
        # Power supply control panel.
        self.power_supply_control = Dynamic_PS(self.power_supply, mode=mode, exp_type=exp_type, debug=self.debug)

        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(power_supply_groupBox)

        self.power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        self.power_supply_groupBox_layout.addRow(self.power_supply_control)

        power_supply_groupBox.setLayout(self.power_supply_groupBox_layout)
        # -------------------------------------------------------------------------------------------------------- #

        # Other parameters.
        self.parameters_groupBox = QGroupBox("Parameters")
        self.parameters_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.widgets_layout.addWidget(self.parameters_groupBox)

        motor_type_lbl = QLabel("Motor Type:")
        motor_type_lbl.setFixedWidth(115)
        self.motor_type = QComboBox()
        motor_types = ['Motor Fiber', 'Motor Ribbon']
        for motor in motor_types:
            self.motor_type.addItem(motor)

        self.parameters_groupBox_layout = QFormLayout()
        self.parameters_groupBox_layout.addRow(motor_type_lbl, self.motor_type)
        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        self.motor_type.currentIndexChanged.connect(self.motor_type_changed)

        self.motor_name_lbl = QLabel("Motor name:")
        self.motor_name = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_name_lbl, self.motor_name)

        self.motor_length_lbl = QLabel("Fiber length (mm):")
        self.motor_length = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_length_lbl, self.motor_length)
        
        self.motor_number_lbl = QLabel("Number of fibers:")
        self.motor_number = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_number_lbl, self.motor_number)
        
        self.insulator_lbl = QLabel("Insulator:")
        self.insulator = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.insulator_lbl, self.insulator)
        
        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        
        self.stator_name_lbl = QLabel("Stator name:")
        self.slider_name_lbl = QLabel("Slider name:")
        
        self.widgets_layout.addStretch(1)
        self.control_panel_layout.addLayout(self.widgets_layout)
    
    # ************************************************************************************************************ #
    
    def experiment_type_widgets(self):
        self.clear_layout(self.widgets_layout)
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Speed':
            self.components_control_widgets(mode='auto', exp_type=experiment_text)
        # if experiment_text == 'Force vs. Voltage and Speed':
        #     self.components_control_widgets(mode='auto', exp_type=experiment_text)
        else:
            pass
        # elif experiment_text == 'Force vs. Voltage and Speed':
        # elif experiment_text == 'Force vs. Frequency and Speed':
        # elif experiment_text == 'Max. Force vs. Voltage':
        # elif experiment_text == 'Max. Force vs. Frequency':
    
    # ************************************************************************************************************ #
    
    def motor_type_changed(self):
        if self.motor_type.currentText() == 'Motor Fiber':
            self.parameters_groupBox_layout.removeRow(self.stator_name_lbl)
            self.parameters_groupBox_layout.removeRow(self.slider_name_lbl)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_name_lbl = QLabel("Motor name:")
            self.motor_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_name_lbl, self.motor_name)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_length_lbl = QLabel("Fiber length (mm):")
            self.motor_length = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_length_lbl, self.motor_length)
            # -------------------------------------------------------------------------------------------------------- #
            self.motor_number_lbl = QLabel("Number of fibers:")
            self.motor_number = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_number_lbl, self.motor_number)
            # -------------------------------------------------------------------------------------------------------- #
            self.insulator_lbl = QLabel("Insulator:")
            self.insulator = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.insulator_lbl, self.insulator)
            # -------------------------------------------------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)

        elif self.motor_type.currentText() == 'Motor Ribbon':
            self.parameters_groupBox_layout.removeRow(self.motor_name_lbl)
            self.parameters_groupBox_layout.removeRow(self.motor_length_lbl)
            self.parameters_groupBox_layout.removeRow(self.motor_number_lbl)
            self.parameters_groupBox_layout.removeRow(self.insulator_lbl)
            # -------------------------------------------------------------------------------------------------------- #
            self.stator_name_lbl = QLabel("Stator name:")
            self.stator_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.stator_name_lbl, self.stator_name)
            # -------------------------------------------------------------------------------------------------------- #
            self.slider_name_lbl = QLabel("Slider name:")
            self.slider_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.slider_name_lbl, self.slider_name)
            # --------------------------------------------------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        # self.characterization_type_layout.addStretch(1) 

    # ************************************************************************************************************ #

    def disable_all_widgets(self, layout, disable=1):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() is not None:
                item.widget().setDisabled(disable)
            elif item.layout() is not None:
                self.disable_all_widgets(item.layout(), disable)

    # ************************************************************************************************************ #

    # def run_dynamic(self):
    #     self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a str
    #     self.zero_step_flag = 0
    #     experiment_text = self.experiment_type.currentText()
    #     if experiment_text == 'Force vs. Position':
    #         # ---------------------------------------------------------------------------------------------------- #
    #         # Get the actuator parameters.
    #         current_pos = self.actuator.get_position()
    #         start_pos = float(self.actuator_control.start_pos_edit.text())
    #         end_pos = float(self.actuator_control.end_pos_edit.text())
    #         step_size = float(self.actuator_control.step_size_edit.text())
    #         speed = float(self.actuator_control.speed_edit.text())

    #         # Set speed to the actuator.
    #         if speed > self.actuator.max_speed:
    #             speed = self.actuator.max_speed
    #         # self.actuator_control.speed_edit.setText(str(speed))
    #         self.actuator.set_speed(speed)
            
    #         # Calculate the time to wait for the actuator to reach the position.
    #         if self.actuator_control.home_chckbox.isChecked():
    #             init_moving_time = start_pos / speed
    #         else:
    #             init_moving_time = np.abs(current_pos - start_pos) / speed

    #         moving_time = np.abs(end_pos - start_pos) / speed

    #         # Calculate the number of steps.
    #         if step_size == 0:
    #             self.zero_step_size.emit()
    #             return
    #         else:
    #             steps_nb = np.abs(np.floor(np.round((end_pos - start_pos) / (step_size / 1000), 10)))  # number of steps
    #             # print("\n[INFO] The number of steps is: ", steps_nb)
    #             # ---------------------------------------------------------------------------------------------------- #
    #             # Get the power supply parameters.
    #             # voltage = float(self.power_supply_control.target_voltage_edit.text())
    #             modulation = self.power_supply_control.state_opt.isChecked()
            
    #             # ---------------------------------------------------------------------------------------------------- #
    #             # Algorithm for the "Force vs Position" experiment.
    #             for step in range(int(steps_nb)+1):
    #                 # ------------------------------------------------------------------------------------------------ #
    #                 if self.stop_event.is_set():
    #                     break
    #                 # ------------------------------------------------------------------------------------------------ #
    #                 self.position = start_pos+step*(step_size/1000) # calculate the position
    #                 # print("\n[INFO] The actuator is moving to the position: ", self.position)
    #                 self.actuator.move(self.position) # move the actuator to the position
    #                 if step == 0:
    #                     time.sleep(init_moving_time+2) # wait for the actuator to reach the starting position
    #                 else:
    #                     time.sleep(moving_time+2) # wait for the actuator to reach the next position
    #                 self.force_sensor.tare() # tare the force sensor
    #                 time.sleep(0.1) # wait for the force sensor to tare
    #                 if modulation == False:
    #                     states = ['A', 'B', 'C']
    #                     for state in states:
    #                         # -------------------------------------------------------------------------------- #
    #                         if self.stop_event.is_set():
    #                             break
    #                         # -------------------------------------------------------------------------------- #
    #                         self.state = state
    #                         self.power_supply_control.set_pressed(state) # set the power supply to the state
    #                         # print("\n[INFO] The power supply is set to the state: ", state)
    #                         time.sleep(0.5) # wait for 1 second
    #                         # -------------------------------------------------------------------------------- #
    #                         if self.stop_event.is_set():
    #                             break
    #                         # -------------------------------------------------------------------------------- #
    #                         self.start_recording.emit() # record the data
    #                         # print("\n[INFO] The data is being recorded")
    #                         time.sleep(2) # measure for 2 seconds
    #                         # -------------------------------------------------------------------------------- #
    #                         if self.stop_event.is_set():
    #                             break
    #                         # -------------------------------------------------------------------------------- #
    #                         self.stop_recording.emit() # stop recording the data
    #                         # print("\n[INFO] The data has been stopped recording")
    #                         # -------------------------------------------------------------------------------- #
    #                         if self.stop_event.is_set():
    #                             break
    #                         # -------------------------------------------------------------------------------- #
    #                         self.power_supply_control.voltage_reset() # reset the voltage
    #                         # print("\n[INFO] The power supply voltage is reset")
    #                         time.sleep(2) # wait for 1 second
    #                 # ------------------------------------------------------------------------------------------------ #
    #                 if self.stop_event.is_set():
    #                     break
    #                 # ------------------------------------------------------------------------------------------------ #
    #             if not self.stop_event.is_set():
    #                 self.finished.emit() # set the finished event

    # # ************************************************************************************************************ #

    def zero_step_size_msg(self):
        self.zero_step_flag = 1
        self.finished.emit() # emit the finished signal

    # # ************************************************************************************************************ #

    def start_indiv_rcd(self):
        if self.auto_mode_toggle.isChecked() == False: # Manual mode
            self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a string
        self.start_time = time.perf_counter()
        self.timer.start(self.plot_interval)
    
    def stop_indiv_rcd(self):
        self.timer.stop()

    def indiv_data_rcd(self):
        # Get the new data from the components.
        if self.power_supply_debug == 1:
            new_power_supply_data = self.power_supply.get_new_data()
        if self.force_sensor_debug == 1:
            new_force_sensor_data = self.force_sensor.get_new_data()
        if self.actuator_debug == 1:
            new_actuator_data = self.actuator.get_new_data()
            
        # Interpolate the data.
        if len(new_power_supply_data)>0 and len(new_force_sensor_data)>0 and len(new_actuator_data)>0:
            if self.interpolation_stop_time < self.start_time:
                interpolation_start_time = self.start_time
            else:
                interpolation_start_time = self.interpolation_stop_time + 1/self.sample_rate

            smallest_last_sample = min(new_power_supply_data[-1,0], new_force_sensor_data[-1,0])
            differential_time_latest_sample = smallest_last_sample - self.start_time
            interpolated_latest_sample_number = np.floor(differential_time_latest_sample/(1/self.sample_rate))
            self.interpolation_stop_time = self.start_time + interpolated_latest_sample_number*(1/self.sample_rate)

            interpolation_time = np.arange(interpolation_start_time, self.interpolation_stop_time, 1/self.sample_rate)
            interpolated_force_sensor_data = np.interp(interpolation_time, new_force_sensor_data[:, 0], new_force_sensor_data[:, 1])
            interpolated_actuator_data = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 1])
            interpolated_power_supply_data = np.zeros((len(interpolation_time), 11))
            for i1 in range(2, 11):
                interpolated_power_supply_data[:, i1] = np.interp(interpolation_time, new_power_supply_data[:, 0], new_power_supply_data[:, i1])

            abs_time_s = interpolation_time
            rel_time_s = abs_time_s - self.start_time
            force_mN = interpolated_force_sensor_data
            position_mm = interpolated_actuator_data
            hv_set_kV = interpolated_power_supply_data[:,2]
            hv_vm_kV = interpolated_power_supply_data[:,3]
            hv_err_V = interpolated_power_supply_data[:,4]
            # lv_set_V = interpolated_power_supply_data[:,5]
            # lv_vm_V = interpolated_power_supply_data[:,6]
            # lv_err_V = interpolated_power_supply_data[:,7]
            cm_w1_uA = interpolated_power_supply_data[:,8]
            cm_w2_uA = interpolated_power_supply_data[:,9]
            cm_w3_uA = interpolated_power_supply_data[:,10]

            # Create a folder to store the data files if it doesn't exist.
            folder_name = 'DataFiles'
            os.makedirs(folder_name, exist_ok=True)

            main_subfolder = os.path.join(folder_name, f"DynamicCharacterization")
            os.makedirs(main_subfolder, exist_ok=True)

            # **************************************************************************************************** #
            if self.auto_mode_toggle.isChecked() == False: # Manual mode
                if self.data_save_opt.isChecked():
                    subfolder = os.path.join(main_subfolder, f"Manual")
                    os.makedirs(subfolder, exist_ok=True)
                    # ------------------------------------------------------------------------------------------------ #
                    # Create a temporary file to store the data.
                    self.temp_file_name = os.path.join(subfolder, f"temp_{self.formatted_time}.csv")
                    # ------------------------------------------------------------------------------------------------ #
                    # Interface parameters.

                    # ------------------------------------------------------------------------------------------------ #
                    # Save the data to the temporary file.
                    save_data = np.column_stack((abs_time_s, rel_time_s,
                                                force_mN, position_mm,
                                                hv_set_kV, hv_vm_kV, hv_err_V,
                                                #  lv_set_V, lv_vm_V, lv_err_V,
                                                cm_w1_uA, cm_w2_uA, cm_w3_uA))
                    with open(self.temp_file_name, 'ab') as t: 
                        np.savetxt(t, save_data, fmt='%.8f, %.4f, ' # abs_time_s, rel_time_s
                                                    '% 4.6f, %4.3f,' # force_mN, position_mm
                                                    '% 6.1f, %6.1f, % 3.1f,' # hv_set_kV, hv_vm_kV, hv_err_V
                                                    #  '% 3.2f, % 3.2f, % 3.2f,' # lv_set_V, lv_vm_V, lv_err_V
                                                    '% 3.1f, % 3.1f, % 3.1f') # cm_w1_uA, cm_w2_uA, cm_w3_uA
                    # ------------------------------------------------------------------------------------------------ #
                    # Now write the final file combining parameters and data from the temporary file.
                    file_name = os.path.join(subfolder, f"date_{self.formatted_time}.csv")
                    with open(file_name, 'w') as final_file:
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('--------------------Experiment_Info------------------------\n\n'
                                        f'Datetime: {self.formatted_time}\n'
                                        f'Characterization: Dynamic\n'
                                        f'Mode: Manual\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n-----------------------Motor_Info--------------------------\n\n')
                        if self.motor_type.currentText() == 'Motor Fiber':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                            f'Motor name: {self.motor_name.text()}\n'
                                            f'Fiber length (mm): {self.motor_length.text()}\n'
                                            f'Number of fibers: {self.motor_number.text()}\n'
                                            f'Insulator: {self.insulator.text()}\n')
                        elif self.motor_type.currentText() == 'Motor Ribbon':
                            final_file.write(f'Motor type: {self.motor_type.currentText()}\n'
                                            f'Stator name: {self.stator_name.text()}\n'
                                            f'Slider name: {self.slider_name.text()}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n---------------------Program_Info-------------------------\n\n'
                                        f'Sample rate (Hz): {self.sample_rate}\n\n')
                        # ------------------------------------------------------------------------------------------------ #
                        final_file.write('\n-------------------Explanatory_Note-----------------------\n\n'
                                        f'When the PS is set ON, the variables (state, freq, DC, phase shifts) '
                                        f'are recorded. If the PS is set OFF, the variables are recorded as "-".\n'
                                        f'Voltage aquired from the PS is recorded with a small delay raletivly to '
                                        f'the other variables. The delay is due to the PS response time.\n')
                        # ----------------------------------------------------------------------------------------------------------------- #
                        final_file.write('\n----------------------Data_Info---------------------------\n\n')
                        final_file.write(f'Absolute time (s), Relative time (s), '
                                            f'Force (mN), Position (mm), '
                                            f'hv_set (kV), hv_vm (kV), hv_err (V), '
                                            # f'lv_set (V), lv_vm (V), lv_err (V), '
                                            f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n\n')

                        # Append the data from the temporary file to the final file.
                        with open(self.temp_file_name, 'r') as t:
                            data = t.read()
                            final_file.write(data)

            # **************************************************************************************************** #
            # elif self.auto_mode_toggle.isChecked() == True: # Auto mode
            #     subfolder = os.path.join(main_subfolder, f"Auto")
            #     os.makedirs(subfolder, exist_ok=True)
            #     subfolder1 = os.path.join(subfolder, f"date_{self.formatted_time}")
            #     os.makedirs(subfolder1, exist_ok=True)
            #     file_name = os.path.join(subfolder1, f"pos_{str(self.position)}_state_{self.state}.csv")

            #     if not os.path.isfile(file_name):
            #         with open(file_name, 'w') as f:
            #             f.write(f'Experiment: {self.experiment_type.currentText()}\n')
            #             if self.motor_type.currentText() == 'Motor Fiber':
            #                 f.write(f'Motor type: {self.motor_type.currentText()}\n'
            #                         f'Motor name: {self.motor_name.text()}\n'
            #                         f'Fiber length (mm): {self.motor_length.text()}\n'
            #                         f'Number of fibers: {self.motor_number.text()}\n'
            #                         f'Insulator: {self.insulator.text()}\n')
            #             elif self.motor_type.currentText() == 'Motor Ribbon':
            #                 f.write(f'Motor type: {self.motor_type.currentText()}\n'
            #                         f'Stator name: {self.stator_name.text()}\n'
            #                         f'Slider name: {self.slider_name.text()}\n')
            #             f.write(f'State: {self.state}\n')
            #             f.write(f'Sample rate (Hz): {self.sample_rate}\n')
            #             f.write(f'Absolute time (s), Relative time (s), '
            #                     f'Force (mN), Position (mm), '
            #                     f'hv_set (kV), hv_vm (kV), hv_err (V), '
            #                     f'lv_set (V), lv_vm (V), lv_err (V), '
            #                     f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n\n')
                        
            #     # Save the data to the .csv file.   
            #     save_data = np.column_stack((abs_time_s, rel_time_s,
            #                                 force_mN, position_mm,
            #                                 hv_set_kV, hv_vm_kV, hv_err_V,
            #                                 lv_set_V, lv_vm_V, lv_err_V,
            #                                 cm_w1_uA, cm_w2_uA, cm_w3_uA))
            #     with open(file_name, 'ab') as f:                       
            #         np.savetxt(f, save_data, fmt='%.8f, %.4f, ' # abs_time_s, rel_time_s
            #                                     '% 4.6f, %4.3f,' # force_mN, position_mm
            #                                     '% 6.1f, %6.1f, % 3.1f,' # hv_set_kV, hv_vm_kV, hv_err_V
            #                                     '% 3.2f, % 3.2f, % 3.2f,' # lv_set_V, lv_vm_V, lv_err_V
            #                                     '% 3.1f, % 3.1f, % 3.1f') # cm_w1_uA, cm_w2_uA, cm_w3_uA
                    
    # ************************************************************************************************************ #
    def remove_temp_files(self):
        os.remove(self.temp_file_name)
