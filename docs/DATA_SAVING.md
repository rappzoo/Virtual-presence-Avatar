# Data Saving Features for 4G/Cellular Connections

## 🎯 Problem

When using the Avatar Tank over 4G/cellular connections, leaving the video stream running wastes expensive mobile data even when no one is watching.

## ✅ Solution

**Automatic stream shutdown when the webpage is closed or connection is lost.**

---

## How It Works

### Scenario 1: User Closes Browser/Tab
```
1. User closes browser or navigates away
   ↓
2. beforeunload event fires
   ↓
3. Synchronous XHR sends stream stop command
   ↓
4. Stream stops immediately (< 1 second)
   ↓
5. No more data transmission = Saved bandwidth! 💾
```

### Scenario 2: Internet Connection Lost
```
1. 4G connection drops or WiFi disconnects
   ↓
2. WebSocket disconnect detected
   ↓
3. Backend removes client from tracking
   ↓
4. Backend checks: Are there any clients left?
   ↓
5. If NO clients: Stream stops automatically
   ↓
6. No more data transmission = Saved bandwidth! 💾
```

### Scenario 3: Multiple Users
```
User A connects → Stream starts
User B connects → Stream continues (2 clients)
User A leaves → Stream continues (1 client)
User B leaves → Stream STOPS (0 clients) → Data saved! 💾
```

---

## Technical Implementation

### Frontend (JavaScript)

**File**: `static/index.html`

```javascript
window.addEventListener('beforeunload', () => {
  console.log('[Motor Safety] Page unloading - stopping motors');
  emergencyStopMotors('Page closing/navigating');
  
  // DATA SAVING: Stop stream to prevent wasting 4G bandwidth
  if (streamActive) {
    // Use synchronous XHR (async fetch won't complete in beforeunload)
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/stream/stop', false);  // false = synchronous
    xhr.send();
  }
});
```

**Why synchronous XHR?**
- `beforeunload` happens very quickly
- Async `fetch()` requests get cancelled before they complete
- Synchronous XHR ensures the command is sent before page closes

### Backend (Python)

**File**: `modules/mediamtx_main.py`

```python
@socketio.on('disconnect')
def handle_disconnect():
    # Remove client from tracking
    motor_clients_connected.discard(request.sid)
    
    # Stop motors (safety)
    motors.stop()
    
    # DATA SAVING: Stop stream when last client disconnects
    if len(motor_clients_connected) == 0:
        print(f"[Stream Safety] 💾 No clients - STOPPING STREAM")
        stop_streaming()
```

**Client Tracking**:
- Each WebSocket connection is tracked
- When client count reaches 0, stream stops
- Automatic cleanup on disconnect

---

## Benefits

### 💰 Cost Savings
- **Prevent data waste**: Stream only runs when someone is watching
- **4G-friendly**: No background data consumption
- **Automatic**: No manual intervention needed

### 📊 Data Usage Comparison

**Without Auto-Stop** (1 hour forgotten stream):
```
Video: 720p @ 10fps = ~2 Mbps
Audio: 64 kbps
Total: ~2.064 Mbps = ~258 KB/s

1 hour = 258 KB/s × 3600s = ~928 MB wasted! 💸
```

**With Auto-Stop** (stream stops in 1 second):
```
1 second of streaming = 258 KB
Savings = 928 MB - 0.258 MB = ~927.7 MB saved! 💾
```

### 🔋 Battery Savings
- Less CPU usage on RPi when stream is off
- Less power consumption overall
- Longer operation time on battery

---

## Testing

### Test 1: Browser Close
```
1. Open web interface
2. Start stream
3. Close browser tab
4. Check server logs:
   → Should see: "[Stream Safety] Stream stopped to prevent data waste"
5. Reopen interface
6. Stream should be stopped
✅ PASS: Stream auto-stopped
```

### Test 2: Internet Loss
```
1. Connect over 4G
2. Start stream
3. Turn off 4G / disconnect WiFi
4. Wait 5 seconds
5. Check server logs:
   → Should see: "[Stream Safety] No clients - STOPPING STREAM"
6. Reconnect internet
7. Open interface
8. Stream should be stopped
✅ PASS: Stream auto-stopped
```

### Test 3: Multiple Clients
```
1. Open interface in Browser A
2. Start stream
3. Open interface in Browser B (same stream continues)
4. Close Browser A
5. Stream should CONTINUE (Browser B still connected)
6. Close Browser B
7. Check logs:
   → Should see: "[Stream Safety] No clients - STOPPING STREAM"
✅ PASS: Stream stops only when all clients disconnect
```

---

## Configuration

### Adjusting Behavior

**Always Auto-Stop** (current behavior):
```python
# In handle_disconnect()
if len(motor_clients_connected) == 0:
    stop_streaming()  # Stop when no clients
```

**Never Auto-Stop** (keep streaming):
```python
# Comment out the stream stop code
# if len(motor_clients_connected) == 0:
#     stop_streaming()
```

**Delayed Auto-Stop** (grace period):
```python
# Stop after 30 seconds with no clients
import threading
import time

def delayed_stream_stop():
    time.sleep(30)
    if len(motor_clients_connected) == 0:
        stop_streaming()

if len(motor_clients_connected) == 0:
    threading.Thread(target=delayed_stream_stop, daemon=True).start()
```

---

## Data Usage Estimates

### Video Stream Data Rates

| Resolution | FPS | Bitrate | MB per hour |
|------------|-----|---------|-------------|
| 320p | 10 | ~500 Kbps | ~225 MB |
| 480p | 10 | ~1 Mbps | ~450 MB |
| 720p | 10 | ~2 Mbps | ~900 MB |
| 720p | 15 | ~3 Mbps | ~1350 MB |
| 720p | 20 | ~4 Mbps | ~1800 MB |

**Plus audio**: ~64 Kbps = ~28 MB per hour

### Monthly 4G Data Usage

**Scenario**: 2 hours/day, 720p @ 10fps

**Without Auto-Stop** (accidentally leave running 24/7):
```
900 MB/hour × 24 hours/day × 30 days = 648 GB/month! 💸💸💸
```

**With Auto-Stop** (only during active use):
```
900 MB/hour × 2 hours/day × 30 days = 54 GB/month 💾
Savings: 594 GB/month!
```

---

## Safety Interactions

### Motor Stop + Stream Stop

**Both happen automatically**:
1. ✅ Motors stop (safety)
2. ✅ Stream stops (data saving)

**Independence**:
- Motors can be stopped without stopping stream
- Stream can be stopped without stopping motors
- But disconnect triggers BOTH

**Manual Control**:
- User can manually stop motors: Motors stop, stream continues
- User can manually stop stream: Stream stops, motors can still run
- Closing page: BOTH stop automatically

---

## Monitoring

### Check If Stream Auto-Stop is Working

**View live logs**:
```bash
sudo journalctl -u avatar-tank.service -f | grep "Stream Safety"
```

**Expected output when page closes**:
```
[Stream Safety] 💾 No clients connected - STOPPING STREAM to save bandwidth
[Stream Safety] Stream stopped to prevent data waste on 4G connection
```

**Check stream status**:
```bash
curl http://localhost:5000/api/streaming_status
```

**Response**:
```json
{
  "streaming": false,
  "camera_active": false,
  "uptime": 12345
}
```

---

## Troubleshooting

### Stream Doesn't Stop When Page Closes

**Check 1: Multiple tabs open?**
```
→ Stream continues if ANY tab is still open
→ Close ALL tabs to test
```

**Check 2: Check logs**
```bash
sudo journalctl -u avatar-tank.service -n 50 | grep disconnect
```
**Expected**:
```
Client disconnected: <socket_id>
Total clients: 0
Stream stopped to prevent data waste
```

**Check 3: WebSocket connected?**
```javascript
// In browser console
console.log(socket.connected)
// Should be: true (when connected)
```

### Stream Stops Too Quickly (Multiple Users)

**Problem**: Last user causes stream to stop for everyone

**Solution**: This is by design for data saving

**Alternative**: Implement delayed auto-stop (see Configuration section)

---

## Best Practices for 4G Use

### 1. Lower Resolution
```
Use 480p or 320p on 4G
Saves ~50-75% bandwidth vs 720p
```

### 2. Lower FPS
```
Use 10 FPS instead of 15-20
Saves ~30-50% bandwidth
```

### 3. Monitor Data Usage
```bash
# Check network usage
ifconfig | grep "RX packets"
vnstat -i wwan0  # For 4G interface
```

### 4. Set Data Budget Alert
```
Monitor monthly data on your 4G plan
Set alerts at 80% usage
```

### 5. Use WiFi When Possible
```
Connect to WiFi hotspots when available
Save 4G data for when truly needed
```

---

## Status Indicators

### Stream Running (Data Being Used)
- Green indicator on web interface
- "Streaming" status text
- Video playing
- **Data is being transmitted** 📊

### Stream Stopped (No Data Used)
- Gray indicator on web interface
- "Stopped" status text
- No video
- **No data transmission** 💾

---

## Cost Savings Calculator

**Your 4G Plan**: $X per GB overages

**Stream accidentally left on**: 1 day = 24 hours

**Data used**: 
- 720p: 900 MB/hour × 24 = 21.6 GB
- Cost: 21.6 GB × $X/GB = $$$

**With auto-stop**: 
- Data used: 0 GB (stream stops immediately)
- Cost: $0
- **Savings: $$$** 💰

---

## Summary

✅ **Automatic**: Stream stops when page closes
✅ **Smart**: Tracks multiple clients
✅ **Fast**: Stops within 1 second
✅ **Safe**: Motors also stop (safety first)
✅ **Cost-Effective**: Saves expensive 4G data
✅ **Reliable**: Works on disconnect, close, navigate
✅ **Transparent**: Shows in logs and status

**Your Avatar Tank now automatically saves 4G data!** 💾📱

---

## Related Features

- **Motor Safety System**: `MOTOR_SAFETY.md`
- **Stream Control**: Web interface Start/Stop buttons
- **Bandwidth Management**: Automatic bitrate adjustment
- **Client Tracking**: Multi-user support

---

## Version History

### v1.0 (Current)
- Automatic stream stop on page close
- Client tracking for multiple users
- Synchronous XHR for beforeunload
- Backend disconnect handler
- Data usage documentation

---

## Questions?

**Q: Will this affect multiple users?**
A: Yes - stream stops when the LAST user disconnects. This saves data.

**Q: Can I disable auto-stop?**
A: Yes - comment out the code in `handle_disconnect()` (see Configuration)

**Q: How much data does this save?**
A: Potentially hundreds of GB per month if stream was accidentally left running

**Q: Does this affect local network use?**
A: No negative effects. Saves bandwidth on any network (4G, WiFi, LAN)

**Q: What about motors?**
A: Motors stop independently for safety. This is about stream/data only.

---

**Enjoy worry-free 4G usage with automatic data saving!** 🚀💾


