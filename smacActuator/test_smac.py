import smac as smac
import time

smac = smac.Smac('COM7')
smac.connect()
smac.start_motor()
#smac.home()
smac.move_absolute(10000)
#5time.sleep(2)
#smac.move_relative(5000)
