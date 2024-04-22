
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout
import numpy as np
from serial import *
import sys
import time

# custom packages
from PowerSupply.ps_modes.old_modes import *
#from PowerSupply.options import *
from PowerSupply.StopReboot import *
from PowerSupply.Voltage import *


class DynamicMode(QWidget):
    def __init__(self, parent=None, ser=None):
        QWidget.__init__(self, parent=parent)

        self.ser = ser
        self.power_supply = PowerSupplyControl(ser=self.ser)
        # ------------------------------------------------------------------------------------------------------------ #

        mode_layout = QVBoxLayout(self)

        # Power supply control panel.
        power_supply_groupBox = QGroupBox("Power Supply")
        power_supply_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(power_supply_groupBox, stretch=1)

        power_supply_groupBox_layout = QFormLayout(power_supply_groupBox)
        power_supply_groupBox_layout.addRow(self.power_supply)
        power_supply_groupBox.setLayout(power_supply_groupBox_layout)

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel). Plan to make two tabs for the linear stage
        # and the linear actuator.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        mode_layout.addWidget(actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.

        # ------------------------------------------------------------------------------------------------------------ #


class PowerSupplyControl(QWidget):
    def __init__(self, ser=None):
        QWidget.__init__(self,None)

        self.ser = ser

        # MODULES
        self.em_stop = StopReboot()
        self.voltage = Voltage()
        #self.Mode3 = Mode3()

        # ------------------------------------------------------------------------------------------------------- #
        # Connect widgets to the serial port.

        self.em_stop.attach_serial(serial=self.ser)
        self.voltage.attach_serial(serial=self.ser)

        # if MODE3 == 1:
        #     self.Mode3.attach_serial(serial=self.ser)

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

        layout_main.addWidget(self.em_stop)
        layout_main.addWidget(self.voltage)
        #layout_main.addWidget(self.Mode3)

        # ------------------------------------------------------------------------------------------------------------ #
        
        # tab = QTabWidget(self)
        # tab.setFixedWidth(700)

        # if MODE1 == 1:
        #     tab.addTab(self.Mode1, 'Mode 1')

        # if MODE2 == 1:
        #     tab.addTab(self.Mode2, 'Mode 2')

        # if MODE3 == 1:
        #     tab.addTab(self.Mode3, 'Mode 3')

        # if MODE4 == 1:
        #     tab.addTab(self.Mode4, 'Mode 4')

        # if OLD_MODE5 == 1:
        #     tab.addTab(self.OldMode5, 'Mode Go and Back')

        # if MODE5 == 1:
        #     tab.addTab(self.Mode5, 'Mode 5')

        # layout_left.addWidget(tab)

        # ------------------------------------------------------------------------------------------------------------ #
        # Add the top layout to the main layout.
        layout_main.addLayout(layout_top)
        
        # Layout of all widgets not plot.
        layout_left.addStretch(1)
        layout_main.addStretch(1)
