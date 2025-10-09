# ESP32 Crawler Motor Control Firmware

This firmware controls two ESCs (Electronic Speed Controllers) for crawler-style movement via USB serial communication with the RPi5.

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

## Wiring Diagram

```
ESP32          ESC1 (Left)    ESC2 (Right)
GPIO 18   -->  Signal Pin
GPIO 19   -->  Signal Pin
GND       -->  GND            GND
5V        -->  VCC            VCC
GPIO 2    -->  LED Anode (+)
GPIO 0    -->  Emergency Stop Button
```

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
// Add this to setup() function for manual calibration
void calibrateESC() {
  Serial.println("ESC_CALIBRATION_START");
  
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
  
  Serial.println("ESC_CALIBRATION_COMPLETE");
}
```

## Communication Protocol

### Command Format
```
MOTOR:L:{left_speed}:R:{right_speed}
```

### Parameters
- `left_speed`: -255 to +255 (negative = reverse)
- `right_speed`: -255 to +255 (negative = reverse)
- `0`: Stop motor

### Example Commands
```
MOTOR:L:150:R:150    // Both motors forward at speed 150
MOTOR:L:-100:R:100   // Turn left (left reverse, right forward)
MOTOR:L:0:R:0        // Stop both motors
MOTOR:L:200:R:180    // Forward with slight right turn
```

### Response Format
```
MOTOR_OK:L:{left_speed}:R:{right_speed}
MOTOR_ERROR:INVALID_SPEED_RANGE
MOTOR_ERROR:INVALID_FORMAT
ERROR:UNKNOWN_COMMAND
```

### Status Commands
```
STATUS              // Get current motor speeds
STOP                // Emergency stop
TEST                // Run test sequence
```

## Testing

### 1. Serial Monitor Test
- Tools → Serial Monitor
- Set baud rate to 115200
- Send `STATUS` command
- Should receive: `STATUS_OK:L:0:R:0`

### 2. Motor Test
- Send `TEST` command
- Motors should run test sequence: forward → backward → left → right → stop
- Watch for any unusual behavior

### 3. Manual Control Test
- Send `MOTOR:L:100:R:100`
- Motors should move forward slowly
- Send `MOTOR:L:0:R:0`
- Motors should stop

## Troubleshooting

### Common Issues

#### Motors Not Moving
- Check ESC power connections
- Verify ESC calibration
- Check motor connections
- Ensure ESCs are compatible with motors

#### Erratic Movement
- Check for loose connections
- Verify ESC calibration
- Check power supply stability
- Reduce speed values

#### Communication Errors
- Check USB cable connection
- Verify baud rate (115200)
- Check RPi5 serial port permissions
- Restart ESP32

#### ESC Beeping
- Normal during startup
- Continuous beeping = calibration issue
- Intermittent beeping = power issue

### Debug Mode
Enable debug output by uncommenting debug lines in the firmware:
```cpp
#define DEBUG_MODE true
```

## Safety Features

### Built-in Safety
- Auto-stop on communication loss (5 seconds)
- Speed range validation (-255 to +255)
- Emergency stop function
- Watchdog timer

### Recommended Safety
- Always test with low speeds first
- Keep emergency stop accessible
- Monitor motor temperature
- Use appropriate fuses/circuit breakers

## Customization

### Pin Configuration
```cpp
#define LEFT_MOTOR_PIN 18    // Change to your preferred pin
#define RIGHT_MOTOR_PIN 19   // Change to your preferred pin
#define STATUS_LED_PIN 2     // Change to your preferred pin
```

### ESC Calibration Values
```cpp
#define ESC_MIN_PULSE 1000   // Adjust for your ESCs
#define ESC_MAX_PULSE 2000   // Adjust for your ESCs
#define ESC_NEUTRAL 1500     // Adjust for your ESCs
```

### Communication Settings
```cpp
Serial.begin(115200);       // Change baud rate if needed
Serial.setTimeout(100);      // Adjust timeout if needed
```

## Integration with RPi5

### Serial Port Setup
```bash
# Check available serial ports
ls /dev/ttyUSB*

# Set permissions (run as root or add user to dialout group)
sudo chmod 666 /dev/ttyUSB0

# Add user to dialout group
sudo usermod -a -G dialout $USER
```

### Python Test Script
```python
import serial
import time

# Open serial connection
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Send test command
ser.write(b'MOTOR:L:100:R:100\n')
time.sleep(2)

# Stop motors
ser.write(b'MOTOR:L:0:R:0\n')

# Close connection
ser.close()
```

## Version History

### v1.0.0
- Initial release
- Basic motor control
- USB serial communication
- ESC calibration support
- Safety features

## Support

For issues or questions:
1. Check troubleshooting section
2. Verify hardware connections
3. Test with serial monitor
4. Check ESC calibration
5. Review error messages

## License

This firmware is provided as-is for educational and hobby use. Use at your own risk.
