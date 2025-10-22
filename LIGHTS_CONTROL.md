# Lights Control System Documentation

## Overview

The Avatar Tank now has front and back lights control via Solid State Relay (SSR) modules, controllable from the web interface.

---

## Hardware Setup

### Components Required
- **2x Solid State Relay (SSR) modules** (5V trigger, AC/DC load compatible)
- **Front lights** (connected to SSR1 output)
- **Back lights** (connected to SSR2 output)
- **Power supply** for lights (separate from ESP32)

### ESP32 GPIO Pins
- **GPIO 25** → Front Lights SSR (trigger pin)
- **GPIO 26** → Back Lights SSR (trigger pin)

### Wiring Diagram
```
ESP32                SSR Module 1 (Front)        Front Lights
GPIO 25  ─────────→  Signal (+)
GND      ─────────→  Signal (-)
                     Load (+)    ─────────→  Light (+)
                     Load (-)    ─────────→  Light (-)

ESP32                SSR Module 2 (Back)         Back Lights  
GPIO 26  ─────────→  Signal (+)
GND      ─────────→  Signal (-)
                     Load (+)    ─────────→  Light (+)
                     Load (-)    ─────────→  Light (-)

Note: SSR modules isolate the high-voltage/high-current lights
      from the low-voltage ESP32 control signals.
```

### Safety Notes
⚠️ **IMPORTANT:**
- SSR modules provide electrical isolation between ESP32 and lights
- Use appropriate SSR for your light power (AC or DC, voltage, current)
- Ensure proper wiring and insulation for high-voltage lights
- Test with low-power LEDs first before connecting main lights
- Use appropriate fuses on the load side

---

## Features

### 🔦 Front Lights
- Yellow/amber indicator
- Controlled via GPIO 25
- Button in Media Controls panel
- Visual feedback on button and status display

### 💡 Back Lights
- Red indicator
- Controlled via GPIO 26
- Button in Media Controls panel
- Visual feedback on button and status display

### 📊 System Integration
- Lights state included in STATUS command
- JSON responses for all operations
- Part of motor watchdog system (updates heartbeat)
- Persistent state tracking

---

## Usage

### Web Interface

**Location**: Media Controls Panel (below Stream Settings)

**Buttons**:
- 🔦 **Front Lights** - Toggle front lights on/off
- 💡 **Back Lights** - Toggle back lights on/off

**Status Display**: Shows current state of both lights
- `FRONT ON | Back Off` - Front is on, back is off
- `Front Off | BACK ON` - Front is off, back is on
- etc.

**Visual Feedback**:
- **OFF**: Gray button with dark border
- **ON (Front)**: Yellow/amber background with bright border
- **ON (Back)**: Red background with bright border

---

## API Documentation

### Control Lights

**Endpoint**: `POST /lights/<position>/<state>`

**Parameters**:
- `position`: `front` or `back`
- `state`: `on` or `off`

**Examples**:
```bash
# Turn on front lights
curl -X POST http://localhost:5000/lights/front/on

# Turn off back lights
curl -X POST http://localhost:5000/lights/back/off
```

**Response** (JSON):
```json
{
  "ok": true,
  "cmd": "LIGHTS",
  "light": "front",
  "state": "on"
}
```

**Error Response**:
```json
{
  "ok": false,
  "error": "invalid_light_position",
  "expected": "FRONT or BACK"
}
```

---

## ESP32 Protocol

### Command Format
```
LIGHTS <position> <state>
```

**Parameters**:
- `<position>`: `FRONT` or `BACK`
- `<state>`: `ON` or `OFF`

### Examples
```
LIGHTS FRONT ON      # Turn on front lights
LIGHTS BACK OFF      # Turn off back lights
```

### Response (JSON)
```json
{
  "ok": true,
  "cmd": "LIGHTS",
  "light": "front",
  "state": "on"
}
```

### Status Command
```
STATUS
```

**Response includes lights state**:
```json
{
  "ok": true,
  "status": {
    "left": 0,
    "right": 0,
    "front_lights": "on",
    "back_lights": "off",
    "uptime": 12345,
    "last_cmd": 100,
    "watchdog_timeout": 2000
  }
}
```

---

## Python Integration

### Using Motor Controller
```python
from modules.motor_controller import motors

# Turn on front lights
result = motors.set_lights('front', True)
print(result)  # {'ok': True, 'cmd': 'LIGHTS', 'light': 'front', 'state': 'on'}

# Turn off back lights
result = motors.set_lights('back', False)
print(result)  # {'ok': True, 'cmd': 'LIGHTS', 'light': 'back', 'state': 'off'}
```

### Direct API Call
```python
import requests

# Turn on front lights
response = requests.post('http://localhost:5000/lights/front/on')
result = response.json()
print(result)

# Turn off back lights
response = requests.post('http://localhost:5000/lights/back/off')
result = response.json()
print(result)
```

---

## JavaScript Integration

### Using Built-in Functions
```javascript
// Toggle lights (automatically manages state)
toggleLights('front');   // Toggles front lights
toggleLights('back');    // Toggles back lights

// Check current state
console.log(lightsState.front);  // true or false
console.log(lightsState.back);   // true or false
```

### Manual API Call
```javascript
async function setLight(position, state) {
  const response = await fetch(`/lights/${position}/${state}`, {
    method: 'POST'
  });
  const result = await response.json();
  return result;
}

// Usage
await setLight('front', 'on');
await setLight('back', 'off');
```

---

## Testing

### 1. ESP32 Serial Monitor Test
```
1. Connect ESP32 to computer
2. Open Serial Monitor (115200 baud)
3. Send: LIGHTS FRONT ON
4. Expect: {"ok":true,"cmd":"LIGHTS","light":"front","state":"on"}
5. Check: GPIO 25 should be HIGH (3.3V)
```

### 2. With LED Test (Recommended First Test)
```
1. Connect LED to GPIO 25 (with 220Ω resistor to GND)
2. Send: LIGHTS FRONT ON
3. LED should light up
4. Send: LIGHTS FRONT OFF
5. LED should turn off
```

### 3. With SSR Module Test
```
1. Connect SSR trigger to GPIO 25 and GND
2. Connect multimeter to SSR output (load side)
3. Send: LIGHTS FRONT ON
4. Multimeter should show continuity/low resistance
5. Send: LIGHTS FRONT OFF
6. Multimeter should show open circuit/high resistance
```

### 4. Full System Test (With Actual Lights)
```
⚠️ ONLY after verifying SSR operation with multimeter!

1. Connect lights to SSR output (load side)
2. Ensure proper power supply for lights
3. Use appropriate fuses
4. Test from web interface:
   - Click "🔦 Front Lights" button
   - Front lights should turn on
   - Button should turn yellow/amber
   - Click again to turn off
```

---

## Troubleshooting

### Lights Don't Turn On

**Check ESP32**:
```bash
# Send STATUS command
echo "STATUS" > /dev/ttyACM0
# Should show lights state
```

**Check GPIO**:
```bash
# Measure voltage on GPIO 25/26 when on
# Should be 3.3V (HIGH) when on
# Should be 0V (LOW) when off
```

**Check SSR Module**:
- Verify trigger voltage (usually 3-5V)
- Check SSR indicator LED (should light when triggered)
- Measure continuity on load side when triggered
- Verify proper wiring (+ to signal+, - to GND)

**Check Wiring**:
- ESP32 GPIO 25 → SSR1 Signal+
- ESP32 GND → SSR1 Signal-
- Power supply → Lights → SSR Load side

### Lights Turn On But Don't Turn Off

**Possible Causes**:
- SSR stuck closed (replace SSR)
- Wiring short circuit
- Software state mismatch

**Debug**:
```python
# Check software state
from modules.motor_controller import motors
status = motors.send_command("STATUS")
print(status)  # Check front_lights and back_lights state
```

### Firmware Not Responding to LIGHTS Command

**Check Firmware Version**:
- Must be v2.0 or later
- Upload latest ESP32 firmware from `esp32_firmware/`

**Test**:
```bash
# Open Serial Monitor
# Send: LIGHTS FRONT ON
# Old firmware: {"ok":false,"error":"unknown_command"}
# New firmware: {"ok":true,"cmd":"LIGHTS",...}
```

---

## Safety Features

### 1. SSR Protection
- Electrical isolation from ESP32
- No feedback voltage to GPIO pins
- Overcurrent protection (via fuses on load side)

### 2. Software Interlocks
- State tracking prevents undefined states
- JSON error responses for invalid commands
- Heartbeat integration (lights update watchdog)

### 3. Emergency Shutdown
- When motors stop (emergency or watchdog), lights remain independently controllable
- Lights do NOT automatically turn off with motors (by design)
- Manual control always available

---

## Specifications

### ESP32 GPIO
- **Voltage**: 3.3V (HIGH)
- **Current**: 40mA max per pin
- **GPIO 25**: Front lights control
- **GPIO 26**: Back lights control

### Recommended SSR
- **Trigger Voltage**: 3-5V DC
- **Trigger Current**: < 10mA
- **Load Voltage**: Match your lights (12V, 24V, 120V AC, etc.)
- **Load Current**: Match your lights with safety margin

### Example SSR Specs
- **Fotek SSR-25DA**: 3-32V DC trigger, 24-380V AC load, 25A
- **Omron G3MB-202P**: 5V DC trigger, 100-240V AC load, 2A  
- **SainSmart 2-channel 5V SSR**: 5V DC trigger, suitable for DC loads

---

## Wiring Best Practices

### 1. Low-Voltage Side (ESP32 to SSR trigger)
```
ESP32 GPIO → SSR Signal+ (short wire, < 30cm)
ESP32 GND → SSR Signal- (shared ground)
```

### 2. High-Voltage Side (SSR load to lights)
```
Power Supply (+) → SSR Load (+)
SSR Load (-) → Lights (+)
Lights (-) → Power Supply (-)

OR

Power Supply (+) → Lights (+)
Lights (-) → SSR Load (+)
SSR Load (-) → Power Supply (-)

(SSR acts as switch in the circuit)
```

### 3. Safety
- Use appropriate wire gauge for load current
- Add fuses on load side (1.5x expected current)
- Ensure proper ventilation for SSR (they can get hot)
- Use heat sink if load > 5A
- Secure all connections
- Insulate exposed terminals

---

## Confirmed Working

✅ **Motor Speed Control**: Slider works (confirmed existing)
✅ **ESP32 Crawler Mode**: Two ESCs for differential drive
✅ **Lights Control**: Two GPIO pins for SSR modules
✅ **Web Interface**: Buttons added to Media Controls panel
✅ **API Integration**: Backend routes functional
✅ **JSON Protocol**: All responses in structured format

---

## Next Steps

1. **Upload Firmware**: Flash ESP32 with updated firmware
2. **Test GPIO**: Verify GPIO 25/26 output with multimeter/LED
3. **Connect SSR**: Wire SSR modules to GPIO pins
4. **Test SSR**: Verify SSR switching with multimeter
5. **Connect Lights**: Wire lights through SSR load side
6. **Test System**: Use web interface to control lights
7. **Add Fuses**: Install appropriate fuses for safety
8. **Enjoy!**: Control your Avatar Tank lights remotely

---

## Version History

### v1.0 (Current)
- Initial lights control implementation
- GPIO 25 (front), GPIO 26 (back)
- Web interface buttons
- JSON API
- Status reporting

---

## Support

For issues or questions:
1. Check ESP32 firmware version (must be v2.0+)
2. Verify GPIO wiring with multimeter
3. Test SSR independently
4. Check Serial Monitor for error messages
5. Review wiring diagram above

---

## License

This feature is part of the Avatar Tank system, provided as-is for educational and hobby use.

