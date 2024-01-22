from machine import Machine
from datetime import datetime, timedelta
import time


machine = Machine(
    certificate='greencure.json',
    arduino_ports=('/dev/ttyUSB0','/dev/ttyACM0')
)

TEMPERATURE_THRESHOLD = 30
MOISTURE_THRESHOLD = 50

start_time = datetime.now()
day_time = datetime.now()

harvest_mode_initialized = False

while True:
    if machine.state:
        if machine.harvest_mode and not harvest_mode_initialized:
            machine.open_hatch()
            machine.start_dc_motor()
            harvest_mode_initialized = True
        elif not machine.harvest_mode and harvest_mode_initialized:
            machine.close_hatch()
            machine.stop_dc_motor()
            harvest_mode_initialized = False

        if machine.harvest_mode:
            continue

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

        if moisture < MOISTURE_THRESHOLD:
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

    else:
        pass
