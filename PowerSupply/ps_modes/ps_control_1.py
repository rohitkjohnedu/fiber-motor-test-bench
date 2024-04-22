# python packages
from PyQt6.QtCore import Qt, QEasingCurve
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QLineEdit, QPushButton
# custom packages
from PowerSupply.py_toggle import PyToggle


class PS_Control_1(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.hb_ser = None

        self.f_max = 200
        self.f_min = 0.01

        mode_layout = QFormLayout(self)

        # ************************************************************************************************************ #
        # TITLES ROW (only labels)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch_number_label = QLabel("Channels number:")
        # self.hb_number_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_label = QLabel("Frequency (Hz):")
        # self.hb_freq_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.duty_label = QLabel("Duty cycle (%):")
        # self.hb_duty_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.first_set_label = QLabel("First Set:")
        # self.hb_on_off_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch1_phase_shift_label = QLabel("Phase shift ch1(°):")
        # self.hb_phase_shift_label.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch2_phase_shift_label = QLabel("Phase shift ch2(°):")
        # self.hb_phase_shift_label.setFixedWidth(80)   
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch3_phase_shift_label = QLabel("Phase shift ch3(°):")
        # self.hb_phase_shift_label.setFixedWidth(80)   
        # ------------------------------------------------------------------------------------------------------------ #
        self.second_set_label = QLabel("Second Set:")
        # self.hb_on_off_label.setFixedWidth(80)   

        # ************************************************************************************************************ #
        # PARAMETERS LINE (LineEdit + ComboBox + QPushButton)
        self.ch_comboBox = QComboBox()
        self.ch_comboBox.addItem('1')
        self.ch_comboBox.addItem('2')
        self.ch_comboBox.addItem('3')
        # self.ch_comboBox.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.freq_edit = QLineEdit("1")
        # self.freq_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.freq_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.duty_cycle_edit = QLineEdit("50")
        self.duty_cycle_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.hb_pos_duty_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_toggle_1 = PyToggle(animation_curve=QEasingCurve.Type.InOutQuint)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch1_phase_shift_edit = QLineEdit("0")
        self.ch1_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.phase_shift_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch2_phase_shift_edit = QLineEdit("0")
        self.ch2_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.phase_shift_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.ch3_phase_shift_edit = QLineEdit("0")
        self.ch3_phase_shift_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        # self.phase_shift_edit.setFixedWidth(80)
        # ------------------------------------------------------------------------------------------------------------ #
        self.set_toggle_2 = PyToggle(animation_curve=QEasingCurve.Type.InOutQuint)
        # ------------------------------------------------------------------------------------------------------------ #
        self.start_button = QPushButton("Start")
        # self.hb_start_button.setFixedWidth(80)
        self.stop_button = QPushButton("Stop")
        # self.hb_stop_button.setFixedWidth(80)
        # ************************************************************************************************************ #
        mode_layout.addRow(self.ch_number_label, self.ch_comboBox)
        mode_layout.addRow(self.freq_label, self.freq_edit)
        mode_layout.addRow(self.duty_label, self.duty_cycle_edit)
        mode_layout.addRow(self.first_set_label, self.set_toggle_1)
        mode_layout.addRow(self.ch1_phase_shift_label, self.ch1_phase_shift_edit)
        mode_layout.addRow(self.ch2_phase_shift_label, self.ch2_phase_shift_edit)
        mode_layout.addRow(self.ch3_phase_shift_label, self.ch3_phase_shift_edit)
        mode_layout.addRow(self.second_set_label, self.set_toggle_2)
        mode_layout.addRow(self.start_button, self.stop_button)
        # ************************************************************************************************************ #
        # ACTIONS
        self.freq_edit.returnPressed.connect(self.first_set)
        self.duty_cycle_edit.returnPressed.connect(self.first_set)
        self.set_toggle_1.stateChanged.connect(self.hb_toggled)

        self.ch1_phase_shift_edit.returnPressed.connect(self.second_set)
        self.ch2_phase_shift_edit.returnPressed.connect(self.second_set)
        self.ch3_phase_shift_edit.returnPressed.connect(self.second_set)
        self.set_toggle_2.stateChanged.connect(self.hb_toggled)

        self.start_button.clicked.connect(self.start_command)
        self.stop_button.clicked.connect(self.stop_command)
        # ************************************************************************************************************ #

    ####################################################################################################################
    # ATTACH SERIAL
    def attach_serial(self, serial):
        self.hb_ser = serial

    ####################################################################################################################
    # SEND COMMAND
    def send_command(self, ser, command):
        to_send = bytearray(command, encoding="utf-8")
        ser.write(to_send)

    ####################################################################################################################
    # CHECKBOX TOGGLED
    def hb_toggled(self):
        if self.set_toggle_1.isChecked() == 1:
            self.first_set()
        elif self.set_toggle_1.isChecked() == 1 and self.set_toggle_2.isChecked() == 1:
            self.second_set()
        else:
            self.stop_command()

    ####################################################################################################################
    # TOGGLE CLICKED = SET STATE
    def first_set(self):
        try:
            channel_val = 0
            hb_val = int(self.ch_comboBox.currentIndex())+1
            for exponent in range(hb_val):
                channel_val += pow(2, exponent)
            freq_val = float(self.freq_edit.text())
            duty_val = float(self.duty_cycle_edit.text())
            # phase_shift_val = float(self.phase_shift_edit.text())
            # check frequency/duty cycle value
            pos_pulse_width = float(10*(duty_val/freq_val))
            if pos_pulse_width < 2:
                self.stop_command()
                print("[ERR] Positive pulse width: {} ms < 2 ms".format(pos_pulse_width))
            else:
                # check frequency value
                if (freq_val >= self.f_min) and (freq_val <= self.f_max):
                    # change the state of toggle
                    self.first_toggle_on()
                    # send through the serial port
                    to_send = "\r\nSMx 5 1 {} {} {} \r\n".format(channel_val, freq_val, duty_val)
                    self.send_command(self.hb_ser, to_send)
                    # display information message
                    print("[INFO] Set: {} Channels | {}Hz | {}%".format(channel_val, freq_val, duty_val))
                else:
                    self.stop_command()
        except Exception as err_fb_freq_edit:
            # display error message
            print("[ERR] FB FREQ VAL: {} - {}".format(self.freq_edit.text(), err_fb_freq_edit))
        return

    ####################################################################################################################
    # SECOND TOGGLE CLICKED = SET STATE
    def second_set(self):
        ch1_phase_shift_val = float(self.ch1_phase_shift_edit.text())
        ch2_phase_shift_val = float(self.ch2_phase_shift_edit.text())
        ch3_phase_shift_val = float(self.ch3_phase_shift_edit.text())
        # change the state of toggle
        self.second_toggle_on()
        # send through the serial port
        to_send = "\r\nSMx 5 2 {} {} {} \r\n".format(ch1_phase_shift_val, ch2_phase_shift_val,
                                                     ch3_phase_shift_val)
        self.send_command(self.hb_ser, to_send)
        # display information message
        print("[INFO] Set phase shift | ch1: {}° | ch2: {}° | ch3: {}°".format(ch1_phase_shift_val,
                                                                               ch2_phase_shift_val,
                                                                               ch3_phase_shift_val)) 
    
    ####################################################################################################################
    # START COMMAND
    def start_command(self):
        # lock the mode
        self.lock_command(state=1)
        # send through the serial port
        to_send = "\r\nSMx 5 0\r\n"
        self.send_command(self.hb_ser, to_send)
        # display information message
        print("[INFO] Mode ON")

    ####################################################################################################################
    # LOCK COMMAND
    def lock_command(self, state):
        if state == 1:
            self.ch_comboBox.setDisabled(True)
            self.freq_edit.setDisabled(True)
            self.duty_cycle_edit.setDisabled(True)
            self.set_toggle_1.setDisabled(True)
            self.ch1_phase_shift_edit.setDisabled(True)
            self.ch2_phase_shift_edit.setDisabled(True)
            self.ch3_phase_shift_edit.setDisabled(True)
            self.set_toggle_2.setDisabled(True)
        else:
            self.ch_comboBox.setDisabled(False)
            self.freq_edit.setDisabled(False)
            self.duty_cycle_edit.setDisabled(False)
            self.set_toggle_1.setDisabled(False)
            self.ch1_phase_shift_edit.setDisabled(False)
            self.ch2_phase_shift_edit.setDisabled(False)
            self.ch3_phase_shift_edit.setDisabled(False)
            self.set_toggle_2.setDisabled(False)
        # display information message
        print("[INFO] Mode locked")

    ####################################################################################################################
    # TOGGLE NOT CLICKED = STOP STATE
    def stop_command(self):
        # unlock the mode
        self.lock_command(state=0)
        # change the state of toggle
        self.hb_toggle_off()
        # send through the serial port
        to_send = "\r\nCMx 5 0\r\n"
        self.send_command(self.hb_ser, to_send)
        # display information message
        print("[INFO] Mode OFF")

    ####################################################################################################################
    def first_toggle_on(self):
        self.set_toggle_1.setChecked(True)
        self.set_toggle_1.start_transition(1)

    def second_toggle_on(self):
        self.set_toggle_2.setChecked(True)
        self.set_toggle_2.start_transition(1)

    ####################################################################################################################
    def hb_toggle_off(self):
        self.set_toggle_1.setChecked(False)
        self.set_toggle_1.start_transition(0)
        self.set_toggle_2.setChecked(False)
        self.set_toggle_2.start_transition(0)
