
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QTabWidget
# custom packages
from PowerSupply.ps_modes.dynamic_characterization.dynamic_ps import Loop_PS

class DynamicMode(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        payload = 1

        self.loop_mode = Loop_Mode(device)

    # ************************************************************************************************************ #
    #                                     DYNAMIC CHARACTERIZATION INTERFACE                                       #
    # ************************************************************************************************************ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type = QTabWidget()

        if payload == 1:
            experiment_type.addTab(self.loop_mode, 'Loop mode')
        
        self.mode_layout.addWidget(experiment_type)


########################################################################################################################

class Loop_Mode(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = Loop_PS(device)

    # ************************************************************************************************************ #
    #                                          CONTROL PANEL INTERFACE                                             #
    # ************************************************************************************************************ #

        experiment_layout = QVBoxLayout(self)

        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        experiment_layout.addWidget(power_supply_groupBox, stretch=1)

        power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        power_supply_groupBox_layout.addRow(self.power_supply)
        power_supply_groupBox.setLayout(power_supply_groupBox_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel). Plan to make two tabs for the linear stage
        # and the linear actuator.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        experiment_layout.addWidget(actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.
