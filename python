import serial
import time
import RPi.GPIO as GPIO
import threading
import firebase_admin
from firebase_admin import credentials, firestore

GPIO.setmode(GPIO.BCM)

# Initialize Firebase
cred = credentials.Certificate('greencure.json')
firebase_admin.initialize_app(cred)

# Access the Firestore database
db = firestore.client()

arduino1 = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # Arduino 1
arduino2 = serial.Serial('/dev/ttyACM0', 115200, timeout=1)  # Arduino 2

def get_conditions_arduino1():
    arduino1.write(bytes('0\n', 'utf-8'))
    response = arduino1.readline().decode('utf-8').rstrip()
    return response

def get_conditions_arduino2():
    arduino2.write(bytes('0\n', 'utf-8'))
    response = arduino2.readline().decode('utf-8').rstrip()
    return response

def send_command_to_arduino2(command):
    arduino2.write(bytes(command, 'utf-8'))

def store_data_to_firestore(collection, data):
    doc_ref = db.collection(collection).add(data)
    print(f"Data stored in Firestore with ID: {doc_ref.id}")

def read_arduino1_data():
    try:
        while True:
            response_arduino1 = get_conditions_arduino1().strip()
            print(response_arduino1)
            data_arduino1 = response_arduino1.split('\t')

            if len(data_arduino1) == 7 and data_arduino1[0] == 'Humidity:':
                try:
                    temperature = float(data_arduino1[2].rstrip('°C'))
                    humidity = float(data_arduino1[4].rstrip('%'))
                    moisture = float(data_arduino1[6].rstrip('%'))

                    print(f"Temperature: {temperature}°C")
                    print(f"Humidity: {humidity}%")
                    print(f"Moisture: {moisture}%")

                    # Store data in Firestore
                    data_to_store = {
                        "timestamp": time.time(),
                        "temperature": temperature,
                        "humidity": humidity,
                        "moisture": moisture,
                        # Add other data fields as needed
                    }
                    store_data_to_firestore("arduino1_data", data_to_store)

                except ValueError as e:
                    print(f"Error converting values: {e}")

            time.sleep(5)

    except KeyboardInterrupt:
        GPIO.cleanup()
        arduino1.close()

def read_arduino2_data():
    try:
        while True:
            response_arduino2 = get_conditions_arduino2().strip()
            print(response_arduino2)
            data_arduino2 = response_arduino2.split('\t')

            # Assuming the NPK data is in a specific format, modify accordingly
            if len(data_arduino2) == 4 and data_arduino2[0] == 'NPK:':
                try:
                    nitrogen = float(data_arduino2[1])
                    phosphorus = float(data_arduino2[2])
                    potassium = float(data_arduino2[3])

                    print(f"Nitrogen: {nitrogen}")
                    print(f"Phosphorus: {phosphorus}")
                    print(f"Potassium: {potassium}")

                    # Store data in Firestore
                    data_to_store = {
                        "timestamp": time.time(),
                        "nitrogen": nitrogen,
                        "phosphorus": phosphorus,
                        "potassium": potassium,
                        # Add other data fields as needed
                    }
                    store_data_to_firestore("arduino2_data", data_to_store)

                except ValueError as e:
                    print(f"Error converting values: {e}")

            time.sleep(5)

    except KeyboardInterrupt:
        GPIO.cleanup()
        arduino2.close()

def command_input_thread():
    try:
        while True:
            command_input = input("Enter command (1 to stop stepper and rotate servo): ")
            if command_input == '1':
                send_command_to_arduino2(command_input)
                print("Command sent to Arduino 2")

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    try:
        thread_arduino1 = threading.Thread(target=read_arduino1_data)
        thread_arduino2 = threading.Thread(target=read_arduino2_data)
        thread_command_input = threading.Thread(target=command_input_thread)

        thread_arduino1.start()
        thread_arduino2.start()
        thread_command_input.start()

        thread_arduino1.join()
        thread_arduino2.join()
        thread_command_input.join()

    except KeyboardInterrupt:
        GPIO.cleanup()
        arduino1.close()
        arduino2.close()
