# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QCheckBox, QHBoxLayout

class Static_PS(QWidget):
    def __init__(self, device=None, mode=None, exp_type=None, debug=0, parent=None):
        QWidget.__init__(self, parent=parent)

        # PS device
        self.device = device
        self.mode = mode
        self.exp_type = exp_type
        self.debug = debug

        # ************************************************************************************************************ #
        # INTERFACE ELEMENTS
        self.mode_layout = QFormLayout(self)
        # ------------------------------------------------------------------------------------------------------------ #
        target_voltage_lbl = QLabel("Voltage (V):")
        target_voltage_lbl.setFixedWidth(107)

        self.target_voltage_edit = QLineEdit("0")
        self.target_voltage_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # ------------------------------------------------------------------------------------------------------------ #
        if self.mode == "manual":
            state_lbl = QLabel("State:")
            # state_lbl.setFixedWidth(150)

            self.st_comboBox = QComboBox()
            states = ['A', 'B', 'C', 'D', 'E', 'F', 'A-D', 'B-E', 'C-F', 'Other']
            for state in states:
                self.st_comboBox.addItem(state)
        else:
            state_lbl = QLabel("Modulation:")
            state_lbl.setFixedWidth(175)

            self.state_opt = QCheckBox()
            self.state_opt.setText("ON")
            self.state_opt.setChecked(False)
            self.state_opt.setDisabled(True)
        # ------------------------------------------------------------------------------------------------------------ #
        # The following widgets are used in "ACTIONS" section as a place holders, but then initialized in "EXTENDED SET"
        self.freq_edit = QLineEdit("1")
        self.duty_cycle_edit = QLineEdit("50")
        self.ch1_phase_shift_edit = QLineEdit("0")
        self.ch2_phase_shift_edit = QLineEdit("0")
        self.ch3_phase_shift_edit = QLineEdit("0")
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_button = QPushButton("Set")
        self.set_button.setFixedWidth(150)

        self.update_button = QPushButton("Update")
        # ------------------------------------------------------------------------------------------------------------ #
        self.mode_layout.addRow(target_voltage_lbl, self.target_voltage_edit)
        if self.mode == "manual":
            self.mode_layout.addRow(state_lbl, self.st_comboBox)
            self.mode_layout.addRow(self.set_button, self.update_button)
        else:
            state_layout = QHBoxLayout()
            state_layout.addWidget(state_lbl)
            state_layout.addWidget(self.state_opt)
            self.mode_layout.addRow(state_layout)
            self.mode_layout.addRow(self.update_button)

        # ************************************************************************************************************ #
        # PARAMETERS
        self.channels_keys = []
        if self.mode == "manual": 
            num_states = self.st_comboBox.count() # 7
            for index in range(1, num_states+1): # 1-7
                self.channels_keys.append(index-1) # [0, 1, 2, 3, 4, 5, 6]
            self.state_index = self.st_comboBox.currentIndex()
        else:
            self.channels_keys = [0, 1, 2]

        self.extended_flag_1 = 0
        self.extended_flag_2 = 0

        # ************************************************************************************************************ #
        # ACTIONS
        if self.device is not None:
            self.target_voltage_edit.returnPressed.connect(self.set_command)
            self.update_button.clicked.connect(self.set_command)
            self.set_button.clicked.connect(self.set_pressed)
        if self.mode == "manual":
            self.st_comboBox.currentIndexChanged.connect(self.extended_set)

    ########################################################################################################################
    # ADD BUTTONS ALWAYS TO THE END OF THE LAYOUT
    def add_buttons(self):
        if self.mode == "manual":
            self.mode_layout.addRow(self.set_button, self.update_button)
        else:
            self.mode_layout.addRow(self.update_button)

    ########################################################################################################################
    # EXTENDED SET for states A-D, B-E, C-F, Other
    def extended_set(self):
        self.state_index = self.st_comboBox.currentIndex()
        # **************************************************************************************************************** #    
        if self.extended_flag_1 == 0 and self.state_index >= 6:
            freq_label = QLabel("Modulation frequency (Hz):")
            freq_label.setFixedWidth(150)
            self.freq_edit = QLineEdit("1")
            self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.mode_layout.addRow(freq_label, self.freq_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.extended_flag_1 = 1
        # **************************************************************************************************************** # 
        if self.extended_flag_1 == 1 and self.state_index == 9 and self.extended_flag_2 == 0:
            duty_cycle_lbl = QLabel("Modulation duty cycle (%):")
            duty_cycle_lbl.setFixedWidth(150)
            self.duty_cycle_edit = QLineEdit("50")
            self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.mode_layout.addRow(duty_cycle_lbl, self.duty_cycle_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            ch1_phase_shift_lbl = QLabel("Phase shift (°), Ch. №1:")
            ch1_phase_shift_lbl.setFixedWidth(150)
            self.ch1_phase_shift_edit = QLineEdit("0")
            self.ch1_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.mode_layout.addRow(ch1_phase_shift_lbl, self.ch1_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            ch2_phase_shift_lbl = QLabel("Phase shift (°), Ch. №2:")
            ch2_phase_shift_lbl.setFixedWidth(150)
            self.ch2_phase_shift_edit = QLineEdit("0")
            self.ch2_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.mode_layout.addRow(ch2_phase_shift_lbl, self.ch2_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            ch3_phase_shift_lbl = QLabel("Phase shift (°), Ch. №3:")
            ch3_phase_shift_lbl.setFixedWidth(150)
            self.ch3_phase_shift_edit = QLineEdit("0")
            self.ch3_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.mode_layout.addRow(ch3_phase_shift_lbl, self.ch3_phase_shift_edit)
            # ------------------------------------------------------------------------------------------------------------ #
            self.extended_flag_2 = 1
        # **************************************************************************************************************** # 
        if self.extended_flag_1 == 1 and self.state_index < 6:
            self.mode_layout.removeRow(self.freq_edit)
            self.extended_flag_1 = 0
        # **************************************************************************************************************** # 
        if self.extended_flag_2 == 1 and self.state_index < 9:
            self.mode_layout.removeRow(self.duty_cycle_edit)
            self.mode_layout.removeRow(self.ch1_phase_shift_edit)
            self.mode_layout.removeRow(self.ch2_phase_shift_edit)
            self.mode_layout.removeRow(self.ch3_phase_shift_edit)
            self.extended_flag_2 = 0
        # **************************************************************************************************************** # 
        self.add_buttons() # add buttons to the end of the layout
        # **************************************************************************************************************** #
        # ACTIONS
        if self.state_index > 5:
            self.freq_edit.returnPressed.connect(self.set_command)
            if self.state_index == 9:
                self.duty_cycle_edit.returnPressed.connect(self.set_command)
                self.ch1_phase_shift_edit.returnPressed.connect(self.set_command)
                self.ch2_phase_shift_edit.returnPressed.connect(self.set_command)
                self.ch3_phase_shift_edit.returnPressed.connect(self.set_command)

    ####################################################################################################################
    # SET BUTTON CLICKED
    def set_pressed(self, state=None):
        new_hv_val = float(self.target_voltage_edit.text())
        if new_hv_val == 0 and self.set_button.text() == "Set":
            zero_volt = QMessageBox.warning(self, "Zero voltage", "Please, set the voltage value")
            if self.debug == 1:
                print("\n[INFO] Please, set the voltage value\n------------------------------------")
            return
        else:
            if self.mode == "manual":
                if self.set_button.text() =="Set":
                    self.set_command(state)
            elif self.mode == "auto":
                self.set_command(state)
            else:
                self.reset_command()

    ####################################################################################################################
    # SET button clicked or ENTER pressed (Votlage => ON)
    def voltage_set(self):
        new_hv_val = float(self.target_voltage_edit.text())
        if new_hv_val == 0:
            self.reset_command()
        else:
            if self.device.set_voltage(new_hv_val) is True:
                if self.debug == 1:
                    print("\n[INFO] HV ON: {} V\n----------------------".format(new_hv_val))
                if self.set_button.text() == "Set":
                    self.set_button.setText("Reset")
                return True

    ####################################################################################################################
    # RESET button clicked or 0 voltage SET (Votlage => OFF)
    def voltage_reset(self):
        if self.device.voltage_stop():
            if self.debug == 1:
                print("\n[INFO] HV OFF\n------------------")

    ####################################################################################################################
    # SET button clicked (state 'A' or 'B' or 'C' => ON)
    def DC_set(self, channels_keys, state_index):
        # DC on one of three channels
        freq_val = 1
        duty_val = 100
        first_ch = 0
        second_ch = 1
        third_ch = 2
        if state_index < 3:
            if self.device.hb_set(channels_keys[state_index], freq_val, duty_val):
                if self.debug == 1:
                    print("[INFO] Mode 1: Half-Bridge {} ON (NO SWITCH)".format(state_index+1))
        else:
            if state_index == 3:
                if self.device.hb_set(second_ch, freq_val, duty_val) and self.device.hb_set(third_ch, freq_val, duty_val):
                    if self.debug == 1:
                        print("[INFO] Mode 1: Half-Bridges 2-3 ON (NO SWITCH)")
            elif state_index == 4:
                if self.device.hb_set(first_ch, freq_val, duty_val) and self.device.hb_set(third_ch, freq_val, duty_val):
                    if self.debug == 1:
                        print("[INFO] Mode 1: Half-Bridges 1-3 ON (NO SWITCH)")
            elif state_index == 5:
                if self.device.hb_set(first_ch, freq_val, duty_val) and self.device.hb_set(second_ch, freq_val, duty_val):
                    if self.debug == 1:
                        print("[INFO] Mode 1: Half-Bridges 1-2 ON (NO SWITCH)")

    ####################################################################################################################
    # SET button clicked or ENTER pressed (state 'A-D' or 'B-E' or 'C-F' or 'other' => ON)
    def AC_set(self, channels_keys, freq_val, duty_val, ph_shifts):
        channel_key = list(range(channels_keys[3])) # all three channels [0, 1, 2]
        three_ch = 3
        if self.device.hb_set(channel_key, freq_val, duty_val, ph_shifts=ph_shifts):
            if self.debug == 1:
                print("[INFO] Set: {} Channels | {}Hz | {}% | {}° | {}° | {}°".format(three_ch, freq_val, duty_val,
                                                                            ph_shifts[0], ph_shifts[1], ph_shifts[2]))

    ####################################################################################################################
    # SET COMMAND
    def set_command(self, state=None):
        new_hv_val = float(self.target_voltage_edit.text())
        if self.mode == "manual":
            if self.debug == 1:
                print("manual")
            if self.st_comboBox is not None:
                state_index = self.st_comboBox.currentIndex()
        else:
            if state == "A":
                state_index = 0
            elif state == "B":
                state_index = 1
            elif state == "C":
                state_index = 2

        if new_hv_val == 0 and self.set_button.text() == "Set":
            zero_volt = QMessageBox.warning(self, "Zero voltage", "Please, set the voltage value")
            if self.debug == 1:
                print("\n[INFO] Please, set the voltage value"
                      "\n------------------------------------")
        else: 
            if self.voltage_set() is True:
                if self.mode == "manual":
                    if self.state_index >= 5:
                        freq_val = float(self.freq_edit.text())
                        duty_val = 50 #%
                        if self.state_index == 9:
                            duty_val = float(self.duty_cycle_edit.text())
                            ch1_phase_shift = float(self.ch1_phase_shift_edit.text())
                            ch2_phase_shift = float(self.ch2_phase_shift_edit.text())
                            ch3_phase_shift = float(self.ch3_phase_shift_edit.text())
                
                    if  state_index < 6:
                        self.DC_set(self.channels_keys, state_index)
                    elif  state_index == 6:
                        ph_shifts = [0, 180, 180]
                        self.AC_set(self.channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for A-D
                    elif  state_index == 7:
                        ph_shifts = [180, 0, 180]
                        self.AC_set(self.channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for B-E
                    elif  state_index == 8:
                        ph_shifts = [180, 180, 0]
                        self.AC_set(self.channels_keys, freq_val, duty_val, ph_shifts) # phase shift set for C-F
                    else:
                        ph_shifts = [ch1_phase_shift, ch2_phase_shift, ch3_phase_shift]
                        self.AC_set(self.channels_keys, freq_val,  duty_val, ph_shifts) # phase shift set for other
                    self.lock_command(is_on=1)
                else:
                    if self.state_opt.isChecked() == False:
                        self.DC_set(self.channels_keys, state_index)


    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, is_on):
        if is_on == 1:
            self.st_comboBox.setDisabled(True)
            if self.debug == 1:
                print("[INFO] Mode locked\n"
                    "------------------")
        else:
            self.st_comboBox.setDisabled(False)
            if self.debug == 1:
                print("[INFO] Mode unlocked\n"
                    "--------------------")

    ####################################################################################################################
    # RESET COMMAND
    def reset_command(self):
        self.set_button.setText("Set")
        self.target_voltage_edit.setText("0")
        self.voltage_reset()
        if self.state_index < 6:
            if self.device.hb_stop(self.channels_keys[self.state_index]):
                if self.debug == 1:
                    print("[INFO] Mode 1: Half-Bridge {} OFF".format(self.state_index+1))
        else:
            if self.device.hb_stop_shift():
                if self.debug == 1:  
                    print("[INFO] Mode 5: Half-Bridges 1-3 OFF")
        # unlock the mode
        self.lock_command(is_on=0)

    ####################################################################################################################
    # EMERGENCY STOP
    def emergency_stop(self, device):
        device.emergency_stop()
        if self.set_button.text() == "Reset":
            self.reset_command()
            self.set_button.setText("Set")
            self.target_voltage_edit.setText("0")
        if self.debug == 1:
            print("[INFO] Emergency stop\n"
                "---------------------")


