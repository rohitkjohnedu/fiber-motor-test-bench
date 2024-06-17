# python packages
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QLabel, QGroupBox, QFormLayout, QPushButton,
                             QComboBox, QLineEdit, QVBoxLayout, QHBoxLayout, QFrame)
import numpy as np
import time
from datetime import datetime
import os.path
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS
from StandaTable.standa_table import StandaTableWidget
from tools.gui_tools.py_toggle import PyToggle

formatted_time = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')  # Get the current date and time as a string

class StaticMode(QWidget):
    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, power_supply=None, force_sensor=None, actuator=None, debug=1, parent=None):
        QWidget.__init__(self, parent=parent)

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

        if self.debug == 0:
            self.start_time = 0
            self.plot_interval = 50#ms
            self.sample_rate = 400#Hz
            self.interpolation_stop_time = 0

            # Timer for the data interpolation.
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.indiv_data_rcd)

            self.start_recording.connect(self.start_indiv_rcd)
            self.stop_recording.connect(self.stop_indiv_rcd)
 
    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
    # ************************************************************************************************************ #

        self.characterization_type_layout = QVBoxLayout(self)

        self.auto_mode_toggle = PyToggle()

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

        if mode == 'manual':
            # # Start button.
            # self.start_btn = QPushButton("START RECORDING")
            # self.start_btn.clicked.connect(self.start_btn_clicked)
            # self.start_btn.setStyleSheet("background-color: white; "
            #                         "color: black; "
            #                         "font-weight: bold; "
            #                         "font-size: 24px; "
            #                         "position: center; ")
            # self.control_panel_layout.addWidget(self.start_btn)   

            # self.bottom_frame1 = QFrame()
            # self.bottom_frame1.setFrameShape(QFrame.Shape.HLine)
            # self.bottom_frame1.setFrameShadow(QFrame.Shadow.Raised)
            # self.control_panel_layout.addWidget(self.bottom_frame1)

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
        # -------------------------------------------------------------------------------------------------------- #
        self.characterization_type_layout.addLayout(self.control_panel_layout)
    # ************************************************************************************************************ #

    # Change control interface based on the mode selected.
    def auto_mode_changed(self, manual):
        if manual:
            self.manual_mode_interface()
        else:
            self.auto_mode_interface()

    def manual_mode_interface(self):
        self.auto_mode_toggle.setChecked(True)
        self.auto_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.clear_layout(self.control_panel_layout)
        self.init_ui('manual')

    def auto_mode_interface(self):
        self.auto_mode_toggle.setChecked(False)
        self.auto_label.setStyleSheet("font-weight: bold; " "font-size: 22px")
        self.manual_label.setStyleSheet("font-weight: normal; " "font-size: 22px")
        self.clear_layout(self.control_panel_layout)
        self.init_ui('auto')

    def mousePressEvent(self, event):
        if self.auto_label.underMouse():
            self.auto_mode_changed(manual=False)
        elif self.manual_label.underMouse():
            self.auto_mode_changed(manual=True)

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
    def run_static(self):
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Position':
            # ---------------------------------------------------------------------------------------------------- #
            # Get the actuator parameters.
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
            init_moving_time = start_pos / speed
            moving_time = np.abs(end_pos - start_pos) / speed

            # Calculate the number of steps.
            steps_nb = np.floor((end_pos - start_pos) / (step_size / 1000)) # number of steps
            # ---------------------------------------------------------------------------------------------------- #
            # # Get the power supply parameters.
            # voltage = float(self.power_supply_control.target_voltage_edit.text())
            modulation = self.power_supply_control.state_opt.isChecked()
        
            # ---------------------------------------------------------------------------------------------------- #
            # Algorithm for the "Force vs Position" experiment.
            for step in range(int(steps_nb)+1):
                self.actuator.move(start_pos+step*(step_size/1000)) # move the actuator to the position
                if step == 0:
                    time.sleep(init_moving_time+2) # wait for the actuator to reach the starting position
                else:
                    time.sleep(moving_time+2) # wait for the actuator to reach the next position
                self.force_sensor.tare() # tare the force sensor
                time.sleep(0.1) # wait for the force sensor to tare
                if modulation == False:
                    states = ['A', 'B', 'C']
                    for state in states:
                        self.state = state
                        self.power_supply_control.set_pressed(state) # set the power supply to the state
                        print("\n[INFO] The power supply is set to the state: ", state)
                        time.sleep(0.5) # wait for 1 second
                        self.start_recording.emit() # record the data
                        print("\n[INFO] The data is being recorded")
                        time.sleep(2) # measure for 2 seconds
                        self.stop_recording.emit() # stop recording the data
                        print("\n[INFO] The data has been stopped recording")
                        self.power_supply_control.voltage_reset() # reset the voltage
                        print("\n[INFO] The power supply voltage is reset")
                        time.sleep(0.5) # wait for 1 second
        self.finished.emit()
    
    def start_indiv_rcd(self):
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
            lv_set_V = interpolated_power_supply_data[:,5]
            lv_vm_V = interpolated_power_supply_data[:,6]
            lv_err_V = interpolated_power_supply_data[:,7]
            cm_w1_uA = interpolated_power_supply_data[:,8]
            cm_w2_uA = interpolated_power_supply_data[:,9]
            cm_w3_uA = interpolated_power_supply_data[:,10]

            # Create a folder to store the data files if it doesn't exist.
            folder_name = 'AdditionalDataFiles'
            os.makedirs(folder_name, exist_ok=True)

            file_name = os.path.join(folder_name, f"pos_{str(position_mm[-1])}_state_{self.state}_date_{formatted_time}.csv")
            if not os.path.isfile(file_name):
                with open(file_name, 'w') as f:
                    f.write(f'Experiment: {self.experiment_type.currentText()}\n')
                    if self.motor_type.currentText() == 'Motor Fiber':
                        f.write(f'Motor type: {self.motor_type.currentText()}\n'
                                f'Fiber length (mm): {self.motor_length.text()}\n'
                                f'Number of fibers: {self.motor_number.text()}\n'
                                f'Insulator: {self.insulator.text()}\n')
                    elif self.motor_type.currentText() == 'Motor Ribbon':
                        f.write(f'Motor type: {self.motor_type.currentText()}\n'
                                f'Stator name: {self.stator_name.text()}\n'
                                f'Slider name: {self.slider_name.text()}\n')
                    f.write(f'State: {self.state}\n')
                    f.write(f'Sample rate (Hz): {self.sample_rate}\n')


                    f.write(f'Absolute time (s), Relative time (s), Force (mN), Position (mm), hv_set (V), hv_vm (V), hv_err (V), lv_set (V), lv_vm (V), lv_err (V),'
                            f'cm_w1 (uA), cm_w2 (uA), cm_w3 (uA)\n')
                    
            # Save the data to the .csv file.   
            save_data = np.column_stack((abs_time_s, rel_time_s, force_mN, position_mm, hv_set_kV, hv_vm_kV, hv_err_V, lv_set_V, lv_vm_V, lv_err_V,
                                         cm_w1_uA, cm_w2_uA, cm_w3_uA))
            with open(file_name, 'ab') as f:
                np.savetxt(f, save_data, fmt='%.8f, %.8f, %4.6f, %4.3f, %6.1f, %6.1f, % 3.1f, % 3.2f, % 3.2f, % 3.2f, % 3.1f, % 3.1f, % 3.1f')
    


