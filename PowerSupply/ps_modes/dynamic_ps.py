# python packages
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton
import time

class LoopThread(QThread):
    loop_finished = pyqtSignal()

    def __init__(self, device, channels_keys, freq_val, duty_val, t_switch_val, sequence_time_total_val):
        super().__init__()

        self.device = device
        self.channels_keys = channels_keys
        self.freq_val = freq_val
        self.duty_val = duty_val
        self.t_switch_val = t_switch_val
        self.sequence_time_total_val = sequence_time_total_val

        self.stop_flag = False

    def run(self):
        print("\n[INFO] Loop started.")
        for sequence in range(self.sequence_time_total_val):
            if not self.stop_flag:
                if self.device.hb_set(self.channels_keys, self.freq_val, self.duty_val, phase_shift=120):
                    print("-----> Forward")
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
            # ------------------------------------------------------------------------------------------- #
            if not self.stop_flag:       
                time.sleep(self.t_switch_val)
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
                time.sleep(self.t_switch_val)
            else:
                print("[INFO] Loop interrupted.\n------------------------")
                self.loop_finished.emit()
                break
        # ------------------------------------------------------------------------------------------- #
        if not self.stop_flag:
            self.loop_finished.emit()
            print("[INFO] Loop finished.\n---------------------")
    

class Loop_PS(QWidget):
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
        hb_bumber_lbl = QLabel("HB №:")
        # # hb_bumber_lbl.setFixedWidth(80)
        frequency_lbl = QLabel("Frequency (Hz):")
        # frequency_lbl.setFixedWidth(80)
        duty_cycle_lbl = QLabel("Duty cycle (%):")
        # duty_cycle_lbl.setFixedWidth(80)
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
        self.t_switch_label = QLabel("Time (s)")
        self.t_switch_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.t_switch_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.t_switch_edit = QLineEdit("1")
        self.t_switch_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.t_switch_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.sequence_time_label = QLabel("Sequences")
        self.sequence_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # self.sequence_time_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.sequence_time_edit = QLineEdit("1")
        self.sequence_time_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.sequence_time_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # self.set_button.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        self.mode_layout.addRow(hb_bumber_lbl, self.hb_comboBox)
        self.mode_layout.addRow(frequency_lbl, self.freq_edit)
        self.mode_layout.addRow(duty_cycle_lbl, self.duty_cycle_edit)
        self.mode_layout.addRow(self.t_switch_label, self.t_switch_edit)
        self.mode_layout.addRow(self.sequence_time_label, self.sequence_time_edit)
        self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        nb_channels = int(self.hb_comboBox.currentIndex()) # 2
        self.channels_keys = list(range(nb_channels+1)) # [0, 1, 2]

        # ************************************************************************************************************ #
        # ACTIONS
        self.set_button.clicked.connect(self.set_pressed)

    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        new_hv_val = float(self.target_voltage_edit.text())
        freq_val = float(self.freq_edit.text())
        duty_val = float(self.duty_cycle_edit.text())
        t_switch_val = float(self.t_switch_edit.text())
        sequence_time_total_val = int(self.sequence_time_edit.text())
        if new_hv_val == 0 and self.set_button.text() == "Set":
            print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else: 
            if self.set_button.text() =="Set":
                self.set_button.setText("Reset")
                self.voltage_set()
                self.lock_command(is_on=1)
                if not self.loop_thread or not self.loop_thread.isRunning():
                    self.loop_thread = LoopThread(self.device, self.channels_keys, freq_val, duty_val, t_switch_val, sequence_time_total_val)
                    self.loop_thread.loop_finished.connect(self.reset_command)
                    self.loop_thread.start()
            else:
                if self.loop_thread and self.loop_thread.isRunning():
                    self.loop_thread.stop_flag = True # Stop existing thread if running

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
            self.t_switch_edit.setDisabled(True)
            self.sequence_time_edit.setDisabled(True)
            print("[INFO] Mode locked\n"
                  "------------------")
        else:
            self.freq_edit.setDisabled(False)
            self.duty_cycle_edit.setDisabled(False)
            self.t_switch_edit.setDisabled(False)
            self.sequence_time_edit.setDisabled(False)
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


