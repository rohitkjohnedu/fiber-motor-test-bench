import logging
import os
import sys
import time
from threading import Thread, RLock
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QMessageBox, QApplication

sys.path.append(os.getcwd())


DEFAULT_BUFFER_LENGTH = 10000000
FUTEK_UNITS_CODE = {
    2: {
        'abbr': 'dyn',
        'unit_name': 'dyne',
        'conversion_to_mN': 0.01
        },
    5: {
        'abbr': 'g',
        'unit_name': 'gram',
        'conversion_to_mN': 9.81
        },
    11: {
        'abbr': 'kdyn',
        'unit_name': 'kilodyne',
        'conversion_to_mN': 10.0
        },
    12: {
        'abbr': 'kg',
        'unit_name': 'kilogram',
        'conversion_to_mN': 9810.0
        },
    16: {
        'abbr': 'klb',
        'unit_name': 'kilopound',
        'conversion_to_mN': 4448221.6
        },
    17: {
        'abbr': 'kN',
        'unit_name': 'kiloNewton',
        'conversion_to_mN': 1000000.0
        },
    20: {
        'abbr': 'lb',
        'unit_name': 'pound',
        'conversion_to_mN': 4448.2216
        },
    21: {
        'abbr': 'Mdyn',
        'unit_name': 'megadyne',
        'conversion_to_mN': 10000.0
        },
    25: {
        'abbr': 'MT',
        'unit_name': 'metric ton',
        'conversion_to_mN': 9810000.0
        },
    26: {
        'abbr': 'N',
        'unit_name': 'Newton',
        'conversion_to_mN': 1000.0
        },
    30: {
        'abbr': 'oz',
        'unit_name': 'ounces',
        'conversion_to_mN': 278.01
        },
    33: {
        'abbr': 'ST',
        'unit_name': 'short ton (US)',
        'conversion_to_mN': 8896443.2
        },
    47: {
        'abbr': 'µg',
        'unit_name': 'microgram',
        'conversion_to_mN': 9.81e-06
        },
    48: {
        'abbr': 'mg',
        'unit_name': 'milligram',
        'conversion_to_mN': 0.009810000000000001
        },
    49: {
        'abbr': 'LT',
        'unit_name': 'long ton (UK)',
        'conversion_to_mN': 9964016.384
        }
    }


def _error_display(error):
    """
    Used to display error using QT messagebox or console

    :param error: error string to display
    :type error: str
    """
    # If a Qt window is opened
    if QApplication.instance() and QApplication.activeWindow():
        QMessageBox.warning(QApplication.activeWindow(), "Force Sensor error",
                                      error)  # The box is displayed
    else:  # Otherwise
        logging.error(error)  # Printing in the console


class FutekSensor():
    """
    Class for reading Futek Force Sensor
    """
    def __init__(self, serial_number="802078"):
        """
        Init Class

        :type serial_number: str
        """
        import clr  # Late import of pydotnet to avoid conflict with Qt
        clr.AddReference("FUTEK_USB_DLL")  # Reference Futek Dll
        import FUTEK_USB_DLL  # Import Futek Dll C# library


        self.serial_number = serial_number  # Serial number of the controller
        self.futek_dll = FUTEK_USB_DLL.USB_DLL()  # Dll object

        self.sensor_capacity = 110.0
        self.fullscale_value = 0
        self.offset = 0
        self.tare_register_value = 0
        self.firmware_version = 0
        self.board_type = 0
        self.sensor_stiffness = 3962.63E3  # 3962 N/m 3962E3 mN/m
        self.taring_force = 0  # Taring initialization
        self.device_handle = None

        self.buffer_length = DEFAULT_BUFFER_LENGTH
        self.taring_buffer_raw_data = np.zeros((self.buffer_length, 2), dtype=np.float64)
        self.buffer_raw_data = np.zeros((self.buffer_length, 2), dtype=np.float64)
        self.buffer_data = np.zeros((self.buffer_length, 2), dtype=np.float64)
        self.sample = 0
        self.taring_sample = 0
        self.read_samples = 0

        self.continuous_reading_flag = False

        self.reading_thread = Thread(target=self._read_device)
        self.reading_thread_lock = RLock()  # Lock for multithreading

        self.connect()

    @property
    def is_connected(self):
        return self.futek_dll.DeviceStatus == 0 and self.futek_dll.DeviceHandle.ToInt64() > 0

    def connect(self, serial_number=None):
        """
        Connect to the Futek force sensor

        :param serial_number: Serial number of the controller to connect to. Optional, if None, will use \
        the serial number passed at object creation.
        """
        if serial_number is not None:
            self.serial_number = serial_number
        try:  # Try to connect from dll
            self.futek_dll.Open_Device_Connection(self.serial_number)
            # Return True if no error
            if not self.is_connected:  # If no exception but connection error
                _error_display(f"Impossible to connect force sensor. \nDevice Error {self.futek_dll.DeviceStatus}")
                self.device_handle = ""  # Handle is empty
            else:  # Otherwise, if forse sensor connected
                self.device_handle = self.futek_dll.DeviceHandle  # Get device Handle
                time.sleep(0.1)  # Pause
                self._get_devices_parameters()  # Get device parameters
                logging.info(f"Futek force sensor connected. Sensor capacity is {self.sensor_capacity:.1f} mN")
        except:  # If exception
            _error_display(f"Device Error {self.futek_dll.DeviceStatus} \nImpossible to connect force sensor.")

        return self.is_connected  # Returns connection state
    
    def disconnect(self):
        """
        Disconnect force sensor
        """
        self.stop_recording()  # Stop continuous reading thread
        # Calling Dll close method
        if self.device_handle:
            self.futek_dll.Close_Device_Connection(self.device_handle)
        return self.is_connected

    def get_sensor_load(self):
        """
        Get sensor full load from internal register

        :return: Sensor capacity in mN
        :type: float
        """
        sensor_capacity_register = self.futek_dll.Get_Internal_Register(self.device_handle, 5)
        sensor_capacity_register = np.float64(sensor_capacity_register)
        sensor_capacity_register_details = self.futek_dll.Get_Internal_Register(self.device_handle, 6)
        sensor_capacity_register_details = int(sensor_capacity_register_details)

        decimal_point_code = sensor_capacity_register_details >> 16
        unit_code = int((sensor_capacity_register_details & 0b1111111100000000) >> 8)
        direction_code = int(sensor_capacity_register_details & 0b11111111)

        sensor_capacity_register *= 10 ** (-np.float64(decimal_point_code))

        if unit_code in FUTEK_UNITS_CODE:
            sensor_capacity_register *= FUTEK_UNITS_CODE[unit_code]['conversion_to_mN']
        else:
            _error_display("Unit code for futek sensor not found")

        direction_code = -1 if direction_code == 0 else 1
        sensor_capacity = sensor_capacity_register * direction_code
        self.sensor_capacity = sensor_capacity
        return sensor_capacity

    def _get_devices_parameters(self, timeout=5):
        """
        Get device fullscale value, offset, full load and tare register.
        The only argument is timeout with default value 5s.

        :param: timeout
        :type: float
        """
        if self.is_connected:  # If force sensor connected
            initial_time = time.perf_counter()  # Start counting for timeout
            error = ""
            while True:  # Try to read fullscale value
                fullscale_value = self.futek_dll.Get_Fullscale_Value(self.device_handle)
                if fullscale_value.isnumeric():  # If the return is numeric (i.e. correct)
                    self.fullscale_value = np.float64(fullscale_value)  # It is saved
                    break  # Quitting the reading process
                if timeout:  # If a timeout has been set
                    if time.perf_counter() > initial_time + timeout:  # Checking timeout has not been reached
                        self.fullscale_value = 1  # Set fullscale to 1
                        # Add error to the error string
                        error += "Force sensor error : fullscale reading timeout\n"
                        break  # Stop trying to get the fullscale value

            initial_time = time.perf_counter()  # Reset clock for timeout
            while True:  # Try to read offset value
                offset = self.futek_dll.Get_Offset_Value(self.device_handle)  # Call Dll function
                if offset.isnumeric():  # If the return value is correct
                    self.offset = np.float64(offset)  # Save the value
                    break  # Stop trying to read
                if timeout:  # If method argument timeout is set
                    if time.perf_counter() > initial_time + timeout:  # Check if timeout time is elapsed
                        self.offset = 0  # Set offset value to zero
                        error += "Force sensor error : offset reading timeout\n"  # Add error to the error string
                        break  # Stop trying to get the offset value

            initial_time = time.perf_counter()  # Reset clock for timeout
            while True:  # Try to read tare register value
                tare_register_value = self.futek_dll.Get_Internal_Register(self.device_handle, 1)
                if tare_register_value.isnumeric():  # If the return value is correct
                    self.tare_register_value = np.float64(tare_register_value)  # Save the value
                    break  # Stop trying to read
                if timeout:  # If method argument timeout is set
                    if time.perf_counter() > initial_time + timeout:  # Check if timeout time is elapsed
                        self.tare_register_value = 0  # Set tare value to zero
                        error += "Force sensor error : tare register reading timeout\n"  # Add error to the error string
                        break  # Stop trying to get the tare value

            self.firmware_version = self.futek_dll.Get_Firmware_Version(self.device_handle)
            self.board_type = self.futek_dll.Get_Type_of_Board(self.device_handle)
            self.get_sensor_load()
            if error != "":  # If there is an error
                _error_display(error)  # Print error in console

    def set_sensor_range(self, capacity):
        """
        Manually set sensor range in milli-newton. if max force of the sensor is 1.1N, set to 1100.

        :param capacity: Capacity of the sensor range in milli-newton
        :type capacity: float
        """
        self.sensor_capacity = capacity

    def tare(self):
        """
        Measure the force during 50ms and uses the mean as taring value
        """
        if self.is_connected:
            if self.continuous_reading_flag:
                self.taring_buffer_raw_data = np.zeros((self.buffer_length, 2))
                self.taring_sample = 0
                time.sleep(0.05)  # Wait for Measurement
                self.taring_force = np.mean(self.taring_buffer_raw_data[0:self.taring_sample, 1])  # Get mean value
            else:
                self.start_recording()
                self.taring_buffer_raw_data = np.zeros((self.buffer_length, 2))
                self.taring_sample = 0
                time.sleep(0.05)  # Wait for Measurement
                self.taring_force = np.mean(self.taring_buffer_raw_data[0:self.taring_sample, 1])  # Get mean value
                self.stop_recording()
        else:
            _error_display("Impossible to tare : Force sensor not connected")

    def start_recording(self):
        """
        Start continuous reading of the force
        """
        self.stop_recording() # Stop continuous reading if already started
        self.continuous_reading_flag = True  # Set flag to true
        self.reading_thread = Thread(target=self._read_device)  # Thread initialization for continuous reading
        self.reading_thread.start() 
        self.clear_buffer()

    def stop_recording(self):
        """
        Stop continuous reading of the force
        """
        self.continuous_reading_flag = False  # Set flag to True
        if self.reading_thread.is_alive():
            self.reading_thread.join()

    def clear_buffer(self):
        """
        Clear both data buffer and raw data buffer
        :return: None
        """
        self.buffer_data = np.zeros((self.buffer_length, 2))
        self.buffer_raw_data = np.zeros((self.buffer_length, 2))
        self.sample = 0

        self.taring_buffer_raw_data = np.zeros((self.buffer_length, 2))
        self.taring_sample = 0

    def get_new_data(self):
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        if self.read_samples - 500 > 0:
            data = self.buffer_data[self.read_samples - 500:self.sample,:]
        else:
            data = self.buffer_data[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        self.read_samples = self.sample
        return data

    def get_buffer(self):
        """
        Get current force buffer from continuous reading.
        clear_buffer reset the buffer.
        initial_t aligns time data to the given value
        (initial_t = 0 make time vector to start at 0)

        :param clear_buffer: If set to True, clear the buffer after reading
        :type clear_buffer: bool
        :param initial_t: Align time buffer to a specific time (if set to zero, time will start from zero,
        otherwise, if None, it'll take the value of the system counter.
        :type initial_t: float
        :return: tuple with time vector as first element and force data
        :rtype: tuple of ndarray
        """
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        data = self.buffer_data[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        return data[:, 0], data[:, 1]  # Return time and forces buffers

    def _read_device(self):
        """
        Routine for continuous reading of the force
        """
        while self.continuous_reading_flag:  # If flag for stoping data acquisition is not true
            if self.is_connected:  # If connected to force sensor
                reading = self.futek_dll.Normal_Data_Request(self.device_handle)  # Read current value
                if reading.isnumeric():  # If the value is valid
                    current_time = time.perf_counter()  # Get corresponding reading time
                    raw_force = np.float64(reading) - self.tare_register_value  # Update raw data
                    current_force = self.sensor_capacity * (raw_force - self.taring_force) / (
                            self.fullscale_value - self.offset)  # Compute current force
                    self.reading_thread_lock.acquire()  # Get multithreading lock
                    self.buffer_data[self.sample, :] = [current_time, current_force]
                    self.buffer_raw_data[self.sample, :] = [current_time, raw_force]
                    self.taring_buffer_raw_data[self.taring_sample, :] = [current_time, raw_force]
                    self.reading_thread_lock.release()  # Release data lock
                    self.sample += 1  # Increment sample counter
                    self.taring_sample += 1   
            else:  # If force sensor is not connected
                time.sleep(0.01)

    def corrected_force_with_stiffness(self, displacement, force):
        """
        Returns the corrected displacement given the stiffness of the sensor assembly
        Expected force in milli newton and displacement in m

        Class attribute sensor_stiffness have to be defined before the computation.
        Displacement and force have to be aligned to the same time using interpolation for example.

        :param displacement: vector with displacement in meter
        :param force: vector with force in mN
        """
        return displacement - force / self.sensor_stiffness

    def get_current_force(self):
        """
        Get last measured force

        :return: current value of the force
        :rtype: float
        """
        return self.buffer_data[self.sample-1, 1]

############################################################################################################

class ForcePlot(QWidget):
    """Widget for plotting the Force sensor"""
    def __init__(self, force_sensor_object: FutekSensor=None):
        """
        :param force_sensor_object: Force sensor object to display
        """
        super(ForcePlot, self).__init__()
        self.futek_sensor = force_sensor_object

        self.plotHistoryLength = 10 #s
        self.maxPlotHistoryLength = 10000000 #samples
        
        plot_layout = QHBoxLayout(self)
        plot_widget = pg.PlotWidget(self)
        force_plot = plot_widget.plotItem
        force_plot.setTitle("Force", bold=True)
        force_plot.setLabel('left', 'Force', units='N')
        force_plot.setLabel('bottom', 'Time', units='s')
        self.force_plot = force_plot.plot()
        plot_layout.addWidget(plot_widget)

    # ************************************************************************************************** #

    def plot_update(self, start_time):
        if self.futek_sensor.is_connected:
            epoch_time_force, force = self.futek_sensor.get_buffer()
            tplot = epoch_time_force - start_time

            if len(tplot) > self.maxPlotHistoryLength:
                    tplot = tplot[-self.maxPlotHistoryLength:]
                    force = force[-self.maxPlotHistoryLength:]

            if len(tplot)>0:
                use = tplot>tplot[-1]-self.plotHistoryLength
                self.force_plot.setData(tplot[use], force[use]/1000.0)

    def set_plot_history(self, history_length):
        self.plotHistoryLength = history_length

