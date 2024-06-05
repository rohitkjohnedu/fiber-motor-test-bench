# python packages
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox, QMessageBox
import time

class Thread(QThread):
    finish = pyqtSignal()

    def __init__(self, device, channels_keys, modul_freq, duty_cycle, sequence_freq, moving_time, direction, 
                 repeated_mode, t_forward, t_backward, repetitions):
        super().__init__()

        self.device = device
        self.channels_keys = channels_keys
        self.modul_freq = modul_freq
        self.duty_cycle = duty_cycle
        self.sequence_freq = sequence_freq
        self.moving_time = moving_time
        self.direction = direction
        self.repeated_mode = repeated_mode
        self.t_forward = t_forward
        self.t_backward = t_backward
        self.repetitions = repetitions
        self.stop_flag = False

    def run(self):
        if self.repeated_mode:
            self.loop()
        else:
            self.single_run()
            
    def loop(self):
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
        print("\n[INFO] Loop started.")
        for repetition in range(self.repetitions):
            if not self.stop_flag:
                    if self.sequence_freq is None:
                        if self.device.hb_set(self.channels_keys, self.modul_freq, self.duty_cycle, phase_shift_1):
                            print(direction_1)
                    else:
                         self.sequence_time = 1/self.sequence_freq
            else:
                    print("[INFO] Loop interrupted.\n------------------------")
                    self.finish.emit()
                    break
                # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:       
                    time.sleep(duration_1)
            else:
                    print("[INFO] Loop interrupted.\n------------------------")
                    self.finish.emit()
                    break
                # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:
                    if self.device.hb_set(self.channels_keys, self.modul_freq, self.duty_cycle, phase_shift_2):
                        print(direction_2)
            else:
                    print("[INFO] Loop interrupted.\n------------------------")
                    self.finish.emit()
                    break
                # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:
                    time.sleep(duration_2)
            else:
                    print("[INFO] Loop interrupted.\n------------------------")
                    self.finish.emit()
                    break
            # ------------------------------------------------------------------------------------------- #
        if not self.stop_flag:
            self.finish.emit()
            print("[INFO] Loop finished.\n---------------------")
    
    def single_run(self):
        print("\n[INFO] Run started.")
        if self.direction == "Forward":
            if self.device.hb_set(self.channels_keys, self.modul_freq, self.duty_cycle, phase_shift=120):
                print("-----> Forward")
                time.sleep(self.moving_time)
                if not self.stop_flag:
                    self.finish.emit()
                    print("[INFO] Run finished.\n--------------------")
        elif self.direction == "Backward":
            if self.device.hb_set(self.channels_keys, self.modul_freq, self.duty_cycle, phase_shift=240):
                print("<----- Backward")
                time.sleep(self.moving_time)
                if not self.stop_flag:
                    self.finish.emit()
                    print("[INFO] Run finished.\n--------------------")


class Dynamic_PS(QWidget):
    def __init__(self, device=None, mode=None, parent=None):
        QWidget.__init__(self, parent=parent)

        # PS device
        self.device = device
        self.mode = mode
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
        
        self.hb_comboBox = QComboBox()
        self.hb_comboBox.addItem('1')
        self.hb_comboBox.addItem('2')
        self.hb_comboBox.addItem('3')
        self.hb_comboBox.setCurrentIndex(2)
        self.hb_comboBox.setDisabled(True)
        # ------------------------------------------------------------------------------------------------------------ #
        modul_freq_lbl = QLabel("Stepping frequency (Hz):")
        
        self.modul_freq_edit = QLineEdit("1")
        self.modul_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        duty_cycle_lbl = QLabel("Stepping duty cycle (%):")

        self.duty_cycle_edit = QLineEdit("50")
        self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        # sequence_freq_lbl = QLabel("Sequence frequency (Hz):")
        
        # self.sequence_freq_edit = QLineEdit("0")
        # self.sequence_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        self.moving_time_label = QLabel("Time (s):")
        self.moving_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

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
        self.repeated_mode_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.repeated_mode_checkbox = QCheckBox()
        self.repeated_mode_checkbox.setChecked(False)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        # self.mode_layout.addRow(hb_number_lbl, self.hb_comboBox)
        self.mode_layout.addRow(modul_freq_lbl, self.modul_freq_edit)
        self.mode_layout.addRow(duty_cycle_lbl, self.duty_cycle_edit)
        # self.mode_layout.addRow(sequence_freq_lbl, self.sequence_freq_edit)
        self.mode_layout.addRow(self.repeated_mode_lbl, self.repeated_mode_checkbox)
        self.mode_layout.addRow(self.direction_label, self.direction_edit)
        self.mode_layout.addRow(self.moving_time_label, self.moving_time_edit)
        if self.mode == "manual":
            self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        nb_channels = int(self.hb_comboBox.currentIndex()) # 2
        self.channels_keys = list(range(nb_channels+1)) # [0, 1, 2]

        # ************************************************************************************************************ #
        # ACTIONS
        if self.device is not None:
            self.set_button.clicked.connect(self.set_pressed)
        self.repeated_mode_checkbox.stateChanged.connect(self.repeated_mode_changed)
        
    ########################################################################################################################
    # ADD BUTTONS ALWAYS TO THE END OF THE LAYOUT
    def add_buttons(self):
        self.mode_layout.addRow(self.set_button)

    ####################################################################################################################
    # REPEATED MODE CHANGED
    def repeated_mode_changed(self):
        if self.repeated_mode_checkbox.isChecked():
            self.mode_layout.removeRow(self.moving_time_label)
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
            # ------------------------------------------------------------------------------------------------------------ #
            self.moving_time_label = QLabel("Time (s):")
            self.moving_time_edit = QLineEdit("1")
            self.t_backward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # ------------------------------------------------------------------------------------------------------------ #
            self.direction_label = QLabel("Direction:")
            self.direction_edit = QComboBox()
            self.direction_edit.addItem("Forward")
            self.direction_edit.addItem("Backward")
            # ------------------------------------------------------------------------------------------------------------ # 
            self.mode_layout.removeRow(self.repetitions_label)
            self.mode_layout.removeRow(self.t_forward_lbl)
            self.mode_layout.removeRow(self.t_backward_lbl)
            self.mode_layout.addRow(self.repeated_mode_lbl, self.repeated_mode_checkbox)
            self.mode_layout.addRow(self.direction_label, self.direction_edit)
            self.mode_layout.addRow(self.moving_time_label, self.moving_time_edit)
        self.add_buttons() # add buttons to the end of the layout

    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        new_hv = float(self.target_voltage_edit.text())
        if new_hv == 0 and self.set_button.text() == "Set":
            zero_volt = QMessageBox.warning(self, "Zero voltage", "Please, set the voltage value")
            print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else: 
            if self.set_button.text() =="Set":
                if self.voltage_set() is True:
                    self.lock_command(is_on=1)
                    modul_freq = float(self.modul_freq_edit.text())
                    duty_cycle = float(self.duty_cycle_edit.text())
                    sequence_freq = None # float(self.sequence_freq_edit.text())
                    if self.repeated_mode_checkbox.isChecked() == False:
                        moving_time = float(self.moving_time_edit.text())
                    else:
                        moving_time = None
                    direction = self.direction_edit.currentText()
                    repeated_mode = self.repeated_mode_checkbox.isChecked()
                    if repeated_mode:
                        repetitions = int(self.repetitions_edit.text())
                        t_forward = float(self.t_forward_edit.text())
                        t_backward = float(self.t_backward_edit.text())
                    else:
                        repetitions = None
                        t_forward = None
                        t_backward = None
                    if not self.run_thread or not self.run_thread.isRunning():
                        self.run_thread = Thread(self.device, self.channels_keys, modul_freq, duty_cycle, sequence_freq,
                                                moving_time, direction, repeated_mode, t_forward, t_backward, repetitions)
                        self.run_thread.finish.connect(self.reset_command)
                        self.run_thread.start()
            else:
                if self.run_thread and self.run_thread.isRunning():
                    self.run_thread.stop_flag = True
                    print("[INFO] Run interrupted.\n----------------------")
                    self.reset_command()

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self):
        new_hv = float(self.target_voltage_edit.text())
        if new_hv == 0:
            self.reset_command()
        else:
            if self.device.set_voltage(new_hv):
                print("\n[INFO] HV ON: {} V\n----------------------".format(new_hv))
                if self.set_button.text() == "Set":
                    self.set_button.setText("Reset")
                return True

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            print("[INFO] HV OFF\n------------------")

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on):
        if is_on == 1:
            self.target_voltage_edit.setDisabled(True)
            self.modul_freq_edit.setDisabled(True)
            self.duty_cycle_edit.setDisabled(True)
            if self.repeated_mode_checkbox.isChecked() == False:
                self.moving_time_edit.setDisabled(True)
            # self.sequence_freq_edit.setDisabled(True)
            self.direction_edit.setDisabled(True)
            self.repeated_mode_checkbox.setDisabled(True)
            if self.repeated_mode_checkbox.isChecked():
                self.repetitions_edit.setDisabled(True)
                self.t_forward_edit.setDisabled(True)
                self.t_backward_edit.setDisabled(True)
            print("[INFO] Mode locked\n"
                  "------------------")
        else:
            self.target_voltage_edit.setDisabled(False)
            self.modul_freq_edit.setDisabled(False)
            self.duty_cycle_edit.setDisabled(False)
            if self.repeated_mode_checkbox.isChecked() == False:
                self.moving_time_edit.setDisabled(False)
            # self.sequence_freq_edit.setDisabled(False)
            self.direction_edit.setDisabled(False)
            self.repeated_mode_checkbox.setDisabled(False)
            if self.repeated_mode_checkbox.isChecked():
                self.repetitions_edit.setDisabled(False)
                self.t_forward_edit.setDisabled(False)
                self.t_backward_edit.setDisabled(False)
            print("\n[INFO] Mode unlocked\n"
                  "--------------------")

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self):
        # unlock the mode
        self.lock_command(is_on=0)
        self.set_button.setText("Set")
        self.voltage_reset()
        if self.device.hb_stop_multi():
            print("[INFO] Mode 3: Half-Bridges 1-3 OFF")


