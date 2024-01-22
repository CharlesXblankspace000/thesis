import time
from machine import Machine

machine = Machine(
    certificate='greencure.json',
    arduino_ports=('/dev/ttyUSB0','/dev/ttyACM0')
)
machine.stop_dc_motor()