import time
from threading import Thread, Lock, Event, RLock

import numpy as np
from serial import Serial
from serial.tools.list_ports import comports
from collections.abc import Iterable

SOFTWARE_VERSION = 1.1
#--------------------------------
DEFAULT_BUFFER_LENGTH = 10000000
#--------------------------------
INITIAL_PCB_PARAMETERS = {
            'name': '',
            'hw_ver': 0.0,
            'fw_ver': '',
            'max_hv': 0.0,
            'min_hv': 0.0,
            'max_freq': 0.0,
            'min_freq': 0.0,
            'min_pulse': 0.0,
        }


def check_connection(func):
    """Decorator for checking connection and acquiring multithreading lock"""
    def is_connected_wrapper(*args):
        args[0].serial_com_lock.acquire()
        if args[0].ser.is_open:
            res = func(*args)
            args[0].serial_com_lock.release()
            return res
        else:
            print("HVPS not connected - not calling %s method" % func.__name__)
            args[0].serial_com_lock.release()
            return None
    is_connected_wrapper.__doc__ = func.__doc__
    return is_connected_wrapper


def _channel_to_channel_key(channel):
    if type(channel) == int:
        channel_key = pow(2, channel)
    elif isinstance(channel, Iterable):
        channel_key = sum(pow(2, r) for r in channel)
    else:
        print("[ERR] channel must be int or list")
        return False
    return channel_key


class HvpsDevice:
    def __init__(self, port_name=None, baudrate=115200, timeout=0.5):

        self.serial_com_lock = Lock()
        self.ser = Serial()
        self.command_buffer = []
        self.start_time = time.perf_counter_ns()
        self.pcb_parameters = INITIAL_PCB_PARAMETERS
        self.cont_reading = False

        # ---------------------------------------------------------------------------------------------------------------------------- #
        # New 
        self.buffer_length = DEFAULT_BUFFER_LENGTH
        self.variables_number = 11
        self.buffer_data = np.zeros((self.buffer_length, self.variables_number), dtype=np.float64)
        self.sample = 0
        self.read_samples = 0
        self.reading_thread_lock = RLock()

        self.dynamic_modulation = False
        self.dynamic = False
        self.switch = 0
        # ---------------------------------------------------------------------------------------------------------------------------- #

        self.buffer_lock = Lock()

        self.last_confirmation_match = ''
        self.confirmed = Event()

        self.exit_reading = Event()
        self.reading_thread = Thread(target=self._reading_thread)

        if port_name is not None:
            self.connect(port_name, baudrate, timeout)

    def detect(self):
        """Detects available serial ports"""
        if not self.ser.is_open:
            self.disconnect()
        ports = [{'device': port.device, 'description': port.description, 'product': port.product, 'manufacturer': port.manufacturer} for port in comports()]
        boards = []
        for port in ports:
            if port['manufacturer'] is None or not port['manufacturer'].startswith("Silicon Labs"):
                continue
            params = self.connect(port['device'])
            if params:
                boards.append({**port, **params})
                self.disconnect()
        return boards

    def auto_connect(self):
        """Detects available serial ports and connects to the first one found"""
        ports = self.detect()
        if len(ports) > 0:
            self.connect(ports[0]['device'])
        else:
            print("No High voltage board found")
        return self

    def connect(self, port_name, baudrate=115200, timeout=0.5):
        if self.ser.is_open:
            self.disconnect()
        try:
            self.serial_com_lock.acquire()
            self.ser.close()
            self.ser = Serial(port=port_name, baudrate=baudrate, timeout=timeout)
        except Exception as e:
            print("Error opening serial port: %s" % e)
            return False
        finally:
            self.serial_com_lock.release()

        self.serial_com_lock.acquire()
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.serial_com_lock.release()

        self.pcb_parameters = self.get_parameters()
        if self.pcb_parameters is False:
            self.ser.close()
            return False
        print("Connected to %s version %s" % (self.pcb_parameters['name'], self.pcb_parameters['hw_ver']))
        self.start_thread()
        return self.pcb_parameters

    def disconnect(self):
        """Closes connection with the HVPS"""
        self.emergency_stop()
        self.exit_reading.set()
        if self.reading_thread.is_alive():
            self.reading_thread.join()
        self.serial_com_lock.acquire()
        self.ser.close()
        self.serial_com_lock.release()
        print(f"Disconnected High voltage board {self.pcb_parameters['name']} version {self.pcb_parameters['hw_ver']}")
        return True

    def get_parameters(self):
        pcb_parameters = {}
        self.serial_com_lock.acquire()
        self.ser.reset_input_buffer()
        self.serial_com_lock.release()
        self._write_serial("QPRM\r")
        patterns_and_keys = [
            ("[PRM] PCB \t\t ", "name"),
            ("[PRM] HW Version \t v", "hw_ver"),
            ("[PRM] FW Version \t ", "fw_ver"),
            ("[PRM] MAX HV    (V)\t ", "max_hv"),
            ("[PRM] MIN HV    (V)\t ", "min_hv"),
            ("[PRM] MAX FREQ  (Hz)\t ", "max_freq"),
            ("[PRM] MIN FREQ  (Hz)\t ", "min_freq"),
            ("[PRM] MIN PULSE (us)\t ", "min_pulse")
        ]

        lines = []
        start_time = time.time()
        while time.time() - start_time < 2: # timeout after 2 seconds
            if not self.ser.is_open:
                break
            if self.ser.in_waiting == 0:
                time.sleep(0.002)
                continue
            line = self._read_serial()
            if line.startswith("[PRM]"):
                lines.append(line)
            if len(lines) == len(patterns_and_keys):
                break
        if len(lines) < len(patterns_and_keys):
            print("[ERR] Could not retrieve all parameters")
            return False

        for i, (pattern, key) in enumerate(patterns_and_keys):
            value = lines[i].replace(pattern, "").replace("\n", "")
            # convert in float only for numeric values
            if key in ('hw_ver', 'max_hv', 'min_hv', 'max_freq', 'min_freq', 'min_pulse'):
                value = float(value)
            pcb_parameters[key] = value
        # check compatibility between hardware/firmware and software
        if pcb_parameters['hw_ver'] != SOFTWARE_VERSION:
            print("[ERR.] SOFTWARE NOT COMPATIBLE WITH BOARD {}!".format(self.pcb_prm['name']))
            print("Please to use another board!")
        self.pcb_parameters = pcb_parameters
        return pcb_parameters

    def start_recording(self):
        self.stop_recording()
        self.cont_reading = True
        self.clear_buffer()
        self.command_buffer.clear()
        self.reading_thread = Thread(target=self._reading_thread)
        self.exit_reading.clear()
        self.reading_thread.start()

    def stop_recording(self):
        self.cont_reading = False
        self.exit_reading.set()
        if self.reading_thread.is_alive():
            self.reading_thread.join()
    
    def clear_buffer(self):
        self.buffer_data = np.zeros((self.buffer_length, self.variables_number), dtype=np.float64)
        self.sample = 0

    def get_buffer(self):
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        data = self.buffer_data[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        return data  # Return time and positions
    
    def start_thread(self):
        if not self.reading_thread.is_alive():
            self.clear_buffer()
            self.command_buffer.clear()
            self.reading_thread = Thread(target=self._reading_thread)
            self.exit_reading.clear()
            self.reading_thread.start()

    def _reading_thread(self):
        waiting_for_answer = False
        waiting_for_answer_time = time.perf_counter()
        while not self.exit_reading.wait(timeout=0.002) and self.is_open:
            if not waiting_for_answer:
                if len(self.command_buffer) > 0:
                    self._write_serial(self.command_buffer.pop(0))
                else:
                    self._write_serial("Moni 1\r")
                waiting_for_answer = True
                waiting_for_answer_time = time.perf_counter()

            # -------------------------------------------------------------------------------------------------------------- #
            if self.dynamic_modulation:
                next_step_time = self.modulation_start_time + self.modulation_counter/self.modulation_step_freq
                if next_step_time-time.perf_counter() < 0.00001:
                    # Moving forward
                    if self.modulation_freq_state == 0:
                        # print("Moving forward")
                        self.write(f"SMx 5 2 {0} {180} {180}\r") # A-D
                        self.write(f"SMx 5 0\r")                 # Start
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 2
                    elif self.modulation_freq_state == 1:
                        # print("A-D")
                        self.write(f"SMx 5 2 {0} {180} {180}\r") # A-D
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 2
                    elif self.modulation_freq_state == 2:
                        # print("B-E")
                        self.write(f"SMx 5 2 {180} {0} {180}\r") # B-E
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 3
                    elif self.modulation_freq_state == 3:
                        # print("C-F")
                        self.write(f"SMx 5 2 {180} {180} {0}\r") # C-F
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 1

                    # Moving backward
                    if self.modulation_freq_state == 10:
                        # print("Moving backward")
                        self.write(f"SMx 5 2 {0} {180} {180}\r") # A-D
                        self.write(f"SMx 5 0\r")                 # Start
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 12
                    elif self.modulation_freq_state == 11:
                        self.write(f"SMx 5 2 {0} {180} {180}\r") # A-D
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 12
                    elif self.modulation_freq_state == 12:
                        self.write(f"SMx 5 2 {180} {180} {0}\r") # C-F
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 13
                    elif self.modulation_freq_state == 13:
                        self.write(f"SMx 5 2 {180} {0} {180}\r") # B-E
                        self._wait_for_confirmation("[SM5]")
                        self.modulation_freq_state = 11

                    self.modulation_counter += 1
            # ----------------------------------------------------------------------------- #
            line = self._read_serial()
            if line.startswith("[moni]") and self.cont_reading is False:
                    waiting_for_answer = False
            elif line.startswith("[moni]") and self.cont_reading is True:
                    data = line.split(",")
                    # --------------------------------------------------------------------- #
                    t_save = int(data[1])
                    hv_set = np.float64(data[2])
                    hv_vm = np.float64(data[5])
                    hv_err = np.float64(data[2]) - np.float64(data[5])
                    # --------------------------------------------------------------------- #
                    lv_set = np.float64(data[3])
                    lv_vm = np.float64(data[4])
                    lv_err = np.float64(data[3]) - np.float64(data[4])
                    # --------------------------------------------------------------------- #
                    cm_val_w1 = np.float64(data[7])/1e6 
                    cm_val_w2 = np.float64(data[8])/1e6
                    cm_val_w3 = np.float64(data[9])/1e6
                    # --------------------------------------------------------------------- #
                    self.buffer_lock.acquire()
                    epoch_time = time.perf_counter()
                    self.buffer_data[self.sample,:] = [epoch_time, t_save,
                                                       hv_set, hv_vm, hv_err,
                                                       lv_set, lv_vm, lv_err, 
                                                       cm_val_w1, cm_val_w2, cm_val_w3]
                    self.buffer_lock.release()
                    self.sample += 1
                    waiting_for_answer = False
            elif not line.startswith(">") and len(line) > 1:
                    cleaned_line = line.strip().replace("\n", "").replace("\r", "")
                    if cleaned_line.startswith(self.last_confirmation_match):
                        self.confirmed.set()
                        self.last_confirmation_match = ''
                        waiting_for_answer = False
            elif time.perf_counter() - waiting_for_answer_time > 0.5:
                    print("Timeout waiting for answer")
                    waiting_for_answer = False

    def get_new_data(self):
        self.reading_thread_lock.acquire()  # Get multithreading lock to avoir data buffer modification
        if self.read_samples - 500 > 0:
            data = self.buffer_data[self.read_samples - 500:self.sample,:]
        else:
            data = self.buffer_data[0:self.sample,:]
        self.reading_thread_lock.release()  # Release lock
        self.read_samples = self.sample
        return data

    def _wait_for_confirmation(self, match, timeout=0.5):
        if not self.ser.is_open:
            return False
        self.last_confirmation_match = match
        self.confirmed.clear()
        if not self.confirmed.wait(timeout=timeout):
            print(f"Timeout waiting for {match}")
            return False
        return True

    @check_connection
    def _write_serial(self, cmd):
        to_send = bytearray(cmd, encoding="utf-8")
        try:
            self.ser.write(to_send)
        except:
            self.ser.close()
            print("Error writing HVPS cmd: %s" % cmd)
            return False
        # print(f'delay={(time.perf_counter_ns() - self.start_time)/1e9:0.6f} s :: wrote {cmd}')
        # self.start_time = time.perf_counter_ns()
        return True

    @check_connection
    def _read_serial(self):  # reads a line on the serial port and removes the end of line characters
        try:
            line = self.ser.readline()
        except:
            self.ser.close()
            line = b""
            print("Error reading HVPS")
        # print(f'delay={(time.perf_counter_ns() - self.start_time)/1e9:0.6f} s :: read {line.decode("utf-8")}')
        # self.start_time = time.perf_counter_ns()
        return line.decode("utf-8")

    def write(self, cmd):
        self.command_buffer.append(cmd)

    def try_reconnect(self):
        print("[INFO] trying to reconnect to the board")
        self.ser.close()
        try:
            self.ser.open()
            self.ser.reset_input_buffer()
            print("[INFO] reconnected to the board")
        except Exception as err_connection:
            print(f"[ERR] connection failed: {err_connection}")
            pass

    @property
    def is_open(self):
        return self.ser.isOpen()

    def emergency_stop(self):
        self.start_thread()
        self.write("EStop\r")
        return self._wait_for_confirmation("[EStop]")

    def voltage_stop(self):
        self.write("SHV 0\r")
        return self._wait_for_confirmation("[HV]")

    def set_voltage(self, voltage = 0):
        if voltage == 0:
            self.start_thread()
            self.write(f"SHV 0\r")
        elif (voltage >= self.pcb_parameters['min_hv']) and (voltage <= self.pcb_parameters['max_hv']):
            self.start_thread()
            self.write(f"SHV {voltage}\r")
        else:
            print(f"\n[ERR] Please respect voltage range [{self.pcb_parameters['min_hv']}; {self.pcb_parameters['max_hv']}] V")
            return False
        return self._wait_for_confirmation("[HV]")

    def hb_stop(self, channel):
        channel_key = _channel_to_channel_key(channel)
        self.write(f"CMx 1 {channel_key}\r")
        return self._wait_for_confirmation("[CM1]")

    def hb_stop_multi(self):
        self.write("CMx 3 0\r")
        return self._wait_for_confirmation("[CM3]")
    
    def hb_stop_shift(self):
        self.start_thread()
        self.write("CMx 5 0\r")
        return self._wait_for_confirmation("[CM5]")

    def hb_set(self, channel, freq=1, pos_duty=50, phase_shift=None, step_freq=None, direction=None):
        """
        Set the output switches in a half bridge with parameters at the channel_key.

        Parameters:
        channel (int or list): The channel number or a list of channel numbers (starting with 0).
        freq (float, optional): The frequency of the burst. Default is 0.
        pos_duty (float, optional): The positive duty cycle. Default is 50.
        phase_shift (float, optional): The phase shift. Default is None.

        Returns:
        bool: True if the operation is successful, False otherwise.
        """
        channel_key = _channel_to_channel_key(channel)
        if not (self.pcb_parameters['min_freq'] <= freq <= self.pcb_parameters['max_freq']):
            print(f"[ERR] Frequency range: [{self.pcb_parameters['min_freq']} - {self.pcb_parameters['max_freq']}] Hz")
            return False
        pos_pulse_width = float(10 * (pos_duty / freq) * 1000)
        if not (0 <= pos_duty <= 100):
            print(f"[ERR] Positive duty cycle range: [0 - 100] °")
            return False
        elif pos_pulse_width < self.pcb_parameters['min_pulse']:
            print(f"[ERR] Positive pulse width: {pos_pulse_width} us < {self.pcb_parameters['min_pulse']} us")
            return False
        # ---------------------------------------------------------------------------------------------------------------------------- #
        if isinstance(channel, Iterable):
            # print("Multi channel")
            if phase_shift is not None:
                # print("phase_shift is not None")
                # Static with modulation
                if isinstance(phase_shift, Iterable):
                    # print("Static with modulation")
                    ph_shift1, ph_shift2, ph_shift3 = phase_shift
                    # print(ph_shift1, ph_shift2, ph_shift3)
                    check_1 = 0 <= ph_shift1 <= 360
                    check_2 = 0 <= ph_shift2 <= 360
                    check_3 = 0 <= ph_shift3 <= 360
                    if not (check_1 and check_2 and check_3):
                        print(f"[ERR] Phase shift range: [0 - 360] °")
                        return False
                    # ---------------------------------------------------------------------------------------------------------- #
                    self.write(f"SMx 5 1 {channel_key} {freq} {pos_duty}\r")
                    self.write(f"SMx 5 2 {ph_shift1} {ph_shift2} {ph_shift3}\r")
                    self.write(f"SMx 5 0\r")
                    return self._wait_for_confirmation("[SM5]")
                # -------------------------------------------------------------------------------------------------------------- #
                # Dynamic with no modulation
                else:
                    # print("Dynamic with no modulation")
                    self.write(f"SMx 3 {channel_key} {freq} {pos_duty} 0 0 {phase_shift}\r") # DC=50%, ph_shift is 120 or 240
                    return self._wait_for_confirmation("[SM3]")
            # ------------------------------------------------------------------------------------------------------------------ #
            # Dynamic with modulation (not possible yet)
            else:
                # print("Dynamic with modulation")
                if not (0 <= step_freq <= 1000):
                    print(f"[ERR] Step frequency range: [0 - 1000] Hz")
                    return False
                self.modulation_step_freq = 3*step_freq
                if not freq >= self.modulation_step_freq:
                    print(f"[ERR] Modulation frequency must be greater than {self.modulation_step_freq} Hz")
                    return False
                self.write(f"SMx 5 1 {channel_key} {freq} {pos_duty}\r")
                if direction == "Forward":
                    self.modulation_freq_state = 10
                elif direction == "Backward":
                    self.modulation_freq_state = 0
                self.modulation_counter = 0
                self.modulation_start_time = time.perf_counter()
                self.dynamic_modulation = True
                return True
        # ---------------------------------------------------------------------------------------------------------------------------- #
        # Static with no modulation
        else:
            # print("Single channel")
            # DC voltage
            if (freq == 1) or (pos_duty == 100):
                self.write(f"SMx 1 {channel_key} 1 100\r")
            # AC voltage
            else:
                self.write(f"SMx 1 {channel_key} {freq} {pos_duty} 0 0 0\r") # is not used in the program 
            return self._wait_for_confirmation("[SM1]")

