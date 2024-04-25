
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout
# custom packages
from PowerSupply.ps_modes.ps_control_1 import PS_Control_1


class StaticMode(QWidget):
    def __init__(self, parent=None, ser=None):
        QWidget.__init__(self, parent=parent)

        self.serial=ser
        force_vs_position = 1
        # force_at_position_with_max_force = 1

        self.Force_vs_Position = Force_vs_Position(ser=self.serial)
        # self.Force_at_Position_with_maxForce = Force_at_Position_with_maxForce()

        # ------------------------------------------------------------------------------------------------------------ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type = QTabWidget()

        if force_vs_position == 1:
            experiment_type.addTab(self.Force_vs_Position, 'Force vs. Position')
        
        # if force_at_position_with_max_force == 1:
        #     experiment_type.addTab(self.Force_at_Position_with_maxForce, 'Force at position with max force')

        self.mode_layout.addWidget(experiment_type)

########################################################################################################################

class Force_vs_Position(QWidget):
    def __init__(self, parent=None, ser=None):
        QWidget.__init__(self, parent=parent)

        self.serial=ser
        self.power_supply = PowerSupplyControl(ser=self.serial)

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

########################################################################################################################

class PowerSupplyControl(QWidget):
    def __init__(self, parent=None, ser=None):
        QWidget.__init__(self, parent=parent)

        self.serial = ser
        self.ps_control = PS_Control_1()
        self.ps_control.attach_serial(serial=self.serial)

    # ************************************************************************************************************ #
    #                                     POWER SUPPLY CONTROL INTERFACE                                           #
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























# class Force_at_Position_with_maxForce(QWidget):
#     def __init__(self, parent=None):
#         QWidget.__init__(self, parent=parent)

#         board_1_port = 'COM3'
#         self.display_currents = 0
#         self.display_voltages = 1
#         self.debug_mode = 0
#         record_data = 0

#         self.power_supply = PowerSupply1(port_name=board_1_port,
#                                         currents_display=self.display_currents,
#                                         voltage_display=self.display_voltages,
#                                         debug_mode=self.debug_mode,
#                                         record_data=record_data)

#         experiment_layout = QVBoxLayout(self)

#         # Power supply control panel.
#         power_supply_groupBox = QGroupBox(self.power_supply.board_name)
#         power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
#         experiment_layout.addWidget(power_supply_groupBox, stretch=1)

#         power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
#         power_supply_groupBox_layout.addRow(self.power_supply)
#         power_supply_groupBox.setLayout(power_supply_groupBox_layout)

#         # ------------------------------------------------------------------------------------------------------------ #

#         # ACTUATOR (Motorized linear stage / Linear actuator control panel). Plan to make two tabs for the linear stage
#         # and the linear actuator.
#         actuator_groupBox = QGroupBox("Actuator")
#         actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
#         experiment_layout.addWidget(actuator_groupBox, stretch=1)

#         # Here will be a code for the actuator control panel.

########################################################################################################################
