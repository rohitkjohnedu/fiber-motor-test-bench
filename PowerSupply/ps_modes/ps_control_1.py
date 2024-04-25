# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton

# custom packages
from SerialSender import *


class PS_Control_1(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.ser = None

        self.hv_max = 4500
        self.hv_min = 350
        self.f_max = 200
        self.f_min = 0.01

        self.extended_flag = 0
        self.previous_index = 0

        self.mode_layout = QFormLayout(self)
        # ************************************************************************************************************ #
        self.target_voltage_lbl = QLabel("Voltage:")
        # self.target_voltage_lbl.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.state = QLabel("State:")
        # self.hb_number_label.setFixedWidth(80)
        # ************************************************************************************************************ #
        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.target_voltage_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        # self.st_comboBox = QComboBox()
        # self.st_comboBox.addItem('A')
        # self.st_comboBox.addItem('B')
        # self.st_comboBox.addItem('C')
        # self.st_comboBox.addItem('A-D')
        # self.st_comboBox.addItem('B-E')
        # self.st_comboBox.addItem('C-F')
        # self.st_comboBox.addItem('Other')
        # self.st_comboBox.setFixedWidth(80)
        # ************************************************************************************************************ #
        # # following widgets are used just for the initialization
        # self.freq_edit = QLineEdit("1")
        # self.duty_cycle_edit = QLineEdit("50")
        # self.ch1_phase_shift_edit = QLineEdit("0")
        # self.ch2_phase_shift_edit = QLineEdit("0")
        # self.ch3_phase_shift_edit = QLineEdit("0")
        # ************************************************************************************************************ #
        # self.set_button = QPushButton("Set")
        # # self.start_button.setFixedWidth(80)
        # self.stop_button = QPushButton("Stop")
        # # self.stop_button.setFixedWidth(80)
        # ************************************************************************************************************ #
        self.mode_layout.addRow(self.target_voltage_lbl, self.target_voltage_edit)
        # self.mode_layout.addRow(self.state, self.st_comboBox)
        # self.mode_layout.addRow(self.set_button, self.stop_button)
        # ************************************************************************************************************ #
        # ACTIONS
        # self.st_comboBox.currentIndexChanged.connect(self.extended_set)
        self.target_voltage_edit.returnPressed.connect(self.voltage_set)
        # self.set_button.clicked.connect(self.set_command)
        # self.stop_button.clicked.connect(self.stop_command)
        # ------------------------------------------------------------------------------------------------------------ #
        # self.freq_edit.returnPressed.connect(self.first_set)
        # self.duty_cycle_edit.returnPressed.connect(self.first_set)
        # self.ch1_phase_shift_edit.returnPressed.connect(self.second_set)
        # self.ch2_phase_shift_edit.returnPressed.connect(self.second_set)
        # self.ch3_phase_shift_edit.returnPressed.connect(self.second_set)

    ########################################################################################################################
    # ADD BUTTONS ALWAYS TO THE END OF THE LAYOUT
    # def add_buttons(self):
    #     self.mode_layout.addRow(self.set_button, self.stop_button)

    ########################################################################################################################
    # EXTENDED SET
    # def extended_set(self):
    #     if self.st_comboBox.currentIndex()+1 >= 4 and self.extended_flag == 0:
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.freq_label = QLabel("Frequency (Hz):")
    #         # self.hb_freq_label.setFixedWidth(80)
    #         self.freq_edit = QLineEdit("1")
    #         self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         # self.freq_edit.setFixedWidth(80)
    #         self.mode_layout.addRow(self.freq_label, self.freq_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.duty_cycle_lbl = QLabel("Duty cycle (%):")
    #         # self.hb_duty_label.setFixedWidth(80)
    #         self.duty_cycle_edit = QLineEdit("50")
    #         self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         # self.hb_pos_duty_edit.setFixedWidth(80)
    #         self.mode_layout.addRow(self.duty_cycle_lbl, self.duty_cycle_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.ch1_phase_shift_lbl = QLabel("Phase shift (°), Ch. №1:")
    #         # self.hb_phase_shift_label.setFixedWidth(80)
    #         self.ch1_phase_shift_edit = QLineEdit("0")
    #         self.ch1_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         # self.phase_shift_edit.setFixedWidth(80)
    #         self.mode_layout.addRow(self.ch1_phase_shift_lbl, self.ch1_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.ch2_phase_shift_lbl = QLabel("Phase shift (°), Ch. №2:")
    #         # self.hb_phase_shift_label.setFixedWidth(80)
    #         self.ch2_phase_shift_edit = QLineEdit("0")
    #         self.ch2_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         # self.phase_shift_edit.setFixedWidth(80)
    #         self.mode_layout.addRow(self.ch2_phase_shift_lbl, self.ch2_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.ch3_phase_shift_lbl = QLabel("Phase shift (°), Ch. №3:")
    #         # self.hb_phase_shift_label.setFixedWidth(80)
    #         self.ch3_phase_shift_edit = QLineEdit("0")
    #         self.ch3_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         # self.phase_shift_edit.setFixedWidth(80)
    #         self.mode_layout.addRow(self.ch3_phase_shift_lbl, self.ch3_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.extended_flag = 1
    #     # **************************************************************************************************************** #
    #     elif self.st_comboBox.currentIndex()+1 < 4 and self.extended_flag == 0:
    #         pass
    #     # **************************************************************************************************************** #
    #     elif self.st_comboBox.currentIndex()+1 >= 4 and self.extended_flag == 1:
    #         pass
    #     # **************************************************************************************************************** #
    #     elif self.st_comboBox.currentIndex()+1 < 4 and self.extended_flag == 1:
    #         self.mode_layout.removeRow(self.freq_edit)
    #         self.mode_layout.removeRow(self.duty_cycle_edit)
    #         self.mode_layout.removeRow(self.ch1_phase_shift_edit)
    #         self.mode_layout.removeRow(self.ch2_phase_shift_edit)
    #         self.mode_layout.removeRow(self.ch3_phase_shift_edit)
    #         self.extended_flag = 0
    #     # **************************************************************************************************************** #
    #     self.add_buttons() # add buttons to the end of the layout
        # **************************************************************************************************************** #

    ####################################################################################################################
    # ATTACH SERIAL
    def attach_serial(self, serial):
        self.ser = serial

    ####################################################################################################################
    # # SEND COMMAND
    # def send_command(self, ser, command):
    #     to_send = bytearray(command, encoding="utf-8")
    #     ser.write(to_send)

    ####################################################################################################################
    # SET BTN clicked or ENTER pressed (STATE => ON)
    def voltage_set(self):
        try:
            self.new_hv_val = float(self.target_voltage_edit.text())
            # check voltage value
            if (self.new_hv_val >= self.hv_min) and (self.new_hv_val <= self.hv_max):
                to_send = "\r\nSHV {}\r\n".format(self.new_hv_val)
                send_command(self.ser, to_send)
                print("[INFO] HV ON: {} V".format(self.new_hv_val))
            elif self.new_hv_val == 0:
                self.voltage_stop()
                # self.stop_command()
            else:
                self.voltage_stop()
                # self.stop_command()
                print(f"[ERR] please respect voltage range [{self.hv_min};{self.hv_max}] V")
        except Exception as err_voltage_edit:
            print("[ERR] HV VAL: {} - {}".format(self.target_voltage_edit.text(), err_voltage_edit))
        return

    ####################################################################################################################
    # STOP button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_stop(self):
        to_send = "\r\nSHV 0\r\n"
        send_command(self.ser, to_send)
        print("[INFO] HV OFF")
        # unlock the mode
        # self.lock_command(is_on=0)
        # reset the previous index
        # self.previous_index = 0
        return

























    ####################################################################################################################
    # def simple_set(self):
    #     if self.st_comboBox.currentText() == 'A':
    #         channel_val = int(pow(2, 0))
    #     elif self.st_comboBox.currentText() == 'B':
    #         channel_val = int(pow(2, 1))
    #     elif self.st_comboBox.currentText() == 'C':
    #         channel_val = int(pow(2, 2))

    #     to_send = "\r\nSMx 1 {} {} {}\r\n" .format(channel_val, 1, 100)
    #     self.send_command(self.ser, to_send)

    #     if self.st_comboBox.currentText() == 'A':
    #         print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(1))
    #     elif self.st_comboBox.currentText() == 'B':
    #         print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(2))
    #     elif self.st_comboBox.currentText() == 'C':
    #         print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(3))

    ####################################################################################################################
    # TOGGLE CLICKED = SET STATE
    # def first_set(self):
    #     try:
    #         channel_val = 0
    #         # hb_val = int(self.st_comboBox.currentIndex())+1
    #         hb_val = 3
    #         for exponent in range(hb_val):
    #             channel_val += pow(2, exponent)
    #         freq_val = float(self.freq_edit.text())
    #         duty_val = float(self.duty_cycle_edit.text())
    #         # check frequency/duty cycle value
    #         pos_pulse_width = float(10*(duty_val/freq_val))
    #         if pos_pulse_width < 2:
    #             self.stop_command()
    #             print("[ERR] Positive pulse width: {} ms < 2 ms".format(pos_pulse_width))
    #         else:
    #             # check frequency value
    #             if (freq_val >= self.f_min) and (freq_val <= self.f_max):
    #                 to_send = "\r\nSMx 5 1 {} {} {} \r\n".format(channel_val, freq_val, duty_val)
    #                 self.send_command(self.ser, to_send)
    #                 print("[INFO] Set: {} Channels | {}Hz | {}%".format(channel_val, freq_val, duty_val))
    #             else:
    #                 self.stop_command()
    #     except Exception as err_fb_freq_edit:
    #         print("[ERR] FB FREQ VAL: {} - {}".format(self.freq_edit.text(), err_fb_freq_edit))
    #     return

    ####################################################################################################################
    # SECOND TOGGLE CLICKED = SET STATE
    # def second_set(self):
    #     if self.st_comboBox.currentText() == 'A-D':
    #         ch1_phase_shift_val = 0
    #         ch2_phase_shift_val = 180
    #         ch3_phase_shift_val = 180
    #     elif self.st_comboBox.currentText() == 'B-E':
    #         ch1_phase_shift_val = 180
    #         ch2_phase_shift_val = 0
    #         ch3_phase_shift_val = 180
    #     elif self.st_comboBox.currentText() == 'C-F':
    #         ch1_phase_shift_val = 180
    #         ch2_phase_shift_val = 180
    #         ch3_phase_shift_val = 0
    #     else:
    #         ch1_phase_shift_val = float(self.ch1_phase_shift_edit.text())
    #         ch2_phase_shift_val = float(self.ch2_phase_shift_edit.text())
    #         ch3_phase_shift_val = float(self.ch3_phase_shift_edit.text())

    #     to_send = "\r\nSMx 5 2 {} {} {} \r\n".format(ch1_phase_shift_val, ch2_phase_shift_val, ch3_phase_shift_val)
    #     self.send_command(self.ser, to_send)
    #     print("[INFO] Set phase shift | Ch. №1: {}° | Ch. №2: {}° | Ch. №3: {}°".format(ch1_phase_shift_val,
    #                                                                                     ch2_phase_shift_val,
    #                                                                                     ch3_phase_shift_val)) 
    
    ####################################################################################################################
    # START COMMAND
    # def set_command(self):
    #     if self.st_comboBox.currentIndex()+1 == self.previous_index:
    #         self.voltage_set()
    #     else:
    #         self.previous_index = self.st_comboBox.currentIndex()+1
    #         self.voltage_set()
    #         if self.st_comboBox.currentIndex()+1 < 4:
    #             self.simple_set()
    #         else:
    #             # print("Here")
    #             self.first_set() # frequency and duty cycle set
    #             self.second_set() # phase shift set

    #             to_send = "\r\nSMx 5 0\r\n"
    #             self.send_command(self.ser, to_send)
    #             print("[INFO] Mode ON")

    #         self.lock_command(is_on=1)

    ####################################################################################################################
    # LOCK COMMAND
    # def lock_command(self, is_on):
    #     if is_on == 1:
    #         self.st_comboBox.setDisabled(True)
    #         if self.st_comboBox.currentIndex()+1 >= 4:
    #             self.freq_edit.setDisabled(True)
    #             self.duty_cycle_edit.setDisabled(True)
    #             self.ch1_phase_shift_edit.setDisabled(True)
    #             self.ch2_phase_shift_edit.setDisabled(True)
    #             self.ch3_phase_shift_edit.setDisabled(True)
    #         print("[INFO] Mode locked")
    #     else:
    #         self.st_comboBox.setDisabled(False)
    #         if self.st_comboBox.currentIndex()+1 >= 4:
    #             self.freq_edit.setDisabled(False)
    #             self.duty_cycle_edit.setDisabled(False)
    #             self.ch1_phase_shift_edit.setDisabled(False)
    #             self.ch2_phase_shift_edit.setDisabled(False)
    #             self.ch3_phase_shift_edit.setDisabled(False)
    #         print("[INFO] Mode unlocked")
        

    ####################################################################################################################
    # TOGGLE NOT CLICKED = STOP STATE
    # def stop_command(self):
    #     if self.st_comboBox.currentText() == 'A':
    #         self.voltage_stop()
    #         to_send = "\r\nCMx 1 {}\r\n".format(pow(2, 0))
    #         self.send_command(self.ser, to_send)
    #         print("[INFO] Mode 1: Half-Bridge {} OFF".format(1))
    #     elif self.st_comboBox.currentText() == 'B':
    #         self.voltage_stop()
    #         to_send = "\r\nCMx 1 {}\r\n".format(pow(2, 1))
    #         self.send_command(self.ser, to_send)
    #         print("[INFO] Mode 1: Half-Bridge {} OFF".format(2))
    #     elif self.st_comboBox.currentText() == 'C':
    #         self.voltage_stop()
    #         to_send = "\r\nCMx 1 {}\r\n".format(pow(2, 2))
    #         self.send_command(self.ser, to_send)
    #         print("[INFO] Mode 1: Half-Bridge {} OFF".format(3))
    #     else:
    #         to_send = "\r\nCMx 5 0\r\n"
    #         self.send_command(self.ser, to_send)
    #         self.voltage_stop()
    #         print("[INFO] Mode 5: Half-Bridges 1-3 OFF")

