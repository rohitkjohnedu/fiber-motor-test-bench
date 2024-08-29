from serial import Serial
from serial.tools.list_ports import comports
from threading import Thread, Lock, Event, RLock

class Smac:
    def __init__(self, port_name=None, baudrate=460800, timeout=0.5):
        self.port_name = port_name
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = Serial()
        self.serial_com_lock = Lock()


    def connect(self):
        if self.ser.is_open:
            self.disconnect()
        try:
            self.serial_com_lock.acquire()
            self.ser.close()
            self.ser = Serial(port=self.port_name, baudrate=self.baudrate, timeout=self.timeout, xonxoff=True)
        except Exception as e:
            print("Error opening serial port: %s" % e)
            return False
        finally:
            self.serial_com_lock.release()

        # self.ser.write(b'RS\r\n')
        # print('RS')
        # for i in range(5):
        #     print(self.ser.readline())


        self.ser.write(b'SG10,SD100,SV10000,SA100000\r\n')
        
        print('SG10,SD100,SV10000,SA100000')
        for i in range(5):
            print(self.ser.readline())

    def start_motor(self):
        self.ser.write(b'PM,MN\r\n')
        print('PM,MN')
        for i in range(5):
            print(self.ser.readline())

    def home(self):
        self.ser.write(b'DI1,VM,MN,GO,WA100\r\n') #Velocity move to negative direction
        print('DI1,VM,MN,GO,WA100')
        for i in range(5):
            print(self.ser.readline())
        self.ser.write(b'RW538,IB-500,NO,MJ4,RP\r\n') #Check if following error < -500
        print('RW538,IB-500,NO,MJ4,RP')
        for i in range(5):
            print(self.ser.readline())
        self.ser.write(b'ST,DH,MF,DI0\r\n')#If the above is true, stop, define home
        print('ST,DH,MF,DI0')
        for i in range(5):
            print(self.ser.readline())

    def move_relative(self, distance):
        self.ser.write(b'MR%d,GO,WS500\r\n' % distance)
        print('MR%d,GO,WS500' % distance)
        for i in range(5):
            print(self.ser.readline())

    def move_absolute(self, position):
        self.ser.write(b'MA%d,GO,WS500\r\n' % position)
        print('MA%d,GO,WS500' % position)
        for i in range(5):
            print(self.ser.readline())
