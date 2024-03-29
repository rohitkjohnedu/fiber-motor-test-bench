########################################################################################################################
# @project    EPFL-HXL_PS_v1.0
# @file       hxl_ps.py
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
import numpy as np
from serial import *
import sys
import time
# custom packages
from PowerSupply.ps_plots import VoltagePlots, VoltageLegend, CurrentPlots, CurrentLegend
from PowerSupply.ps_modes import *
from PowerSupply.options import *
from PowerSupply.StopReboot import *
from PowerSupply.Voltage import *

from threading import Thread, RLock

DEFAULT_BUFFER_LENGTH = 10000000

class PowerSupply(QWidget):
    def __init__(self, parent=None, port_name=None, currents_display=None, voltage_display=None,
                 debug_mode=None, record_data=None):

        QWidget.__init__(self, parent=parent)

        self.port_name = port_name
        self.display_currents = currents_display
        self.display_voltages = voltage_display
        self.debug_mode = debug_mode
        self.record_data = record_data

        self.buffer_length = DEFAULT_BUFFER_LENGTH

        if self.display_voltages == 1 and self.display_currents == 0:
            self.variables_number = 5
        elif self.display_voltages == 2 and self.display_currents == 0:
            self.variables_number = 8
        elif self.display_currents != 0 and self.display_voltages == 0:
            self.variables_number = 11
        else:
            self.variables_number = 0
        self.variables_number = 11

        self.buffer_data = np.zeros((self.buffer_length, self.variables_number), dtype=np.float64)
        self.values_labels = np.zeros((self.buffer_length, 6), dtype=np.float64)
        self.sample = 0
        self.plotHistoryLength = 10#seconds
        self.maxPlotHistoryLength = 100000#samples
        self.reading_thread_lock = RLock()
        # ************************************************************************************************************ #

        # MODULES
        self.em_stop = StopReboot()
        self.voltage = Voltage()
        self.Mode1 = Mode1()
        self.Mode2 = Mode2()
        self.Mode3 = Mode3()
        self.Mode4 = Mode4()
        self.OldMode5 = OldMode5()
        self.Mode5 = Mode5()
 
        # ************************************************************************************************************ #
        #                                                VOLTAGE PLOTS
        # ************************************************************************************************************ #

        # High voltage plot.
        if self.display_voltages == 1:
            self.voltage_plots = VoltagePlots(plot_title="Voltage", y_min=0, y_hv_max=hv_vm_plot_max)     

        # ------------------------------------------------------------------------------------------------------------ #
            
        # High and Low voltage plots.               
        if self.display_voltages == 2:
            self.voltage_plots = VoltagePlots(plot_title="Voltage", y_min=0, y_hv_max=hv_vm_plot_max,
                                         y_lv_max=lv_vm_plot_max, plots = "HV + LV")

        # ------------------------------------------------------------------------------------------------------------ #
            
        # Voltage labels.
        # self.voltage_legend = VoltageLegend.VoltageLegend()

        # ************************************************************************************************************ #
        #                                              CURRENT PLOTS
        # ************************************************************************************************************ #
        
        # Current plot.
        if self.display_currents != 0:
            self.current_plots = CurrentPlots(y_min=0, y_max=hb_cm_plot_max)

        # ------------------------------------------------------------------------------------------------------------ #
 
            # Current labels.
            # self.current_legend.append(CurrentLegend.CurrentLegend(plot_name=self.y_name[HalfBridges+1],
            #                                                        plot_index=HalfBridges+1))
           
        # ************************************************************************************************************ #
        #                                           SERIAL COMMUNICATION
        # ************************************************************************************************************ #

        # Open serial port.
        try:
            self.ser = Serial(self.port_name, 115200, timeout=0.5)
        except Exception as err_com_port:
            print("[ERR.] Please make sure that you use the right COM port: {}".format(err_com_port))
            sys.exit(-1)
            
        # Remove old data in input buffer.
        self.ser.reset_input_buffer()

        # Enable debug.
        to_send = "QName\r\n"
        send_command(self.ser, to_send)

        # ------------------------------------------------------------------------------------------------------- #
        # Connect widgets to the serial port.

        self.em_stop.attach_serial(serial=self.ser)
        self.voltage.attach_serial(serial=self.ser)

        if MODE1 == 1:
            self.Mode1.attach_serial(serial=self.ser)

        if MODE2 == 1:
            self.Mode2.attach_serial(serial=self.ser)

        if MODE3 == 1:
            self.Mode3.attach_serial(serial=self.ser)

        if MODE4 == 1:
            self.Mode4.attach_serial(serial=self.ser)

        if OLD_MODE5 == 1:
            self.OldMode5.attach_serial(serial=self.ser)

        if MODE5 == 1:
            self.Mode5.attach_serial(serial=self.ser)

        # ************************************************************************************************************ #
        # Read a first time to ensure connection.
            
        line = self.ser.readline()                                              # can't use the port which is not open
        line = line.decode("utf-8")
        if line == "":
            print("[ERR.] no data received... ensure that the board has not been disconnected")
            sys.exit(-1)

        # Read from serial.
        try:
            line = self.ser.readline()
            line = line.decode("utf-8")
        except Exception as e:
            print("[ERR] unable to read line: {}".format(e))
            self.try_reconnect()

        self.board_name = "Power Supply " + line.replace("[QName] ", "").replace("\n", "")

        # ------------------------------------------------------------------------------------------------------------ #

        # Enable debug.
        to_send = "QVer\r\n"
        send_command(self.ser, to_send)

        for x in range(3):
            line = self.ser.readline()
            line = line.decode("utf-8")
            if line == "":
                print("[ERR.] no data received... ensure that the board has not been disconnected")
                sys.exit(-1)

        # Read from serial.
        try:
            line = self.ser.readline()
            line = line.decode("utf-8")
        except Exception as e:
            print("[ERR] unable to read line: {}".format(e))
            self.try_reconnect()
            return

        self.board_version = line.replace("[QVer] ", "").replace("\n", "")

        # ************************************************************************************************************ #

        # Init file to record data.
        if self.record_data == 1:
            self.RecordData = RecordData(board_name=self.board_name,
                                         board_version=self.board_version,
                                         port_name=port_name,
                                         sequential=False)
            self.SequentialRecord = SequentialRecord(board_name=self.board_name,
                                                     board_version=self.board_version,
                                                     port_name=port_name)


    # ************************************************************************************************************ #
    #                                           INITIALIZE PS UI
    # ************************************************************************************************************ #

        layout_main = QVBoxLayout()
        self.setLayout(layout_main)
        layout_main.setSpacing(3)

        layout_top = QHBoxLayout()
        layout_top.setSpacing(3)

        # Control panel is on the left side.
        layout_left = QVBoxLayout()
        layout_left.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout_left.setSpacing(0)
        layout_top.addLayout(layout_left)

        # ------------------------------------------------------------------------------------------------------------ #

        layout_left.addWidget(self.em_stop)
        layout_left.addWidget(self.voltage)

        # ------------------------------------------------------------------------------------------------------------ #
        tab = QTabWidget(self)
        tab.setFixedWidth(700)

        if MODE1 == 1:
            tab.addTab(self.Mode1, 'Mode 1')

        if MODE2 == 1:
            tab.addTab(self.Mode2, 'Mode 2')

        if MODE3 == 1:
            tab.addTab(self.Mode3, 'Mode 3')

        if MODE4 == 1:
            tab.addTab(self.Mode4, 'Mode 4')

        if OLD_MODE5 == 1:
            tab.addTab(self.OldMode5, 'Mode Go and Back')

        if MODE5 == 1:
            tab.addTab(self.Mode5, 'Mode 5')

        layout_left.addWidget(tab)

        # ------------------------------------------------------------------------------------------------------------ #
        # Add the top layout to the main layout.
        layout_main.addLayout(layout_top)
        
        # ************************************************************************************************************ #

        # Data save info.
        if self.record_data == 1:
            layout_left.addWidget(self.RecordData)
            layout_left.addWidget(self.SequentialRecord)
        
        # ************************************************************************************************************ #
        
        # Layout of all widgets not plot.
        layout_left.addStretch(1)
        layout_main.addStretch(1)   

    # ************************************************************************************************************ #
    #                                           CALLBACK FUNCTION
    # ************************************************************************************************************ #

    def start_recording(self):
        self.continuous_reading_flag = True
        self.reading_thread = Thread(target=self.data_reader_callback)
        self.reading_thread.start()
        self.clear_buffer()

    def stop_recording(self):
        self.continuous_reading_flag = False

    def clear_buffer(self):
        self.buffer_data = np.zeros((self.buffer_length, self.variables_number), dtype=np.float64)
        self.sample = 0
        
    def get_buffer(self):
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        data = self.buffer_data[0:self.sample,:]
        # values = self.values_labels[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        return data
    
    def data_reader_callback(self):
        while self.continuous_reading_flag:  # If flag for data acquisition is True
            # Read from serial.
            try:
                line = self.ser.readline()
                line = line.decode("utf-8")
            except Exception as e:
                print("[ERR] unable to read line: {}".format(e))
                self.try_reconnect()
                continue

            if len(line) <= 1:
                # Enable debug.
                to_send = "\r\nMoni 1\r\n"
                send_command(self.ser, to_send)
                continue

            if not line.startswith("[moni]"):
                continue   

            # ************************************************************************************************************ #
            # Handle data.
            # Remove units, spaces, split with coma.
            # Refer to documentation of HVPS to assign data to fields.
            data = line.replace(" ", "").replace("uA", "").replace("V", "").replace("Hz", "").replace("\r\n", "").split(",")

            try:
                if self.display_voltages != 0 or self.display_currents != 0:
                    t_save = int(data[1])/1000
            # -------------------------------------------------------------------------------------------------------- #
                if self.display_voltages != 0:
                    hv_set = np.float64(data[2])
                    hv_set_now = format(hv_set, '4.0f')

                    hv_vm = np.float64(data[5])
                    hv_vm_now = format(hv_vm, '4.0f')

                    hv_err = np.float64(data[2]) - np.float64(data[5])
                    hv_err_now = format(hv_err, '4.0f')
            # -------------------------------------------------------------------------------------------------------- #    
                if self.display_voltages == 2:
                    lv_set = np.float64(data[3])
                    lv_set_now = format(lv_set, '2.1f')

                    lv_vm = np.float64(data[4])
                    lv_vm_now = format(lv_vm, '2.1f')

                    lv_err = np.float64(data[3]) - np.float64(data[4])
                    lv_err_now = format(lv_err, '2.1f')
            # -------------------------------------------------------------------------------------------------------- #
                if self.display_currents != 0:
                    cm_val_w1 = np.float64(data[7])
                    cm_val_w2 = np.float64(data[8])
                    cm_val_w3 = np.float64(data[9])
            # -------------------------------------------------------------------------------------------------------- #
            except Exception as e:
                print("[ERR] Unable to convert line: {} - {}".format(line, e))
                continue
            
            self.reading_thread_lock.acquire()  # Get multithreading lock
            epoch_time = time.perf_counter()

            if self.display_voltages != 0 or self.display_currents != 0:
                # Only High Voltage.
                if self.display_voltages == 1 and self.display_currents == 0:
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       hv_set, hv_vm, hv_err,
                                                       0, 0, 0, 
                                                       0, 0, 0]
                # High and Low Voltage.
                if self.display_voltages == 2 and self.display_currents == 0:
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       hv_set, hv_vm, hv_err,
                                                       lv_set, lv_vm, lv_err, 
                                                       0, 0, 0]
                # Only Currents.
                if self.display_currents != 0 and self.display_voltages == 0:
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       0, 0, 0,
                                                       0, 0, 0, 
                                                       cm_val_w1, cm_val_w2, cm_val_w3]
                # High Voltage and Currents.
                if self.display_currents != 0 and self.display_voltages == 1:
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       hv_set, hv_vm, hv_err,
                                                       0, 0, 0, 
                                                       cm_val_w1, cm_val_w2, cm_val_w3]
                # High and Low Voltage and Currents.
                if self.display_currents != 0 and self.display_voltages == 2:
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       hv_set, hv_vm, hv_err,
                                                       lv_set, lv_vm, lv_err, 
                                                       cm_val_w1, cm_val_w2, cm_val_w3]

            # self.values_labels[self.sample,:] = [hv_set_now, hv_vm_now, hv_err_now,
            #                                      lv_set_now, lv_vm_now, lv_err_now]
            
            self.reading_thread_lock.release()  # Release data lock
            self.sample = self.sample + 1

            # # Save data to file.
            # if self.record_data == 1:
            #     self.RecordData.save_data(line)
            #     self.SequentialRecord.is_recording_now(line)

        # ************************************************************************************************************ #
        #                                           UPDATE PLOTS/LABELS
        # ************************************************************************************************************ #

    def plot_update(self, start_time):
        all_data = self.get_buffer()
        data = all_data
        hv_vm = data[:, 3]
        # Update voltage button.
        if len(hv_vm) > 0:
            self.voltage.update_data(current_voltage=hv_vm[-1])

        if self.display_voltages != 0 or self.display_currents != 0:
            # values = all_data[1]
            epoch_time = data[:, 0]
            tplot = epoch_time - start_time

            if len(tplot) > self.maxPlotHistoryLength:
                tplot = tplot[-self.maxPlotHistoryLength:]

            # Update voltage plots.
            if self.display_voltages != 0:
                hv_set = data[:, 2]
                # hv_err = data[:, 4]
                # if len(tplot) > 0:
                #     hv_set_now = values[-1, 0]
                #     hv_vm_now = values[-1, 1]
                #     hv_err_now = values[-1, 2]
                if len(tplot) > self.maxPlotHistoryLength:
                                hv_set = hv_set[-self.maxPlotHistoryLength:]
                                hv_vm = hv_vm[-self.maxPlotHistoryLength:]
            
            if self.display_voltages == 1:
                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.voltage_plots.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use])
                    # self.voltage_legend.update_label(hv_set_now, hv_vm_now, hv_err_now)

            if self.display_voltages == 2:
                lv_set = data[:, 5]
                lv_vm = data[:, 6]
                # lv_err = data[:, 7]
                # if len(tplot) > 0:
                #     lv_set_now = values[-1, 3]
                #     lv_vm_now = values[-1, 4]
                #     lv_err_now = values[-1, 5]

                if len(tplot) > self.maxPlotHistoryLength:
                    lv_set = lv_set[-self.maxPlotHistoryLength:]
                    lv_vm = lv_vm[-self.maxPlotHistoryLength:]

                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.voltage_plots.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use],
                                                    y3=lv_set[use], y4=lv_vm[use])
                    # self.voltage_legend.update_label(lv_set_now, lv_vm_now, lv_err_now)

            # Update current plots.
            if self.display_currents == 1:
                cm_val_w1 = data[:, 8]
                cm_val_w2 = data[:, 9]
                cm_val_w3 = data[:, 10]

                if len(tplot) > self.maxPlotHistoryLength:
                    cm_val_w1 = cm_val_w1[:, -self.maxPlotHistoryLength:]
                    cm_val_w2 = cm_val_w2[:, -self.maxPlotHistoryLength:]
                    cm_val_w3 = cm_val_w3[:, -self.maxPlotHistoryLength:]

                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.current_plots.update_plot(t=tplot[use], y1=cm_val_w1[use],
                                                   y2=cm_val_w2[use], y3=cm_val_w3[use])
                    self.current_plots.update_legend(cm_val_w1[-1], cm_val_w2[-1], cm_val_w3[-1])
                    
        # ************************************************************************************************************ #
        
            # save data to file
            # if self.record_data == 1:
            #     self.RecordData.save_data(self.line)
            #     self.SequentialRecord.is_recording_now(self.line)   
            
            # ************************************************************************************************************ #
                
            # Flush input if too much data not handled: avoid keeping very old values.
            # if self.ser.in_waiting > 200:
            #     self.ser.reset_input_buffer()

    def set_plot_history(self, history_length):
        self.plotHistoryLength = history_length
                    
    ####################################################################################################################
    # RECONNECTION WITH BOARD
    def try_reconnect(self):
        self.ser.close()
        try:
            self.ser.open()
            self.ser.reset_input_buffer()
            print("[INFO] reconnected to the board")
        except Exception as err_connection:
            print("[ERR] connection failed: {}".format(err_connection))
            pass

    ####################################################################################################################
    # STOP COMMUNICATION
    def stop_comm(self):
        # Disable HV and monitoring.
        send_command(self.ser, "\r\nEStop\r\n")
        if self.record_data == 1:
            self.record_data = 0
            self.RecordData.close_record(sequential=False)