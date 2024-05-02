from ForceSensor import FutekSensor
import time

force_sensor = FutekSensor()
force_sensor.start_recording()

for i in range(100):
    time.sleep(0.01)