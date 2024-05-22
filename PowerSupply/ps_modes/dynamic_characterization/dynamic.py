# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGroupBox, QFormLayout, QLabel, QPushButton, QComboBox, QVBoxLayout, QLineEdit
# custom packages
from PowerSupply.ps_modes.dynamic_characterization.dynamic_ps import Dynamic_PS
from StandaTable.standa_table import StandaTableWidget

class DynamicMode(QWidget):
    def __init__(self, power_supply=None, force_sensor=None, actuator=None, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = power_supply
        self.force_sensor = force_sensor
        self.actuator = actuator
        # -------------------------------------------------------------------------------------------------------- #
        self.power_supply_control = Dynamic_PS(self.power_supply)
        self.actuator_control = StandaTableWidget(self.actuator)

    # ************************************************************************************************************ #
    #                                     DYNAMIC CHARACTERIZATION INTERFACE                                       #
    # ************************************************************************************************************ #

        mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type_layout = QFormLayout()
        experiment_type_label = QLabel("Type of Experiment:")
        self.experiment_type = QComboBox()
        experiments = ['Force vs. Speed', 'Force vs. Voltage and Speed', 'Force vs. Frequency and Speed']
        for experiment in experiments:
            self.experiment_type.addItem(experiment)
        experiment_type_layout.addRow(experiment_type_label, self.experiment_type)
        if self.power_supply is not None:
            self.experiment_type.currentIndexChanged.connect(self.experiment_type_changed)
        mode_layout.addLayout(experiment_type_layout)
        # -------------------------------------------------------------------------------------------------------- #

        # Force sensor "Tare" button.
        tare_btn = QPushButton("TARE FORCE")
        if self.force_sensor is not None:
            tare_btn.clicked.connect(self.force_sensor.tare) # Make it actually do something
        tare_btn.setStyleSheet("background-color: #ADD8E6; "
                                "color: black; "
                                "font-weight: bold; "
                                "font-size: 24px; "
                                "position: center; ")
        tare_btn.setFixedWidth(320)
        tare_btn.setFixedHeight(50)
        mode_layout.addWidget(tare_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        # -------------------------------------------------------------------------------------------------------- #

        # Actuator control panel.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(actuator_groupBox, alignment=Qt.AlignmentFlag.AlignCenter)

        self.actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        self.actuator_groupBox_layout.addRow(self.actuator_control)
        # -------------------------------------------------------------------------------------------------------- #

        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(power_supply_groupBox, alignment=Qt.AlignmentFlag.AlignCenter)

        self.power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        self.power_supply_groupBox_layout.addRow(self.power_supply_control)

        self.emg_stop_btn = QPushButton("EMERGENCY STOP")
        if self.power_supply is not None:
            self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
        self.emg_stop_btn.setStyleSheet("background-color: red; "
                                        "color: white; "
                                        "font-weight: bold; "
                                        "font-size: 24px; "
                                        "position: center; ")
                                        # "border: 1px solid black;")
        self.emg_stop_btn.setFixedHeight(50)        
        self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)

        power_supply_groupBox.setLayout(self.power_supply_groupBox_layout)
        # -------------------------------------------------------------------------------------------------------- #

        # Other parameters.
        parameters_groupBox = QGroupBox("Parameters")
        parameters_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(parameters_groupBox)

        motor_type_lbl = QLabel("Motor Type:")
        motor_type = QComboBox()
        motor_types = ['Motor Fiber', 'Motor Ribbon']
        for motor in motor_types:
            motor_type.addItem(motor)

        parameters_groupBox_layout = QFormLayout(parameters_groupBox)
        parameters_groupBox_layout.addRow(motor_type_lbl, motor_type)
        if motor_type.currentText == 'Motor Fiber':
            # ------------------------------------------------------------- #
            motor_length_lbl = QLabel("Fiber length:")
            motor_length = QLineEdit()
            parameters_groupBox_layout.addRow(motor_length_lbl, motor_length)
            # ------------------------------------------------------------- #
            motor_number_lbl = QLabel("Number of fibers:")
            motor_number = QLineEdit()
            parameters_groupBox_layout.addRow(motor_number_lbl, motor_number)
            # ------------------------------------------------------------- #
            insulator_lbl = QLabel("Insulator:")
            insulator = QLineEdit()
            parameters_groupBox_layout.addRow(insulator_lbl, insulator)

        elif motor_type.currentText == 'Motor Ribbon':
            # ------------------------------------------------------------- #
            stator_name_lbl = QLabel("Stator name:")
            stator_name = QLineEdit()
            parameters_groupBox_layout.addRow(stator_name_lbl, stator_name)
            # ------------------------------------------------------------- #
            slider_name_lbl = QLabel("Slider name:")
            slider_name = QLineEdit()
            parameters_groupBox_layout.addRow(slider_name_lbl, slider_name)
        mode_layout.addStretch(1)

    # ************************************************************************************************************ #
    def experiment_type_changed(self):
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Speed':
            self.power_supply_groupBox_layout.addRow(self.power_supply_control)
            self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)
        elif experiment_text == 'Force vs. Voltage and Speed':
            self.power_supply_groupBox_layout.addRow(self.power_supply_control)
            self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)
        # elif experiment_text == 'Force vs. Frequency and Position':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)
        # elif experiment_text == 'Max. Force vs. Voltage':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)
        # elif experiment_text == 'Max. Force vs. Frequency':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)

    # ************************************************************************************************************ #
    def emg_stop_btn_clicked(self):
        self.power_supply.emergency_stop()
