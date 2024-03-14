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
        self.main_layout = QHBoxLayout(self)

        # ************************************************************************************************************ #
        #                       ASSIGNMENT OF VALUES TO VARIABLES FOR OPTIONS AND PORT SELECTION
        # ************************************************************************************************************ #
        # Comment the dialog for the port and options selection; assign values to variables instead below.

        '''
        # open a dialog to ask port
        dialog = ComSelect("CP210")
        if not dialog.exec():
            print("[ERR] Canceled")
            sys.exit(0)
        '''

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

        # ************************************************************************************************************ #
        #                                   DEFINITION OF THE INTERFACE OBJECTS
        # ************************************************************************************************************ #

        # BOARD #1
        board_1_port = None #dialog.get_board_1_port_results()
        self.board_1 = PowerSupply(port_name=board_1_port,
                                        estimate_rate=self.estimateRate,
                                        currents_display=display_currents,
                                        voltage_display=display_voltages,
                                        debug_mode=self.debug_mode,
                                        rcv_data=display_cmd,
                                        record_data=record_data)
        
        # ------------------------------------------------------------------------------------------------------------ #

        # BOARD #2
        # board_2_port = None
        # if self.number_board == 2:
        #     board_2_port = dialog.get_board_2_port_results()
        #     self.board_2 = PowerSupply(port_name=board_2_port,
        #                                     estimate_rate=self.estimateRate,
        #                                     currents_display=display_currents,
        #                                     voltage_display=display_voltages,
        #                                     debug_mode=self.debug_mode,
        #                                     rcv_data=display_cmd,
        #                                     record_data=record_data)

        # ************************************************************************************************************ #
        self.force_sensor = None
        # FUTEK FORCE SENSOR (Load cell)
        self.force_sensor = FutekSensor()
        self.force_sensor_widget = FutekSensorWidget(self.force_sensor, controls=True)

        # ************************************************************************************************************ #

        # DEBUG MODE
        # if self.debug_mode == 1:
        #     print("[INFO] Selected Board {} (com port {})".format(self.board_1.board_name, board_1_port))
        #     # if self.number_board == 2:
        #     #     print("[INFO] Selected Board {} (com port {})".format(self.board_2.board_name, board_2_port))

        #     print("[INFO] User selected display_voltage: {}".format(display_voltages))
        #     print("[INFO] User selected display_current: {}".format(display_currents))

        #     print("[INFO] User selected display: {}".format(display_cmd))
        #     print("[INFO] User selected Debug: {}".format(self.debug_mode))
        #     print("[INFO] User selected Record: {}".format(record_data))

        # ************************************************************************************************************ #
        #                                     INITIALIZATION OF THE USER INTERFACE
        # ************************************************************************************************************ #
        # Init user interface + callback for buttons...                                                                

        # self.setWindowTitle("{} - {}" .format(PROGRAM_NAME, PROGRAM_VERSION))
        # self.main_layout = QHBoxLayout(self)

        # ************************************************************************************************************ #
        # CONTROL PANEL (Left side of the main window: control panel of the power supply and actuator).
        self.control_panel_layout = QVBoxLayout()
        # ------------------------------------------------------------------------------------------------------------ #

        # BOARD #1 (Power supply control panel).
        self.board_1_groupBox = QGroupBox(self.board_1.board_name)
        self.board_1_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.board_1_groupBox, stretch=1)

        self.board_1_groupBox_layout = QFormLayout(self.board_1_groupBox) #
        self.board_1_groupBox_layout.addRow(self.board_1)
        self.board_1_groupBox.setLayout(self.board_1_groupBox_layout)

        self.board_1.init_vi()

        # ------------------------------------------------------------------------------------------------------------ #

        # ACTUATOR (Motorized linear stage / Linear actuator control panel).    Plan to make two tabs for the linear stage
        # and the linear actuator.
        self.actuator_groupBox = QGroupBox("Actuator")
        self.actuator_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.control_panel_layout.addWidget(self.actuator_groupBox, stretch=1)

        # Here will be a code for the actuator control panel.

        # ------------------------------------------------------------------------------------------------------------ #
        self.main_layout.addLayout(self.control_panel_layout, 0) # add the control panel on the left side.

        # ************************************************************************************************************ #
        # MONITORING (Right side of the main window: plots of measured and controlled variables: force, voltage, and currents.
        # Position and speed will be added later).
        self.monitoring_groupBox_layout = QVBoxLayout()

        self.plots_groupBox = QGroupBox("Monitoring")
        self.plots_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.monitoring_groupBox_layout.addWidget(self.plots_groupBox)

        self.all_plots_layout = QVBoxLayout(self.plots_groupBox)
        self.all_plots_layout.setSpacing(0)
        # ------------------------------------------------------------------------------------------------------------ #
        # FORCE SENSOR PLOT
        self.all_plots_layout.addWidget(self.force_sensor_widget)

        self.force_sensor_layout = QHBoxLayout()
        self.force_sensor_controls_layout = QVBoxLayout()
        self.force_sensor_controls_layout.setContentsMargins(0, 10, 0, 10)

        self.force_sensor_layout.addWidget(self.force_sensor_widget)

        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.heading)
        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.connect_button)
        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.tare_button)
        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.clear_button)
        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.continuous_acq)
        self.force_sensor_controls_layout.addWidget(self.force_sensor_widget.save_data_button)

        self.force_sensor_controls_layout.addStretch(1)
        self.force_sensor_layout.addLayout(self.force_sensor_controls_layout)
        self.all_plots_layout.addLayout(self.force_sensor_layout)

        # # ------------------------------------------------------------------------------------------------------------ #
        # POWER SUPPLY VOLTAGE PLOT
        self.voltage_layout = QHBoxLayout()
        self.voltage_labels_layout = QVBoxLayout()
        self.voltage_labels_layout.setContentsMargins(0, 10, 0, 10)

        # self.voltage_labels_layout.setContentsMargins(5, 0, 0, 0)
        self.voltage_layout.addWidget(self.board_1.hv_plots)

        self.voltage_labels_layout.addWidget(self.board_1.hv_set_name_label)
        self.voltage_labels_layout.addWidget(self.board_1.hv_set_value_label)
        # self.voltage_labels_layout.addSpacerItem(QSpacerItem(10, 16))
        self.voltage_labels_layout.addWidget(self.board_1.hv_vm_name_label)
        self.voltage_labels_layout.addWidget(self.board_1.hv_vm_value_label)
        # self.voltage_labels_layout.addSpacerItem(QSpacerItem(10, 16))
        self.voltage_labels_layout.addWidget(self.board_1.hv_err_name_label)
        self.voltage_labels_layout.addWidget(self.board_1.hv_err_value_label)
        # self.voltage_labels_layout.addSpacerItem(QSpacerItem(10, 16))

        self.voltage_labels_layout.addStretch(1)
        self.voltage_layout.addLayout(self.voltage_labels_layout)
        self.all_plots_layout.addLayout(self.voltage_layout)

        # # ------------------------------------------------------------------------------------------------------------ #
        # POWER SUPPLY CURRENT PLOTS
        self.currents_layout = QHBoxLayout()
        # self.currents_layout.setContentsMargins(0, 0, 0, 0)
        self.currents_layout.setSpacing(0)

        self.current_labels_layout = QVBoxLayout()
        self.current_labels_layout.setContentsMargins(0, 10, 0, 10)

        for plots_row in range(3):  # three phases means 3 current plots
            self.currents_layout.addWidget(self.board_1.hb_cm_plots[plots_row])

            self.current_labels_layout.addWidget(self.board_1.names_labels[plots_row])     
            self.current_labels_layout.addWidget(self.board_1.values_labels[plots_row])

        self.current_labels_layout.addStretch(1) 
        self.currents_layout.addLayout(self.current_labels_layout)
        self.all_plots_layout.addLayout(self.currents_layout)

        # # ------------------------------------------------------------------------------------------------------------ #
        self.plots_groupBox.setLayout(self.all_plots_layout)
        self.main_layout.addLayout(self.monitoring_groupBox_layout, 1) # add the monitoring on the right side.

        # ************************************************************************************************************ #

        # BOARD #2
        # elif self.number_board == 2:
        #     Board #2
        #     self.board_2_groupBox = QGroupBox("Board {}".format(self.board_2.board_name))
        #     self.board_2_groupBox.setStyleSheet('QGroupBox {font-weight: bold;}')
        #     self.main_layout.addWidget(self.board_2_groupBox, 0)

        #     self.board_2_groupBox_layout = QFormLayout(self)
        #     self.board_2_groupBox_layout.addRow(self.board_2)
        #     self.board_2_groupBox.setLayout(self.board_2_groupBox_layout)

        #     self.board_2.init_vi()
        #     self.setGeometry(0, 0, 20, 20)

        #     self.main_layout.addStretch(1)

        # ************************************************************************************************************ #

        # if self.number_board == 1:
        #     if display_voltages == 0:
        #         self.setGeometry(0, 0, 10, 10)
        #     elif display_voltages == 1:
        #         self.setGeometry(0, 0, 1500, 500)
        #     else:
        #         self.setGeometry(0, 0, 1500, 500)

        # self.show()
        # self.showMaximized()

        # ************************************************************************************************************ #
        # ************************************************************************************************************ #
        
        # # set a timer with the callback function which reads data from serial port and plot
        # # period is 30ms => 33Hz, if enough data sent by the board
        # self.timer = QTimer(self)
        # self.timer.timeout.connect(self.data_reader_callback)
        # self.timer.start(self.time)

        # ************************************************************************************************************ #
        # ************************************************************************************************************ #

    # def data_reader_callback(self):
    #     self.board_1.data_reader_callback()
        # if self.number_board == 2:
        #     self.board_2.data_reader_callback()

    # def closeEvent(self, event):
    #     reply = QMessageBox.question(self, "Window Close", "Are you sure you want to close the window?")

    #     if reply == QMessageBox.StandardButton.Yes:
    #         self.board_1.stop_comm()
    #         if self.number_board == 2:
    #             self.board_2.stop_comm()

    #         event.accept()
    #         if self.debug_mode == 1:
    #             print("[INFO] Program closed.")

    #     else:
    #         event.ignore()

    # ************************************************************************************************************ #
    # ************************************************************************************************************ #

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(PROGRAM_NAME)

    window = PowerSupplyInterface()
    window.show()
    window.showMaximized()

    app.exec()


if __name__ == '__main__':
    main()
