from machine import Machine
from datetime import datetime, timedelta
import time


machine = Machine(
    certificate='greencure.json',
    arduino_ports=(None, None)
)

TEMPERATURE_THRESHOLD = 30
MOISTURE_THRESHOLD = 50

start_time = datetime.now()
day_time = datetime.now()

while True:
    temperature = machine.get_temperature()
    humidity = machine.get_humidity()
    moisture = machine.get_moisture()
    nitrogen = machine.get_nitrogen()
    phosphorus = machine.get_phosphorus()
    potassium = machine.get_potassium()

    data = {
        'temperature': temperature,
        'humidity': humidity,
        'moisture': moisture,
        'nitrogen': nitrogen,
        'phosphorus': phosphorus,
        'potassium': potassium
    }

    if temperature > TEMPERATURE_THRESHOLD:
        machine.turn_on_fan()
    else:
        machine.turn_off_fan()

    if moisture > MOISTURE_THRESHOLD:
        machine.turn_on_water_pump()
    else:
        machine.turn_off_water_pump()

    machine.update_parameters(data)

    if datetime.now() - day_time >= timedelta(days=1):
        machine.start_stepper_motor()
        time.sleep(30)
        machine.stop_stepper_motor()
        day_time = datetime.now()

    time.sleep(5)
