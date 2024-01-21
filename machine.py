from arduino import Arduino
from firebase_admin import credentials, firestore, messaging
from datetime import datetime, timezone
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

        self.arduino1 = Arduino(None, baudrate=9600, commands=arduino_1_commands)
        self.arduino2 = Arduino(None, baudrate=115200,  commands=arduino_2_commands)

        cred = credentials.Certificate(certificate)
        app = firebase_admin.initialize_app(cred)
        db = firestore.client()
        self.parameter_reference = db.collection('parameters')
        self.user_reference = db.collection('users')

        self._fan_state = False
        self._water_pump_state = False



    def __initialize_logger(self):
        format = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s.')
        main_handler = logging.FileHandler('machine.log')
        main_handler.setFormatter(format)
        self.logger = logging.getLogger('machine')
        self.logger.addHandler(main_handler)
        self.logger.setLevel(logging.INFO)


    #############################################
    #                                           #
    #            Firebase Functions             #
    #                                           #
    #############################################
        

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
        self.arduino1.send_command(0)
        while True:
            response = self.arduino1.get_response()
            try:
                temperature = float(response)
                break
            except:
                pass
        return temperature
    


    def get_humidity(self) -> float:
        '''
        Get humidity from arduino

        Returns:
        humidity (float) : Humidity
        '''
        self.arduino1.send_command(1)
        while True:
            response = self.arduino1.get_response()
            try:
                humidity = float(response)
                break
            except:
                pass
        return humidity
    


    def get_moisture(self) -> float:
        '''
        Get moisture from arduino

        Returns:
        moisture (float) : Moisture
        '''
        self.arduino1.send_command(2)
        while True:
            response = self.arduino1.get_response()
            try:
                moisture = float(response)
                break
            except:
                pass
        return moisture
    


    def get_nitrogen(self) -> float:
        '''
        Get nitrogen from arduino

        Returns:
        nitrogen (float) : Nitrogen
        '''
        self.arduino2.send_command(100)
        while True:
            response = self.arduino1.get_response()
            try:
                nitrogen = float(response)
                break
            except:
                pass
        return nitrogen
    


    def get_phosphorus(self) -> float:
        '''
        Get phosphorus from arduino

        Returns:
        phosphorus (float) : Phosphorus
        '''
        self.arduino2.send_command(101)
        while True:
            response = self.arduino1.get_response()
            try:
                phosphorus = float(response)
                break
            except:
                pass
        return phosphorus
    


    def get_potassium(self) -> float:
        '''
        Get potassium from arduino

        Returns:
        potassium (float) : Potassium
        '''
        self.arduino2.send_command(102)
        while True:
            response = self.arduino1.get_response()
            try:
                potassium = float(response)
                break
            except:
                pass
        return potassium
    


    def display_latest_readings_thm(self):
        '''
        Display latest DHT and moisture readings in LCD.
        Corresponding functions must be invoked for latest
        readings to reflect
        '''
        self.arduino1.send_command(3)



    def display_latest_readings_npk(self):
        '''
        Display latest NPK readings in LCD
        Corresponding functions must be invoked for latest
        readings to reflect
        '''
        self.arduino2.send_command(103)


    
    def turn_on_fan(self):
        '''
        Turn on fan in the arduino
        '''
        if self._fan_state:
            return
        self.arduino1.send_command(4)
        self._fan_state = True


    
    def turn_off_fan(self):
        '''
        Turn off fan in the arduino
        '''
        if not self._fan_state:
            return
        self.arduino1.send_command(5)
        self._fan_state = False



    def turn_on_water_pump(self):
        '''
        Turn on water pump in the arduino
        '''
        if self._water_pump_state:
            return
        self.arduino1.send_command(6)
        self._water_pump_state = True


    
    def turn_off_water_pump(self):
        '''
        Turn off water pump in the arduino
        '''
        if not self._water_pump_state:
            return
        self.arduino1.send_command(7)
        self._water_pump_state = False



    def start_stepper_motor(self):
        '''
        Start stepper motor in the arduino
        '''
        self.arduino2.send_command(104)



    def stop_stepper_motor(self):
        '''
        Start stepper motor in the arduino
        '''
        self.arduino2.send_command(105)



    def open_hatch(self):
        '''
        Rotate servo in the arduino to open hatch 
        '''
        self.arduino2.send_command(106)



    def close_hatch(self):
        '''
        Rotate servo in the arduino to close hatch 
        '''
        self.arduino2.send_command(107)



    def start_dc_motor(self):
        '''
        Start DC Motor in the arduino
        '''
        self.arduino2.send_command(108)



    def stop_dc_motor(self):
        '''
        Stop DC Motor in the arduino
        '''
        self.arduino2.send_command(109)
