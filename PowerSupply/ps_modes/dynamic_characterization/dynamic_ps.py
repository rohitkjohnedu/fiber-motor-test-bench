# python packages
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QCheckBox
import time

class LoopThread(QThread):
    loop_finished = pyqtSignal()

    def __init__(self, device, channels_keys, freq_val, duty_val, modul_freq, t_forward_val, t_backward_val, sequences_val):
        super().__init__()

        self.device = device
        self.channels_keys = channels_keys
        self.freq_val = freq_val
        self.duty_val = duty_val
        self.modul_freq = modul_freq
        self.t_forward_val = t_forward_val
        self.t_backward_val = t_backward_val
        self.sequences_val = sequences_val

        self.stop_flag = False

    def run(self):
        print("\n[INFO] Loop started.")
        for sequence in range(self.sequences_val):
            if not self.stop_flag:
                if self.device.hb_set(self.channels_keys, self.freq_val, self.duty_val, phase_shift=120):
                    print("-----> Forward")
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
            # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:       
                time.sleep(self.t_forward_val)
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
            # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:
                if self.device.hb_set(self.channels_keys, self.freq_val, self.duty_val, phase_shift=240):
                    print("<----- Backward")
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
            # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:
                time.sleep(self.t_backward_val)
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
        # ------------------------------------------------------------------------------------------- #
        if not self.stop_flag:
            self.loop_finished.emit()
            print("[INFO] Loop finished.\n---------------------")
    

class Dynamic_PS(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        # PS device
        self.device = device
        # ------------------- #
        self.loop_thread = None

        # ************************************************************************************************************ #
        # INTERFACE ELEMENTS
        self.mode_layout = QFormLayout(self)
        # ------------------------------------------------------------------------------------------------------------ #
        target_voltage_lbl = QLabel("Voltage:")
        # target_voltage_lbl.setFixedWidth(80)
        hb_number_lbl = QLabel("Channels:")
        # hb_number_lbl.setFixedWidth(80)
        frequency_lbl = QLabel("Frequency (Hz):")
        # frequency_lbl.setFixedWidth(80)
        duty_cycle_lbl = QLabel("Duty cycle (%):")
        # duty_cycle_lbl.setFixedWidth(80)
        modul_freq_lbl = QLabel("Modulation\n"
                                "frequency (Hz):")
        # modul_freq_lbl.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # target_voltage_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # target_voltage_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.hb_comboBox = QComboBox()
        self.hb_comboBox.addItem('1')
        self.hb_comboBox.addItem('2')
        self.hb_comboBox.addItem('3')
        self.hb_comboBox.setCurrentIndex(2)
        self.hb_comboBox.setDisabled(True)
        # hb_combobox.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_edit = QLineEdit("1")
        self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # freq_edit.setFixedWidth(80)
        self.duty_cycle_edit = QLineEdit("50")
        self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # duty_cycle_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.modul_freq_edit = QLineEdit("0")
        self.modul_freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.modul_freq_edit.setFixedWidth(80)
        self.modul_freq_edit.setFixedHeight(30)
        # ------------------------------------------------------------------------------------------------------------ #
        self.moving_time_label = QLabel("Time (s):")
        self.moving_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.moving_time_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.moving_time_edit = QLineEdit("1")
        self.moving_time_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.moving_time_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.direction_label = QLabel("Direction:")
        self.direction_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.direction_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.direction_edit = QComboBox()
        self.direction_edit.addItem('Forward')
        self.direction_edit.addItem('Backward')
        # self.direction_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.repeated_mode_lbl = QLabel("Repeated mode:")
        self.repeated_mode_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.repeated_mode_lbl.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.repeated_mode_checkbox = QCheckBox()
        self.repeated_mode_checkbox.setChecked(False)
        # self.repeated_mode_checkbox.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.sequences_label = QLabel("Sequences:")
        self.sequences_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.sequence_time_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.sequences_edit = QLineEdit("1")
        self.sequences_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.sequence_time_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.t_forward_lbl = QLabel("Time forward (s):")
        self.t_forward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.t_switch_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.t_forward_edit = QLineEdit("1")
        self.t_forward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.t_switch_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.t_backward_lbl = QLabel("Time backward (s):")
        self.t_backward_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.t_switch_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.t_backward_edit = QLineEdit("1")
        self.t_backward_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.t_switch_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # self.set_button.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        # self.update_button = QPushButton("Update")
        # # self.update_button.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        # self.mode_layout.addRow(hb_number_lbl, self.hb_comboBox)
        self.mode_layout.addRow(frequency_lbl, self.freq_edit)
        self.mode_layout.addRow(duty_cycle_lbl, self.duty_cycle_edit)
        self.mode_layout.addRow(modul_freq_lbl, self.modul_freq_edit)
        self.mode_layout.addRow(self.moving_time_label, self.moving_time_edit)
        self.mode_layout.addRow(self.direction_label, self.direction_edit)
        self.mode_layout.addRow(self.repeated_mode_lbl, self.repeated_mode_checkbox)
        self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        nb_channels = int(self.hb_comboBox.currentIndex()) # 2
        self.channels_keys = list(range(nb_channels+1)) # [0, 1, 2]

        # ************************************************************************************************************ #
        # ACTIONS
        self.set_button.clicked.connect(self.set_pressed)
        # self.update_button.clicked.connect(self.set_pressed)
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
            self.mode_layout.removeRow(self.direction_label)
            # ------------------------------------------------------------------------------------------------------------ #
            self.sequences_label = QLabel("Sequences:")
            self.sequences_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            # self.sequence_time_label.setFixedWidth(80)
            # ------------------------------------------------------------------------------------------------------------ #
            self.sequences_edit = QLineEdit("1")
            self.sequences_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.sequence_time_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.sequences_label, self.sequences_edit)
            self.mode_layout.addRow(self.t_forward_lbl, self.t_forward_edit)
            self.mode_layout.addRow(self.t_backward_lbl, self.t_backward_edit)
        else:
            self.mode_layout.addRow(self.moving_time_label)
            self.mode_layout.addRow(self.direction_label)
            self.mode_layout.removeRow(self.sequences_label, self.sequences_edit)
            self.mode_layout.removeRow(self.t_forward_lbl, self.t_forward_edit)
            self.mode_layout.removeRow(self.t_backward_lbl, self.t_backward_edit)
        self.add_buttons() # add buttons to the end of the layout

    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        new_hv_val = float(self.target_voltage_edit.text())
        freq_val = float(self.freq_edit.text())
        duty_val = float(self.duty_cycle_edit.text())
        modul_freq = float(self.modul_freq_edit.text())
        moving_time_val = float(self.moving_time_edit.text())
        direction_val = self.direction_edit.currentText()

        if new_hv_val == 0 and self.set_button.text() == "Set":
            print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else: 
            if self.set_button.text() =="Set":
                self.set_button.setText("Reset")
                self.voltage_set()
                self.lock_command(is_on=1)
                if self.repeated_mode_checkbox.isChecked():
                    sequences_val = int(self.sequences_edit.text())
                    t_forward_val = float(self.t_forward_edit.text())
                    t_backward_val = float(self.t_backward_edit.text())
                    if not self.loop_thread or not self.loop_thread.isRunning():
                        self.loop_thread = LoopThread(self.device, self.channels_keys, freq_val, duty_val, modul_freq,
                                                      t_forward_val, t_backward_val, sequences_val)
                        self.loop_thread.loop_finished.connect(self.reset_command)
                        self.loop_thread.start()
                    else:
                        if self.loop_thread and self.loop_thread.isRunning():
                            self.loop_thread.stop_flag = True # Stop existing thread if running
                else:
                    if direction_val == "Forward":
                        if self.device.hb_set(self.channels_keys, freq_val, duty_val, phase_shift=120):
                            print("-----> Forward")
                            time.sleep(moving_time_val)
                            self.reset_command()
                    elif direction_val == "Backward":
                        if self.device.hb_set(self.channels_keys, freq_val, duty_val, phase_shift=240):
                            print("<----- Backward")
                            time.sleep(moving_time_val)
                            self.reset_command()

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self):
        new_hv_val = float(self.target_voltage_edit.text())
        if new_hv_val == 0:
            self.reset_command()
            # reset the set button
            self.set_button.setText("Set")
        else:
            if self.device.set_voltage(new_hv_val):
                print("\n[INFO] HV ON: {} V\n----------------------".format(new_hv_val))
            if self.set_button.text() == "Set":
                self.set_button.setText("Reset")

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            print("\n[INFO] HV OFF\n------------------")

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on):
        if is_on == 1:
            self.freq_edit.setDisabled(True)
            self.duty_cycle_edit.setDisabled(True)
            self.moving_time_edit.setDisabled(True)
            self.modul_freq_edit.setDisabled(True)
            self.direction_edit.setDisabled(True)
            self.repeated_mode_checkbox.setDisabled(True)
            if self.repeated_mode_checkbox.isChecked():
                self.sequences_edit.setDisabled(True)
                self.t_forward_edit.setDisabled(True)
                self.t_backward_edit.setDisabled(True)
            print("[INFO] Mode locked\n"
                  "------------------")
        else:
            self.freq_edit.setDisabled(False)
            self.duty_cycle_edit.setDisabled(False)
            self.moving_time_edit.setDisabled(False)
            self.modul_freq_edit.setDisabled(False)
            self.direction_edit.setDisabled(False)
            if self.repeated_mode_checkbox.isChecked():
                self.sequences_edit.setDisabled(False)
                self.t_forward_edit.setDisabled(False)
                self.t_backward_edit.setDisabled(False)
            print("[INFO] Mode unlocked\n"
                  "--------------------")

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self):
        self.set_button.setText("Set")
        self.voltage_reset()
        if self.device.hb_stop_multi():
                print("[INFO] Mode 3: Half-Bridges 1-3 OFF")
        # unlock the mode
        self.lock_command(is_on=0)


