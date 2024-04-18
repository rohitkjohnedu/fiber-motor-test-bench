

# python packages
from PyQt6.QtWidgets import QWidget
import numpy as np
from serial import Serial
import sys
import time

# custom packages
from PowerSupply.ps_plots import VoltagePlots, CurrentPlots
from threading import Thread, RLock

DEFAULT_BUFFER_LENGTH = 10000000

class PowerSupply(QWidget):
    # Board parameters
    nbFullBridges = 4
    nbHalfBridges = 8

    hv_max = 4500
    hv_min = 350

    f_max = 500
    f_min = 0.01

    # Interface parameters
    MODE1 = 1
    MODE2 = 1
    MODE3 = 1
    MODE4 = 1
    OLD_MODE5 = 1
    MODE5 = 1

    hv_vm_plot_max = 4500
    lv_vm_plot_max = 12
    hb_cm_plot_max = 6

    def __init__(self, parent=None, port_name=None, voltage_display=None, currents_display=None):

        QWidget.__init__(self, parent=parent)

        self.port_name = port_name
        self.display_voltages = voltage_display
        self.display_currents = currents_display

        self.buffer_length = DEFAULT_BUFFER_LENGTH
        self.variables_number = 11
        self.buffer_data = np.zeros((self.buffer_length, self.variables_number), dtype=np.float64)
        self.values_labels = np.zeros((self.buffer_length, 6), dtype=np.float64)
        self.sample = 0
        self.read_samples = 0
        self.plotHistoryLength = 10#seconds
        self.maxPlotHistoryLength = 100000#samples
        self.reading_thread_lock = RLock()
        self.interpolation_stop_time = 0
        # ************************************************************************************************************ #
        #                                                VOLTAGE PLOTS
        # ************************************************************************************************************ #

        # High voltage plot.
        if self.display_voltages == 1:
            self.voltage_plots = VoltagePlots(plot_title="High Voltage of the Power Supply",
                                              y_min=0, y_hv_max=self.hv_vm_plot_max)     

        # ------------------------------------------------------------------------------------------------------------ #
            
        # High and Low voltage plots.               
        if self.display_voltages == 2:
            self.voltage_plots = VoltagePlots(plot_title="High and Low Voltage of the Power Supply", y_min=0,
                                              y_hv_max=self.hv_vm_plot_max, y_lv_max=self.lv_vm_plot_max, plots = "HV + LV")

        # ************************************************************************************************************ #
        #                                              CURRENT PLOTS
        # ************************************************************************************************************ #
        
        # Current plot.
        if self.display_currents != 0:
            self.current_plots = CurrentPlots(y_min=0, y_max=self.hb_cm_plot_max)
           
        # ************************************************************************************************************ #
        #                                        SERIAL COMMUNICATION WITH HVPS
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
        self.send_command(self.ser, to_send)

        # ************************************************************************************************************ #
        # Read a first time to ensure connection.
            
        line = self.ser.readline()                                              # can't use the port which is not open
        line = line.decode("utf-8")
        if line == "":
            print("[ERR.] no data received... ensure that the high voltage power supply is connected")
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
        self.send_command(self.ser, to_send)

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
    #                                           CALLBACK FUNCTION
    # ************************************************************************************************************ #

    def start_recording(self):
        self.stop_recording()
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
                self.send_command(self.ser, to_send)
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
                    t_save = int(data[1])
            # -------------------------------------------------------------------------------------------------------- #
                if self.display_voltages != 0:
                    hv_set = np.float64(data[2])
                    hv_vm = np.float64(data[5])
                    hv_err = np.float64(data[2]) - np.float64(data[5])
            # -------------------------------------------------------------------------------------------------------- #    
                if self.display_voltages == 2:
                    lv_set = np.float64(data[3])
                    lv_vm = np.float64(data[4])
                    lv_err = np.float64(data[3]) - np.float64(data[4])
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
            
            self.reading_thread_lock.release()  # Release data lock
            self.sample = self.sample + 1

        # ************************************************************************************************************ #
        #                                           UPDATE PLOTS/LABELS
        # ************************************************************************************************************ #

    def get_new_data(self):
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        if self.read_samples - 500 > 0:
            data = self.buffer_data[self.read_samples - 500:self.sample,:]
        else:
            data = self.buffer_data[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        self.read_samples = self.sample
        return data
        # if len(data) == 0:
        #     return np.array([])
        # if self.interpolation_stop_time < start_time:
        #     interpolation_start_time = start_time
        # else:
        #     interpolation_start_time = self.interpolation_stop_time + 1/sample_rate

        # differential_time_latest_sample = data[-1,0] - start_time
        # interpolated_latest_sample_number = np.floor(differential_time_latest_sample/(1/sample_rate))
        # self.interpolation_stop_time = start_time + interpolated_latest_sample_number*(1/sample_rate)

        # interpolartion_time = np.arange(interpolation_start_time,self.interpolation_stop_time,1/sample_rate)
        # interpolated_data = np.zeros((len(interpolartion_time),11))
        # for i1 in range(1,11):
        #     interpolated_data[:,0] =  interpolartion_time            
        #     interpolated_data[:,1] = np.interp(interpolartion_time, data[:, 0], data[:, i1])

        # return interpolated_data

    def plot_update(self, start_time):
        all_data = self.get_buffer()
        data = all_data
        hv_vm = data[:, 3]

        if self.display_voltages != 0 or self.display_currents != 0:
            epoch_time = data[:, 0]
            tplot = epoch_time - start_time

            if len(tplot) > self.maxPlotHistoryLength:
                tplot = tplot[-self.maxPlotHistoryLength:]

            # Update voltage plots.
            if self.display_voltages != 0:
                hv_set = data[:, 2]
                if len(tplot) > self.maxPlotHistoryLength:
                                hv_set = hv_set[-self.maxPlotHistoryLength:]
                                hv_vm = hv_vm[-self.maxPlotHistoryLength:]
            
            if self.display_voltages == 1:
                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.voltage_plots.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use])
                    self.voltage_plots.update_legend(hv_set[-1], hv_vm[-1])

            if self.display_voltages == 2:
                lv_set = data[:, 5]
                lv_vm = data[:, 6]
                
                if len(tplot) > self.maxPlotHistoryLength:
                    lv_set = lv_set[-self.maxPlotHistoryLength:]
                    lv_vm = lv_vm[-self.maxPlotHistoryLength:]

                if len(tplot) > 0:
                    use = tplot > tplot[-1] - self.plotHistoryLength
                    self.voltage_plots.update_plot(t=tplot[use], y1=hv_set[use], y2=hv_vm[use],
                                                    y3=lv_set[use], y4=lv_vm[use])
                    self.voltage_plots.update_legend(hv_set[-1], hv_vm[-1], lv_set[-1], lv_vm[-1])

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

    def send_command(self, ser, command):
        to_send = bytearray(command, encoding="utf-8")
        ser.write(to_send)

    ####################################################################################################################
    # STOP COMMUNICATION
    def stop_comm(self):
        # Disable HV and monitoring.
        self.send_command(self.ser, "\r\nEStop\r\n")

