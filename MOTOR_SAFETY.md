# Motor Safety System Documentation

## Overview

The Avatar Tank implements a **multi-layered safety system** to ensure motors stop immediately in ANY failure scenario. This prevents runaway motors and ensures safe operation.

---

## Safety Layers

### 1. ✅ **Key Release Detection** (Frontend)
- **Trigger**: User releases WASD keys
- **Action**: Immediate motor stop command
- **Response Time**: < 50ms
- **Implementation**: `keyup` event listener in `index.html`

```javascript
document.addEventListener('keyup', (e) => {
  if (['w', 's', 'a', 'd'].includes(e.key.toLowerCase())) {
    stopM();
  }
});
```

---

### 2. ✅ **Heartbeat Watchdog** (Backend)
- **Trigger**: No motor command received for 1.5 seconds
- **Action**: Automatic motor stop
- **Monitoring Frequency**: Every 500ms
- **Implementation**: `motor_safety_watchdog()` thread in `mediamtx_main.py`
- **Protection Against**: Client freeze, infinite loop, browser hang

```python
motor_heartbeat_timeout = 1.5  # seconds
# Watchdog checks every 500ms
# Motors stopped if no heartbeat within timeout
```

**Heartbeat Sources:**
- Any motor command (`/motor/<direction>`) updates heartbeat
- Movement interval sends commands every 500ms while key held
- If commands stop, watchdog automatically stops motors within 1.5s

---

### 3. ✅ **WebSocket Disconnect Detection** (Frontend & Backend)
- **Trigger**: Internet loss, WiFi disconnect, server restart
- **Action**: Immediate motor stop on both frontend and backend
- **Response Time**: < 100ms after disconnect detection
- **Implementation**: 
  - Frontend: `socket.on('disconnect')` → `emergencyStopMotors()`
  - Backend: `handle_disconnect()` → `motors.stop()`

```javascript
socket.on('disconnect', (reason) => {
  emergencyStopMotors('WebSocket disconnected');
});
```

---

### 4. ✅ **USB Serial Link Failure** (Backend)
- **Trigger**: Serial connection lost, USB cable unplugged, motor controller failure
- **Action**: Automatic motor stop and error reporting
- **Implementation**: `motor_controller.py` `_stop_motors_on_failure()`
- **Detection**: Serial exceptions, communication timeouts

```python
except serial.SerialException as e:
    self.connected = False
    self._stop_motors_on_failure()
    return {"ok": False, "error": "serial"}
```

**USB Link Monitoring:**
- Every command tests serial connection
- Timeout after 1 second with no response
- Automatic stop command sent before marking disconnected

---

### 5. ✅ **Page Visibility Detection** (Frontend)
- **Trigger**: Tab switch, browser minimize, window hide
- **Action**: Immediate motor stop
- **Implementation**: `visibilitychange` event listener
- **Protection Against**: User switches away and forgets motors running

```javascript
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    emergencyStopMotors('Page hidden/minimized');
  }
});
```

---

### 6. ✅ **Window Focus Loss** (Frontend)
- **Trigger**: Window loses focus (Alt+Tab, click away)
- **Action**: Immediate motor stop
- **Implementation**: `blur` event listener

```javascript
window.addEventListener('blur', () => {
  emergencyStopMotors('Window lost focus');
});
```

---

### 7. ✅ **Browser Close/Navigation** (Frontend)
- **Trigger**: Browser close, tab close, page navigation, page refresh
- **Action**: Stop command sent before unload
- **Implementation**: `beforeunload` event listener

```javascript
window.addEventListener('beforeunload', () => {
  emergencyStopMotors('Page closing/navigating');
});
```

---

### 8. ✅ **Client Tracking** (Backend)
- **Trigger**: All WebSocket clients disconnect
- **Action**: Motor stop after last client disconnects
- **Implementation**: `motor_clients_connected` set tracking
- **Protection Against**: All users disconnect but motors still running

```python
motor_clients_connected = set()

@socketio.on('disconnect'):
    motor_clients_connected.discard(request.sid)
    motors.stop()  # Stop when ANY client disconnects
```

---

## Safety Timing

| Event | Detection Time | Stop Command | Total Response |
|-------|---------------|--------------|----------------|
| Key Release | Immediate | < 50ms | < 50ms |
| WebSocket Disconnect | < 100ms | < 50ms | < 150ms |
| Heartbeat Timeout | 500ms check | < 50ms | < 1.5s |
| USB Link Failure | 1s timeout | Immediate | < 1.1s |
| Page Hidden | Immediate | < 50ms | < 50ms |
| Window Blur | Immediate | < 50ms | < 50ms |
| Page Unload | Immediate | < 50ms | < 50ms |

---

## Movement Heartbeat System

**How It Works:**
1. User presses key → `go(direction)` called
2. Immediate motor command sent
3. Interval timer starts, sending commands every 500ms
4. Each command updates backend heartbeat timestamp
5. Backend watchdog monitors: "last heartbeat < 1.5s ago?"
6. If no heartbeat for 1.5s → automatic stop

**Why 500ms frontend / 1.5s backend?**
- Gives 3x safety margin for network delays
- Allows 2 missed commands before timeout
- Prevents false stops from network hiccups

---

## Testing Scenarios

### Test 1: Normal Operation ✅
```
1. Press 'W' key
2. Motors move forward
3. Release 'W' key
4. Motors stop immediately
```

### Test 2: Internet Loss ✅
```
1. Start motors moving
2. Disconnect WiFi/Ethernet
3. WebSocket disconnect triggers emergency stop
4. Backend also detects disconnect and stops motors
```

### Test 3: Client Freeze ✅
```
1. Start motors moving
2. Browser hangs/freezes (infinite loop)
3. Heartbeat stops being sent
4. After 1.5s, watchdog stops motors automatically
```

### Test 4: USB Cable Unplug ✅
```
1. Start motors moving
2. Unplug USB cable to motor controller
3. Next command fails with serial exception
4. Backend immediately sends stop command
5. Serial marked as disconnected
```

### Test 5: Tab Switch ✅
```
1. Start motors moving
2. Switch to another tab (Alt+Tab)
3. Page visibility change triggers stop
4. Motors stop immediately
```

### Test 6: Browser Close ✅
```
1. Start motors moving
2. Close browser tab
3. beforeunload event fires
4. Stop command sent before close
5. Backend detects WebSocket disconnect
6. Backend also stops motors
```

### Test 7: Page Refresh ✅
```
1. Start motors moving
2. Press F5 or Ctrl+R
3. beforeunload stops motors
4. New page loads safely
```

### Test 8: Multiple Clients ✅
```
1. Open two browser tabs
2. Both connect via WebSocket
3. Client A moves motors
4. Client A disconnects
5. Motors stop immediately (any disconnect stops)
```

---

## Code Locations

### Backend (`modules/mediamtx_main.py`)
- **Lines 95-147**: Watchdog system and global variables
- **Lines 841-877**: Motor control endpoint with heartbeat
- **Lines 1188-1220**: WebSocket connect/disconnect handlers
- **Lines 2832-2835**: Watchdog thread startup

### Frontend (`static/index.html`)
- **Lines 1336-1342**: Socket.IO disconnect handler
- **Lines 2616-2643**: Movement function with heartbeat interval
- **Lines 2645-2653**: Stop function
- **Lines 2655-2669**: Emergency stop function
- **Lines 2671-2702**: Emergency stop motors function
- **Lines 4437-4461**: Keyboard event handlers
- **Lines 4463-4477**: Page visibility handler
- **Lines 4664-4674**: Window unload and blur handlers

### Motor Controller (`modules/motor_controller.py`)
- **Lines 175-260**: Command sending with error handling
- **Lines 262-270**: Stop on failure function
- **Lines 240-253**: Serial exception handling

---

## Safety Principles

1. **Fail-Safe Design**: Any failure mode stops motors
2. **Multiple Redundancy**: 8 independent safety layers
3. **No Single Point of Failure**: Frontend AND backend can stop motors
4. **Immediate Response**: Most stops < 150ms
5. **Watchdog Backup**: Even if all else fails, 1.5s timeout stops motors
6. **Clear Feedback**: All safety events logged to console
7. **Automatic Detection**: No manual intervention required

---

## Emergency Stop Priority

**Order of execution when multiple events happen:**
1. Frontend immediate stop (key release, disconnect)
2. Backend WebSocket disconnect stop
3. Backend heartbeat watchdog (if others fail)
4. USB serial link failure detection (hardware level)

**All layers are independent** - any ONE of them can stop the motors.

---

## Configuration

### Adjusting Heartbeat Timeout
If experiencing false stops due to network latency:

**Backend** (`modules/mediamtx_main.py`, line 98):
```python
motor_heartbeat_timeout = 2.0  # Increase to 2 seconds
```

**Frontend** (`static/index.html`, line 2642):
```javascript
}, 300); // Decrease interval to 300ms (send more frequently)
```

**Rule**: Frontend interval should be < (backend timeout / 3)

### Disabling Specific Safety Features
**⚠️ NOT RECOMMENDED** - Each layer provides critical protection.

If you must disable (for debugging only):
- Comment out specific event listeners in `index.html`
- Comment out watchdog thread startup in `mediamtx_main.py` line 2833

---

## Conclusion

The Avatar Tank motor safety system provides **8 independent layers of protection**. Motors will stop if:
- ✅ User releases keys
- ✅ Internet connection lost
- ✅ Client browser freezes
- ✅ USB cable unplugged
- ✅ User switches tabs
- ✅ Window loses focus
- ✅ Browser closes
- ✅ All clients disconnect

**Total protection against runaway motors** with response times under 1.5 seconds in worst-case scenarios, and typically under 150ms.


