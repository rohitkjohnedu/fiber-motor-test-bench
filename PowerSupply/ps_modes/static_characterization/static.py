# python packages
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QLabel, QGroupBox, QFormLayout, QPushButton,
                             QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame)
import numpy as np
import time
import threading
from datetime import datetime
import os.path
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS
from StandaTable.standa_table import StandaTableWidget
from tools.gui_tools.py_toggle import PyToggle

class StaticMode(QWidget):
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

            # if self.actuator_control is not None:
            #     # Save metadata that changes during the experiment.
            #     self.actuator_control.speed_edit.textChanged.connect(self.speed_in_array)
 
    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
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

    # ************************************************************************************************************ #

    def init_ui(self, mode):

        self.control_panel_layout = QVBoxLayout()

        if mode == 'auto':   
            # Type of experiment.
            experiment_type_layout = QFormLayout()
            experiment_type_label = QLabel("Experiment:")
            self.experiment_type = QComboBox()
            experiments = ['Force vs. Position', 'Force vs. Voltage and Position']
            # experiments = ['Force vs. Position', 'Force vs. Voltage and Position', 'Force vs. Frequency and Position', 
            #             'Max. Force vs. Voltage', 'Max. Force vs. Frequency']
            for experiment in experiments:
                self.experiment_type.addItem(experiment)
            experiment_type_layout.addRow(experiment_type_label, self.experiment_type)
            self.experiment_type.currentIndexChanged.connect(self.experiment_type_widgets)
            self.control_panel_layout.addLayout(experiment_type_layout)

            self.components_control_widgets(mode, exp_type=self.experiment_type.currentText())
        # -------------------------------------------------------------------------------------------------------- #

        elif mode == 'manual':
            # Force sensor "Tare" button.
            self.tare_btn = QPushButton("TARE FORCE")
            if self.force_sensor is not None:
                self.tare_btn.clicked.connect(self.force_sensor.tare)
            self.tare_btn.setStyleSheet("background-color: white; "
                                    "color: black; "
                                    "font-weight: bold; "
                                    "font-size: 24px; "
                                    "position: center; ")
            self.control_panel_layout.addWidget(self.tare_btn)
        
            self.components_control_widgets(mode)
            self.disable_all_widgets(self.control_panel_layout, disable=1)
        # -------------------------------------------------------------------------------------------------------- #
        self.characterization_type_layout.addLayout(self.control_panel_layout)

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
        self.clear_layout(self.control_panel_layout)
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

        actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        actuator_groupBox_layout.addRow(self.actuator_control)

        # self.actuator_control.speed_edit.textChanged.connect(self.speed_in_array)
        # -------------------------------------------------------------------------------------------------------- #
            
        # Power supply control panel.
        self.power_supply_control = Static_PS(self.power_supply, mode=mode, exp_type=exp_type, debug=self.debug)

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
        if experiment_text == 'Force vs. Position':
            self.components_control_widgets(mode='auto', exp_type=experiment_text)
        # if experiment_text == 'Force vs. Voltage and Position':
        #     self.components_control_widgets(mode='auto', exp_type=experiment_text)
        else:
            pass
        # elif experiment_text == 'Force vs. Voltage and Position':
        # elif experiment_text == 'Force vs. Frequency and Position':
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
            # -------------------------------------------------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
    
    # ************************************************************************************************************ #

    def disable_all_widgets(self, layout, disable=1):
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() is not None:
                item.widget().setDisabled(disable)
            elif item.layout() is not None:
                self.disable_all_widgets(item.layout(), disable)

    # ************************************************************************************************************ #

    def run_static(self):
        self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a str
        self.zero_step_flag = 0
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Position':
            # ---------------------------------------------------------------------------------------------------- #
            # Get the actuator parameters.
            current_pos = self.actuator.get_position()
            start_pos = float(self.actuator_control.start_pos_edit.text())
            end_pos = float(self.actuator_control.end_pos_edit.text())
            step_size = float(self.actuator_control.step_size_edit.text())
            speed = float(self.actuator_control.speed_edit.text())

            # Set speed to the actuator.
            if speed > self.actuator.max_speed:
                speed = self.actuator.max_speed
            # self.actuator_control.speed_edit.setText(str(speed))
            self.actuator.set_speed(speed)
            
            # Calculate the time to wait for the actuator to reach the position.
            if self.actuator_control.home_chckbox.isChecked():
                init_moving_time = start_pos / speed
            else:
                init_moving_time = np.abs(current_pos - start_pos) / speed

            moving_time = np.abs(end_pos - start_pos) / speed

            # Calculate the number of steps.
            if step_size == 0:
                self.zero_step_size.emit()
                return
            else:
                steps_nb = np.abs(np.floor(np.round((end_pos - start_pos) / (step_size / 1000), 10)))  # number of steps
                # print("\n[INFO] The number of steps is: ", steps_nb)
                # ---------------------------------------------------------------------------------------------------- #
                # Get the power supply parameters.
                # voltage = float(self.power_supply_control.target_voltage_edit.text())
                modulation = self.power_supply_control.state_opt.isChecked()
            
                # ---------------------------------------------------------------------------------------------------- #
                # Algorithm for the "Force vs Position" experiment.
                for step in range(int(steps_nb)+1):
                    # ------------------------------------------------------------------------------------------------ #
                    if self.stop_event.is_set():
                        break
                    # ------------------------------------------------------------------------------------------------ #
                    self.position = start_pos+step*(step_size/1000) # calculate the position
                    # print("\n[INFO] The actuator is moving to the position: ", self.position)
                    self.actuator.move(self.position) # move the actuator to the position
                    if step == 0:
                        time.sleep(init_moving_time+2) # wait for the actuator to reach the starting position
                    else:
                        time.sleep(moving_time+2) # wait for the actuator to reach the next position
                    self.force_sensor.tare() # tare the force sensor
                    time.sleep(0.1) # wait for the force sensor to tare
                    if modulation == False:
                        states = ['A', 'B', 'C']
                        for state in states:
                            # -------------------------------------------------------------------------------- #
                            if self.stop_event.is_set():
                                break
                            # -------------------------------------------------------------------------------- #
                            self.state = state
                            self.power_supply_control.set_pressed(state) # set the power supply to the state
                            # print("\n[INFO] The power supply is set to the state: ", state)
                            time.sleep(0.5) # wait for 1 second
                            # -------------------------------------------------------------------------------- #
                            if self.stop_event.is_set():
                                break
                            # -------------------------------------------------------------------------------- #
                            self.start_recording.emit() # record the data
                            # print("\n[INFO] The data is being recorded")
                            time.sleep(2) # measure for 2 seconds
                            # -------------------------------------------------------------------------------- #
                            if self.stop_event.is_set():
                                break
                            # -------------------------------------------------------------------------------- #
                            self.stop_recording.emit() # stop recording the data
                            # print("\n[INFO] The data has been stopped recording")
                            # -------------------------------------------------------------------------------- #
                            if self.stop_event.is_set():
                                break
                            # -------------------------------------------------------------------------------- #
                            self.power_supply_control.voltage_reset() # reset the voltage
                            # print("\n[INFO] The power supply voltage is reset")
                            time.sleep(2) # wait for 1 second
                    # ------------------------------------------------------------------------------------------------ #
                    if self.stop_event.is_set():
                        break
                    # ------------------------------------------------------------------------------------------------ #
                if not self.stop_event.is_set():
                    self.finished.emit() # set the finished event

    # ************************************************************************************************************ #

    def zero_step_size_msg(self):
        self.zero_step_flag = 1
        self.finished.emit() # emit the finished signal

    # ************************************************************************************************************ #

    def start_indiv_rcd(self):
        if self.auto_mode_toggle.isChecked() == False: # Manual mode
            self.formatted_time = datetime.now().strftime('%H-%M-%S_%d-%m-%Y')  # Get the current date and time as a string
        self.start_time = time.perf_counter()
        # init_time = f"{time.perf_counter():.8f}"
        # if self.actuator_control.speed_edit.text() != '':
        #     init_speed = f"{float(self.actuator_control.speed_edit.text()):.1f}"
        #     self.speed_arr = [[init_time, init_speed]]
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
            interpolated_actuator_pos = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 1])
            interpolated_actuator_speed = np.interp(interpolation_time, new_actuator_data[:, 0], new_actuator_data[:, 2])
            interpolated_power_supply_data = np.zeros((len(interpolation_time), 11))
            for i1 in range(2, 11):
                interpolated_power_supply_data[:, i1] = np.interp(interpolation_time, new_power_supply_data[:, 0], new_power_supply_data[:, i1])

            state = np.full(len(interpolation_time), self.power_supply_control.st_comboBox.currentText(), dtype='<U32')
            abs_time_s = interpolation_time
            rel_time_s = abs_time_s - self.start_time
            force_mN = interpolated_force_sensor_data
            position_mm = interpolated_actuator_pos
            speed_mm_s = interpolated_actuator_speed
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

            main_subfolder = os.path.join(folder_name, f"StaticCharacterization")
            os.makedirs(main_subfolder, exist_ok=True)

            # **************************************************************************************************** #
            if self.auto_mode_toggle.isChecked() == False: # Manual mode
                subfolder = os.path.join(main_subfolder, f"Manual")
                os.makedirs(subfolder, exist_ok=True)
                # ------------------------------------------------------------------------------------------------ #
                # Create a temporary file to store the data.
                self.temp_file_name = os.path.join(subfolder, f"temp_{self.formatted_time}.csv")

                save_data = np.zeros(abs_time_s.size, dtype=[('state', '<U32'), ('abs_time_s', '<f8'), ('rel_time_s', '<f8'),
                                                            ('force_mN', '<f8'), ('position_mm', '<f8'), ('speed_mm_s', '<f8'),
                                                            ('hv_set_kV', '<f8'), ('hv_vm_kV', '<f8'), ('hv_err_V', '<f8'),
                                                            # ('lv_set_V', '<f8'), ('lv_vm_V', '<f8'), ('lv_err_V', '<f8'),
                                                            ('cm_w1_uA', '<f8'), ('cm_w2_uA', '<f8'), ('cm_w3_uA', '<f8')])
                save_data['state'] = state
                save_data['abs_time_s'] = abs_time_s
                save_data['rel_time_s'] = rel_time_s
                save_data['force_mN'] = force_mN
                save_data['position_mm'] = position_mm
                save_data['speed_mm_s'] = speed_mm_s
                save_data['hv_set_kV'] = hv_set_kV
                save_data['hv_vm_kV'] = hv_vm_kV
                save_data['hv_err_V'] = hv_err_V
                # save_data['lv_set_V'] = lv_set_V
                # save_data['lv_vm_V'] = lv_vm_V
                # save_data['lv_err_V'] = lv_err_V
                save_data['cm_w1_uA'] = cm_w1_uA
                save_data['cm_w2_uA'] = cm_w2_uA
                save_data['cm_w3_uA'] = cm_w3_uA

                with open(self.temp_file_name, 'ab') as t:
                    np.savetxt(t, save_data, fmt='%s, %.8f, %.4f, ' # state, abs_time_s, rel_time_s
                                                 '% 4.6f, %3.3f, %.1f,' # force_mN, position_mm, speed_mm_s
                                                 '%5.1f, %5.1f, % 5.1f,' # hv_set_kV, hv_vm_kV, hv_err_V
                                                 # '% 3.2f, %3.2f, % 3.2f,' # lv_set_V, lv_vm_V, lv_err_V
                                                 '% 3.1f, % 3.1f, % 3.1f') # cm_w1_uA, cm_w2_uA, cm_w3_uA
                # ------------------------------------------------------------------------------------------------ #
                # Now write the final file combining parameters and data from the temporary file.
                file_name = os.path.join(subfolder, f"date_{self.formatted_time}.csv")
                with open(file_name, 'w') as final_file:
                    # ------------------------------------------------------------------------------------------------ #
                    final_file.write('--------------------Experiment_Info------------------------\n\n'
                                     f'Datetime: {self.formatted_time}\n'
                                     f'Characterization: Static\n'
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
                                        f'Sample rate (Hz): {self.sample_rate}\n')
                    # ------------------------------------------------------------------------------------------------ #
                    # final_file.write('\n-------------------Power_Supply_Info----------------------\n\n')
                    # self.state_index = self.power_supply_control.state_index
                    # final_file.write(f'State: {self.power_supply_control.states[self.state_index]}\n')
                    # if self.state_index >= 6:
                    #     final_file.write(f'Frequency (Hz): {self.power_supply_control.freq_edit.text()}\n'
                    #                      f'Duty cycle (%): {self.power_supply_control.duty_cycle_edit.text()}\n') # always 50%
                    #     if self.state_index == 6: # 'A-D'
                    #         final_file.write(f'CH1 Phase shift (degrees): 0\n'
                    #                          f'CH2 Phase shift (degrees): 180\n'
                    #                          f'CH3 Phase shift (degrees): 180\n')
                    #     elif self.state_index == 7: # 'B-E'
                    #         final_file.write(f'CH1 Phase shift (degrees): 180\n'
                    #                          f'CH2 Phase shift (degrees): 0\n'
                    #                          f'CH3 Phase shift (degrees): 180\n')
                    #     elif self.state_index == 8: # 'C-F'
                    #         final_file.write(f'CH1 Phase shift (degrees): 180\n'
                    #                          f'CH2 Phase shift (degrees): 180\n'
                    #                          f'CH3 Phase shift (degrees): 0\n')
                    #     elif self.state_index == 9: # 'Other'
                    #         final_file.write(f'CH1 Phase shift (degrees): {self.power_supply_control.ch1_phase_shift_edit.text()}\n'
                    #                          f'CH2 Phase shift (degrees): {self.power_supply_control.ch2_phase_shift_edit.text()}\n'
                    #                          f'CH3 Phase shift (degrees): {self.power_supply_control.ch3_phase_shift_edit.text()}\n')                   
                    # ----------------------------------------------------------------------------------------------------------------- #
                    final_file.write('\n----------------------Data_Info---------------------------\n\n')
                    final_file.write(f'state, abs. t (s), rel. t (s), '
                                     f'F (mN), p (mm), v (mm/s), '
                                    #  f'f (Hz), DC (%), '
                                    #  f'ph1 (deg), ph2 (deg), ph3 (deg), '
                                     f'hv_set (kV), hv_vm (kV), hv_err (V), '
                                    #  f'lv_set (V), lv_vm (V), lv_err (V), '
                                     f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n\n')

                    # Append the data from the temporary file to the final file.
                    with open(self.temp_file_name, 'r') as t:
                        data = t.read()
                        final_file.write(data)

            # **************************************************************************************************** #
            elif self.auto_mode_toggle.isChecked() == True: # Auto mode
                subfolder = os.path.join(main_subfolder, f"Auto")
                os.makedirs(subfolder, exist_ok=True)
                subfolder1 = os.path.join(subfolder, f"date_{self.formatted_time}")
                os.makedirs(subfolder1, exist_ok=True)
                file_name = os.path.join(subfolder1, f"pos_{str(self.position)}_state_{self.state}.csv")

                if not os.path.isfile(file_name):
                    with open(file_name, 'w') as f:
                        f.write(f'Experiment: {self.experiment_type.currentText()}\n')
                        if self.motor_type.currentText() == 'Motor Fiber':
                            f.write(f'Motor type: {self.motor_type.currentText()}\n'
                                    f'Motor name: {self.motor_name.text()}\n'
                                    f'Fiber length (mm): {self.motor_length.text()}\n'
                                    f'Number of fibers: {self.motor_number.text()}\n'
                                    f'Insulator: {self.insulator.text()}\n')
                        elif self.motor_type.currentText() == 'Motor Ribbon':
                            f.write(f'Motor type: {self.motor_type.currentText()}\n'
                                    f'Stator name: {self.stator_name.text()}\n'
                                    f'Slider name: {self.slider_name.text()}\n')
                        f.write(f'State: {self.state}\n')
                        # ------------------------------------------------------------------------------------------------ #
                        # final_file.write('------------------------------------------------------------\n')
                        # if self.power_supply_control.modulation_opt.isChecked():
                        #     final_file.write(f'Modulation: ON\n\n')
                        # else:
                        #     final_file.write(f'Modulation: OFF\n\n')
                        f.write(f'Sample rate (Hz): {self.sample_rate}\n')
                        f.write(f'Absolute time (s), Relative time (s), '
                                f'Force (mN), Position (mm), '
                                f'hv_set (kV), hv_vm (kV), hv_err (V), '
                                # f'lv_set (V), lv_vm (V), lv_err (V), '
                                f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n\n')
                        
                # Save the data to the .csv file.   
                save_data = np.column_stack((abs_time_s, rel_time_s,
                                            force_mN, position_mm,
                                            hv_set_kV, hv_vm_kV, hv_err_V,
                                            # lv_set_V, lv_vm_V, lv_err_V,
                                            cm_w1_uA, cm_w2_uA, cm_w3_uA))
                with open(file_name, 'ab') as f:                       
                    np.savetxt(f, save_data, fmt='%.8f, %.4f, ' # abs_time_s, rel_time_s
                                                 '% 4.6f, %4.3f, ' # force_mN, position_mm
                                                 '%5.1f, %5.1f, % 5.1f,' # hv_set_kV, hv_vm_kV, hv_err_V
                                                 # '% 3.2f, % 3.2f, % 3.2f,' # lv_set_V, lv_vm_V, lv_err_V
                                                 '% 3.1f, % 3.1f, % 3.1f') # cm_w1_uA, cm_w2_uA, cm_w3_uA
                    
    # ************************************************************************************************************ #
    def remove_temp_files(self):
        os.remove(self.temp_file_name)
    
    # ************************************************************************************************************ #
    # def speed_in_array(self):
    #     Time = f"{time.perf_counter():.8f}"
    #     if self.actuator_control.speed_edit.text() != '':
    #         Speed = f"{float(self.actuator_control.speed_edit.text()):.1f}"
    #         self.speed_arr = np.append(self.speed_arr, [Time, Speed])
    
