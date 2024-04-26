# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton


class Static_PS(QWidget):
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

        state_lbl = QLabel("State:")
        # state.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        target_voltage_edit = QLineEdit("0")
        target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        target_voltage_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.st_comboBox = QComboBox()
        states = ['A', 'B', 'C', 'A-D', 'B-E', 'C-F', 'Other']
        for state in states:
            self.st_comboBox.addItem(state)
        # self.st_comboBox.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        # The following widgets are used in "ACTIONS" section as a place holders, but then initialized in "EXTENDED SET"
        self.freq_edit = QLineEdit("1")
        self.duty_cycle_edit = QLineEdit("50")
        self.ch1_phase_shift_edit = QLineEdit("0")
        self.ch2_phase_shift_edit = QLineEdit("0")
        self.ch3_phase_shift_edit = QLineEdit("0")
        ## ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        # self.set_button.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, target_voltage_edit)
        self.mode_layout.addRow(state_lbl, self.st_comboBox)
        self.mode_layout.addRow(self.set_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        channels_keys = []
        num_states = self.st_comboBox.count()
        for index in range(1, num_states):
            channels_keys.append(int(pow(2, index-1)))
        state_index = self.st_comboBox.currentIndex()
        extended_flag = 0
        previous_index = -1
        # ------------------------------------------------------------------------------------------------------------ #
        new_hv_val = float(target_voltage_edit.text())
        freq_val = float(self.freq_edit.text())
        duty_val = float(self.duty_cycle_edit.text())
        ph_shift_1 = float(self.ch1_phase_shift_edit.text())
        ph_shift_2 = float(self.ch2_phase_shift_edit.text())
        ph_shift_3 = float(self.ch3_phase_shift_edit.text())
        ph_shifts = [ph_shift_1, ph_shift_2, ph_shift_3]
        # ------------------------------------------------------------------------------------------------------------ #
        parameters = [channels_keys, state_index, previous_index, new_hv_val]
        if state_index >= 3:
            parameters.append(freq_val, duty_val)
            if state_index == 6:
                parameters.append(ph_shifts)

        # ************************************************************************************************************ #
        # ACTIONS
        self.st_comboBox.currentIndexChanged.connect(self.extended_set(state_index, extended_flag)) # here is an error
        target_voltage_edit.returnPressed.connect(self.voltage_set(new_hv_val))
        self.set_button.clicked.connect(self.set_command(parameters))
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_edit.returnPressed.connect(self.AC_set)
        self.duty_cycle_edit.returnPressed.connect(self.AC_set)
        self.ch1_phase_shift_edit.returnPressed.connect(self.AC_set)
        self.ch2_phase_shift_edit.returnPressed.connect(self.AC_set)
        self.ch3_phase_shift_edit.returnPressed.connect(self.AC_set)

    ########################################################################################################################
    # ADD BUTTONS ALWAYS TO THE END OF THE LAYOUT
    def add_buttons(self):
        self.mode_layout.addRow(self.set_button)

    ########################################################################################################################
    # EXTENDED SET for states A-D, B-E, C-F, Other
    def extended_set(self, state_index, extended_flag):
        if state_index >= 3 and extended_flag == 0:
            # ------------------------------------------------------------------------------------------------------------ #
            self.freq_label = QLabel("Frequency (Hz):")
            # self.hb_freq_label.setFixedWidth(80)
            self.freq_edit = QLineEdit("1")
            self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.freq_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.freq_label, self.freq_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.duty_cycle_lbl = QLabel("Duty cycle (%):")
            # self.hb_duty_label.setFixedWidth(80)
            self.duty_cycle_edit = QLineEdit("50")
            self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.hb_pos_duty_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.duty_cycle_lbl, self.duty_cycle_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.ch1_phase_shift_lbl = QLabel("Phase shift (°), Ch. №1:")
            # self.hb_phase_shift_label.setFixedWidth(80)
            self.ch1_phase_shift_edit = QLineEdit("0")
            self.ch1_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.phase_shift_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.ch1_phase_shift_lbl, self.ch1_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.ch2_phase_shift_lbl = QLabel("Phase shift (°), Ch. №2:")
            # self.hb_phase_shift_label.setFixedWidth(80)
            self.ch2_phase_shift_edit = QLineEdit("0")
            self.ch2_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.phase_shift_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.ch2_phase_shift_lbl, self.ch2_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.ch3_phase_shift_lbl = QLabel("Phase shift (°), Ch. №3:")
            # self.hb_phase_shift_label.setFixedWidth(80)
            self.ch3_phase_shift_edit = QLineEdit("0")
            self.ch3_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            # self.phase_shift_edit.setFixedWidth(80)
            self.mode_layout.addRow(self.ch3_phase_shift_lbl, self.ch3_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            extended_flag = 1
        # **************************************************************************************************************** #
        elif state_index < 3 and extended_flag == 0:
            pass
        # **************************************************************************************************************** #
        elif state_index >= 3 and extended_flag == 1:
            pass
        # **************************************************************************************************************** #
        elif state_index < 3 and extended_flag == 1:
            self.mode_layout.removeRow(self.freq_edit)
            self.mode_layout.removeRow(self.duty_cycle_edit)
            self.mode_layout.removeRow(self.ch1_phase_shift_edit)
            self.mode_layout.removeRow(self.ch2_phase_shift_edit)
            self.mode_layout.removeRow(self.ch3_phase_shift_edit)
            extended_flag = 0
        # **************************************************************************************************************** #
        self.add_buttons() # add buttons to the end of the layout
        # **************************************************************************************************************** #
        
    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self):
        if self.set_button.text() =="Set":
            self.set_command()
            self.set_button.setText("Reset")
        else:
            self.reset_command()
            self.set_button.setText("Set")

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self, new_hv_val):
        if self.device.set_voltage(new_hv_val):
            print("[INFO] HV ON: {} V".format(new_hv_val))

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            print("[INFO] HV OFF")
            # unlock the mode
            self.lock_command(is_on=0)
            # reset the previous index
            self.previous_index = 0

    ####################################################################################################################
    # SET button clicked (state 'A' or 'B' or 'C' => ON)
    def DC_set(self, channels_keys, state_index):
        # DC on one of three channels
        freq_val = 0
        duty_val = 100
        if self.device.hb_set(channels_keys[state_index], freq_val, duty_val):
            print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(state_index+1))

    ####################################################################################################################
    # SET button clicked or ENTER pressed (state 'A-D' or 'B-E' or 'C-F' or 'other' => ON)
    def AC_set(self, channels_keys, freq_val, duty_val, ph_shifts):
        channel_key = channels_keys[2] # all three channels
        three_ch = 3
        if self.device.hb_set(channel_key, freq_val, duty_val, ph_shifts):
            print("[INFO] Set: {} Channels | {}Hz | {}% | {}° | {}° | {}°".format(three_ch, freq_val, duty_val,
                                                                                  ph_shifts[0], ph_shifts[1], ph_shifts[2]))

    ####################################################################################################################
    # SET COMMAND
    def set_command(self, channels_keys, state_index, previous_index, new_hv_val, freq_val, duty_val, ph_shifts):
        if state_index == previous_index:
            self.voltage_set(new_hv_val)
        else:
            previous_index = state_index
            self.voltage_set(new_hv_val)
            if state_index < 3:
                self.DC_set(channels_keys, state_index)
            elif state_index == 3:
                ph_shifts = [0, 180, 180]
                self.AC_set(channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for A-D
            elif state_index == 4:
                ph_shifts = [180, 0, 180]
                self.AC_set(channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for B-E
            elif state_index == 5:
                ph_shifts = [180, 180, 0]
                self.AC_set(channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for C-F
            else:
                self.AC_set(channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for other

            self.lock_command(is_on=1, state_index=state_index)

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on, state_index):
        if is_on == 1:
            self.st_comboBox.setDisabled(True)
            if state_index >= 3:
                self.freq_edit.setDisabled(True)
                self.duty_cycle_edit.setDisabled(True)
                self.ch1_phase_shift_edit.setDisabled(True)
                self.ch2_phase_shift_edit.setDisabled(True)
                self.ch3_phase_shift_edit.setDisabled(True)
            print("[INFO] Mode locked")
        else:
            self.st_comboBox.setDisabled(False)
            if state_index >= 3:
                self.freq_edit.setDisabled(False)
                self.duty_cycle_edit.setDisabled(False)
                self.ch1_phase_shift_edit.setDisabled(False)
                self.ch2_phase_shift_edit.setDisabled(False)
                self.ch3_phase_shift_edit.setDisabled(False)
            print("[INFO] Mode unlocked")
        

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self, channels_keys, state_index):
        self.voltage_reset()
        if state_index < 3:
            if self.device.hb_stop(channels_keys[state_index]):
                print("[INFO] Mode 1: Half-Bridge {} OFF".format(state_index+1))
        else:
            if self.device.hb_stop_shift():
                print("[INFO] Mode 5: Half-Bridges 1-3 OFF")


