#include <SoftwareSerial.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

#define PIN_RE 6
#define PIN_DE 7
SoftwareSerial LC_NPK_SER(8, 9);
byte databuf[11];
const byte nitrogenCommand[] = {0x01, 0x03, 0x00, 0x1e, 0x00, 0x01, 0xe4, 0x0c};
const byte phosphorusCommand[] = {0x01, 0x03, 0x00, 0x1f, 0x00, 0x01, 0xb5, 0xcc};
const byte potassiumCommand[] = {0x01, 0x03, 0x00, 0x20, 0x00, 0x01, 0x85, 0xc0};

LiquidCrystal_I2C lcd(0x3F, 16, 2);

const int stepPin = 2;
const int dirPin = 3;
const int enPin = 10;
bool stepperMotorEnabled = false;
bool stepState = false;
unsigned long previousMillis = 0;
const long stepInterval = 4; // in microseconds

Servo servoMotor;
const int servoPin = 5;

const int motorRelayPin = 4;
bool relayOpen = false;

byte latestNitrogen = 0;
byte latestPhophorus = 0;
byte latestPotassium = 0;

String UUID = "ARDUINO2";
int currentCommand = -1;

void setup()
{
  Serial.begin(115200);

  LC_NPK_SER.begin(4800);
  pinMode(PIN_RE, OUTPUT);
  pinMode(PIN_DE, OUTPUT);
  digitalWrite(PIN_DE, LOW);
  digitalWrite(PIN_RE, LOW);

  lcd.init();
  lcd.clear();
  lcd.backlight();

  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enPin, OUTPUT);
  digitalWrite(enPin, LOW);

  servoMotor.attach(servoPin);
  servoMotor.write(0);
  pinMode(motorRelayPin, OUTPUT);
}

void loop()
{
if (currentCommand == -1) {
    receiveCommand();
  } 
  
  else if (currentCommand == 100) {
    byte nitrogen = getNitrogen();
    sendResponse(String(nitrogen));
    currentCommand = -1;
  }

  else if (currentCommand == 101) {
    byte phosphorus = getPhosphorus();
    sendResponse(String(phosphorus));
    currentCommand = -1;
  }

  else if (currentCommand == 102) {
    byte potassium = getPotassium();
    sendResponse(String(potassium));
    currentCommand = -1;
  }

  else if (currentCommand == 103) {
    displayLatestReadings();
    currentCommand = -1;
  }

  else if (currentCommand == 104) {
    startStepperMotor();
    currentCommand = -1;
  }

  else if (currentCommand == 105) {
    stopStepperMotor();
    currentCommand = -1;
  }

  else if (currentCommand == 106) {
    openHatch();
    currentCommand = -1;
  }

  else if (currentCommand == 107) {
    closeHatch();
    currentCommand = -1;
  }

  else if (currentCommand == 108) {
    startDCMotor();
    currentCommand = -1;
  }

  else if (currentCommand == 109) {
    stopDCMotor();
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

  runBackground();
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

byte getNitrogen(){
  LC_NPK_SER.flush();
  digitalWrite(PIN_DE, HIGH);
  digitalWrite(PIN_RE, HIGH);
  delay(1);

  for (uint8_t i = 0; i < sizeof(nitrogenCommand); i++)
    LC_NPK_SER.write(nitrogenCommand[i]);
  
  LC_NPK_SER.flush();
  digitalWrite(PIN_DE, LOW);
  digitalWrite(PIN_RE, LOW);
  delay(200);

  if (LC_NPK_SER.available() >= 7){
    for (byte i = 0; i < 7; i++){
      databuf[i] = LC_NPK_SER.read();
    }
    latestNitrogen = databuf[4];
    return databuf[4];
  }

  return 0;
}

byte getPhosphorus(){
  LC_NPK_SER.flush();
  digitalWrite(PIN_DE, HIGH);
  digitalWrite(PIN_RE, HIGH);
  delay(1);

  for (uint8_t i = 0; i < sizeof(phosphorusCommand); i++)
    LC_NPK_SER.write(phosphorusCommand[i]);

  LC_NPK_SER.flush();
  digitalWrite(PIN_DE, LOW);
  digitalWrite(PIN_RE, LOW);
  delay(200);

  if (LC_NPK_SER.available() >= 7){
    for (byte i = 0; i < 7; i++){
      databuf[i] = LC_NPK_SER.read();
    }
    latestPhophorus = databuf[4];
    return databuf[4];
  }

  return 0;
}

byte getPotassium(){
  while (LC_NPK_SER.available()){
    LC_NPK_SER.read();
  }

  digitalWrite(PIN_DE, HIGH);
  digitalWrite(PIN_RE, HIGH);
  delay(1);

  for (uint8_t i = 0; i < sizeof(potassiumCommand); i++)
    LC_NPK_SER.write(potassiumCommand[i]);

  LC_NPK_SER.flush();
  digitalWrite(PIN_DE, LOW);
  digitalWrite(PIN_RE, LOW);
  delay(200);

  if (LC_NPK_SER.available() >= 7){
    for (byte i = 0; i < 7; i++){
      databuf[i] = LC_NPK_SER.read();
    }
    latestPotassium = databuf[4];
    return databuf[4];
  }

  return 0;
}

void startStepperMotor(){
  digitalWrite(dirPin, HIGH);
  stepperMotorEnabled = true;
}

void stopStepperMotor(){
  digitalWrite(enPin, LOW);
  stepperMotorEnabled = false;
}

void openHatch(){
  servoMotor.write(180);
}

void closeHatch(){
  servoMotor.write(0);
}

void startDCMotor(){
  digitalWrite(motorRelayPin, HIGH);
}

void stopDCMotor(){
  digitalWrite(motorRelayPin, LOW);
}

void displayLatestReadings(){
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("N: ");
  lcd.print(latestNitrogen);

  lcd.setCursor(0, 1);
  lcd.print("P: ");
  lcd.print(latestPhophorus);
  lcd.print("  K: ");
  lcd.print(latestPotassium);
}

void runBackground(){
  unsigned long currentMillis = millis();
  if(stepperMotorEnabled){
    if(currentMillis - previousMillis >= stepInterval){
      stepState = !stepState;
      previousMillis = currentMillis;

      if(stepState){
        digitalWrite(stepPin, HIGH);
      }
      else{
        digitalWrite(stepPin, LOW);
      }
    }
  }
}

void getUUID(){
  sendResponse(UUID);
}

void resetState(){
  latestNitrogen = 0;
  latestPhophorus = 0;
  latestPotassium = 0;
  stopStepperMotor();
  stopDCMotor();
  closeHatch();
  lcd.clear();
}
