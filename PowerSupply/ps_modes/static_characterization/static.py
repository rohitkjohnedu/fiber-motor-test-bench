
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QGroupBox, QFormLayout, QPushButton
# custom packages
from PowerSupply.ps_modes.static_characterization.static_ps import Static_PS


class StaticMode(QWidget):
    def __init__(self, device, parent=None):
        QWidget.__init__(self, parent=parent)

        self.device = device
        self.power_supply = Static_PS(device)

        force_vs_position = 1
        # force_at_position_with_max_force = 1

        self.Force_vs_Position = Force_vs_Position(self.power_supply )
        
        # self.Force_at_Position_with_maxForce = Force_at_Position_with_maxForce()

    # ************************************************************************************************************ #
    #                                     STATIC CHARACTERIZATION INTERFACE                                        #
    # ************************************************************************************************************ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type = QTabWidget()

        if force_vs_position == 1:
            experiment_type.addTab(self.Force_vs_Position, 'Force vs. Position')
        # if force_at_position_with_max_force == 1:
        #     experiment_type.addTab(self.Force_at_Position_with_maxForce, 'Force at position with max force')
        self.mode_layout.addWidget(experiment_type)

        emg_stop_btn = QPushButton("EMERGENCY STOP")
        emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)
        emg_stop_btn.setStyleSheet("background-color: red; "
                                        "color: white; "
                                        "font-weight: bold; "
                                        'font-size: 24px;'
                                        "position: center; "
                                        "border: 1px solid black;")
        emg_stop_btn.setFixedWidth(300)
        emg_stop_btn.setFixedHeight(50)        
        self.mode_layout.addWidget(emg_stop_btn, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def emg_stop_btn_clicked(self):
        self.power_supply.emergency_stop(device=self.device)

########################################################################################################################

class Force_vs_Position(QWidget):
    def __init__(self, power_supply, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = power_supply

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

