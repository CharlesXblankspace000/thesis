#include "DHT.h"
#include <LiquidCrystal_I2C.h>
#include <Wire.h>

const int dhtPin = 8;
const int moistureSensorPin = A0;
const int fanRelayPin = 9;
const int waterPumpRelayPin = 7;

DHT dht11(dhtPin, DHT22);
LiquidCrystal_I2C lcd(0x27, 16, 2);

const int minMoistureValue = 1023;
const int maxMoistureValue = 0;

float latestTemperature = 0;
float latestHumidity = 0;
int latestMoisture = 0;

String UUID = "ARDUINO1";
int currentCommand = -1;

void setup() {
  Serial.begin(9600);
  dht11.begin();
  Wire.begin();
  lcd.init();
  lcd.backlight(); 
  pinMode(dhtPin, INPUT);
  pinMode(fanRelayPin, OUTPUT);
  pinMode(waterPumpRelayPin, OUTPUT);
}

void loop() {
  if (currentCommand == -1) {
    receiveCommand();
  } 
  
  else if (currentCommand == 0) {
    float temperature = getTemperature();
    sendResponse(String(temperature));
    currentCommand = -1;
  }

  else if (currentCommand == 1) {
    float humidity = getHumidity();
    sendResponse(String(humidity));
    currentCommand = -1;
  }

  else if (currentCommand == 2) {
    int moisture = getMoisture();
    sendResponse(String(moisture));
    currentCommand = -1;
  }

  else if (currentCommand == 3) {
    displayLatestReadings();
    currentCommand = -1;
  }

  else if (currentCommand == 4) {
    turnOffFan();
    currentCommand = -1;
  }

  else if (currentCommand == 5) {
    turnOnFan();
    currentCommand = -1;
  }

  else if (currentCommand == 6) {
    turnOnWaterPump();
    currentCommand = -1;
  }

  else if (currentCommand == 7) {
    turnOffWaterPump();
    currentCommand = -1;
  }

  else if (currentCommand == 98) {
    getUUID();
    currentCommand = -1;
  }

  else if (currentCommand == 99) {
    resetState();
    currentCommand = -1;
  }
}

void receiveCommand() {
  if (Serial.available()) {
    int sent = Serial.readStringUntil('\n').toInt();
    Serial.println("ok");
    currentCommand = sent;
  }
}

void sendResponse(String message){
  Serial.println(message);
}

float getTemperature() {
  float temperature = dht11.readTemperature();
  latestTemperature = temperature;
  return temperature;
}

float getHumidity() {
  float humidity = dht11.readHumidity();
  latestHumidity = humidity;
  return humidity;
}

int getMoisture() {
  int rawInput = analogRead(moistureSensorPin);
  int moistureLevel = map(moistureLevel, minMoistureValue, maxMoistureValue, 0, 100);
  latestMoisture = moistureLevel;
  return moistureLevel;
}

void displayLatestReadings(){
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T: ");
  lcd.print(latestTemperature, 1);
  lcd.print("C M: ");
  lcd.print(latestMoisture);
  lcd.print("%");
  lcd.setCursor(0, 1);
  lcd.print("H: ");
  lcd.print(latestHumidity, 2);
  lcd.print("%      ");
}

void turnOnFan(){
  digitalWrite(fanRelayPin, HIGH);
}

void turnOffFan(){
  digitalWrite(fanRelayPin, LOW);
}

void turnOnWaterPump(){
  digitalWrite(waterPumpRelayPin, HIGH);
}

void turnOffWaterPump(){
  digitalWrite(waterPumpRelayPin, LOW);
}

void getUUID(){
  sendResponse(UUID);
}

void resetState(){
  latestTemperature = 0;
  latestHumidity = 0;
  latestMoisture = 0;
  turnOffFan();
  turnOffWaterPump();
  lcd.clear();
}
