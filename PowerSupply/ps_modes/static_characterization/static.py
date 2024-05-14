# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QLabel, QGroupBox, QFormLayout, QPushButton, QComboBox 
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS
from StandaTable.standa_table import StandaTableWidget


class StaticMode(QWidget):
    def __init__(self, power_supply, actuator, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = power_supply
        self.actuator = actuator
        self.power_supply = Static_PS(self.power_supply)
        self.actuator_widget = StandaTableWidget(self.actuator)

    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
    # ************************************************************************************************************ #

        mode_layout = QFormLayout(self)

        # Type of experiment.
        experiment_type_label = QLabel("Type of Experiment:")
        self.experiment_type = QComboBox()
        experiments = ['Force vs. Position', 'Force vs. Voltage and Position', 'Force vs. Frequency and Position', 
                       'Max. Force vs. Voltage', 'Max. Force vs. Frequency']
        for experiment in experiments:
            self.experiment_type.addItem(experiment)
        mode_layout.addRow(experiment_type_label, self.experiment_type)
        self.experiment_type.currentIndexChanged.connect(self.experiment_type_changed)
        # -------------------------------------------------------------------------------------------------------- #
        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addRow(power_supply_groupBox)

        self.power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        self.power_supply_groupBox_layout.addRow(self.power_supply)

        self.emg_stop_btn = QPushButton("EMERGENCY STOP")
        self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
        self.emg_stop_btn.setStyleSheet("background-color: red; "
                                        "color: white; "
                                        "font-weight: bold; "
                                        'font-size: 24px;'
                                        "position: center; "
                                        "border: 1px solid black;")
        self.emg_stop_btn.setFixedWidth(300)
        self.emg_stop_btn.setFixedHeight(50)        
        self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)

        power_supply_groupBox.setLayout(self.power_supply_groupBox_layout)
        # -------------------------------------------------------------------------------------------------------- #
        # Actuator control panel.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addRow(actuator_groupBox)

        self.actuator_groupBox_layout = QFormLayout(actuator_groupBox)
        self.actuator_groupBox_layout.addRow(self.actuator_widget)
    
    # ************************************************************************************************************ #
    def experiment_type_changed(self):
        experiment_text = self.experiment_type.currentText()
        if experiment_text == 'Force vs. Position':
            self.power_supply_groupBox_layout.addRow(self.power_supply)
            self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)
        elif experiment_text == 'Force vs. Voltage and Position':
            self.power_supply_groupBox_layout.addRow(self.power_supply)
            self.power_supply_groupBox_layout.addRow(self.emg_stop_btn)
        # elif experiment_text == 'Force vs. Frequency and Position':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)
        # elif experiment_text == 'Max. Force vs. Voltage':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)
        # elif experiment_text == 'Max. Force vs. Frequency':
        #     self.power_supply_groupBox_layout.addRow(self.power_supply)

    # ************************************************************************************************************ #
    def emg_stop_btn_clicked(self):
        self.power_supply.emergency_stop(device=self.power_supply)



