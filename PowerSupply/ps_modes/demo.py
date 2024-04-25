
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout

# custom packages



class DemoMode(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.power_supply = PowerSupplyControl()
        # ------------------------------------------------------------------------------------------------------------ #

        mode_layout = QVBoxLayout()

        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(power_supply_groupBox, stretch=1)

        power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        power_supply_groupBox_layout.addRow(self.power_supply)
        power_supply_groupBox.setLayout(power_supply_groupBox_layout)

        # ------------------------------------------------------------------------------------------------------------ #


class PowerSupplyControl(QWidget):
    def __init__(self):
        QWidget.__init__(self, None)



    # ************************************************************************************************************ #
    #                                                  INTERFACE                                                   #
    # ************************************************************************************************************ #

        layout_main = QVBoxLayout()
        self.setLayout(layout_main)
        layout_main.setSpacing(3)

        layout_top = QHBoxLayout()
        layout_top.setSpacing(3)

        # Control panel is on the left side.
        layout_left = QVBoxLayout()
        layout_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_left.setSpacing(3)
        layout_top.addLayout(layout_left)

        # ------------------------------------------------------------------------------------------------------------ #

        #layout_main.addWidget(self.Mode3)

        # ------------------------------------------------------------------------------------------------------------ #
        # Add the top layout to the main layout.
        layout_main.addLayout(layout_top)
        
        # Layout of all widgets not plot.
        layout_left.addStretch(1)
        layout_main.addStretch(1)