########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       main.py
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

import os
import sys
#add path to source
# print(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# custom packages
from ComSelect import *
from PowerSupply import *
from Userdef import *
from Instruments.futek import FutekSensor, FutekSensorWidget


class PowerSupplyInterface(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        self.init_ui()


    # **************************************************************************************************************** #
    #                                           UNITIALIZATION OF THE INTERFACE
    # **************************************************************************************************************** #
    def init_ui(self):
        self.main_layout = QHBoxLayout(self)

        self.debug_mode = 0 #dialog.get_debug_mode_results()
        # ------------------------------------------------------------------------------------------------------------ #
        # RECEIVED DATA
        display_cmd = 0 #dialog.get_rvc_data_results()
        # ------------------------------------------------------------------------------------------------------------ #
        # RECORD DATA
        record_data = 0 #dialog.get_record_data_results()
        # ------------------------------------------------------------------------------------------------------------ #
        # VOLTAGES PLOTS
        display_currents = 3 #dialog.get_currents_display_results()     To show currents in separate plots.
        # ------------------------------------------------------------------------------------------------------------ #
        # CURRENTS PLOTS
        display_voltages = 1 #dialog.get_voltages_display_results()     To show high voltage.
        # ------------------------------------------------------------------------------------------------------------ #
        # Estimation of data rate transmission used for nice beginning of plot and not totally inaccurate time basis on
        # plots
        if display_currents == 0:
            self.time = 5    # 5
            self.estimateRate = 1
        if display_currents == 1:
            self.time = 5    # 5
            self.estimateRate = 0.01
        if display_currents == 2:
            self.time = 5
            self.estimateRate = 0.01
        if display_currents == 3:
            self.time = 1
            self.estimateRate = 0.005
        # ------------------------------------------------------------------------------------------------------------ #
        self.number_board = 1 #dialog.get_number_boards_used()      Privilege the use of one board for the moment.

        # BOARD #1
        board_1_port = None #dialog.get_board_1_port_results()
        self.board_1 = PowerSupply(port_name=board_1_port,
                                        estimate_rate=self.estimateRate,
                                        currents_display=display_currents,
                                        voltage_display=display_voltages,
                                        debug_mode=self.debug_mode,
                                        rcv_data=display_cmd,
                                        record_data=record_data)
        
        # ************************************************************************************************************ #

        self.setupControlPanel()
        self.setMonitoringPanel()



        # ************************************************************************************************************ #
        #                                               CONTROL PANEL
        # ************************************************************************************************************ #
    def setupControlPanel(self):
        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        control_panel_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #

        # BOARD #1 (Power supply control panel).
        board_1_groupBox = QGroupBox(self.board_1.board_name)
        board_1_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        control_panel_layout.addWidget(board_1_groupBox, stretch=1)

        board_1_groupBox_layout = QFormLayout(board_1_groupBox)
        board_1_groupBox_layout.addRow(self.board_1)
        board_1_groupBox.setLayout(board_1_groupBox_layout)

        self.board_1.init_vi()

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel).    Plan to make two tabs for the linear stage
        # and the linear actuator.
        actuator_groupBox = QGroupBox("Actuator")
        actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        control_panel_layout.addWidget(actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.

        # ------------------------------------------------------------------------------------------------------------ #
        self.main_layout.addLayout(control_panel_layout, 0) # add the control panel on the left side.



        # ************************************************************************************************************ #
        #                                               MONITORING PANEL
        # ************************************************************************************************************ #
    def setMonitoringPanel(self):
        # MONITORING (Right side of the main window: plots of measured and controlled variables: force, voltage, currents.
        # Position and speed will be added later). 
        monitoring_groupBox_layout = QVBoxLayout()

        plots_groupBox = QGroupBox("Monitoring")
        plots_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        monitoring_groupBox_layout.addWidget(plots_groupBox)

        all_plots_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #
        # FORCE SENSOR PLOT
        force_sensor = FutekSensor()
        force_sensor_widget = FutekSensorWidget(force_sensor, controls=True)
        all_plots_layout.addWidget(force_sensor_widget)
        # ------------------------------------------------------------------------------------------------------------ #
        # POWER SUPPLY VOLTAGE PLOT
        all_plots_layout.addWidget(self.board_1.hv_plots)
        # ------------------------------------------------------------------------------------------------------------ #
        # POWER SUPPLY CURRENT PLOTS
        # self.currents_layout = QHBoxLayout()
        # for plots_row in range(3):  # three phases means 3 current plots
        #     self.currents_layout.addWidget(self.board_1.hb_cm_plots[plots_row])
        # self.all_plots_layout.addLayout(self.currents_layout)
        # ------------------------------------------------------------------------------------------------------------ #
        self.board_1.hv_plots.setLayout(all_plots_layout)
        plots_groupBox.setLayout(all_plots_layout)
        self.main_layout.addLayout(monitoring_groupBox_layout, 1) # add the monitoring on the right side.


# ******************************************************************************************************************** #
# ******************************************************************************************************************** #
def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)

    window = PowerSupplyInterface()
    window.show()
    window.showMaximized()

    app.exec()


if __name__ == '__main__':
    main()