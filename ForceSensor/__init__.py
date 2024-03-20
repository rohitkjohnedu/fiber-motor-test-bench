# -*- coding: utf-8 -*-
"""
Driver and widget for Reading Futek Force sensor

:Example:

    >>> from LMTS.instruments.futek import FutekSensor
    >>> import matplotlib.pyplot as pp
    >>> import time
    >>> force_sensor = FutekSensor(serial_number="577685")
    >>> force_sensor.connect()
    >>> plot = pg.plot()
    >>> t_0 = time.perf_counter()
    >>> while time.perf_counter()<t_0+10:
    >>>     pass
    >>> data = force_sensor.get_buffer()
    >>> force_sensor.disconnect()
    >>> pp.plot(data[:,0],data[:,1])
    >>> pp.show()

:Widget Usage example:

    >>> import LMTS.instruments.futek
    >>> import sys
    >>> from qtpy import QtWidgets
    >>> fs = LMTS.instruments.futek.FutekSensor()
    >>> app = QtWidgets.QApplication(sys.argv)
    >>> widget = LMTS.instruments.futek.FutekSensorWidget(fs)
    >>> widget.show()
    >>> app.exec_()

"""
__all__ = ["FutekSensor", "FutekSensorWidget", "interface", "FutekSensorDaqmx"]

from .futek import FutekSensor, FutekSensorPlot, FutekSensorControl #interface # FutekSensorDaqmx
