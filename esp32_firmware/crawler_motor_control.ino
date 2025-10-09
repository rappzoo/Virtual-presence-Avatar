/*
 * ESP32 Crawler Motor Control Firmware
 * Controls two ESCs for crawler-style movement
 * Communicates with RPi5 via USB Serial
 * 
 * Hardware Setup:
 * - ESC1 connected to GPIO 18 (Left Motor)
 * - ESC2 connected to GPIO 19 (Right Motor)
 * - USB Serial connection to RPi5
 * 
 * Command Format: MOTOR:L:{left_speed}:R:{right_speed}
 * Speed Range: -255 to +255 (negative = reverse)
 */

#include <ESP32Servo.h>

// Motor control pins
#define LEFT_MOTOR_PIN 18
#define RIGHT_MOTOR_PIN 19

// ESC calibration values
#define ESC_MIN_PULSE 1000  // Minimum pulse width (stop)
#define ESC_MAX_PULSE 2000  // Maximum pulse width (full speed)
#define ESC_NEUTRAL 1500    // Neutral position (stop)

// Servo objects for ESC control
Servo leftESC;
Servo rightESC;

// Motor speed variables
int leftSpeed = 0;
int rightSpeed = 0;

// Communication variables
String inputString = "";
bool stringComplete = false;

// Status LED (optional - connect LED to GPIO 2)
#define STATUS_LED_PIN 2

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.setTimeout(100);
  
  // Initialize status LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  
  // Initialize ESCs
  leftESC.attach(LEFT_MOTOR_PIN, ESC_MIN_PULSE, ESC_MAX_PULSE);
  rightESC.attach(RIGHT_MOTOR_PIN, ESC_MIN_PULSE, ESC_MAX_PULSE);
  
  // Send neutral signal to ESCs (stop motors)
  leftESC.writeMicroseconds(ESC_NEUTRAL);
  rightESC.writeMicroseconds(ESC_NEUTRAL);
  
  // Wait for ESCs to initialize
  delay(2000);
  
  // Send startup message
  Serial.println("ESP32_CRAWLER_READY");
  Serial.println("Command format: MOTOR:L:{speed}:R:{speed}");
  Serial.println("Speed range: -255 to +255");
  
  // Blink LED to indicate ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(200);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("ESP32_CRAWLER_INITIALIZED");
}

void loop() {
  // Handle incoming serial commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Small delay to prevent overwhelming the system
  delay(10);
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  command.trim();
  
  // Check if command starts with "MOTOR:"
  if (command.startsWith("MOTOR:")) {
    // Parse motor command: MOTOR:L:{left_speed}:R:{right_speed}
    int firstColon = command.indexOf(':');
    int secondColon = command.indexOf(':', firstColon + 1);
    int thirdColon = command.indexOf(':', secondColon + 1);
    
    if (firstColon != -1 && secondColon != -1 && thirdColon != -1) {
      // Extract left speed
      String leftSpeedStr = command.substring(secondColon + 1, thirdColon);
      int newLeftSpeed = leftSpeedStr.toInt();
      
      // Extract right speed
      String rightSpeedStr = command.substring(thirdColon + 1);
      int newRightSpeed = rightSpeedStr.toInt();
      
      // Validate speed range
      if (newLeftSpeed >= -255 && newLeftSpeed <= 255 && 
          newRightSpeed >= -255 && newRightSpeed <= 255) {
        
        // Update motor speeds
        leftSpeed = newLeftSpeed;
        rightSpeed = newRightSpeed;
        
        // Apply motor speeds
        setMotorSpeed(LEFT_MOTOR_PIN, leftSpeed, leftESC);
        setMotorSpeed(RIGHT_MOTOR_PIN, rightSpeed, rightESC);
        
        // Send confirmation
        Serial.print("MOTOR_OK:L:");
        Serial.print(leftSpeed);
        Serial.print(":R:");
        Serial.println(rightSpeed);
        
        // Blink LED to indicate command received
        digitalWrite(STATUS_LED_PIN, HIGH);
        delay(50);
        digitalWrite(STATUS_LED_PIN, LOW);
        
      } else {
        Serial.println("MOTOR_ERROR:INVALID_SPEED_RANGE");
      }
    } else {
      Serial.println("MOTOR_ERROR:INVALID_FORMAT");
    }
  }
  // Handle status request
  else if (command == "STATUS") {
    Serial.print("STATUS_OK:L:");
    Serial.print(leftSpeed);
    Serial.print(":R:");
    Serial.println(rightSpeed);
  }
  // Handle stop command
  else if (command == "STOP") {
    leftSpeed = 0;
    rightSpeed = 0;
    leftESC.writeMicroseconds(ESC_NEUTRAL);
    rightESC.writeMicroseconds(ESC_NEUTRAL);
    Serial.println("MOTOR_STOPPED");
  }
  // Handle test command
  else if (command == "TEST") {
    Serial.println("MOTOR_TEST_START");
    
    // Test sequence: forward, backward, left, right, stop
    testSequence();
    
    Serial.println("MOTOR_TEST_COMPLETE");
  }
  // Handle unknown command
  else {
    Serial.println("ERROR:UNKNOWN_COMMAND");
  }
}

void setMotorSpeed(int motorPin, int speed, Servo& esc) {
  // Convert speed (-255 to +255) to ESC pulse width (1000 to 2000)
  int pulseWidth;
  
  if (speed == 0) {
    pulseWidth = ESC_NEUTRAL;
  } else if (speed > 0) {
    // Forward: map 1-255 to 1500-2000
    pulseWidth = map(speed, 1, 255, ESC_NEUTRAL + 1, ESC_MAX_PULSE);
  } else {
    // Reverse: map -1 to -255 to 1000-1499
    pulseWidth = map(abs(speed), 1, 255, ESC_MIN_PULSE, ESC_NEUTRAL - 1);
  }
  
  // Ensure pulse width is within valid range
  pulseWidth = constrain(pulseWidth, ESC_MIN_PULSE, ESC_MAX_PULSE);
  
  // Send pulse to ESC
  esc.writeMicroseconds(pulseWidth);
}

void testSequence() {
  // Test forward
  Serial.println("TEST:FORWARD");
  leftESC.writeMicroseconds(1600);
  rightESC.writeMicroseconds(1600);
  delay(1000);
  
  // Test backward
  Serial.println("TEST:BACKWARD");
  leftESC.writeMicroseconds(1400);
  rightESC.writeMicroseconds(1400);
  delay(1000);
  
  // Test left turn
  Serial.println("TEST:LEFT_TURN");
  leftESC.writeMicroseconds(1400);
  rightESC.writeMicroseconds(1600);
  delay(1000);
  
  // Test right turn
  Serial.println("TEST:RIGHT_TURN");
  leftESC.writeMicroseconds(1600);
  rightESC.writeMicroseconds(1400);
  delay(1000);
  
  // Stop
  Serial.println("TEST:STOP");
  leftESC.writeMicroseconds(ESC_NEUTRAL);
  rightESC.writeMicroseconds(ESC_NEUTRAL);
  delay(500);
}

// Emergency stop function (can be called via interrupt)
void emergencyStop() {
  leftSpeed = 0;
  rightSpeed = 0;
  leftESC.writeMicroseconds(ESC_NEUTRAL);
  rightESC.writeMicroseconds(ESC_NEUTRAL);
  Serial.println("EMERGENCY_STOP");
  
  // Flash LED rapidly
  for (int i = 0; i < 10; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(100);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(100);
  }
}

// Watchdog timer to prevent runaway motors
void watchdogReset() {
  // This function can be called periodically to reset watchdog
  // If communication is lost, motors will stop automatically
  static unsigned long lastCommandTime = 0;
  static unsigned long currentTime = millis();
  
  // If no command received for 5 seconds, stop motors
  if (currentTime - lastCommandTime > 5000) {
    if (leftSpeed != 0 || rightSpeed != 0) {
      emergencyStop();
    }
  }
}
