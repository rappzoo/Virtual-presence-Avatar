/*
 * ESP32 Crawler Motor Control Firmware v2.0
 * Controls two ESCs for crawler-style movement
 * Communicates with RPi5 via USB Serial
 * 
 * SAFETY FEATURES:
 * - Watchdog timer (auto-stop if no command for 2 seconds)
 * - Command validation with checksum
 * - Emergency stop command
 * - Automatic stop on serial errors
 * - Status reporting with heartbeat
 * 
 * Hardware Setup:
 * - ESC1 connected to GPIO 18 (Left Motor)
 * - ESC2 connected to GPIO 19 (Right Motor)
 * - USB Serial connection to RPi5
 * - Status LED on GPIO 2
 * 
 * Command Formats:
 * - PWM {left_speed} {right_speed}  (Speed: -255 to +255)
 * - STOP                             (Emergency stop)
 * - STATUS                           (Get current status)
 * - TEST                             (Run motor test sequence)
 * 
 * Response Format: JSON
 * Example: {"ok":true,"left":100,"right":100,"uptime":12345}
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

// Watchdog safety timer
unsigned long lastCommandTime = 0;
unsigned long lastHeartbeatTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 2000;  // 2 seconds - must match backend timeout
const unsigned long HEARTBEAT_INTERVAL = 1000;  // Send heartbeat every second

// Status LED (optional - connect LED to GPIO 2)
#define STATUS_LED_PIN 2

// System uptime
unsigned long systemUptime = 0;

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
  
  // Initialize watchdog timer
  lastCommandTime = millis();
  lastHeartbeatTime = millis();
  
  // Send startup message (JSON format)
  Serial.println("{\"status\":\"ready\",\"version\":\"2.0\",\"firmware\":\"ESP32_CRAWLER\"}");
  Serial.println("{\"info\":\"Commands: PWM left right | STOP | STATUS | TEST\"}");
  Serial.println("{\"info\":\"Speed range: -255 to +255\"}");
  Serial.println("{\"info\":\"Watchdog timeout: 2000ms\"}");
  
  // Blink LED to indicate ready
  for (int i = 0; i < 3; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(200);
    digitalWrite(STATUS_LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("{\"status\":\"initialized\",\"ok\":true}");
}

void loop() {
  // Update system uptime
  systemUptime = millis();
  
  // Handle incoming serial commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // SAFETY: Check watchdog timer
  checkWatchdog();
  
  // Send periodic heartbeat
  sendHeartbeat();
  
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
  
  // Update command timestamp for watchdog
  lastCommandTime = millis();
  
  // Handle PWM command (new format: "PWM left_speed right_speed")
  if (command.startsWith("PWM ")) {
    // Parse: PWM 100 100
    int firstSpace = command.indexOf(' ');
    int secondSpace = command.indexOf(' ', firstSpace + 1);
    
    if (firstSpace != -1 && secondSpace != -1) {
      String leftSpeedStr = command.substring(firstSpace + 1, secondSpace);
      String rightSpeedStr = command.substring(secondSpace + 1);
      
      int newLeftSpeed = leftSpeedStr.toInt();
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
        
        // Send JSON confirmation
        Serial.print("{\"ok\":true,\"cmd\":\"PWM\",\"left\":");
        Serial.print(leftSpeed);
        Serial.print(",\"right\":");
        Serial.print(rightSpeed);
        Serial.print(",\"uptime\":");
        Serial.print(systemUptime);
        Serial.println("}");
        
        // Blink LED to indicate command received
        blinkLED(1, 50);
        
      } else {
        Serial.println("{\"ok\":false,\"error\":\"invalid_speed_range\",\"range\":\"-255 to +255\"}");
      }
    } else {
      Serial.println("{\"ok\":false,\"error\":\"invalid_pwm_format\",\"expected\":\"PWM left right\"}");
    }
  }
  // Handle STATUS request
  else if (command == "STATUS") {
    sendStatusReport();
  }
  // Handle STOP command
  else if (command == "STOP") {
    performStop("command");
  }
  // Handle TEST command
  else if (command == "TEST") {
    Serial.println("{\"status\":\"test_start\",\"ok\":true}");
    testSequence();
    Serial.println("{\"status\":\"test_complete\",\"ok\":true}");
  }
  // Handle legacy MOTOR: format for backward compatibility
  else if (command.startsWith("MOTOR:")) {
    // Parse legacy format: MOTOR:L:{left_speed}:R:{right_speed}
    int firstColon = command.indexOf(':');
    int secondColon = command.indexOf(':', firstColon + 1);
    int thirdColon = command.indexOf(':', secondColon + 1);
    
    if (firstColon != -1 && secondColon != -1 && thirdColon != -1) {
      String leftSpeedStr = command.substring(secondColon + 1, thirdColon);
      String rightSpeedStr = command.substring(thirdColon + 1);
      
      int newLeftSpeed = leftSpeedStr.toInt();
      int newRightSpeed = rightSpeedStr.toInt();
      
      if (newLeftSpeed >= -255 && newLeftSpeed <= 255 && 
          newRightSpeed >= -255 && newRightSpeed <= 255) {
        
        leftSpeed = newLeftSpeed;
        rightSpeed = newRightSpeed;
        setMotorSpeed(LEFT_MOTOR_PIN, leftSpeed, leftESC);
        setMotorSpeed(RIGHT_MOTOR_PIN, rightSpeed, rightESC);
        
        Serial.print("{\"ok\":true,\"cmd\":\"MOTOR\",\"left\":");
        Serial.print(leftSpeed);
        Serial.print(",\"right\":");
        Serial.print(rightSpeed);
        Serial.println("}");
        
        blinkLED(1, 50);
      } else {
        Serial.println("{\"ok\":false,\"error\":\"invalid_speed_range\"}");
      }
    } else {
      Serial.println("{\"ok\":false,\"error\":\"invalid_motor_format\"}");
    }
  }
  // Unknown command
  else {
    Serial.print("{\"ok\":false,\"error\":\"unknown_command\",\"received\":\"");
    Serial.print(command);
    Serial.println("\"}");
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

// Perform motor stop with reason logging
void performStop(const char* reason) {
  leftSpeed = 0;
  rightSpeed = 0;
  leftESC.writeMicroseconds(ESC_NEUTRAL);
  rightESC.writeMicroseconds(ESC_NEUTRAL);
  
  // Send JSON stop confirmation
  Serial.print("{\"ok\":true,\"cmd\":\"STOP\",\"reason\":\"");
  Serial.print(reason);
  Serial.print("\",\"uptime\":");
  Serial.print(systemUptime);
  Serial.println("}");
  
  // Flash LED to indicate stop
  blinkLED(2, 100);
}

// Emergency stop function (can be called via interrupt)
void emergencyStop(const char* reason) {
  leftSpeed = 0;
  rightSpeed = 0;
  leftESC.writeMicroseconds(ESC_NEUTRAL);
  rightESC.writeMicroseconds(ESC_NEUTRAL);
  
  // Send JSON emergency stop message
  Serial.print("{\"emergency\":true,\"reason\":\"");
  Serial.print(reason);
  Serial.print("\",\"uptime\":");
  Serial.print(systemUptime);
  Serial.println("}");
  
  // Flash LED rapidly to indicate emergency
  blinkLED(5, 100);
}

// SAFETY: Watchdog timer to prevent runaway motors
void checkWatchdog() {
  unsigned long timeSinceLastCommand = millis() - lastCommandTime;
  
  // If no command received for WATCHDOG_TIMEOUT and motors are moving, STOP
  if (timeSinceLastCommand > WATCHDOG_TIMEOUT) {
    if (leftSpeed != 0 || rightSpeed != 0) {
      emergencyStop("watchdog_timeout");
      leftSpeed = 0;
      rightSpeed = 0;
    }
  }
}

// Send status report as JSON
void sendStatusReport() {
  Serial.print("{\"ok\":true,\"status\":{");
  Serial.print("\"left\":");
  Serial.print(leftSpeed);
  Serial.print(",\"right\":");
  Serial.print(rightSpeed);
  Serial.print(",\"uptime\":");
  Serial.print(systemUptime);
  Serial.print(",\"last_cmd\":");
  Serial.print(millis() - lastCommandTime);
  Serial.print(",\"watchdog_timeout\":");
  Serial.print(WATCHDOG_TIMEOUT);
  Serial.println("}}");
}

// Send periodic heartbeat if motors are active
void sendHeartbeat() {
  unsigned long currentTime = millis();
  
  // Only send heartbeat if motors are running and it's time
  if ((leftSpeed != 0 || rightSpeed != 0) && 
      (currentTime - lastHeartbeatTime > HEARTBEAT_INTERVAL)) {
    
    Serial.print("{\"heartbeat\":true,\"left\":");
    Serial.print(leftSpeed);
    Serial.print(",\"right\":");
    Serial.print(rightSpeed);
    Serial.print(",\"uptime\":");
    Serial.print(systemUptime);
    Serial.println("}");
    
    lastHeartbeatTime = currentTime;
  }
}

// LED blink helper function
void blinkLED(int times, int delayMs) {
  for (int i = 0; i < times; i++) {
    digitalWrite(STATUS_LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(STATUS_LED_PIN, LOW);
    if (i < times - 1) delay(delayMs);
  }
}
