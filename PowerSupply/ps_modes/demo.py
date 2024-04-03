
# python packages
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout
import numpy as np
from serial import *
import sys
import time

# custom packages
from PowerSupply.ps_modes import *
from PowerSupply.options import *
from PowerSupply.StopReboot import *
from PowerSupply.Voltage import *


class DemoMode(QWidget):
    def __init__(self, parent=None, ser=None):
        QWidget.__init__(self, parent=parent)

        self.ser = ser

        # ------------------------------------------------------------------------------------------------------------ #

        self.mode_layout = QVBoxLayout(self)

        # Type of experiment.
        experiment_type = QTabWidget()

        self.mode_layout.addWidget(experiment_type)
