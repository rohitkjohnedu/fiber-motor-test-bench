import argparse
import logging
import os
import sys
import time
import warnings
from threading import Thread, RLock

import numpy as np
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore
from scipy.signal import savgol_filter

sys.path.append(os.getcwd())


from tools.data_tools import CircularDataBuffer
from tools.gui_tools import get_application_path, create_qt_app_from_widget



DEFAULT_BUFFER_LENGTH = 100000
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
    if QtWidgets.QApplication.instance() and QtWidgets.QApplication.activeWindow():
        QtWidgets.QMessageBox.warning(QtWidgets.QApplication.activeWindow(), "Force Sensor error",
                                      error)  # The box is displayed
    else:  # Otherwise
        logging.error(error)  # Printing in the console


class FutekSensor:
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
        self.buffer_raw_data = CircularDataBuffer((self.buffer_length, 2))
        self.buffer_data = CircularDataBuffer((self.buffer_length, 2))

        self.continuous_reading_flag = False
        # Thread initialization for continuous reading
        self.reading_thread = Thread(target=self._read_device)
        self.reading_thread_lock = RLock()  # Lock for multithreading

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
                self.start_reading()  # Start continuous reading
                logging.info(f"Futek force sensor connected. Sensor capacity is {self.sensor_capacity:.1f} mN")
        except:  # If exception
            _error_display(f"Device Error {self.futek_dll.DeviceStatus} \nImpossible to connect force sensor.")

        return self.is_connected  # Returns connection state

    def get_sensor_load(self):
        """
        Get sensor full load from internal register

        :return: Sensor capacity in mN
        :type: float
        """
        sensor_capacity_register = self.futek_dll.Get_Internal_Register(self.device_handle, 5)
        sensor_capacity_register = float(sensor_capacity_register)
        sensor_capacity_register_details = self.futek_dll.Get_Internal_Register(self.device_handle, 6)
        sensor_capacity_register_details = int(sensor_capacity_register_details)

        decimal_point_code = sensor_capacity_register_details >> 16
        unit_code = int((sensor_capacity_register_details & 0b1111111100000000) >> 8)
        direction_code = int(sensor_capacity_register_details & 0b11111111)

        sensor_capacity_register *= 10 ** (-float(decimal_point_code))

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
                    self.fullscale_value = float(fullscale_value)  # It is saved
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
                    self.offset = float(offset)  # Save the value
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
                    self.tare_register_value = float(tare_register_value)  # Save the value
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
            self.get_buffer(clear_buffer=True)  # Reset buffer
            time.sleep(0.05)  # Wait for Measurement
            self.taring_force = np.mean(self.buffer_raw_data[:, 1])  # Get mean value
            self.get_buffer(clear_buffer=True)  # Reset buffer
        else:
            _error_display("Impossible to tare : Force sensor not connected")

    def start_reading(self):
        """
        Start continuous reading of the force
        """
        self.stop_reading()
        self.buffer_data.clear()
        self.buffer_raw_data.clear()
        self.continuous_reading_flag = True  # Set flag to true
        self.reading_thread = Thread(target=self._read_device)  # Thread initialization for continuous reading
        self.reading_thread.start()

    def stop_reading(self):
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
        self.buffer_data.clear()
        self.buffer_raw_data.clear()

    def get_buffer(self, clear_buffer=True, initial_t=None):
        """
        Get current force buffer from continuous reading.
        clear_buffer reset the buffer.
        initial_t aligns time data to the given value
        (initial_t = 0 make time vector to start at 0)

        :param clear_buffer: If set to True, clear the buffer after reading
        :type clear_buffer: bool
        :param initial_t: Align time buffer to a specific time (if set to zero, time will start from zero,
        otherwise, if None, it'll take the value of the syster counter.
        :type initial_t: float
        :return: tuple with time vector as first element and force data
        :rtype: tuple of ndarray
        """
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        data = self.buffer_data.copy()
        if clear_buffer:  # If flag clearBuffer set to true
            self.clear_buffer()
        if initial_t is not None:
            data[:, 0] -= data[0, 0]
            data[:, 0] += initial_t
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
                    raw_force = float(reading) - self.tare_register_value  # Update raw data
                    current_force = self.sensor_capacity * (raw_force - self.taring_force) / (
                            self.fullscale_value - self.offset)  # Compute current force
                    self.reading_thread_lock.acquire()  # Get multithreading lock
                    self.buffer_data.append([current_time, current_force])
                    self.buffer_raw_data.append([current_time, raw_force])
                    self.reading_thread_lock.release()  # Release data lock
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

    def disconnect(self):
        """
        Disconnect force sensor
        """
        self.stop_reading()  # Stop continuous reading thread
        if self.device_handle:
            # Calling Dll close method
            self.futek_dll.Close_Device_Connection(self.device_handle)
        return self.is_connected

    def get_current_force(self):
        """
        Get last measured force

        :return: current value of the force
        :rtype: float
        """
        return self.buffer_data[-1, 1]

    def __del__(self):
        """
        Class Destructor
        """
        self.stop_reading()
        self.disconnect()


# class FutekSensorDaqmx():
#     def __init__(self, daq_mx: LMTS.instruments.daqmx.DaqMx, channel=0, sensitivity=1, max_force=1, amplifier_gain=495,
#                  excitation_voltage=10):
#         """
#         Force sensor management object for FUTEK force sensor.
#         Requires a NI-Daqmx card and the daqmx lmts library.

#         :param daq_mx: Daqmx object
#         :param channel: channel number for the force channel
#         :param sensitivity: force sensor sensitivity [V/V]
#         :param max_force: force sensor max force
#         :param amplifier_gain: conditioning electronics amplifier gain
#         :param excitation_voltage: conditioning electronics excitation voltage.
#         """
#         self.daqmx = daq_mx
#         self.channel = channel

#         # Sensor profile
#         self.sensor_sensitivity = sensitivity
#         self.max_force = max_force
#         # Conditionning electronics
#         self.amplifier_gain = amplifier_gain
#         self.excitation_voltage = excitation_voltage
#         # Taring props
#         self.tare_force = 0
#         self.taring_time = 0.1
#         # Filtering props
#         # self.filtering_time = 0.03
#         self.filtering_time = 0
#         self.filtering_window = 11
#         self.lock = RLock()
#         self.has_been_tested = False

#     @property
#     def is_connected(self):
#         if not self.has_been_tested:
#             self.has_been_tested = self.wait_for_sensor_input()
#         if not self.daqmx.acquisition_thread.is_running or not self.has_been_tested:
#             warnings.warn("Futek sensor: The daqmx continuous acquisition is not running, please start first.")
#             return False
#         return True

#     def tare(self):
#         """
#         Tare force sensor.
#         """
#         self.lock.acquire()
#         self.set_filtering(self.filtering_time)
#         self.clear_buffer()
#         time.sleep(self.taring_time)
#         time_data, force_data = self.get_buffer(clear_buffer=True, ignore_tare=True)
#         self.tare_force = force_data.mean()
#         self.lock.release()

#     def clear_buffer(self):
#         """
#         Clear buffer.
#         Will clear all daqmx buffer.
#         """
#         self.daqmx.clear_buffer()

#     def set_filtering(self, filtering_time):
#         """
#         Set the time for the moving average filter.
#         A value of zero will disable filtering.
#         """
#         self.filtering_time = filtering_time
#         fech = self.daqmx.get_task_sampling_rate(self.daqmx.acquisition_task)
#         window = filtering_time * fech
#         if window>0 and window % 2 == 0:
#             window += 1
#         self.filtering_window = int(window)

#     def filter_force(self, force):
#         """
#         Filter force routine.
#         """
#         if self.filtering_window > 0 and len(force)>self.filtering_window:
#             return savgol_filter(force, self.filtering_window, polyorder=1)
#         else:
#             return force

#     def voltage_to_force(self, voltage, ignore_tare=False):
#         """
#         Convert sensed voltage to force.
#         """
#         factor = 1 / (self.excitation_voltage * self.amplifier_gain * self.sensor_sensitivity) * self.max_force*1e3
#         if ignore_tare:
#             force = voltage * factor
#         else:
#             force = voltage * factor - self.tare_force
#         return self.filter_force(force)

#     def get_buffer(self, clear_buffer=False, ignore_tare=False):
#         """
#         Get force buffer converted to milli-newton.
#         """
#         self.lock.acquire()
#         if not self.daqmx.acquisition_thread.is_running:
#             return None
#         force_data = self.daqmx.get_buffer(clear_buffer=clear_buffer)[:, self.channel * 2:self.channel * 2 + 2].copy()
#         force_data[:, 1] = self.voltage_to_force(force_data[:, 1], ignore_tare)
#         self.lock.release()
#         return force_data[:,0],force_data[:,1]

#     def set_sensor_range(self, max_force):
#         self.max_force = max_force

#     def get_current_force(self):
#         if self.is_connected:
#             return self.get_buffer()[1]
#         else:
#             return np.nan

#     def wait_for_sensor_input(self):
#         print("WAITING FOR Sensor input")
#         self.clear_buffer()
#         box = None
#         if QtWidgets.QApplication.instance() and QtWidgets.QApplication.activeWindow():
#             box = QtWidgets.QDialog()
#             box.setWindowTitle("Waiting for force sensor input")
#             box_layout = QtWidgets.QVBoxLayout()
#             box.setLayout(box_layout)
#             # box_layout.addWidget(FutekSensorWidget(self,controls=False))
#             box_layout.addWidget(QtWidgets.QLabel("Safety: Press or tap on the force sensor to confirm it can sense."))
#             box.show()
#         else:  # Otherwise
#             logging.error("Safety: Press or tap on the force sensor to confirm it can sense.")  # Printing in the console
#         sensor_moves = False
#         threshold = 5/100
#         timeout = 10
#         t_0 = time.perf_counter()
#         while time.perf_counter()-t_0<timeout:
#             QtWidgets.QApplication.processEvents()
#             time_f, force = self.get_buffer()
#             if len(force)>1:
#                 sensor_moves = (force.max()-force.min())/(self.max_force*1e3)>threshold
#                 if sensor_moves: break
#             time.sleep(0.01)
#         if box:
#             box.close()
#         return sensor_moves


class FutekSensorWidget(QtWidgets.QWidget):
    """Widget for controlling Force sensor"""
    plotHistoryLength = 10000

    def __init__(self, force_sensor_object: FutekSensor, controls=True):
        """
        :param force_sensor_object: Force sensor object to display
        """
        super(FutekSensorWidget, self).__init__()
        self.futek_sensor = force_sensor_object

        main_layout = QtWidgets.QHBoxLayout(self)

        connect_layout = QtWidgets.QFormLayout()
        if controls:
            main_layout.addLayout(connect_layout)
        connect_layout.addRow(QtWidgets.QLabel("Force Sensor"))
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.released.connect(self._connect_button_callback)
        connect_layout.addRow(self.connect_button)
        tare_button = QtWidgets.QPushButton("Tare")
        tare_button.clicked.connect(self._tare_button_callback)
        connect_layout.addRow(tare_button)
        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(self.futek_sensor.clear_buffer)
        connect_layout.addRow(clear_button)
        continuous_acq = QtWidgets.QPushButton("Continuous display")

        continuous_acq.setCheckable(True)
        continuous_acq.setChecked(True)
        continuous_acq.toggled.connect(self._continuous_acq_button_callback)
        connect_layout.addRow(continuous_acq)
        save_data_button = QtWidgets.QPushButton("Save Data")
        save_data_button.clicked.connect(self._save_data_button_callback)
        connect_layout.addRow(save_data_button)

        self.plot_force_widget = pg.PlotWidget(self, title="Force sensor reading")
        self.plot_force_widget.setMinimumWidth(600)
        self.plot_force_widget.setMinimumHeight(250)
        self.plot_force_widget.setLabel('left', 'Force', units='mN')
        self.plot_force_widget.setLabel('bottom', 'Time', units='s')
        self.plot_force = self.plot_force_widget.plot()
        main_layout.addWidget(self.plot_force_widget)

        self.plot_update_timer = QtCore.QTimer(self)
        self.plot_update_timer.timeout.connect(self.plot_update)
        self.plot_update_timer.setInterval(50)

        self.init_widget()

    def init_widget(self):
        if self.futek_sensor.is_connected:
            self.connect_button.setText("Disconnect")
            self.start_display_timer()
        else:
            self.connect_button.setText("Connect")
            self.stop_display_timer()

    def _save_data_button_callback(self):
        t, pos = self.futek_sensor.get_buffer(clear_buffer=False)
        f = QtWidgets.QFileDialog.getSaveFileName()
        if f[0] != '':
            np.savetxt(f[0], np.transpose([t, pos]))

    def _continuous_acq_button_callback(self):
        sender = self.sender()
        if sender.isChecked():
            self.start_display_timer()
        else:
            self.stop_display_timer()

    def _connect_button_callback(self):
        self.connect_button.setEnabled(False)
        if not self.futek_sensor.is_connected:
            connect_query = self.futek_sensor.connect()
            if connect_query:
                self.connect_button.setText("Disconnect")
                self.start_display_timer()
        else:
            connect_query = self.futek_sensor.disconnect()
            if not connect_query:
                self.connect_button.setText("Connect")
            self.stop_display_timer()
        self.connect_button.setEnabled(True)

    def _tare_button_callback(self):
        self.futek_sensor.tare()

    def plot_update(self):
        if self.futek_sensor.is_connected:
            time_force, force = self.futek_sensor.get_buffer(clear_buffer=False)
            self.plot_force.setData(time_force[-self.plotHistoryLength:], force[-self.plotHistoryLength:])

    def start_display_timer(self):
        self.plot_update_timer.start()

    def stop_display_timer(self):
        self.plot_update_timer.stop()

    def closeEvent(self, event):
        self.stop_display_timer()
        event.accept()


def interface():
    APP_NAME = "Futek force sensor"
    APP = QtWidgets.QApplication(sys.argv)
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-sn', '--serial-number', default=577685, type=int)
    arguments = parser.parse_args()
    FS_OBJECT = FutekSensor(serial_number=arguments.serial_number)  # Default serial number is 577685
    WIDGET = FutekSensorWidget(FS_OBJECT)
    APP = create_qt_app_from_widget(APP, WIDGET, APP_NAME)



if __name__ == '__main__':
    interface()
