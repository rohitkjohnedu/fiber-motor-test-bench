
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QTabWidget
# custom packages
from PowerSupply.ps_modes.dynamic_ps import Dynamic_PS

class DynamicMode(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        payload = 1

        self.payload_mode = Payload_Mode(device)

    # ************************************************************************************************************ #
    #                                     DYNAMIC CHARACTERIZATION INTERFACE                                       #
    # ************************************************************************************************************ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type = QTabWidget()

        if payload == 1:
            experiment_type.addTab(self.payload_mode, 'Payload mode')
        
        self.mode_layout.addWidget(experiment_type)


########################################################################################################################

class Payload_Mode(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = PowerSupplyControl(device)

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


########################################################################################################################

class PowerSupplyControl(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        self.ps_control = Dynamic_PS(device)

    # ************************************************************************************************************ #
    #                                    1) POWER SUPPLY CONTROL INTERFACE                                         #
    # ************************************************************************************************************ #

        layout_main = QVBoxLayout()
        self.setLayout(layout_main)
        layout_main.setSpacing(0)

        layout_top = QHBoxLayout()
        layout_top.setSpacing(0)

        # Control panel is on the left side.
        layout_left = QVBoxLayout()
        layout_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_left.setSpacing(0)
        layout_top.addLayout(layout_left)

        # ------------------------------------------------------------------------------------------------------------ #
        
        layout_left.addWidget(self.ps_control)

        # ------------------------------------------------------------------------------------------------------------ #
        # Add the top layout to the main layout.
        layout_main.addLayout(layout_top)
        
        # Layout of all widgets not plot.
        layout_left.addStretch(1)
        layout_main.addStretch(1)