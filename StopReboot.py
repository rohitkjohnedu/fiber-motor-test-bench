########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       StopReboot.py
# @brief      Author:             MBE
#             Institute:          EPFL
#             Laboratory:         LMTS
#             Software version:   v1.09 (SYLVAIN/MARTIJN/MYKHAILO)
#             Created on:         11.03.2024
#             Last modifications: 11.03.2024
#
# Copyright 2021/2024 EPFL-LMTS
# All rights reserved.
# NO HELP WILL BE GIVEN IF YOU MODIFY THIS CODE !!!
########################################################################################################################

# python packages
from PyQt6.QtWidgets import *
# custom packages
from SerialSender import *


class StopReboot(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)

        self.ser = None
        # ************************************************************************************************************ #

        self.emg_stop_btn = QPushButton("STOP")
        self.emg_stop_btn.setStyleSheet("background-color: red; "
                                        "color: white; "
                                        "font-weight: bold; "
                                        'font-size: 24px;'
                                        "position: center; "
                                        "border: 1px solid black;")
        self.emg_stop_btn.setFixedWidth(680)
        self.emg_stop_btn.setFixedHeight(50)
        # ------------------------------------------------------------------------------------------------------------ #
        self.lay = QVBoxLayout(self)
        self.lay.addWidget(self.emg_stop_btn)
        # ------------------------------------------------------------------------------------------------------------ #
        # ACTIONS
    #     self.emg_stop_btn.clicked.connect(self.emg_stop_btn_clicked)

    # ####################################################################################################################
    # def attach_serial(self, serial):
    #     self.ser = serial

    # ####################################################################################################################
    # def emg_stop_btn_clicked(self):
    #     # send through the serial port
    #     to_send = "\r\nEStop\r\n"
    #     send_command(self.ser, to_send)
    #     # display information message
    #     print("[INFO] Emergency stop")
