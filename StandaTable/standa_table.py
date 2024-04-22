import ctypes
import logging
import time
from threading import Thread, Lock, RLock

import pyqtgraph as pg

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.gui_tools import create_qt_app_from_widget

if __name__ == '__main__':
    import pyximc
else:
    from . import pyximc
from PyQt6 import QtCore, QtWidgets, QtGui

from tools.data_tools import CircularDataBuffer # change according to your data buffer implementation

DEFAULT_BUFFER_LENGTH = 1000000


def check_connection(func):
    """
    Decorator for getting motor lock and checking motor is connected.

    :return: Decorated function or None
    """

    def is_connected_wrapper(*args):
        if args[0].is_connected:
            args[0].motor_lock.acquire()
            a = func(*args)
            args[0].motor_lock.release()
            if not args[0].result == pyximc.Result.Ok:
                logging.error("Error calling function : %s" % func.__name__)
            time.sleep(0.01)
            return a
        else:
            logging.warning("Motor not Connected")

    is_connected_wrapper.__doc__ = func.__doc__

    return is_connected_wrapper


class StandaTable():
    """
    Class for driving StandaTable controller.
    The position and speed might be different depending on which table you're using.
    The default scaling_factor is set to 1/2.5E-3 (one step is 2.5 micrometer)
    """
    DEBUG_MODE = 0

    def __init__(self, id=0):
        self.max_speed = 4  # Maximum speed X,Y,Z (mm/s)
        self.scaling_factor = 1 / 2.5E-3  # Scalng Factor mm/step
        self.x_pos = pyximc.get_position_t()
        self.pos = None
        self.speed = 0
        self.acceleration = 0
        self.deceleration = 0
        self.available_devices = []

        self.lib = pyximc.lib

        # State Flags
        self.continuous_reading_flag = False
        self.is_connected = False
        self.device_id = -1

        # Threading and continuous acquisition definitions
        self.reading_thread = Thread()  # Thread initialization
        self.data_lock = Lock()
        self.motor_lock = RLock()

        self.buffer_length = DEFAULT_BUFFER_LENGTH
        self.buffer_data = CircularDataBuffer((self.buffer_length, 2))

        # AutoConnect
        self.get_available_devices()
        self.connect(id)

    def get_available_devices(self):
        """Get Available devices list"""
        #        probe_flags = pyximc.EnumerateFlags.ENUMERATE_ALL_COM
        probe_flags = pyximc.EnumerateFlags.ENUMERATE_PROBE
        devenum = pyximc.lib.enumerate_devices(probe_flags, b"")

        dev_count = pyximc.lib.get_device_count(devenum)
        controller_name = pyximc.controller_name_t()
        self.available_devices = []
        for dev_ind in range(dev_count):
            enum_name = pyximc.lib.get_device_name(devenum, dev_ind)
            self.result = pyximc.lib.get_enumerate_device_controller_name(devenum, dev_ind,
                                                                          ctypes.byref(controller_name))
            if self.result == pyximc.Result.Ok:
                self.available_devices.append(enum_name)
        return self.available_devices

    def connect(self, index=0):
        """
        Connect to motor with the specified index.

        :param index: index of the motor
        :type index: int
        """
        self.close()
        if len(self.available_devices) > index:
            open_name = self.available_devices[index]
            if type(open_name) is str:
                open_name = open_name.encode()
            self.device_id = self.lib.open_device(open_name)
            if self.device_id > 0:
                self.is_connected = True
                self.start_reading()
        return self.is_connected

    @check_connection
    def is_moving(self):
        """
        Returns True if motor is moving.

        :return: True if motor is moving False otherwise
        :rtype: bool
        """
        status = self.get_status()
        if status:
            moving = status.MvCmdSts == 129
            return moving
        else:
            return False

    @check_connection
    def move(self, distance, udistance=0):
        """
        Moves to an absolute position distance
        :param distance: position in mm
        :param udistance: unimplemented, microstep displacement
        :return: True if success
        """
        self.result = self.lib.command_move(self.device_id, ctypes.c_int32(int(distance * self.scaling_factor)),
                                            ctypes.c_int16(int(udistance)))
        return self.result == 0

    @check_connection
    def move_relative(self, distance, udistance=0):
        """
        Move relatively from the current position.

        :param distance: distance in mm
        :param udistance: unimplemented, for microstep mode
        :return:
        """
        self.result = self.lib.command_movr(self.device_id, ctypes.c_int32(int(distance * self.scaling_factor)),
                                            ctypes.c_int16(int(udistance)))
        return self.result == 0

    @check_connection
    def right(self):
        """
        Starts moving the motor to the Right.
        Use stop to stop the table
        :return: True if success
        """
        self.result = self.lib.command_right(self.device_id)
        return self.result == 0

    @check_connection
    def left(self):
        """
        Starts moving the motor to the left.
        Use stop to stop the table.

        :return: True if success
        """
        self.result = self.lib.command_left(self.device_id)
        return self.result == 0

    @check_connection
    def stop(self):
        """
        Stops the motor

        :return: True if success
        """
        self.result = self.lib.command_stop(self.device_id)
        return self.result == 0

    @check_connection
    def home(self):
        """
        Go to home of the motor. Can't be stopped.

        :return: True if success
        """
        self.result = self.lib.command_home(self.device_id)
        return self.result == 0

    @check_connection
    def home_zero(self):
        """
        Go home and set zero position.

        :return: True if success
        """
        initial_speed = self.get_speed()
        self.set_speed(self.max_speed)
        self.result = self.lib.command_homezero(self.device_id)
        self.set_speed(initial_speed)
        return self.result == 0

    @check_connection
    def get_position(self):
        """
        Returns current position of the motor.

        :return: current position
        :rtype: float
        """
        self.x_pos = pyximc.get_position_t()
        self.result = self.lib.get_position(self.device_id, ctypes.byref(self.x_pos))
        if self.result == pyximc.Result.Ok:
            self.pos = (self.x_pos.Position + self.x_pos.uPosition / 360) / self.scaling_factor
        else:
            self.pos = None
        return self.pos

    @check_connection
    def wait_for_stop(self, timeout=30):
        """
        Blocking method to wait until motor stops.
        Will process Qt event to keep the gui responsive if an app is running.

        :param timeout: timeout in seconds, default is 30
        """
        t_0 = time.perf_counter()
        app = QtWidgets.QApplication.instance()
        while self.is_moving() and time.perf_counter() - t_0 < timeout:
            if app:
                app.processEvents()
            time.sleep(0.01)

    @check_connection
    def set_speed(self, speed):
        """
        Set motor speed in mm/s

        :param speed: speed in mm/s
        :type speed: float
        :return: True if success
        """
        mvst = pyximc.move_settings_t()  # Create move settings structure
        self.result = self.lib.get_move_settings(self.device_id,
                                                 ctypes.byref(mvst))  # Get current move settings from controller
        mvst.Speed = int(speed * self.scaling_factor)
        self.result = self.lib.set_move_settings(self.device_id, ctypes.byref(mvst))
        return self.result == 0

    @check_connection
    def set_acceleration(self, acceleration=None, deceleration=None):
        """
        Set motor acceleration/deceleration in mm/s^2

        :param acceleration: acceleration in mm/s^2
        :param deceleration: deceleration in mm/s^2
        :type acceleration: float
        :type deceleration: float
        :return: True if success
        """
        mvst = pyximc.move_settings_t()  # Create move settings structure
        self.result = self.lib.get_move_settings(self.device_id,
                                                 ctypes.byref(mvst))  # Get current move settings from controller
        if acceleration is not None:
            mvst.Accel = int(acceleration * self.scaling_factor)
        if deceleration is not None:
            mvst.Decel = int(deceleration * self.scaling_factor)
        self.result = self.lib.set_move_settings(self.device_id, ctypes.byref(mvst))
        return self.result == 0

    @check_connection
    def get_acceleration(self):
        """
        Get current acceleration and deceleration from controller.

        :return: (acceleration, deceleration) in mm/s^2
        """
        mvst = pyximc.move_settings_t()  # Create move settings structure
        self.result = self.lib.get_move_settings(self.device_id,
                                                 ctypes.byref(mvst))  # Get current move settings from controller
        return float(mvst.Accel) / self.scaling_factor, float(mvst.Decel) / self.scaling_factor

    @check_connection
    def get_speed(self):
        """
        Get current motor speed from controller.

        :return: Speed in mm/s
        """
        mvst = pyximc.move_settings_t()  # Create move settings structure
        self.result = self.lib.get_move_settings(self.device_id,
                                                 ctypes.byref(mvst))  # Get current move settings from controller
        self.speed = int(mvst.Speed)
        self.acceleration = int(mvst.Accel)
        self.deceleration = int(mvst.Decel)
        return mvst.Speed / self.scaling_factor

    def start_reading(self):
        """
        Routine for starting continuous position reading.
        """
        self.continuous_reading_flag = True  # Flag set to true
        self.buffer_data.clear()
        self.reading_thread = Thread()  # Thread for continuous reading
        self.reading_thread.run = self._read_device  # Method associated to thread
        self.reading_thread.start()  # Starting Thread

    def stop_reading(self):
        """
        Routine for stopping continuous position reading
        """
        self.continuous_reading_flag = False  # Set Flag to False
        if self.reading_thread.is_alive():
            self.reading_thread.join()

    def get_buffer(self, clear_buffer=True, initial_t=None):
        """
        Method for retrieving position buffer. clearBuffer=True causes the buffer to be reset

        :returns: time vector and position vector
        """
        self.data_lock.acquire()  # Get Data lock for multithreading
        data = self.buffer_data.copy()
        if initial_t:
            data[:, 0] -= data[0, 0]
            data[:, 0] += initial_t
        if clear_buffer:  # If buffer reset
            self.buffer_data.clear()
        self.data_lock.release()  # Release lock
        return data[:, 0], data[:, 1]  # Return time and positions

    def get_current_position(self):
        """
        Get current position from the continuous reading buffer.
        Continuous reading needs to be started using start_reading method.

        :return: Current position in mm
        """
        position = self.buffer_data[-1, 1]
        return position

    def close(self):
        """
        Close device communication.
        """
        self.stop_reading()
        if self.is_connected:
            pyximc.lib.close(ctypes.byref(ctypes.cast(self.device_id, ctypes.POINTER(ctypes.c_int))))
            self.is_connected = False

    def get_library_version(self):
        """
        Retrieve current version of ximc library
        """
        sbuf = ctypes.create_string_buffer(64)
        self.lib.ximc_version(sbuf)
        self.library_version = sbuf.raw.decode().rstrip("\0")

    @check_connection
    def get_info(self):
        """Get device info:
            properties:
                Manufacturer
                ManufacturerId
                ProductDescription
                Major
                Minor
                Release
            :Usage:

                >>> table = StandaTable()
                >>> info = table.get_info()
                >>> print(info.Manufacturer)

            :return: Device information as c_types structure
        """
        x_device_information = pyximc.device_information_t()
        self.result = self.lib.get_device_information(self.device_id, ctypes.byref(x_device_information))
        if self.result == pyximc.Result.Ok:
            return x_device_information
        else:
            return None

    @check_connection
    def get_status(self):
        """
        Get current Status of the device. Accessible parameters are:
            - MoveSts
            - MvCmdSts
            - PWRSts
            - EncSts
            - WindSts
            - CurPosition
            - uCurPosition
            - uCurSpeed
            - Ipwr
            - Upwr
            - Iusb
            - Uusb
            - CurT
            - Flags
            - GPIOFlags
            - CmdBufFreeSpace
        Refer to programming manual to understand parameters.

        :Usage:
            >>> status = table.get_status()
            >>> print(status.Ipwr)

        """
        self.x_status = pyximc.status_t()
        self.result = self.lib.get_status(self.device_id, ctypes.byref(self.x_status))
        if self.result == pyximc.Result.Ok:
            return self.x_status
        else:
            return None

    @check_connection
    def get_serial_number(self):
        """
        Get serial number of the device.

        :return: Serial number
        """
        x_serial = ctypes.c_uint()
        self.result = self.lib.get_serial_number(self.device_id, ctypes.byref(x_serial))
        if self.result == pyximc.Result.Ok:
            return x_serial.value
        else:
            return None

    @check_connection
    def set_microstep_mode_256(self):
        """
        Set microstep mode to 256
        """
        # Create engine settings structure
        eng = pyximc.engine_settings_t()
        # Get current engine settings from controller
        self.result = self.lib.get_engine_settings(self.device_id, ctypes.byref(eng))
        # Print command return status. It will be 0 if all is OK
        # Change MicrostepMode parameter to MICROSTEP_MODE_FRAC_256
        # (use MICROSTEP_MODE_FRAC_128, MICROSTEP_MODE_FRAC_64 ... for other microstep modes)
        eng.MicrostepMode = pyximc.MicrostepMode.MICROSTEP_MODE_FRAC_256
        # Write new engine settings to controller
        self.result = self.lib.set_engine_settings(self.device_id, ctypes.byref(eng))
        # Print command return status. It will be 0 if all is OK
        return self.result == pyximc.Result.Ok

    def _read_device(self):
        """
        Method for continuous reading
        """
        while self.continuous_reading_flag and self.is_connected:  # While Flag is true and Table is connected
            try:
                pos = self.get_position()  # Read current position
            except:
                pos = None
            if isinstance(pos, (int, float)):
                self.data_lock.acquire()  # Set Lock for data manipulation
                current_time = time.perf_counter()  # Current time
                self.buffer_data.append([current_time, pos])
                self.data_lock.release()  # Release data lock

    def __del__(self):
        self.stop_reading()
        self.close()
        time.sleep(0.1)


class StandaTableWidget(QtWidgets.QWidget):
    graphHistory = 10000  # Number of point for graph history
    buttonMaxWidth = 150

    def __init__(self, Motor: StandaTable, display_graph=False):
        super(StandaTableWidget, self).__init__()
        self.setMaximumWidth(self.buttonMaxWidth)
        self.display_graph = display_graph
        self.Motor = Motor  # Motor controller object
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.buttonLayout = QtWidgets.QFormLayout()
        self.mainLayout.addLayout(self.buttonLayout, stretch=0)
        # self.buttonLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        title = QtWidgets.QLabel("Motor Control")
        title.setFont(QtGui.QFont('Arial', 15, weight=10))
        self.buttonLayout.addRow(title)
        self.connectButton = QtWidgets.QPushButton("Connect")
        # self.connectButton.setMaximumWidth(self.buttonMaxWidth)
        self.buttonLayout.addRow(self.connectButton)
        self.connectButton.setCheckable(True)
        if (self.Motor.is_connected):
            self.connectButton.setChecked(True)
            self.connectButton.setText("Connected")
        self.connectButton.clicked.connect(self.connectCallback)

        homeButton = QtWidgets.QPushButton("HOME")
        self.buttonLayout.addRow(homeButton)
        homeButton.released.connect(self.Motor.home_zero)

        upButton = QtWidgets.QPushButton("UP")
        upButton.pressed.connect(self.Motor.left)
        upButton.released.connect(self.Motor.stop)
        downButton = QtWidgets.QPushButton("DOWN")
        downButton.pressed.connect(self.Motor.right)
        downButton.released.connect(self.Motor.stop)
        self.buttonLayout.addRow(upButton, downButton)

        stopButton = QtWidgets.QPushButton("STOP")
        self.buttonLayout.addRow(stopButton)
        stopButton.released.connect(self.Motor.stop)

        self.positionEdit = QtWidgets.QLineEdit("0.0")
        self.goToPosition = QtWidgets.QPushButton("To Pos")
        self.goToPosition.clicked.connect(self.goToPositionCallback)
        self.buttonLayout.addRow(self.positionEdit, self.goToPosition)

        self.speedSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.buttonLayout.addRow("Speed", self.speedSlider)
        self.speedSlider.setMaximum(self.Motor.max_speed * 100)
        cSpeed = self.Motor.get_speed()
        if cSpeed: self.speedSlider.setValue(int(cSpeed * 100))

        self.speedSlider.valueChanged.connect(self.speedSliderCallback)

        self.position_label = QtWidgets.QLabel("0")
        self.buttonLayout.addRow("Current Pos", self.position_label)
        if self.display_graph:
            graph = pg.PlotWidget(self, title="Position")
            graph.setMinimumWidth(600)
            graph.setLabel('left', 'Position', units='mm')
            graph.setLabel('bottom', 'Time', units='s')
            self.mainLayout.addWidget(graph, stretch=100)
            self.positionPlot = graph.plot()
        # else:
        #     self.mainLayout.addStretch(1)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.plotUpdate)
        self.timer.setInterval(100)
        self.startDisplayTimer()

    def goToPositionCallback(self):
        target_position = float(self.positionEdit.text())
        self.Motor.move(target_position, 0)

    def connectCallback(self):
        if self.Motor.is_connected:
            self.Motor.close()
        else:
            self.Motor.get_available_devices()
            self.Motor.connect()
        self.connectButton.setChecked(self.Motor.is_connected)
        if self.Motor.is_connected:
            self.speedSlider.setValue(int(self.Motor.get_speed() * 100))
            self.connectButton.setText("Disconnect")
        else:
            self.connectButton.setText("Connect")

    def speedSliderCallback(self):
        self.Motor.set_speed(float(self.speedSlider.value()) / 100)

    def plotUpdate(self):
        t, pos = self.Motor.get_buffer(clear_buffer=False)
        if pos.size > 0:
            self.position_label.setText("%.3f" % pos[-1])
        if self.display_graph:
            self.positionPlot.setData(t[-self.graphHistory:], pos[-self.graphHistory:])
        if not self.Motor.is_connected:
            self.connectButton.setChecked(self.Motor.is_connected)
            self.connectButton.setText("Connect")

    #        QtWidgets.QApplication.processEvents()
    def startDisplayTimer(self):
        self.timer.start()

    def stopDisplayTimer(self):
        self.timer.stop()

def interface():
    APP_NAME = "Standa motor control"
    APP = QtWidgets.QApplication([])
    motor = StandaTable()
    MW = StandaTableWidget(motor)
    APP = create_qt_app_from_widget(APP, MW, APP_NAME)


if __name__ == '__main__':
    interface()
