#include <ESP32Servo.h>

Servo doorServo;
const int servoPin = "PIN connected to the ESP32";     

bool doorOpen = false;
unsigned long doorOpenTime = 0;
const unsigned long autoCloseDelay = 3000;  

void setup() {
  Serial.begin(115200);
  doorServo.attach(servoPin);
  doorServo.write(90);    
  Serial.println("System ready - awaiting commands...");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    Serial.print("Received command: ");
    Serial.println(command);

    if ((command == "OPEN" || command == "MANUAL_OPEN") && !doorOpen) {
      openDoor();
    }
    else if (command == "MANUAL_DENY") {
      Serial.println("Access denied via Telegram");
    }
  }

  if (doorOpen && millis() - doorOpenTime > autoCloseDelay) {
    Serial.println("⌛️ Time's up - closing the door.");
    closeDoor();
  }

  delay(100);  
}

void openDoor() {
  doorServo.write(0);    
  doorOpen = true;
  doorOpenTime = millis();
  Serial.println("🚪 The door is open (in the other direction) for 3 seconds.");
}

void closeDoor() {
  doorServo.write(90);  
  doorOpen = false;
  Serial.println("🚪The door is closed.");
}
