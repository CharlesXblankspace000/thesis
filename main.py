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
npk_failed_notified = False

harvest_mode_initialized = False

def validate_parameters(parameters: dict):
    for key, value in parameters.items():
        if not isinstance(value, (int, float)) or value == 'NaN':
            return False
    return True


just_started = True

while True:
    if machine.state:
        if just_started:
            machine.start_stepper_motor()
            time.sleep(30)
            machine.stop_stepper_motor()
            just_started = False

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

        machine.display_latest_readings_npk()
        machine.display_latest_readings_thm()

        data = {
            'temperature': temperature,
            'humidity': humidity,
            'moisture': moisture,
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': potassium
        }

        if not validate_parameters(data):
            continue

        if temperature > TEMPERATURE_THRESHOLD:
            machine.turn_on_fan()
        else:
            machine.turn_off_fan()

        if moisture < MOISTURE_THRESHOLD:
            machine.turn_on_water_pump()
        else:
            machine.turn_off_water_pump()

        machine.update_parameters(data)

        if datetime.now() - day_time >= timedelta(hours=1):
            machine.start_stepper_motor()
            time.sleep(30)
            machine.stop_stepper_motor()
            day_time = datetime.now()
            machine.backtrack_start(hours=23)

        # Flag checker if npk failed to met required values
        if not npk_failed_notified and \
            datetime.now() - day_time >= timedelta(days=10):
            if nitrogen <= 200 or phosphorus <= 100 or potassium <= 100:
                machine.update_npk_failed()
            npk_failed_notified = True

        # Flag checker if harvest is ready
        if not machine.harvest_ready and nitrogen >= 200 \
            and phosphorus >= 100 and potassium >= 100:
            machine.update_harvest_ready(True)

        time.sleep(10)

    else:
        pass