# python packages
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QMessageBox,
                              QHBoxLayout)
import time

class Thread(QThread):
    finish = pyqtSignal()

    def __init__(self, device, channels_keys, step_freq, step_duty, modul_freq, moving_time,
                    direction, repeated_mode, t_forward, t_backward, repetitions, debug=0):
        super().__init__()

        self.device = device
        self.channels_keys = channels_keys
        self.step_freq = step_freq
        self.step_duty = step_duty
        self.modul_freq = modul_freq
        self.modul_duty = 50
        self.moving_time = moving_time
        self.direction = direction
        self.repeated_mode = repeated_mode
        self.t_forward = t_forward
        self.t_backward = t_backward
        self.repetitions = repetitions
        self.stop_flag = False
        self.debug = debug

    def run(self):
        if self.repeated_mode:
            self.loop()
        else:
            self.single_run()
    
    # **************************************************************************************************************** #
            
    def loop(self):
        if self.modul_freq is not None:
            self.loop_modulation()
        else:
            self.loop_no_modulation()
    
    def loop_modulation(self):
        pass

    def loop_no_modulation(self):
        if self.direction == "Forward":
            phase_shift_1 = 120
            duration_1 = self.t_forward
            direction_1 = "-----> Forward"
            phase_shift_2 = 240
            duration_2 = self.t_backward
            direction_2 = "-----> Backward"
        elif self.direction == "Backward":
            phase_shift_1 = 240
            duration_1 = self.t_backward
            direction_1 = "-----> Backward"
            phase_shift_2 = 120
            duration_2 = self.t_forward
            direction_2 = "-----> Forward"
        if self.debug == 2:
            print("\n[INFO] Loop started.")
        for repetition in range(self.repetitions):
            if self.stop_flag:
                print("[INFO] Loop interrupted.\n----------------------")
                break
            # ------------------------------------------------------------------------------------------- #
            self.device.hb_set(self.channels_keys, self.step_freq, self.step_duty, phase_shift_1)
            if self.debug == 2:
                print(direction_1)
            # ------------------------------------------------------------------------------------------- #
            time.sleep(duration_1)
            # ------------------------------------------------------------------------------------------- #
            self.device.hb_set(self.channels_keys, self.step_freq, self.step_duty, phase_shift_2)
            if self.debug == 2:
                print(direction_2)
            # ------------------------------------------------------------------------------------------- #
            time.sleep(duration_2)
            # ------------------------------------------------------------------------------------------- #
            if self.debug == 2:
                print("[INFO] Repetition: {}".format(repetition+1))
        if not self.stop_flag:
            self.finish.emit()
            if self.debug == 2:
                print("[INFO] Loop finished.\n---------------------")

    # **************************************************************************************************************** #
    
    def single_run(self):
        if self.modul_freq is not None:
            self.single_run_modulation()
        else:
            self.single_run_no_modulation()

    def single_run_modulation(self):
        print("\n[INFO] Run started.")
        if self.device.hb_set(self.channels_keys, self.modul_freq, self.modul_duty, step_freq=self.step_freq, direction=self.direction):
            time.sleep(self.moving_time)
            self.device.dynamic_modulation = False
            self.finish.emit()
        
    def single_run_no_modulation(self):
        if self.debug == 2:
            print("\n[INFO] Run started.")
        # ------------------------------------------------------------------------------------------------------------ #
        if self.direction == "Forward":
            if self.device.hb_set(self.channels_keys, self.step_freq, self.step_duty, phase_shift=120):
                # --------------------------- #
                if self.debug == 2:
                    print("-----> Forward")
                # --------------------------- #
                time.sleep(self.moving_time)
                # --------------------------- #
                if not self.stop_flag:
                    self.finish.emit()
                # --------------------------- #
                if self.debug == 2:
                    print("[INFO] Run finished.\n--------------------")
        # ------------------------------------------------------------------------------------------------------------ #            
        elif self.direction == "Backward":
            if self.device.hb_set(self.channels_keys, self.step_freq, self.step_duty, phase_shift=240):
                # --------------------------- #
                if self.debug == 2:
                    print("<----- Backward")
                # --------------------------- #
                time.sleep(self.moving_time)
                # --------------------------- #
                if not self.stop_flag:
                    self.finish.emit()
                # --------------------------- #
                if self.debug == 2:
                    print("[INFO] Run finished.\n--------------------")

############################################################################################################################   

class Dynamic_PS(QWidget):
    def __init__(self, device=None, mode=None, exp_type=None, debug=0, parent=None):
        QWidget.__init__(self, parent=parent)

        # PS device
        self.device = device
        self.mode = mode
        self.exp_type = exp_type
        self.debug = debug
        # ------------------- #
        self.run_thread = None
        self.sleep_thread = None

        # ************************************************************************************************************ #
        # INTERFACE ELEMENTS
        self.mode_layout = QFormLayout(self)
        # ------------------------------------------------------------------------------------------------------------ #
        target_voltage_lbl = QLabel("Voltage (V):")
        
        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        # hb_number_lbl = QLabel("Channels:")
        # hb_number_lbl.setFixedWidth(200)
        
        hb_comboBox = QComboBox()
        hb_comboBox.addItem('1')
        hb_comboBox.addItem('2')
        hb_comboBox.addItem('3')
        hb_comboBox.setCurrentIndex(2)
        hb_comboBox.setDisabled(True)
        # ------------------------------------------------------------------------------------------------------------ #
        modulation_lbl = QLabel("Modulation:")
        modulation_lbl.setFixedWidth(160)

        self.modulation_opt = QCheckBox()
        self.modulation_opt.setText("ON")
        self.modulation_opt.setChecked(False)

        self.modulation_layout = QHBoxLayout()
        self.modulation_layout.addWidget(modulation_lbl)
        self.modulation_layout.addWidget(self.modulation_opt)
        # ------------------------------------------------------------------------------------------------------------ #
        step_freq_lbl = QLabel("Step. frequency (Hz):")
        
        self.step_freq_edit = QLineEdit("1")
        self.step_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        # step_dc_lbl = QLabel("Step. duty cycle (%):")

        self.step_dc_edit = QLineEdit("50")
        self.step_dc_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        self.moving_time_lbl = QLabel("Time (s):")
        self.moving_time_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.moving_time_edit = QLineEdit("1")
        self.moving_time_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        self.direction_label = QLabel("Direction:")
        self.direction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.direction_edit = QComboBox()
        self.direction_edit.addItem("Forward")
        self.direction_edit.addItem("Backward")
        # ------------------------------------------------------------------------------------------------------------ #
        self.repeated_mode_lbl = QLabel("Repeated mode:")
        self.repeated_mode_lbl.setFixedWidth(160)
        self.repeated_mode_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.repeated_mode_checkbox = QCheckBox()
        self.repeated_mode_checkbox.setText("ON")
        self.repeated_mode_checkbox.setChecked(False)

        self.repeated_mode_layout = QHBoxLayout()
        self.repeated_mode_layout.addWidget(self.repeated_mode_lbl)
        self.repeated_mode_layout.addWidget(self.repeated_mode_checkbox)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        self.mode_layout.addRow(step_freq_lbl, self.step_freq_edit)
        self.mode_layout.addRow(self.modulation_layout)
        self.mode_layout.addRow(self.repeated_mode_layout)
        self.mode_layout.addRow(self.direction_label, self.direction_edit)
        self.mode_layout.addRow(self.moving_time_lbl, self.moving_time_edit)
        if self.mode == "manual":
            self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        nb_channels = int(hb_comboBox.currentIndex()) # 2
        self.channels_keys = list(range(nb_channels+1)) # [0, 1, 2]

        # ************************************************************************************************************ #
        # ACTIONS
        if self.device is not None:
            self.set_button.clicked.connect(self.set_pressed)
        self.repeated_mode_checkbox.stateChanged.connect(self.repeated_mode_changed)
        self.modulation_opt.stateChanged.connect(self.modulation_opt_changed)
            
    ####################################################################################################################
    # REPEATED MODE CHANGED
    def repeated_mode_changed(self):
        if self.repeated_mode_checkbox.isChecked():
            self.mode_layout.removeRow(self.moving_time_lbl)
            # ------------------------------------------------------------------------------------------------------------ #
            self.repetitions_label = QLabel("Repetitions:")
            self.repetitions_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.repetitions_edit = QLineEdit("1")
            self.repetitions_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.t_forward_lbl = QLabel("Time forward (s):")
            self.t_forward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.t_forward_edit = QLineEdit("1")
            self.t_forward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.t_backward_lbl = QLabel("Time backward (s):")
            self.t_backward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.t_backward_edit = QLineEdit("1")
            self.t_backward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.mode_layout.addRow(self.repetitions_label, self.repetitions_edit)
            self.mode_layout.addRow(self.t_forward_lbl, self.t_forward_edit)
            self.mode_layout.addRow(self.t_backward_lbl, self.t_backward_edit)
        else:
            self.mode_layout.removeRow(self.direction_label)
            self.mode_layout.removeRow(self.repetitions_label)
            # ------------------------------------------------------------------------------------------------------------ #
            self.moving_time_lbl = QLabel("Time (s):")
            self.moving_time_edit = QLineEdit("1")
            self.moving_time_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.direction_label = QLabel("Direction:")
            self.direction_edit = QComboBox()
            self.direction_edit.addItem("Forward")
            self.direction_edit.addItem("Backward")
            # ------------------------------------------------------------------------------------------------------------ # 
            self.mode_layout.removeRow(self.t_forward_lbl)
            self.mode_layout.removeRow(self.t_backward_lbl)
            self.mode_layout.addRow(self.direction_label, self.direction_edit)
            self.mode_layout.addRow(self.moving_time_lbl, self.moving_time_edit)
        if self.mode == "manual":
            self.mode_layout.addRow(self.set_button)
    
    ########################################################################################################################
    # MODULATION OPTION CHECKED
    def modulation_opt_changed(self):
        if self.modulation_opt.isChecked():
            rep = self.repeated_mode_checkbox.isChecked()
            self.mode_layout.removeRow(self.repeated_mode_layout)
            self.mode_layout.removeRow(self.direction_label)
            if rep == False:
                self.mode_layout.removeRow(self.moving_time_lbl)
            else:
                self.mode_layout.removeRow(self.repetitions_label)
                self.mode_layout.removeRow(self.t_forward_lbl)
                self.mode_layout.removeRow(self.t_backward_lbl)
            # ------------------------------------------------------------------------------------------------------------ #
            modul_freq_lbl = QLabel("Modul. frequency (Hz):")
            self.modul_freq_edit = QLineEdit("1")
            self.modul_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.modul_dc_edit = QLineEdit("50")
            # ------------------------------------------------------------------------------------------------------------ #
            step_freq_lbl = QLabel("Step. frequency (Hz):")
            self.step_freq_edit = QLineEdit("1")
            self.step_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.repeated_mode_lbl = QLabel("Repeated mode:")
            self.repeated_mode_lbl.setFixedWidth(160)
            self.repeated_mode_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            self.repeated_mode_checkbox = QCheckBox()
            self.repeated_mode_checkbox.setText("ON")

            self.repeated_mode_layout = QHBoxLayout()
            self.repeated_mode_layout.addWidget(self.repeated_mode_lbl)
            self.repeated_mode_layout.addWidget(self.repeated_mode_checkbox)
            # ------------------------------------------------------------------------------------------------------------ #
            self.moving_time_lbl = QLabel("Time (s):")
            self.moving_time_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

            self.moving_time_edit = QLineEdit("1")
            self.moving_time_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.direction_label = QLabel("Direction:")
            self.direction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            self.direction_edit = QComboBox()
            self.direction_edit.addItem("Forward")
            self.direction_edit.addItem("Backward")
            # ------------------------------------------------------------------------------------------------------------ #
            self.repetitions_label = QLabel("Repetitions:")
            self.repetitions_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.repetitions_edit = QLineEdit("1")
            self.repetitions_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.t_forward_lbl = QLabel("Time forward (s):")
            self.t_forward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.t_forward_edit = QLineEdit("1")
            self.t_forward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.t_backward_lbl = QLabel("Time backward (s):")
            self.t_backward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
                
            self.t_backward_edit = QLineEdit("1")
            self.t_backward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.mode_layout.addRow(modul_freq_lbl, self.modul_freq_edit)
            self.mode_layout.addRow(self.repeated_mode_layout)
            self.mode_layout.addRow(self.direction_label, self.direction_edit)
            if rep == False:
                self.mode_layout.addRow(self.moving_time_lbl, self.moving_time_edit)
            else:
                self.repeated_mode_checkbox.setChecked(True)
                self.mode_layout.addRow(self.repetitions_label, self.repetitions_edit)
                self.mode_layout.addRow(self.t_forward_lbl, self.t_forward_edit)
                self.mode_layout.addRow(self.t_backward_lbl, self.t_backward_edit)
            if self.mode == "manual":
                self.mode_layout.addRow(self.set_button)
            self.repeated_mode_checkbox.stateChanged.connect(self.repeated_mode_changed)
        else:
            self.mode_layout.removeRow(self.modul_freq_edit)
            if self.mode == "manual":
                self.mode_layout.addRow(self.set_button)
    
    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        new_hv = float(self.target_voltage_edit.text())
        if new_hv == 0 and self.set_button.text() == "Set":
            zero_volt = QMessageBox.warning(self, "Zero voltage", "Please, set the voltage value")
            if self.debug == 2:
                print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else: 
            if self.set_button.text() =="Set":
                if self.voltage_set() is True:
                    self.lock_command(is_on=1)
                    # ------------------------------------------------------------------------------ #
                    step_freq = float(self.step_freq_edit.text())
                    step_duty = float(self.step_dc_edit.text()) # 50 %
                    # ------------------------------------------------------------------------------ #
                    if self.modulation_opt.isChecked():
                        modul_freq = float(self.modul_freq_edit.text())
                    else:
                        modul_freq = None
                    # ------------------------------------------------------------------------------ #
                    direction = self.direction_edit.currentText()
                    # ------------------------------------------------------------------------------ #
                    repeated_mode = self.repeated_mode_checkbox.isChecked()
                    if repeated_mode:
                        moving_time = None
                        repetitions = int(self.repetitions_edit.text())
                        t_forward = float(self.t_forward_edit.text())
                        t_backward = float(self.t_backward_edit.text())
                    else:
                        moving_time = float(self.moving_time_edit.text())
                        repetitions = None
                        t_forward = None
                        t_backward = None
                    # ------------------------------------------------------------------------------ #
                    if not self.run_thread or not self.run_thread.isRunning():
                        self.run_thread = Thread(self.device, self.channels_keys, step_freq, step_duty,
                                                 modul_freq, moving_time, direction, repeated_mode,
                                                 t_forward, t_backward, repetitions, debug=self.debug)
                        self.run_thread.finish.connect(self.reset_command)
                        self.run_thread.start()
            else:
                if self.run_thread and self.run_thread.isRunning():
                    self.run_thread.stop_flag = True
                    self.reset_command()
                    if self.debug == 2:
                        print("[INFO] Run interrupted.\n----------------------")
                    

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self):
        new_hv = float(self.target_voltage_edit.text())
        if new_hv == 0:
            self.reset_command()
        else:
            if self.device.set_voltage(new_hv):
                if self.debug == 2:
                    print("\n[INFO] HV ON: {} V\n----------------------".format(new_hv))
                if self.set_button.text() == "Set":
                    self.set_button.setText("Reset")
                return True

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            if self.debug == 2:
                print("[INFO] HV OFF\n------------------")

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on):
        if is_on == 1:
            self.target_voltage_edit.setDisabled(True)
            if self.repeated_mode_checkbox.isChecked() == False:
                self.moving_time_edit.setDisabled(True)
            self.direction_edit.setDisabled(True)
            self.repeated_mode_checkbox.setDisabled(True)
            if self.repeated_mode_checkbox.isChecked():
                self.repetitions_edit.setDisabled(True)
                self.t_forward_edit.setDisabled(True)
                self.t_backward_edit.setDisabled(True)
            if self.debug == 2:
                print("[INFO] Mode locked\n"
                    "------------------")
        else:
            self.target_voltage_edit.setDisabled(False)
            if self.repeated_mode_checkbox.isChecked() == False:
                self.moving_time_edit.setDisabled(False)
            self.direction_edit.setDisabled(False)
            self.repeated_mode_checkbox.setDisabled(False)
            if self.repeated_mode_checkbox.isChecked():
                self.repetitions_edit.setDisabled(False)
                self.t_forward_edit.setDisabled(False)
                self.t_backward_edit.setDisabled(False)
            if self.debug == 2:
                print("\n[INFO] Mode unlocked\n"
                    "--------------------")

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self):
        # unlock the mode
        self.lock_command(is_on=0)
        self.set_button.setText("Set")
        self.voltage_reset()
        if self.modulation_opt.isChecked():
            if self.device.hb_stop_shift():
                if self.debug == 2:
                    print("[INFO] Mode 5: Half-Bridges 1-3 OFF")
        else:
            if self.device.hb_stop_multi():
                if self.debug == 2:
                    print("[INFO] Mode 3: Half-Bridges 1-3 OFF")


