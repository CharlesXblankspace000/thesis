from arduino import Arduino
from firebase_admin import credentials, firestore, messaging
from datetime import datetime, timezone, timedelta
import RPi.GPIO as GPIO
import firebase_admin
import logging


class Machine:
    def __init__(self, certificate: str, arduino_ports: tuple = (None, None)) -> None:
        '''
        Initialize machine

        Parameters:
        certificate (str) : Google certificate path
        arduino_ports (tuple) : Port where arduino is connection (A1, A2)
        '''
        self.__initialize_logger()

        arduino_1_commands = list(range(0, 8))
        arduino_1_commands.extend([98, 99])
        arduino_2_commands = list(range(100, 110))
        arduino_2_commands.extend([98, 99])

        self.arduino1 = Arduino(arduino_ports[0], baudrate=9600, commands=arduino_1_commands, timeout=1)
        self.arduino2 = Arduino(arduino_ports[1], baudrate=115200,  commands=arduino_2_commands, timeout=1)
        
        self.arduino1.reset_state()
        self.arduino2.reset_state()

        self._state = False
        self._harvest_mode = False
        self._fan_state = False
        self._water_pump_state = False
        self.__initialized = False
        self._npk_failed = False
        self._harvest_ready = False
        self._last_start = datetime.now(tz=timezone.utc)

        cred = credentials.Certificate(certificate)
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        self.parameter_reference = db.collection('parameters')
        self.state_reference = db.collection('states').document('current')
        self.harvest_trigger_reference = db.collection('triggers').document('harvest')
        self.user_reference = db.collection('users')
        self.harvest_trigger_reference.on_snapshot(self._switch_harvest_mode_firebase)

        self.update_state()

        state_button = 10
        harvest_button = 9
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(state_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(harvest_button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(state_button, GPIO.RISING, callback = self._switch_state, bouncetime=2000)
        #GPIO.add_event_detect(harvest_button, GPIO.RISING, callback = self._switch_harvest_mode, bouncetime=2000)

        self.__initialized = True



    @property
    def state(self):
        '''
        Machine state
        '''
        return self._state
    


    @property
    def harvest_mode(self):
        '''
        Harvest mode
        '''
        return self._harvest_mode
    


    @property
    def last_start(self):
        '''
        Machine last started
        '''
        return self._last_start



    @property
    def harvest_ready(self):
        '''
        Is harvest ready?
        '''
        return self._harvest_ready
    
    

    def __initialize_logger(self):
        format = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s.')
        main_handler = logging.FileHandler('machine.log')
        main_handler.setFormatter(format)
        self.logger = logging.getLogger('machine')
        self.logger.addHandler(main_handler)
        self.logger.setLevel(logging.DEBUG)


    #############################################
    #                                           #
    #              GPIO Functions               #
    #                                           #
    #############################################
        

    def _switch_state(self, channel):
        '''
        Switch machine state
        '''
        if not self.__initialized:
            return
        self._state = not self._state
        self.logger.info(f'State changed to: {self._state}')
        if not self._state:
            self._harvest_mode = False
            self.logger.info('Harvest mode change to False')
        self.update_state()



    def _switch_harvest_mode(self, channel):
        '''
        Switch harvest mode
        '''
        if not self.__initialized or not self._state:
            return
        self._harvest_mode = not self._harvest_mode
        self.update_state()
        self.logger.info(f'Harvest mode changed to: {self._harvest_mode}')


    #############################################
    #                                           #
    #            Firebase Functions             #
    #                                           #
    #############################################
        

    def _switch_harvest_mode_firebase(self, doc_snapshot, changes, read_time):
        '''
        Switch harvest mode
        '''
        if not self.__initialized:
            return
        print(doc_snapshot[-1].to_dict())
        self._harvest_mode = not self._harvest_mode
        self.update_state()
        self.logger.info(f'Harvest mode changed via firebase to: {self._harvest_mode}')



    def update_parameters(self, parameters: dict):
        '''
        Add parameter to firebase
        Sample format:
        ```python
        parameters = {
            'temperature': 10.1,
            'humidity': 15.1,
            'moisture': 23.4,
            'nitrogen': 34,
            'phosphorus': 42,
            'potassium': 23,
        }
        ```
        '''
        data = {
            'temperature': parameters['temperature'],
            'humidity': parameters['humidity'],
            'moisture': parameters['moisture'],
            'nitrogen': parameters['nitrogen'],
            'phosphorus': parameters['phosphorus'],
            'potassium': parameters['potassium'],
            'created_at': datetime.now(tz=timezone.utc)
        }
        self.parameter_reference.add(data)
        self.logger.info(f'Added parameter to firebase: {data}')



    def update_state(self):
        '''
        Update state to firebase
        '''
        data = {
            'power': self._state,
            'harvest': self._harvest_mode,
            'failed': self._npk_failed,
            'ready': self._harvest_ready
        }

        if self._state:
            start = datetime.now(tz=timezone.utc)
            data['started'] = start
            self._last_start = start
        else:
            data['started'] = self._last_start

        self.state_reference.update(data)



    def backtrack_start(self, hours: int):
        '''
        Modifies the last started variable to
        x number of hours

        Parameters:
        hours (int) : Number of hours
        '''
        if not self._state:
            return
        
        deduct = timedelta(hours=hours)
        self._last_start = self._last_start -  deduct
        self.update_state()



    def _get_user_tokens(self) -> list:
        '''
        Get all existing user tokens from firebase

        Returns:
        tokens (list) : List of all retrieved tokens
        '''
        tokens = []
        users = self.user_reference.stream()
        for user in users:
            tokens.append(user.id)
        return tokens



    def send_notification(self, title: str, body: str):
        '''
        Send a notification to all users

        Parameters:
        title (str) : Title message
        body (str) : Message content
        '''
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title= title,
                body= body,
            ),
            tokens= self._get_user_tokens()
        )
        messaging.send_multicast(message)
        self.logger.info(f'Notification sent: {title}, {body}')



    def update_npk_failed(self, value: bool):
        '''
        Update npk failed value

        Parameters:
        value (bool) : NPK failed?
        '''
        self._npk_failed = value
        self.update_state()



    def update_harvest_ready(self, value: bool):
        '''
        Update harvest ready value

        Parameters:
        value (bool) : Harvest ready?
        '''
        self._harvest_ready = value
        self.update_state()


    #############################################
    #                                           #
    #             Arduino Functions             #
    #                                           #
    #############################################
        

    def get_temperature(self) -> float:
        '''
        Get temperature from arduino

        Returns:
        temperature (float) : Temperature
        '''
        self.logger.info('Getting temperature')
        self.arduino1.send_command(0)
        while True:
            response = self.arduino1.get_response()
            try:
                temperature = float(response)
                break
            except:
                pass
        self.logger.info(f'Got temperature: {temperature}')
        return temperature
    


    def get_humidity(self) -> float:
        '''
        Get humidity from arduino

        Returns:
        humidity (float) : Humidity
        '''
        self.logger.info('Getting humidity')
        self.arduino1.send_command(1)
        while True:
            response = self.arduino1.get_response()
            try:
                humidity = float(response)
                break
            except:
                pass
        self.logger.info(f'Got humidity: {humidity}')
        return humidity
    


    def get_moisture(self) -> float:
        '''
        Get moisture from arduino

        Returns:
        moisture (float) : Moisture
        '''
        self.logger.info('Getting moisture')
        self.arduino1.send_command(2)
        while True:
            response = self.arduino1.get_response()
            try:
                moisture = float(response)
                break
            except:
                pass
        self.logger.info(f'Got moisture: {moisture}')
        return moisture
    


    def get_nitrogen(self) -> float:
        '''
        Get nitrogen from arduino

        Returns:
        nitrogen (float) : Nitrogen
        '''
        self.logger.info('Getting nitrogen')
        self.arduino2.send_command(100)
        while True:
            response = self.arduino2.get_response()
            try:
                nitrogen = float(response)
                break
            except:
                pass
        self.logger.info(f'Got nitrogen: {nitrogen}')
        return nitrogen
    


    def get_phosphorus(self) -> float:
        '''
        Get phosphorus from arduino

        Returns:
        phosphorus (float) : Phosphorus
        '''
        self.logger.info('Getting phosphorus')
        self.arduino2.send_command(101)
        while True:
            response = self.arduino2.get_response()
            try:
                phosphorus = float(response)
                break
            except:
                pass
        self.logger.info(f'Got phosphorus: {phosphorus}')
        return phosphorus
    


    def get_potassium(self) -> float:
        '''
        Get potassium from arduino

        Returns:
        potassium (float) : Potassium
        '''
        self.logger.info('Getting potassium')
        self.arduino2.send_command(102)
        while True:
            response = self.arduino2.get_response()
            try:
                potassium = float(response)
                break
            except:
                pass
        self.logger.info(f'Got potassium: {potassium}')
        return potassium
    


    def display_latest_readings_thm(self):
        '''
        Display latest DHT and moisture readings in LCD.
        Corresponding functions must be invoked for latest
        readings to reflect
        '''
        self.arduino1.send_command(3)
        self.logger.info('Displayed latest THM readings')



    def display_latest_readings_npk(self):
        '''
        Display latest NPK readings in LCD
        Corresponding functions must be invoked for latest
        readings to reflect
        '''
        self.arduino2.send_command(103)
        self.logger.info('Displayed latest NPK readings')


    
    def turn_on_fan(self):
        '''
        Turn on fan in the arduino
        '''
        if self._fan_state:
            return
        self.arduino1.send_command(4)
        self._fan_state = True
        self.logger.info('Fan turned on')


    
    def turn_off_fan(self):
        '''
        Turn off fan in the arduino
        '''
        if not self._fan_state:
            return
        self.arduino1.send_command(5)
        self._fan_state = False
        self.logger.info('Fan turned off')



    def turn_on_water_pump(self):
        '''
        Turn on water pump in the arduino
        '''
        if self._water_pump_state:
            return
        self.arduino1.send_command(6)
        self._water_pump_state = True
        self.logger.info('Water pump turned on')


    
    def turn_off_water_pump(self):
        '''
        Turn off water pump in the arduino
        '''
        if not self._water_pump_state:
            return
        self.arduino1.send_command(7)
        self._water_pump_state = False
        self.logger.info('Water pump turned off')



    def start_stepper_motor(self):
        '''
        Start stepper motor in the arduino
        '''
        self.arduino2.send_command(104)
        self.logger.info('Stepper motor started')



    def stop_stepper_motor(self):
        '''
        Start stepper motor in the arduino
        '''
        self.arduino2.send_command(105)
        self.logger.info('Stepper motor stopped')



    def open_hatch(self):
        '''
        Rotate servo in the arduino to open hatch 
        '''
        self.arduino2.send_command(106)
        self.logger.info('Hatched opened')



    def close_hatch(self):
        '''
        Rotate servo in the arduino to close hatch 
        '''
        self.arduino2.send_command(107)
        self.logger.info('Hatch closed')



    def start_dc_motor(self):
        '''
        Start DC Motor in the arduino
        '''
        self.arduino2.send_command(108)
        self.logger.info('DC Motor started')



    def stop_dc_motor(self):
        '''
        Stop DC Motor in the arduino
        '''
        self.arduino2.send_command(109)
        self.logger.info('DC Motor stopped')