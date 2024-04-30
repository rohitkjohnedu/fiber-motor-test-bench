# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton


class Dynamic_PS(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        # PS device
        self.device = device

        # ************************************************************************************************************ #
        # INTERFACE ELEMENTS
        self.mode_layout = QFormLayout(self)
        # ------------------------------------------------------------------------------------------------------------ #
        target_voltage_lbl = QLabel("Voltage:")
        # target_voltage_lbl.setFixedWidth(80)
        frequency_lbl = QLabel("Frequency (Hz):")
        # target_voltage_lbl.setFixedWidth(80)
        seq_frequency_lbl = QLabel("Sequence Frequency (Hz):")
        # target_voltage_lbl.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # target_voltage_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        # The following widgets are used in "ACTIONS" section as a place holders, but then initialized in "EXTENDED SET"
        self.freq_edit = QLineEdit("1")
        # self.duty_cycle_edit = QLineEdit("50")
        # self.ch1_phase_shift_edit = QLineEdit("0")
        # self.ch2_phase_shift_edit = QLineEdit("0")
        # self.ch3_phase_shift_edit = QLineEdit("0")
        self.seq_freq_edit = QLineEdit("20")
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # self.set_button.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        self.mode_layout.addRow(frequency_lbl, self.freq_edit)
        self.mode_layout.addRow(seq_frequency_lbl, self.seq_freq_edit)
        self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        self.channels_keys = []
        # num_states = self.st_comboBox.count()
        # for index in range(1, num_states+1):
        #     self.channels_keys.append(index-1)
        # self.state_index = self.st_comboBox.currentIndex()
        # self.extended_flag_1 = 0
        # self.extended_flag_2 = 0
        # self.previous_index = -1
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_val = float(self.freq_edit.text())
        # self.duty_val = float(self.duty_cycle_edit.text())
        self.seq_freq_val = float(self.seq_freq_edit.text())

        # ************************************************************************************************************ #
        # ACTIONS
        # self.st_comboBox.currentIndexChanged.connect(self.extended_set)
        self.target_voltage_edit.returnPressed.connect(self.set_command)
        self.set_button.clicked.connect(self.set_pressed)
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_edit.returnPressed.connect(self.payload_set)
        self.seq_freq_edit.returnPressed.connect(self.payload_set)
        # self.duty_cycle_edit.returnPressed.connect(self.AC_set)
        # self.ch1_phase_shift_edit.returnPressed.connect(self.AC_set)
        # self.ch2_phase_shift_edit.returnPressed.connect(self.AC_set)
        # self.ch3_phase_shift_edit.returnPressed.connect(self.AC_set)

    # ########################################################################################################################
    # # ADD BUTTONS ALWAYS TO THE END OF THE LAYOUT
    # def add_buttons(self):
    #     self.mode_layout.addRow(self.set_button)

    # ########################################################################################################################
    # # EXTENDED SET for states A-D, B-E, C-F, Other
    # def extended_set(self):
    #     self.state_index = self.st_comboBox.currentIndex()
    #     # **************************************************************************************************************** #    
    #     if self.extended_flag_1 == 0 and self.state_index >= 3:
    #         self.freq_label = QLabel("Frequency (Hz):")
    #         self.freq_edit = QLineEdit("1")
    #         self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         self.mode_layout.addRow(self.freq_label, self.freq_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.duty_cycle_lbl = QLabel("Duty cycle (%):")
    #         self.duty_cycle_edit = QLineEdit("50")
    #         self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         self.mode_layout.addRow(self.duty_cycle_lbl, self.duty_cycle_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.extended_flag_1 = 1
    #     # **************************************************************************************************************** # 
    #     if self.extended_flag_1 == 1 and self.state_index == 6 and self.extended_flag_2 == 0:
    #         self.ch1_phase_shift_lbl = QLabel("Phase shift (°), Ch. №1:")
    #         self.ch1_phase_shift_edit = QLineEdit("0")
    #         self.ch1_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         self.mode_layout.addRow(self.ch1_phase_shift_lbl, self.ch1_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.ch2_phase_shift_lbl = QLabel("Phase shift (°), Ch. №2:")
    #         self.ch2_phase_shift_edit = QLineEdit("0")
    #         self.ch2_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         self.mode_layout.addRow(self.ch2_phase_shift_lbl, self.ch2_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.ch3_phase_shift_lbl = QLabel("Phase shift (°), Ch. №3:")
    #         self.ch3_phase_shift_edit = QLineEdit("0")
    #         self.ch3_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
    #         self.mode_layout.addRow(self.ch3_phase_shift_lbl, self.ch3_phase_shift_edit)
    #         # ------------------------------------------------------------------------------------------------------------ #
    #         self.extended_flag_2 = 1
    #     # **************************************************************************************************************** # 
    #     if self.extended_flag_1 == 1 and self.state_index < 3:
    #         self.mode_layout.removeRow(self.freq_edit)
    #         self.mode_layout.removeRow(self.duty_cycle_edit)
    #         self.extended_flag_1 = 0
    #     # **************************************************************************************************************** # 
    #     if self.extended_flag_2 == 1 and self.state_index < 6:
    #         self.mode_layout.removeRow(self.ch1_phase_shift_edit)
    #         self.mode_layout.removeRow(self.ch2_phase_shift_edit)
    #         self.mode_layout.removeRow(self.ch3_phase_shift_edit)
    #         self.extended_flag_2 = 0
    #     # **************************************************************************************************************** # 
    #     self.add_buttons() # add buttons to the end of the layout
    #     # **************************************************************************************************************** #

    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        self.new_hv_val = float(self.target_voltage_edit.text())
        if self.new_hv_val == 0 and self.set_button.text() == "Set":
            print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else: 
            if self.set_button.text() =="Set":
                self.set_command()
                self.set_button.setText("Reset")
            else:
                self.reset_command()
                self.set_button.setText("Set")

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self):
        self.new_hv_val = float(self.target_voltage_edit.text())
        if self.new_hv_val == 0:
            self.reset_command()
            # reset the set button
            self.set_button.setText("Set")
        else:
            if self.device.set_voltage(self.new_hv_val):
                print("\n[INFO] HV ON: {} V\n----------------------".format(self.new_hv_val))
            if self.set_button.text() == "Set":
                self.set_button.setText("Reset")

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            print("\n[INFO] HV OFF\n------------------")
            # reset the previous index
            # self.previous_index = -1

    ####################################################################################################################
    # SET button clicked (state 'A' or 'B' or 'C' => ON)
    # def DC_set(self, channels_keys, state_index):
    #     # DC on one of three channels
    #     freq_val = 1
    #     duty_val = 100
    #     if self.device.hb_set(channels_keys[state_index], freq_val, duty_val):
    #         print(channels_keys[state_index])
    #         print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(state_index+1))

    ####################################################################################################################
    # SET button clicked or ENTER pressed (state 'A-D' or 'B-E' or 'C-F' or 'other' => ON)
    # def AC_set(self, channels_keys, freq_val, duty_val, ph_shifts):
    #     channel_key = list(range(channels_keys[4])) # all three channels
    #     three_ch = 3
    #     if self.device.hb_set(channel_key, freq_val, duty_val, ph_shifts):
    #         print("[INFO] Set: {} Channels | {}Hz | {}% | {}° | {}° | {}°".format(three_ch, freq_val, duty_val,
    #                                                                               ph_shifts[0], ph_shifts[1], ph_shifts[2]))

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Moving mode => ON)
    def payload_set(self, channel_keys, freq_val, seq_freq_val):
        if self.device.hb_set(channel_keys, freq_val, seq_freq=seq_freq_val):
            print("[INFO] Mode 5 ON (3 Phases | freq.: {}Hz | seq. freq.: {}Hz)".format(freq_val, seq_freq_val))

    ####################################################################################################################
    # SET COMMAND
    def set_command(self):
        self.new_hv_val = float(self.target_voltage_edit.text())
        if self.new_hv_val == 0 and self.set_button.text() == "Set":
            print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else:
            self.voltage_set()
            self.payload_set(self.channels_keys, self.freq_val, self.seq_freq_val)
            self.lock_command(is_on=1)

            # if self.state_index == self.previous_index:
            #     self.voltage_set()
            # else:
            #     self.previous_index =  self.state_index
            #     self.voltage_set()
            #     if  self.state_index < 3:
            #         self.DC_set(self.channels_keys,  self.state_index)
            #     elif  self.state_index == 3:
            #         ph_shifts = [0, 180, 180]
            #         self.AC_set(self.channels_keys, self.freq_val, self.duty_val, ph_shifts) # phase shift set for A-D
            #     elif  self.state_index == 4:
            #         ph_shifts = [180, 0, 180]
            #         self.AC_set(self.channels_keys, self.freq_val, self.duty_val, ph_shifts) # phase shift set for B-E
            #     elif  self.state_index == 5:
            #         ph_shifts = [180, 180, 0]
            #         self.AC_set(self.channels_keys, self.freq_val, self.duty_val, ph_shifts) # phase shift set for C-F
            #     else:
            #         ph_shifts = [float(self.ch1_phase_shift_edit.text()), float(self.ch2_phase_shift_edit.text()), float(self.ch3_phase_shift_edit.text())]
            #         self.AC_set(self.channels_keys, self.freq_val,  self.duty_val, ph_shifts) # phase shift set for other
            #     self.lock_command(is_on=1)

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on):
        if is_on == 1:
            # self.st_comboBox.setDisabled(True)
            # if self.state_index >= 3:
            self.freq_edit.setDisabled(True)
            self.seq_freq_edit.setDisabled(True)
                # self.duty_cycle_edit.setDisabled(True)
                # if self.state_index == 6:
                #     self.ch1_phase_shift_edit.setDisabled(True)
                #     self.ch2_phase_shift_edit.setDisabled(True)
                #     self.ch3_phase_shift_edit.setDisabled(True)
            print("[INFO] Mode locked\n"
                  "------------------")
        else:
            # self.st_comboBox.setDisabled(False)
            # if self.state_index >= 3:
            self.freq_edit.setDisabled(False)
            self.seq_freq_edit.setDisabled(False)
                # self.duty_cycle_edit.setDisabled(False)
                # if self.state_index == 6:
                #     self.ch1_phase_shift_edit.setDisabled(False)
                #     self.ch2_phase_shift_edit.setDisabled(False)
                #     self.ch3_phase_shift_edit.setDisabled(False)
            print("[INFO] Mode unlocked\n"
                  "--------------------")

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self):
        self.voltage_reset()
        if self.device.hb_stop_shift():
                print("[INFO] Mode 5: Half-Bridges 1-3 OFF")
        # unlock the mode
        self.lock_command(is_on=0)

        # if self.state_index < 3:
        #     if self.device.hb_stop(self.channels_keys[self.state_index]):
        #         print("[INFO] Mode 1: Half-Bridge {} OFF".format(self.state_index+1))
        # else:
        #     if self.device.hb_stop_shift():
        #         print("[INFO] Mode 5: Half-Bridges 1-3 OFF")
        # # unlock the mode
        # self.lock_command(is_on=0)


