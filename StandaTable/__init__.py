# -*- coding: utf-8 -*-
"""
Library for driving the standa table controllers.

Install the driver before using the library. It is available here:
http://files.xisupport.com/Software.en.html

:Usage Example:

    >>> from LMTS.instruments.standa_table import StandaTable
    >>> import matplotlib.pyplot as pp
    >>> table = StandaTable(id=0)
    >>> table.start_reading()
    >>> table.home_zero()
    >>> table.set_speed(5)
    >>> table.move_relative(5)
    >>> table.wait_for_stop()
    >>> table.move_relative(-5)
    >>> time_vector, data_vector = table.get_buffer()
    >>> pp.plot(time_vector, data_vector)
    >>> table.close()
    >>> pp.show()

"""
__all__ = ["StandaTable", "StandaTableWidget", "PositionPlot", "interface"]

from .standa_table import StandaTable, StandaTableWidget, PositionPlot #, interface
