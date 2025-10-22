# ESP32 Crawler Motor Control Firmware v2.0

This firmware controls two ESCs (Electronic Speed Controllers) for crawler-style movement via USB serial communication with the RPi5.

## 🆕 Version 2.0 Updates

### New Safety Features
- **2-Second Watchdog Timer** - Auto-stops motors if no command received
- **JSON Response Format** - Structured error handling and status reporting
- **Heartbeat System** - Periodic status updates when motors active
- **Enhanced Stop Commands** - Multiple stop mechanisms with reason logging
- **Improved Error Messages** - Detailed JSON error responses

### New Command Format
- **PWM Command** - `PWM left_speed right_speed` (primary format)
- **Legacy Support** - Old `MOTOR:L:x:R:x` format still works
- **JSON Responses** - All responses now in JSON format

---

## Hardware Requirements

### ESP32 Development Board
- ESP32 DevKit V1 or similar
- USB cable for programming and communication
- Power supply (5V recommended)

### ESCs (Electronic Speed Controllers)
- Two ESCs compatible with your motors
- ESC calibration required (see calibration section)

### Motors
- Two brushed or brushless motors
- Appropriate power supply for motors

### Optional Components
- Status LED (connected to GPIO 2)
- Emergency stop button (connected to GPIO 0 with pull-up)

---

## Wiring Diagram

```
ESP32          ESC1 (Left)    ESC2 (Right)
GPIO 18   -->  Signal Pin
GPIO 19   -->                  Signal Pin
GND       -->  GND             GND
5V        -->  VCC             VCC
GPIO 2    -->  LED Anode (+)
GPIO 0    -->  Emergency Stop Button
```

---

## Installation Instructions

### 1. Install Arduino IDE
- Download Arduino IDE from https://www.arduino.cc/en/software
- Install ESP32 board support:
  - File → Preferences → Additional Boards Manager URLs
  - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  - Tools → Board → Boards Manager → Search "ESP32" → Install

### 2. Configure Arduino IDE
- Tools → Board → ESP32 Arduino → ESP32 Dev Module
- Tools → Port → Select your ESP32 port
- Tools → Upload Speed → 115200
- Tools → CPU Frequency → 240MHz (WiFi/BT)
- Tools → Flash Frequency → 80MHz
- Tools → Flash Mode → QIO
- Tools → Flash Size → 4MB (32Mb)
- Tools → Partition Scheme → Default 4MB with spiffs

### 3. Install Required Libraries
- Tools → Manage Libraries → Search "ESP32Servo" → Install

### 4. Upload Firmware
- Open `crawler_motor_control.ino`
- Click Upload button
- Wait for upload to complete

---

## Communication Protocol v2.0

### Primary Command Format (NEW)
```
PWM left_speed right_speed
```

**Examples:**
```
PWM 100 100      // Both motors forward at speed 100
PWM -50 50       // Turn left (left reverse, right forward)
PWM 0 0          // Stop both motors
PWM 150 130      // Forward with slight right turn
```

**Response:**
```json
{"ok":true,"cmd":"PWM","left":100,"right":100,"uptime":12345}
```

### Legacy Format (BACKWARD COMPATIBLE)
```
MOTOR:L:{left_speed}:R:{right_speed}
```

**Example:**
```
MOTOR:L:150:R:150
```

**Response:**
```json
{"ok":true,"cmd":"MOTOR","left":150,"right":150}
```

### Control Commands

| Command | Description | Response |
|---------|-------------|----------|
| `PWM left right` | Set motor speeds | `{"ok":true,"left":x,"right":x}` |
| `STOP` | Emergency stop | `{"ok":true,"cmd":"STOP","reason":"command"}` |
| `STATUS` | Get current status | `{"ok":true,"status":{...}}` |
| `TEST` | Run test sequence | `{"status":"test_start","ok":true}` |

### Parameters
- **Speed Range**: -255 to +255
  - Positive = Forward
  - Negative = Reverse
  - 0 = Stop
- **JSON Format**: All responses in JSON

---

## Safety Features

### 🛡️ Multi-Layer Safety System

#### 1. Watchdog Timer
- **Timeout**: 2000ms (2 seconds)
- **Action**: Auto-stop if no command received
- **Status**: Active when motors running
- **Response**: `{"emergency":true,"reason":"watchdog_timeout"}`

#### 2. Command Validation
- Speed range: -255 to +255
- Invalid commands return error JSON
- Malformed data rejected with error message

#### 3. Heartbeat System
- Periodic status updates every 1 second
- Only when motors are active
- Format: `{"heartbeat":true,"left":x,"right":x,"uptime":x}`

#### 4. Emergency Stop
- Multiple ways to trigger stop
- Reason logging for debugging
- Immediate motor shutdown
- LED flash indication

#### 5. Status Reporting
```json
{
  "ok": true,
  "status": {
    "left": 0,
    "right": 0,
    "uptime": 12345,
    "last_cmd": 500,
    "watchdog_timeout": 2000
  }
}
```

---

## Testing

### 1. Serial Monitor Test (v2.0)
```
1. Tools → Serial Monitor
2. Set baud rate to 115200
3. Send: STATUS
4. Expect: {"ok":true,"status":{...}}
```

### 2. Motor Test (PWM Format)
```
1. Send: PWM 50 50
2. Expect: {"ok":true,"cmd":"PWM","left":50,"right":50}
3. Motors move forward slowly
4. Send: PWM 0 0
5. Expect: {"ok":true,"cmd":"PWM","left":0,"right":0}
6. Motors stop
```

### 3. Watchdog Test
```
1. Send: PWM 100 100
2. Wait 3 seconds (no commands)
3. Expect: {"emergency":true,"reason":"watchdog_timeout"}
4. Motors stop automatically
```

### 4. Full Test Sequence
```
1. Send: TEST
2. Expect: {"status":"test_start","ok":true}
3. Watch test sequence run
4. Expect: {"status":"test_complete","ok":true}
```

---

## ESC Calibration

### Important: Calibrate ESCs Before First Use

1. **Power off everything**
2. **Upload firmware to ESP32**
3. **Power on ESP32 only** (no ESCs connected)
4. **Connect ESCs to ESP32**
5. **Power on ESCs** (they will beep)
6. **Wait for calibration sequence** (about 2 seconds)
7. **Test with low speeds first**

### Manual ESC Calibration (if needed)
```cpp
void calibrateESC() {
  Serial.println("{\"status\":\"calibration_start\"}");
  
  // Send maximum signal
  leftESC.writeMicroseconds(2000);
  rightESC.writeMicroseconds(2000);
  delay(2000);
  
  // Send minimum signal
  leftESC.writeMicroseconds(1000);
  rightESC.writeMicroseconds(1000);
  delay(2000);
  
  // Send neutral signal
  leftESC.writeMicroseconds(1500);
  rightESC.writeMicroseconds(1500);
  delay(2000);
  
  Serial.println("{\"status\":\"calibration_complete\"}");
}
```

---

## Integration with RPi5

### Python Integration (v2.0)
```python
import serial
import json
import time

class MotorController:
    def __init__(self, port='/dev/ttyACM0', baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Wait for ESP32 to initialize
        
    def send_pwm(self, left, right):
        """Send PWM command in new format"""
        cmd = f"PWM {left} {right}\n"
        self.ser.write(cmd.encode())
        
        # Read JSON response
        response = self.ser.readline().decode().strip()
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"ok": False, "error": "invalid_response"}
    
    def stop(self):
        """Emergency stop"""
        self.ser.write(b"STOP\n")
        response = self.ser.readline().decode().strip()
        try:
            return json.loads(response)
        except:
            return {"ok": False}
    
    def status(self):
        """Get current status"""
        self.ser.write(b"STATUS\n")
        response = self.ser.readline().decode().strip()
        try:
            return json.loads(response)
        except:
            return {"ok": False}

# Usage
motors = MotorController('/dev/ttyACM0')

# Move forward
result = motors.send_pwm(100, 100)
print(f"Move result: {result}")

# Get status
status = motors.status()
print(f"Status: {status}")

# Stop
stop = motors.stop()
print(f"Stop result: {stop}")
```

---

## Troubleshooting

### Common Issues

#### JSON Parse Errors
- **Cause**: Multiple messages in buffer
- **Fix**: Read all available lines until valid JSON
- **Solution**: Clear input buffer before sending command

#### Watchdog Triggering Too Soon
- **Cause**: Command interval > 2 seconds
- **Fix**: Send commands every 500ms while moving
- **Config**: Adjust `WATCHDOG_TIMEOUT` in firmware

#### Motors Not Responding
- **Check**: ESC power connections
- **Check**: ESC calibration
- **Check**: JSON response for errors
- **Test**: Send STATUS command

#### Communication Timeout
- **Check**: USB cable connection
- **Check**: Baud rate (115200)
- **Check**: Serial port permissions
- **Fix**: `sudo chmod 666 /dev/ttyACM0`

---

## Configuration

### Pin Configuration
```cpp
#define LEFT_MOTOR_PIN 18    // Change to your preferred pin
#define RIGHT_MOTOR_PIN 19   // Change to your preferred pin
#define STATUS_LED_PIN 2     // Change to your preferred pin
```

### Safety Timing
```cpp
const unsigned long WATCHDOG_TIMEOUT = 2000;  // 2 seconds
const unsigned long HEARTBEAT_INTERVAL = 1000;  // 1 second
```

### ESC Calibration Values
```cpp
#define ESC_MIN_PULSE 1000   // Adjust for your ESCs
#define ESC_MAX_PULSE 2000   // Adjust for your ESCs
#define ESC_NEUTRAL 1500     // Adjust for your ESCs
```

---

## Safety Recommendations

### Testing Safety
1. ✅ Always test with low speeds first (< 100)
2. ✅ Keep emergency stop accessible
3. ✅ Monitor watchdog timeout behavior
4. ✅ Test communication failure scenarios

### Operational Safety
1. ✅ Backend should send commands every 500ms
2. ✅ Backend timeout should be > 2s (e.g., 3s)
3. ✅ Monitor heartbeat messages
4. ✅ Handle JSON errors gracefully

### Hardware Safety
1. ✅ Use appropriate fuses/circuit breakers
2. ✅ Monitor motor temperature
3. ✅ Check ESC ratings
4. ✅ Verify power supply capacity

---

## Version History

### v2.0.0 (Current)
- ✅ New PWM command format
- ✅ JSON response format
- ✅ 2-second watchdog timer
- ✅ Heartbeat system
- ✅ Enhanced error handling
- ✅ Backward compatibility

### v1.0.0
- Initial release
- Basic motor control
- Legacy MOTOR: format
- 5-second watchdog

---

## License

This firmware is provided as-is for educational and hobby use. Use at your own risk.
