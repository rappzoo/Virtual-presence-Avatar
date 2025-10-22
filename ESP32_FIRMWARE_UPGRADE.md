# ESP32 Firmware v2.0 - Upgrade Guide

## 🎯 Overview

The ESP32 firmware has been upgraded to **version 2.0** with comprehensive safety features that match the backend motor safety system.

---

## ✨ What's New

### 🛡️ Enhanced Safety System

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Watchdog Timeout | 5 seconds | **2 seconds** |
| Response Format | Plain text | **JSON** |
| Heartbeat | None | **1-second interval** |
| Error Reporting | Basic | **Detailed JSON** |
| Stop Reasons | None | **Reason logging** |
| Command Format | MOTOR:L:x:R:x | **PWM x x** (+ legacy) |

---

## 🔄 Upgrade Process

### Option 1: Upload New Firmware (Recommended)

1. **Connect ESP32 to Computer**
   - Use USB cable
   - Note the COM port

2. **Open Arduino IDE**
   - File → Open → `esp32_firmware/crawler_motor_control.ino`

3. **Configure Arduino IDE**
   - Tools → Board → ESP32 Dev Module
   - Tools → Port → Select your ESP32 port
   - Tools → Upload Speed → 115200

4. **Upload Firmware**
   - Click Upload button (→)
   - Wait for "Done uploading" message

5. **Verify Upload**
   - Open Serial Monitor (Tools → Serial Monitor)
   - Set baud rate to 115200
   - Look for: `{"status":"initialized","ok":true}`

### Option 2: No Changes Needed

The backend Python code is **backward compatible** with v1.0 firmware. If your current firmware works, you can keep using it. However, **v2.0 is strongly recommended** for enhanced safety.

---

## 📊 Compatibility Matrix

| Backend | Firmware v1.0 | Firmware v2.0 |
|---------|---------------|---------------|
| Current (with safety) | ✅ Works | ✅ **Recommended** |
| Old (no safety) | ✅ Works | ✅ Works |

---

## 🔍 New Command Format

### v2.0 Primary Format (PWM)
```
Command:  PWM 100 100
Response: {"ok":true,"cmd":"PWM","left":100,"right":100,"uptime":12345}
```

### Legacy Format (Still Works)
```
Command:  MOTOR:L:100:R:100
Response: {"ok":true,"cmd":"MOTOR","left":100,"right":100}
```

### Status Command
```
Command:  STATUS
Response: {
  "ok": true,
  "status": {
    "left": 100,
    "right": 100,
    "uptime": 12345,
    "last_cmd": 500,
    "watchdog_timeout": 2000
  }
}
```

### Stop Command
```
Command:  STOP
Response: {"ok":true,"cmd":"STOP","reason":"command","uptime":12345}
```

---

## 🛡️ Safety Features

### 1. Watchdog Timer
- **Timeout**: 2 seconds
- **Behavior**: Auto-stops motors if no command received
- **Alert**: `{"emergency":true,"reason":"watchdog_timeout"}`
- **Purpose**: Prevents runaway motors

### 2. Heartbeat System
- **Interval**: 1 second (when motors active)
- **Format**: `{"heartbeat":true,"left":100,"right":100,"uptime":12345}`
- **Purpose**: Confirms firmware is responsive

### 3. Command Validation
- **Range**: -255 to +255
- **Invalid**: `{"ok":false,"error":"invalid_speed_range"}`
- **Purpose**: Prevents motor damage

### 4. Emergency Stop
- **Multiple Triggers**: STOP command, watchdog, errors
- **LED Flash**: 5 rapid blinks
- **Logging**: Reason included in response

---

## 🔧 Testing Your Firmware

### Test 1: Version Check
```bash
# Send STATUS command
echo "STATUS" > /dev/ttyACM0

# Expected v2.0 response:
# {"ok":true,"status":{...}}

# Old v1.0 response:
# STATUS_OK:L:0:R:0
```

### Test 2: PWM Format
```bash
# Send new PWM command
echo "PWM 50 50" > /dev/ttyACM0

# Expected v2.0 response:
# {"ok":true,"cmd":"PWM","left":50,"right":50}

# v1.0: No response (command not recognized)
```

### Test 3: Watchdog
```bash
# Start motors
echo "PWM 100 100" > /dev/ttyACM0

# Wait 3 seconds (don't send any commands)

# Expected v2.0 response:
# {"emergency":true,"reason":"watchdog_timeout"}

# Motors should stop automatically
```

---

## 🐛 Troubleshooting

### Issue: Motors don't stop after 2 seconds

**Cause**: Still using v1.0 firmware (5-second timeout)

**Solution**: Upload v2.0 firmware

**Quick Test**:
```bash
echo "PWM 100 100" > /dev/ttyACM0
# Wait and observe - v2.0 stops at 2s, v1.0 at 5s
```

---

### Issue: Getting "ERROR:UNKNOWN_COMMAND" for PWM

**Cause**: v1.0 firmware doesn't support PWM format

**Solution**: Upload v2.0 firmware OR use legacy format:
```bash
# Use this with v1.0:
echo "MOTOR:L:100:R:100" > /dev/ttyACM0
```

---

### Issue: No JSON responses

**Cause**: v1.0 firmware uses plain text

**Solution**: 
- Upload v2.0 for JSON, OR
- Backend already handles both formats automatically

---

### Issue: Upload fails in Arduino IDE

**Common Fixes**:
1. **Check Port**: Tools → Port → Select correct port
2. **Close Serial Monitor**: Must be closed during upload
3. **Press Boot Button**: Hold BOOT on ESP32 during upload start
4. **Check Cable**: Try different USB cable
5. **Driver**: Install CH340/CP2102 driver if needed

---

## 📱 Backend Integration

### Current Backend (Already Compatible)

The Python `motor_controller.py` already handles both formats:

```python
# Sends PWM format (v2.0 compatible)
command = f"PWM {left_speed} {right_speed}"
self.ser.write(command_bytes)

# Reads JSON response from v2.0
# Falls back to plain text for v1.0
response = self.ser.read_all().decode('utf-8', 'ignore')
```

**No backend code changes needed!** The motor controller auto-detects response format.

---

## 🎯 Timing Configuration

### Recommended Settings

| Component | Timeout | Purpose |
|-----------|---------|---------|
| Frontend heartbeat | 500ms | Send commands every 500ms |
| Backend heartbeat | 1500ms | Stop if no command for 1.5s |
| ESP32 watchdog | 2000ms | Hardware-level safety |

**Safety Margin**: 4x (firmware timeout is 4x longer than command interval)

### Why These Times?

```
Frontend sends commands every 500ms
  ↓
Backend expects command every 1500ms (3x margin)
  ↓
ESP32 expects command every 2000ms (4x margin)
  ↓
If all fail, ESP32 watchdog stops motors at 2s
```

---

## 🔄 Rollback Plan

### If v2.0 Causes Issues

1. **Keep v1.0 Firmware**: 
   - Old firmware file is in `archive/` or git history
   - Backend is fully compatible

2. **Upload Old Firmware**:
   ```bash
   # Get old version from git
   cd /home/havatar/Avatar-robot
   git show HEAD~1:esp32_firmware/crawler_motor_control.ino > old_firmware.ino
   
   # Upload via Arduino IDE
   ```

3. **Report Issue**: Note any errors or unexpected behavior

---

## ✅ Verification Checklist

After uploading v2.0, verify:

- [ ] Serial Monitor shows `{"status":"initialized","ok":true}`
- [ ] `STATUS` command returns JSON
- [ ] `PWM 50 50` moves motors and returns JSON
- [ ] Motors stop automatically after 2 seconds
- [ ] `STOP` command works
- [ ] Heartbeat messages appear when motors running
- [ ] LED blinks on command received

---

## 📚 Additional Resources

- **Full Documentation**: `esp32_firmware/README.md`
- **Motor Safety System**: `MOTOR_SAFETY.md`
- **Firmware Source**: `esp32_firmware/crawler_motor_control.ino`
- **Test Scripts**: `esp32_firmware/test_esp32_communication.py`

---

## 🎉 Benefits of Upgrading

1. ✅ **Faster Safety Response** - 2s vs 5s watchdog
2. ✅ **Better Error Handling** - JSON with detailed messages
3. ✅ **Heartbeat Monitoring** - Know firmware is alive
4. ✅ **Improved Debugging** - Structured JSON logs
5. ✅ **Modern Protocol** - PWM format is cleaner
6. ✅ **Full Compatibility** - Works with both old and new backend

---

## 💡 Recommendation

**Upload v2.0 firmware** for the best safety and reliability. The upgrade takes 2 minutes and provides significant safety improvements.

**The backend already supports v2.0**, so no software changes needed on the RPi5 side!

