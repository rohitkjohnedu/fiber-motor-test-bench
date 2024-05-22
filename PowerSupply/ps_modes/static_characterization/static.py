# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QGroupBox, QFormLayout, QPushButton, QComboBox, QLineEdit, QVBoxLayout
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS
from StandaTable.standa_table import StandaTableWidget


class StaticMode(QWidget):
    def __init__(self, power_supply=None, force_sensor=None, actuator=None, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = power_supply
        self.force_sensor = force_sensor
        self.actuator = actuator
        # -------------------------------------------------------------------------------------------------------- #
        self.power_supply_control = Static_PS(self.power_supply)
        self.actuator_control = StandaTableWidget(self.actuator)
        # -------------------------------------------------------------------------------------------------------- #

    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
    # ************************************************************************************************************ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type_layout = QFormLayout()
        experiment_type_label = QLabel("Type of Experiment:")
        self.experiment_type = QComboBox()
        experiments = ['Force vs. Position', 'Force vs. Voltage and Position', 'Force vs. Frequency and Position', 
                       'Max. Force vs. Voltage', 'Max. Force vs. Frequency']
        for experiment in experiments:
            self.experiment_type.addItem(experiment)
        experiment_type_layout.addRow(experiment_type_label, self.experiment_type)
        self.experiment_type.currentIndexChanged.connect(self.experiment_type_changed)
        self.mode_layout.addLayout(experiment_type_layout)
        # -------------------------------------------------------------------------------------------------------- #

        # Force sensor "Tare" button.
        tare_btn = QPushButton("TARE FORCE")
        if self.force_sensor is not None:
            tare_btn.clicked.connect(self.force_sensor.tare)
        tare_btn.setStyleSheet("background-color: #ADD8E6; "
                                "color: black; "
                                "font-weight: bold; "
                                "font-size: 24px; "
                                "position: center; ")
        tare_btn.setFixedHeight(50)
        tare_btn.setFixedWidth(320)
        self.mode_layout.addWidget(tare_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        # -------------------------------------------------------------------------------------------------------- #
        
        # Actuator control panel.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.mode_layout.addWidget(actuator_groupBox)

        actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        actuator_groupBox_layout.addRow(self.actuator_control)
        # -------------------------------------------------------------------------------------------------------- #

        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.mode_layout.addWidget(power_supply_groupBox)

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
        self.parameters_groupBox = QGroupBox("Parameters")
        self.parameters_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.mode_layout.addWidget(self.parameters_groupBox)

        motor_type_lbl = QLabel("Motor Type:")
        self.motor_type = QComboBox()
        motor_types = ['Motor Fiber', 'Motor Ribbon']
        for motor in motor_types:
            self.motor_type.addItem(motor)

        self.parameters_groupBox_layout = QFormLayout()
        self.parameters_groupBox_layout.addRow(motor_type_lbl, self.motor_type)
        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        self.motor_type.currentIndexChanged.connect(self.motor_type_changed)
        # ------------------------------------------------------------- #
        self.motor_length_lbl = QLabel("Fiber length (mm):")
        motor_length = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_length_lbl, motor_length)
        # ------------------------------------------------------------- #
        self.motor_number_lbl = QLabel("Number of fibers:")
        motor_number = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.motor_number_lbl, motor_number)
        # ------------------------------------------------------------- #
        self.insulator_lbl = QLabel("Insulator:")
        insulator = QLineEdit()
        self.parameters_groupBox_layout.addRow(self.insulator_lbl, insulator)
        # ------------------------------------------------------------- #
        self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)

        self.stator_name_lbl = QLabel("Stator name:")
        self.slider_name_lbl = QLabel("Slider name:")

        self.mode_layout.addStretch(1) 
    
    # ************************************************************************************************************ #
    def experiment_type_changed(self):
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Position':
            self.power_supply_groupBox_layout.addRow(self.power_supply_control)
            self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)
        elif experiment_text == 'Force vs. Voltage and Position':
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

    # ************************************************************************************************************ #
    def motor_type_changed(self):
        if self.motor_type.currentText() == 'Motor Fiber':
            self.parameters_groupBox_layout.removeRow(self.stator_name_lbl)
            self.parameters_groupBox_layout.removeRow(self.slider_name_lbl)
            # ------------------------------------------------------------- #
            self.motor_length_lbl = QLabel("Fiber length (mm):")
            motor_length = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_length_lbl, motor_length)
            # ------------------------------------------------------------- #
            self.motor_number_lbl = QLabel("Number of fibers:")
            motor_number = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.motor_number_lbl, motor_number)
            # ------------------------------------------------------------- #
            self.insulator_lbl = QLabel("Insulator:")
            insulator = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.insulator_lbl, insulator)
            # ------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)

        elif self.motor_type.currentText() == 'Motor Ribbon':
            self.parameters_groupBox_layout.removeRow(self.motor_length_lbl)
            self.parameters_groupBox_layout.removeRow(self.motor_number_lbl)
            self.parameters_groupBox_layout.removeRow(self.insulator_lbl)
            # ------------------------------------------------------------- #
            self.stator_name_lbl = QLabel("Stator name:")
            stator_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.stator_name_lbl, stator_name)
            # ------------------------------------------------------------- #
            self.slider_name_lbl = QLabel("Slider name:")
            slider_name = QLineEdit()
            self.parameters_groupBox_layout.addRow(self.slider_name_lbl, slider_name)
            # ------------------------------------------------------------- #
            self.parameters_groupBox.setLayout(self.parameters_groupBox_layout)
        self.mode_layout.addStretch(1)    



