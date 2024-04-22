import ctypes
import os.path
import platform
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(os.path.abspath(sys.executable))
elif __file__:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.environ['PATH'] = application_path + os.pathsep + os.environ['PATH']


def ximc_shared_lib():
    if platform.system() == "Linux":
        return ctypes.CDLL("libximc.so")
    elif platform.system() == "FreeBSD":
        return ctypes.CDLL("libximc.so")
    elif platform.system() == "Darwin":
        return ctypes.CDLL("libximc.framework/libximc")
    elif platform.system() == "Windows":
        return ctypes.WinDLL(Path(application_path).joinpath("libximc.dll").absolute().as_posix())
    else:
        return None


lib = ximc_shared_lib()


# Common declarations

class Result:
    Ok = 0
    Error = -1
    NotImplemented = -2
    ValueError = -3
    NoDevice = -4


class calibration_t(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('A', ctypes.c_double), ('MicrostepMode', ctypes.c_uint)]


class device_enumeration_t(ctypes.LittleEndianStructure):
    pass


class device_network_information_t(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('ipv4', ctypes.c_uint32), ('nodename', ctypes.c_char * 16), ('axis_state', ctypes.c_uint),
                ('locker_username', ctypes.c_char * 16), ('locker_nodename', ctypes.c_char * 16),
                ('locked_time', ctypes.c_ulonglong), ]


# Clarify function types

lib.enumerate_devices.restype = ctypes.POINTER(device_enumeration_t)
lib.get_device_name.restype = ctypes.c_char_p


# ---------------------------
# BEGIN OF GENERATED code
# ---------------------------
class EnumerateFlags:
    ENUMERATE_PROBE = 0x01
    ENUMERATE_ALL_COM = 0x02
    ENUMERATE_NETWORK = 0x04


class MoveState:
    MOVE_STATE_MOVING = 0x01
    MOVE_STATE_TARGET_SPEED = 0x02
    MOVE_STATE_ANTIPLAY = 0x04


class ControllerFlags:
    EEPROM_PRECEDENCE = 0x01


class PowerState:
    PWR_STATE_UNKNOWN = 0x00
    PWR_STATE_OFF = 0x01
    PWR_STATE_NORM = 0x03
    PWR_STATE_REDUCT = 0x04
    PWR_STATE_MAX = 0x05


class StateFlags:
    STATE_CONTR = 0x00003F
    STATE_ERRC = 0x000001
    STATE_ERRD = 0x000002
    STATE_ERRV = 0x000004
    STATE_EEPROM_CONNECTED = 0x000010
    STATE_IS_HOMED = 0x000020
    STATE_SECUR = 0x73FFC0
    STATE_ALARM = 0x000040
    STATE_CTP_ERROR = 0x000080
    STATE_POWER_OVERHEAT = 0x000100
    STATE_CONTROLLER_OVERHEAT = 0x000200
    STATE_OVERLOAD_POWER_VOLTAGE = 0x000400
    STATE_OVERLOAD_POWER_CURRENT = 0x000800
    STATE_OVERLOAD_USB_VOLTAGE = 0x001000
    STATE_LOW_USB_VOLTAGE = 0x002000
    STATE_OVERLOAD_USB_CURRENT = 0x004000
    STATE_BORDERS_SWAP_MISSET = 0x008000
    STATE_LOW_POWER_VOLTAGE = 0x010000
    STATE_H_BRIDGE_FAULT = 0x020000
    STATE_CURRENT_MOTOR_BITS = 0x0C0000
    STATE_CURRENT_MOTOR0 = 0x000000
    STATE_CURRENT_MOTOR1 = 0x040000
    STATE_CURRENT_MOTOR2 = 0x080000
    STATE_CURRENT_MOTOR3 = 0x0C0000
    STATE_WINDING_RES_MISMATCH = 0x100000
    STATE_ENCODER_FAULT = 0x200000
    STATE_MOTOR_CURRENT_LIMIT = 0x400000


class GPIOFlags:
    STATE_DIG_SIGNAL = 0xFFFF
    STATE_RIGHT_EDGE = 0x0001
    STATE_LEFT_EDGE = 0x0002
    STATE_BUTTON_RIGHT = 0x0004
    STATE_BUTTON_LEFT = 0x0008
    STATE_GPIO_PINOUT = 0x0010
    STATE_GPIO_LEVEL = 0x0020
    STATE_HALL_A = 0x0040
    STATE_HALL_B = 0x0080
    STATE_HALL_C = 0x0100
    STATE_BRAKE = 0x0200
    STATE_REV_SENSOR = 0x0400
    STATE_SYNC_INPUT = 0x0800
    STATE_SYNC_OUTPUT = 0x1000
    STATE_ENC_A = 0x2000
    STATE_ENC_B = 0x4000


class EncodeStatus:
    ENC_STATE_ABSENT = 0x00
    ENC_STATE_UNKNOWN = 0x01
    ENC_STATE_MALFUNC = 0x02
    ENC_STATE_REVERS = 0x03
    ENC_STATE_OK = 0x04


class WindStatus:
    WIND_A_STATE_ABSENT = 0x00
    WIND_A_STATE_UNKNOWN = 0x01
    WIND_A_STATE_MALFUNC = 0x02
    WIND_A_STATE_OK = 0x03
    WIND_B_STATE_ABSENT = 0x00
    WIND_B_STATE_UNKNOWN = 0x10
    WIND_B_STATE_MALFUNC = 0x20
    WIND_B_STATE_OK = 0x30


class MvcmdStatus:
    MVCMD_NAME_BITS = 0x3F
    MVCMD_UKNWN = 0x00
    MVCMD_MOVE = 0x01
    MVCMD_MOVR = 0x02
    MVCMD_LEFT = 0x03
    MVCMD_RIGHT = 0x04
    MVCMD_STOP = 0x05
    MVCMD_HOME = 0x06
    MVCMD_LOFT = 0x07
    MVCMD_SSTP = 0x08
    MVCMD_ERROR = 0x40
    MVCMD_RUNNING = 0x80


class EngineFlags:
    ENGINE_REVERSE = 0x01
    ENGINE_CURRENT_AS_RMS = 0x02
    ENGINE_MAX_SPEED = 0x04
    ENGINE_ANTIPLAY = 0x08
    ENGINE_ACCEL_ON = 0x10
    ENGINE_LIMIT_VOLT = 0x20
    ENGINE_LIMIT_CURR = 0x40
    ENGINE_LIMIT_RPM = 0x80


class MicrostepMode:
    MICROSTEP_MODE_FULL = 0x01
    MICROSTEP_MODE_FRAC_2 = 0x02
    MICROSTEP_MODE_FRAC_4 = 0x03
    MICROSTEP_MODE_FRAC_8 = 0x04
    MICROSTEP_MODE_FRAC_16 = 0x05
    MICROSTEP_MODE_FRAC_32 = 0x06
    MICROSTEP_MODE_FRAC_64 = 0x07
    MICROSTEP_MODE_FRAC_128 = 0x08
    MICROSTEP_MODE_FRAC_256 = 0x09


class EngineType:
    ENGINE_TYPE_NONE = 0x00
    ENGINE_TYPE_DC = 0x01
    ENGINE_TYPE_2DC = 0x02
    ENGINE_TYPE_STEP = 0x03
    ENGINE_TYPE_TEST = 0x04
    ENGINE_TYPE_BRUSHLESS = 0x05


class DriverType:
    DRIVER_TYPE_DISCRETE_FET = 0x01
    DRIVER_TYPE_INTEGRATE = 0x02
    DRIVER_TYPE_EXTERNAL = 0x03


class PowerFlags:
    POWER_REDUCT_ENABLED = 0x01
    POWER_OFF_ENABLED = 0x02
    POWER_SMOOTH_CURRENT = 0x04


class SecureFlags:
    ALARM_ON_DRIVER_OVERHEATING = 0x01
    LOW_UPWR_PROTECTION = 0x02
    H_BRIDGE_ALERT = 0x04
    ALARM_ON_BORDERS_SWAP_MISSET = 0x08
    ALARM_FLAGS_STICKING = 0x10
    USB_BREAK_RECONNECT = 0x20


class PositionFlags:
    SETPOS_IGNORE_POSITION = 0x01
    SETPOS_IGNORE_ENCODER = 0x02


class FeedbackType:
    FEEDBACK_ENCODER = 0x01
    FEEDBACK_ENCODERHALL = 0x03
    FEEDBACK_EMF = 0x04
    FEEDBACK_NONE = 0x05


class FeedbackFlags:
    FEEDBACK_ENC_REVERSE = 0x01
    FEEDBACK_HALL_REVERSE = 0x02
    FEEDBACK_ENC_TYPE_BITS = 0xC0
    FEEDBACK_ENC_TYPE_AUTO = 0x00
    FEEDBACK_ENC_TYPE_SINGLE_ENDED = 0x40
    FEEDBACK_ENC_TYPE_DIFFERENTIAL = 0x80


class SyncInFlags:
    SYNCIN_ENABLED = 0x01
    SYNCIN_INVERT = 0x02
    SYNCIN_GOTOPOSITION = 0x04


class SyncOutFlags:
    SYNCOUT_ENABLED = 0x01
    SYNCOUT_STATE = 0x02
    SYNCOUT_INVERT = 0x04
    SYNCOUT_IN_STEPS = 0x08
    SYNCOUT_ONSTART = 0x10
    SYNCOUT_ONSTOP = 0x20
    SYNCOUT_ONPERIOD = 0x40


class ExtioSetupFlags:
    EXTIO_SETUP_OUTPUT = 0x01
    EXTIO_SETUP_INVERT = 0x02


class ExtioModeFlags:
    EXTIO_SETUP_MODE_IN_BITS = 0x0F
    EXTIO_SETUP_MODE_IN_NOP = 0x00
    EXTIO_SETUP_MODE_IN_STOP = 0x01
    EXTIO_SETUP_MODE_IN_PWOF = 0x02
    EXTIO_SETUP_MODE_IN_MOVR = 0x03
    EXTIO_SETUP_MODE_IN_HOME = 0x04
    EXTIO_SETUP_MODE_IN_ALARM = 0x05
    EXTIO_SETUP_MODE_OUT_BITS = 0xF0
    EXTIO_SETUP_MODE_OUT_OFF = 0x00
    EXTIO_SETUP_MODE_OUT_ON = 0x10
    EXTIO_SETUP_MODE_OUT_MOVING = 0x20
    EXTIO_SETUP_MODE_OUT_ALARM = 0x30
    EXTIO_SETUP_MODE_OUT_MOTOR_ON = 0x40
    EXTIO_SETUP_MODE_OUT_MOTOR_FOUND = 0x50


class BorderFlags:
    BORDER_IS_ENCODER = 0x01
    BORDER_STOP_LEFT = 0x02
    BORDER_STOP_RIGHT = 0x04
    BORDERS_SWAP_MISSET_DETECTION = 0x08


class EnderFlags:
    ENDER_SWAP = 0x01
    ENDER_SW1_ACTIVE_LOW = 0x02
    ENDER_SW2_ACTIVE_LOW = 0x04


class BrakeFlags:
    BRAKE_ENABLED = 0x01
    BRAKE_ENG_PWROFF = 0x02


class ControlFlags:
    CONTROL_MODE_BITS = 0x03
    CONTROL_MODE_OFF = 0x00
    CONTROL_MODE_JOY = 0x01
    CONTROL_MODE_LR = 0x02
    CONTROL_BTN_LEFT_PUSHED_OPEN = 0x04
    CONTROL_BTN_RIGHT_PUSHED_OPEN = 0x08


class JoyFlags:
    JOY_REVERSE = 0x01


class CtpFlags:
    CTP_ENABLED = 0x01
    CTP_BASE = 0x02
    CTP_ALARM_ON_ERROR = 0x04
    REV_SENS_INV = 0x08
    CTP_ERROR_CORRECTION = 0x10


class HomeFlags:
    HOME_DIR_FIRST = 0x001
    HOME_DIR_SECOND = 0x002
    HOME_MV_SEC_EN = 0x004
    HOME_HALF_MV = 0x008
    HOME_STOP_FIRST_BITS = 0x030
    HOME_STOP_FIRST_REV = 0x010
    HOME_STOP_FIRST_SYN = 0x020
    HOME_STOP_FIRST_LIM = 0x030
    HOME_STOP_SECOND_BITS = 0x0C0
    HOME_STOP_SECOND_REV = 0x040
    HOME_STOP_SECOND_SYN = 0x080
    HOME_STOP_SECOND_LIM = 0x0C0
    HOME_USE_FAST = 0x100


class UARTSetupFlags:
    UART_PARITY_BITS = 0x03
    UART_PARITY_BIT_EVEN = 0x00
    UART_PARITY_BIT_ODD = 0x01
    UART_PARITY_BIT_SPACE = 0x02
    UART_PARITY_BIT_MARK = 0x03
    UART_PARITY_BIT_USE = 0x04
    UART_STOP_BIT = 0x08


class MotorTypeFlags:
    MOTOR_TYPE_UNKNOWN = 0x00
    MOTOR_TYPE_STEP = 0x01
    MOTOR_TYPE_DC = 0x02
    MOTOR_TYPE_BLDC = 0x03


class EncoderSettingsFlags:
    ENCSET_DIFFERENTIAL_OUTPUT = 0x001
    ENCSET_PUSHPULL_OUTPUT = 0x004
    ENCSET_INDEXCHANNEL_PRESENT = 0x010
    ENCSET_REVOLUTIONSENSOR_PRESENT = 0x040
    ENCSET_REVOLUTIONSENSOR_ACTIVE_HIGH = 0x100


class MBSettingsFlags:
    MB_AVAILABLE = 0x01
    MB_POWERED_HOLD = 0x02


class TSSettingsFlags:
    TS_TYPE_BITS = 0x07
    TS_TYPE_UNKNOWN = 0x00
    TS_TYPE_THERMOCOUPLE = 0x01
    TS_TYPE_SEMICONDUCTOR = 0x02
    TS_AVAILABLE = 0x08


class LSFlags:
    LS_ON_SW1_AVAILABLE = 0x01
    LS_ON_SW2_AVAILABLE = 0x02
    LS_SW1_ACTIVE_LOW = 0x04
    LS_SW2_ACTIVE_LOW = 0x08
    LS_SHORTED = 0x10


class feedback_settings_t(ctypes.Structure):
    _fields_ = [("IPS", ctypes.c_uint), ("FeedbackType", ctypes.c_uint), ("FeedbackFlags", ctypes.c_uint),
                ("HallSPR", ctypes.c_uint), ("HallShift", ctypes.c_int), ]


class home_settings_t(ctypes.Structure):
    _fields_ = [("FastHome", ctypes.c_uint), ("uFastHome", ctypes.c_uint), ("SlowHome", ctypes.c_uint),
                ("uSlowHome", ctypes.c_uint), ("HomeDelta", ctypes.c_int), ("uHomeDelta", ctypes.c_int),
                ("HomeFlags", ctypes.c_uint), ]


class home_settings_calb_t(ctypes.Structure):
    _fields_ = [("FastHome", ctypes.c_float), ("SlowHome", ctypes.c_float), ("HomeDelta", ctypes.c_float),
                ("HomeFlags", ctypes.c_uint), ]


class move_settings_t(ctypes.Structure):
    _fields_ = [("Speed", ctypes.c_uint), ("uSpeed", ctypes.c_uint), ("Accel", ctypes.c_uint), ("Decel", ctypes.c_uint),
                ("AntiplaySpeed", ctypes.c_uint), ("uAntiplaySpeed", ctypes.c_uint), ]


class move_settings_calb_t(ctypes.Structure):
    _fields_ = [("Speed", ctypes.c_float), ("Accel", ctypes.c_float), ("Decel", ctypes.c_float),
                ("AntiplaySpeed", ctypes.c_float), ]


class engine_settings_t(ctypes.Structure):
    _fields_ = [("NomVoltage", ctypes.c_uint), ("NomCurrent", ctypes.c_uint), ("NomSpeed", ctypes.c_uint),
                ("uNomSpeed", ctypes.c_uint), ("EngineFlags", ctypes.c_uint), ("Antiplay", ctypes.c_int),
                ("MicrostepMode", ctypes.c_uint), ("StepsPerRev", ctypes.c_uint), ]


class engine_settings_calb_t(ctypes.Structure):
    _fields_ = [("NomVoltage", ctypes.c_uint), ("NomCurrent", ctypes.c_uint), ("NomSpeed", ctypes.c_float),
                ("EngineFlags", ctypes.c_uint), ("Antiplay", ctypes.c_float), ("MicrostepMode", ctypes.c_uint),
                ("StepsPerRev", ctypes.c_uint), ]


class entype_settings_t(ctypes.Structure):
    _fields_ = [("EngineType", ctypes.c_uint), ("DriverType", ctypes.c_uint), ]


class power_settings_t(ctypes.Structure):
    _fields_ = [("HoldCurrent", ctypes.c_uint), ("CurrReductDelay", ctypes.c_uint), ("PowerOffDelay", ctypes.c_uint),
                ("CurrentSetTime", ctypes.c_uint), ("PowerFlags", ctypes.c_uint), ]


class secure_settings_t(ctypes.Structure):
    _fields_ = [("LowUpwrOff", ctypes.c_uint), ("CriticalIpwr", ctypes.c_uint), ("CriticalUpwr", ctypes.c_uint),
                ("CriticalT", ctypes.c_uint), ("CriticalIusb", ctypes.c_uint), ("CriticalUusb", ctypes.c_uint),
                ("MinimumUusb", ctypes.c_uint), ("Flags", ctypes.c_uint), ]


class edges_settings_t(ctypes.Structure):
    _fields_ = [("BorderFlags", ctypes.c_uint), ("EnderFlags", ctypes.c_uint), ("LeftBorder", ctypes.c_int),
                ("uLeftBorder", ctypes.c_int), ("RightBorder", ctypes.c_int), ("uRightBorder", ctypes.c_int), ]


class edges_settings_calb_t(ctypes.Structure):
    _fields_ = [("BorderFlags", ctypes.c_uint), ("EnderFlags", ctypes.c_uint), ("LeftBorder", ctypes.c_float),
                ("RightBorder", ctypes.c_float), ]


class pid_settings_t(ctypes.Structure):
    _fields_ = [("KpU", ctypes.c_uint), ("KiU", ctypes.c_uint), ("KdU", ctypes.c_uint), ("Kpf", ctypes.c_float),
                ("Kif", ctypes.c_float), ("Kdf", ctypes.c_float), ]


class sync_in_settings_t(ctypes.Structure):
    _fields_ = [("SyncInFlags", ctypes.c_uint), ("ClutterTime", ctypes.c_uint), ("Position", ctypes.c_int),
                ("uPosition", ctypes.c_int), ("Speed", ctypes.c_uint), ("uSpeed", ctypes.c_uint), ]


class sync_in_settings_calb_t(ctypes.Structure):
    _fields_ = [("SyncInFlags", ctypes.c_uint), ("ClutterTime", ctypes.c_uint), ("Position", ctypes.c_float),
                ("Speed", ctypes.c_float), ]


class sync_out_settings_t(ctypes.Structure):
    _fields_ = [("SyncOutFlags", ctypes.c_uint), ("SyncOutPulseSteps", ctypes.c_uint), ("SyncOutPeriod", ctypes.c_uint),
                ("Accuracy", ctypes.c_uint), ("uAccuracy", ctypes.c_uint), ]


class sync_out_settings_calb_t(ctypes.Structure):
    _fields_ = [("SyncOutFlags", ctypes.c_uint), ("SyncOutPulseSteps", ctypes.c_uint), ("SyncOutPeriod", ctypes.c_uint),
                ("Accuracy", ctypes.c_float), ]


class extio_settings_t(ctypes.Structure):
    _fields_ = [("EXTIOSetupFlags", ctypes.c_uint), ("EXTIOModeFlags", ctypes.c_uint), ]


class brake_settings_t(ctypes.Structure):
    _fields_ = [("t1", ctypes.c_uint), ("t2", ctypes.c_uint), ("t3", ctypes.c_uint), ("t4", ctypes.c_uint),
                ("BrakeFlags", ctypes.c_uint), ]


class control_settings_t(ctypes.Structure):
    _fields_ = [("MaxSpeed", ctypes.c_uint * 10), ("uMaxSpeed", ctypes.c_uint * 10), ("Timeout", ctypes.c_uint * 9),
                ("MaxClickTime", ctypes.c_uint), ("Flags", ctypes.c_uint), ("DeltaPosition", ctypes.c_int),
                ("uDeltaPosition", ctypes.c_int), ]


class control_settings_calb_t(ctypes.Structure):
    _fields_ = [("MaxSpeed", ctypes.c_float * 10), ("Timeout", ctypes.c_uint * 9), ("MaxClickTime", ctypes.c_uint),
                ("Flags", ctypes.c_uint), ("DeltaPosition", ctypes.c_float), ]


class joystick_settings_t(ctypes.Structure):
    _fields_ = [("JoyLowEnd", ctypes.c_uint), ("JoyCenter", ctypes.c_uint), ("JoyHighEnd", ctypes.c_uint),
                ("ExpFactor", ctypes.c_uint), ("DeadZone", ctypes.c_uint), ("JoyFlags", ctypes.c_uint), ]


class ctp_settings_t(ctypes.Structure):
    _fields_ = [("CTPMinError", ctypes.c_uint), ("CTPFlags", ctypes.c_uint), ]


class uart_settings_t(ctypes.Structure):
    _fields_ = [("Speed", ctypes.c_uint), ("UARTSetupFlags", ctypes.c_uint), ]


class calibration_settings_t(ctypes.Structure):
    _fields_ = [("CSS1_A", ctypes.c_float), ("CSS1_B", ctypes.c_float), ("CSS2_A", ctypes.c_float),
                ("CSS2_B", ctypes.c_float), ("FullCurrent_A", ctypes.c_float), ("FullCurrent_B", ctypes.c_float), ]


class controller_name_t(ctypes.Structure):
    _fields_ = [("ControllerName", ctypes.c_char * 17), ("CtrlFlags", ctypes.c_uint), ]


class nonvolatile_memory_t(ctypes.Structure):
    _fields_ = [("UserData", ctypes.c_uint * 7), ]


class command_add_sync_in_action_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_int), ("uPosition", ctypes.c_int), ("Time", ctypes.c_uint), ]


class command_add_sync_in_action_calb_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_float), ("Time", ctypes.c_uint), ]


class get_position_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_int), ("uPosition", ctypes.c_int), ("EncPosition", ctypes.c_longlong), ]


class get_position_calb_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_float), ("EncPosition", ctypes.c_longlong), ]


class set_position_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_int), ("uPosition", ctypes.c_int), ("EncPosition", ctypes.c_longlong),
                ("PosFlags", ctypes.c_uint), ]


class set_position_calb_t(ctypes.Structure):
    _fields_ = [("Position", ctypes.c_float), ("EncPosition", ctypes.c_longlong), ("PosFlags", ctypes.c_uint), ]


class status_t(ctypes.Structure):
    _fields_ = [("MoveSts", ctypes.c_uint), ("MvCmdSts", ctypes.c_uint), ("PWRSts", ctypes.c_uint),
                ("EncSts", ctypes.c_uint), ("WindSts", ctypes.c_uint), ("CurPosition", ctypes.c_int),
                ("uCurPosition", ctypes.c_int), ("EncPosition", ctypes.c_longlong), ("CurSpeed", ctypes.c_int),
                ("uCurSpeed", ctypes.c_int), ("Ipwr", ctypes.c_int), ("Upwr", ctypes.c_int), ("Iusb", ctypes.c_int),
                ("Uusb", ctypes.c_int), ("CurT", ctypes.c_int), ("Flags", ctypes.c_uint), ("GPIOFlags", ctypes.c_uint),
                ("CmdBufFreeSpace", ctypes.c_uint), ]


class status_calb_t(ctypes.Structure):
    _fields_ = [("MoveSts", ctypes.c_uint), ("MvCmdSts", ctypes.c_uint), ("PWRSts", ctypes.c_uint),
                ("EncSts", ctypes.c_uint), ("WindSts", ctypes.c_uint), ("CurPosition", ctypes.c_float),
                ("EncPosition", ctypes.c_longlong), ("CurSpeed", ctypes.c_float), ("Ipwr", ctypes.c_int),
                ("Upwr", ctypes.c_int), ("Iusb", ctypes.c_int), ("Uusb", ctypes.c_int), ("CurT", ctypes.c_int),
                ("Flags", ctypes.c_uint), ("GPIOFlags", ctypes.c_uint), ("CmdBufFreeSpace", ctypes.c_uint), ]


class measurements_t(ctypes.Structure):
    _fields_ = [("Speed", ctypes.c_int * 25), ("Error", ctypes.c_int * 25), ("Length", ctypes.c_uint), ]


class chart_data_t(ctypes.Structure):
    _fields_ = [("WindingVoltageA", ctypes.c_int), ("WindingVoltageB", ctypes.c_int), ("WindingVoltageC", ctypes.c_int),
                ("WindingCurrentA", ctypes.c_int), ("WindingCurrentB", ctypes.c_int), ("WindingCurrentC", ctypes.c_int),
                ("Pot", ctypes.c_uint), ("Joy", ctypes.c_uint), ("DutyCycle", ctypes.c_int), ]


class device_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 5), ("ManufacturerId", ctypes.c_char * 3),
                ("ProductDescription", ctypes.c_char * 9), ("Major", ctypes.c_uint), ("Minor", ctypes.c_uint),
                ("Release", ctypes.c_uint), ]


class serial_number_t(ctypes.Structure):
    _fields_ = [("SN", ctypes.c_uint), ("Key", ctypes.c_ubyte * 32), ("Major", ctypes.c_uint), ("Minor", ctypes.c_uint),
                ("Release", ctypes.c_uint), ]


class analog_data_t(ctypes.Structure):
    _fields_ = [("A1Voltage_ADC", ctypes.c_uint), ("A2Voltage_ADC", ctypes.c_uint), ("B1Voltage_ADC", ctypes.c_uint),
                ("B2Voltage_ADC", ctypes.c_uint), ("SupVoltage_ADC", ctypes.c_uint), ("ACurrent_ADC", ctypes.c_uint),
                ("BCurrent_ADC", ctypes.c_uint), ("FullCurrent_ADC", ctypes.c_uint), ("Temp_ADC", ctypes.c_uint),
                ("Joy_ADC", ctypes.c_uint), ("Pot_ADC", ctypes.c_uint), ("L5_ADC", ctypes.c_uint),
                ("H5_ADC", ctypes.c_uint), ("A1Voltage", ctypes.c_int), ("A2Voltage", ctypes.c_int),
                ("B1Voltage", ctypes.c_int), ("B2Voltage", ctypes.c_int), ("SupVoltage", ctypes.c_int),
                ("ACurrent", ctypes.c_int), ("BCurrent", ctypes.c_int), ("FullCurrent", ctypes.c_int),
                ("Temp", ctypes.c_int), ("Joy", ctypes.c_int), ("Pot", ctypes.c_int), ("L5", ctypes.c_int),
                ("H5", ctypes.c_int), ("deprecated", ctypes.c_uint), ("R", ctypes.c_int), ("L", ctypes.c_int), ]


class debug_read_t(ctypes.Structure):
    _fields_ = [("DebugData", ctypes.c_ubyte * 128), ]


class debug_write_t(ctypes.Structure):
    _fields_ = [("DebugData", ctypes.c_ubyte * 128), ]


class stage_name_t(ctypes.Structure):
    _fields_ = [("PositionerName", ctypes.c_char * 17), ]


class stage_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 17), ("PartNumber", ctypes.c_char * 25), ]


class stage_settings_t(ctypes.Structure):
    _fields_ = [("LeadScrewPitch", ctypes.c_float), ("Units", ctypes.c_char * 9), ("MaxSpeed", ctypes.c_float),
                ("TravelRange", ctypes.c_float), ("SupplyVoltageMin", ctypes.c_float),
                ("SupplyVoltageMax", ctypes.c_float), ("MaxCurrentConsumption", ctypes.c_float),
                ("HorizontalLoadCapacity", ctypes.c_float), ("VerticalLoadCapacity", ctypes.c_float), ]


class motor_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 17), ("PartNumber", ctypes.c_char * 25), ]


class motor_settings_t(ctypes.Structure):
    _fields_ = [("MotorType", ctypes.c_uint), ("ReservedField", ctypes.c_uint), ("Poles", ctypes.c_uint),
                ("Phases", ctypes.c_uint), ("NominalVoltage", ctypes.c_float), ("NominalCurrent", ctypes.c_float),
                ("NominalSpeed", ctypes.c_float), ("NominalTorque", ctypes.c_float), ("NominalPower", ctypes.c_float),
                ("WindingResistance", ctypes.c_float), ("WindingInductance", ctypes.c_float),
                ("RotorInertia", ctypes.c_float), ("StallTorque", ctypes.c_float), ("DetentTorque", ctypes.c_float),
                ("TorqueConstant", ctypes.c_float), ("SpeedConstant", ctypes.c_float),
                ("SpeedTorqueGradient", ctypes.c_float), ("MechanicalTimeConstant", ctypes.c_float),
                ("MaxSpeed", ctypes.c_float), ("MaxCurrent", ctypes.c_float), ("MaxCurrentTime", ctypes.c_float),
                ("NoLoadCurrent", ctypes.c_float), ("NoLoadSpeed", ctypes.c_float), ]


class encoder_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 17), ("PartNumber", ctypes.c_char * 25), ]


class encoder_settings_t(ctypes.Structure):
    _fields_ = [("MaxOperatingFrequency", ctypes.c_float), ("SupplyVoltageMin", ctypes.c_float),
                ("SupplyVoltageMax", ctypes.c_float), ("MaxCurrentConsumption", ctypes.c_float), ("PPR", ctypes.c_uint),
                ("EncoderSettings", ctypes.c_uint), ]


class hallsensor_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 17), ("PartNumber", ctypes.c_char * 25), ]


class hallsensor_settings_t(ctypes.Structure):
    _fields_ = [("MaxOperatingFrequency", ctypes.c_float), ("SupplyVoltageMin", ctypes.c_float),
                ("SupplyVoltageMax", ctypes.c_float), ("MaxCurrentConsumption", ctypes.c_float),
                ("PPR", ctypes.c_uint), ]


class gear_information_t(ctypes.Structure):
    _fields_ = [("Manufacturer", ctypes.c_char * 17), ("PartNumber", ctypes.c_char * 25), ]


class gear_settings_t(ctypes.Structure):
    _fields_ = [("ReductionIn", ctypes.c_float), ("ReductionOut", ctypes.c_float), ("RatedInputTorque", ctypes.c_float),
                ("RatedInputSpeed", ctypes.c_float), ("MaxOutputBacklash", ctypes.c_float),
                ("InputInertia", ctypes.c_float), ("Efficiency", ctypes.c_float), ]


class accessories_settings_t(ctypes.Structure):
    _fields_ = [("MagneticBrakeInfo", ctypes.c_char * 25), ("MBRatedVoltage", ctypes.c_float),
                ("MBRatedCurrent", ctypes.c_float), ("MBTorque", ctypes.c_float), ("MBSettings", ctypes.c_uint),
                ("TemperatureSensorInfo", ctypes.c_char * 25), ("TSMin", ctypes.c_float), ("TSMax", ctypes.c_float),
                ("TSGrad", ctypes.c_float), ("TSSettings", ctypes.c_uint), ("LimitSwitchesSettings", ctypes.c_uint), ]


class init_random_t(ctypes.Structure):
    _fields_ = [("key", ctypes.c_ubyte * 16), ]


class globally_unique_identifier_t(ctypes.Structure):
    _fields_ = [("UniqueID0", ctypes.c_uint), ("UniqueID1", ctypes.c_uint), ("UniqueID2", ctypes.c_uint),
                ("UniqueID3", ctypes.c_uint), ]


class command_change_motor_t(ctypes.Structure):
    _fields_ = [
        ("Motor", ctypes.c_uint), ]  # -------------------------  # END OF GENERATED code  # -------------------------


# vim: set ft=python
