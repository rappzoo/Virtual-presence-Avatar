# 🤖 Avatar Tank - Remote Presence Robot

A comprehensive remote presence robot system with live video streaming, audio communication, motor control, and text-to-speech capabilities. Built for Raspberry Pi with professional-grade streaming and control interfaces powered by MediaMTX and Flask.

![Avatar Tank](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🎥 **Live Video Streaming**
- **WebRTC & HLS Support** - Low-latency streaming with automatic fallback
- **Dynamic Resolution** - 320p, 480p, 720p with real-time switching
- **Synchronized Audio + Video** - Crystal-clear audio with video
- **Recording & Snapshots** - Capture video recordings and still images
- **VU Meter** - Real-time audio level visualization
- **Adaptive Quality** - Automatic quality adjustment based on network

### 🎮 **Motor Control**
- **ESP32/Serial Communication** - Direct motor controller interface
- **Movement Commands** - Forward, backward, left, right, stop
- **Real-time Control** - Responsive movement with status feedback
- **Reconnection Support** - Automatic motor controller reconnection

### 🔊 **Audio System**
- **Multi-language TTS** - English, Romanian, German with Piper engine
- **Live Audio Streaming** - Real-time microphone input with WebRTC
- **Sound Effects** - 20 customizable sound effect slots
- **TTS-to-Sound Generator** - Create custom sound effects from text
- **Volume Control** - Adjustable audio levels and mute

### 🎵 **Sound Effects Management**
- **20 Sound Slots** - Store and play custom sound effects
- **TTS Sound Generation** - Convert any text to a sound effect
- **Sound Renaming** - Customize sound button labels
- **Multi-language Support** - Generate sounds in EN, RO, or DE

### 🌐 **Web Interface**
- **Modern Responsive UI** - Works on phones, tablets, and desktops
- **WebSocket Communication** - Real-time status and control updates
- **System Diagnostics** - Comprehensive health monitoring
- **Persistent Settings** - Remembers your preferences

### ⚙️ **System Management**
- **Auto-Start on Boot** - Systemd service automatically starts
- **Persistent State** - Remembers settings across restarts
- **Auto-Recovery** - Automatic stream and connection recovery
- **Process Monitoring** - Health checks with graceful error handling
- **Remote Reboot** - Safely reboot the system from web interface

## 🚀 Quick Start

### 1. **Prerequisites**
```bash
# Required Hardware
- Raspberry Pi 4/5 (2GB+ RAM recommended)
- USB Camera (e.g., C270, C922)
- USB Microphone
- USB Speaker
- Motor controller (ESP32/Arduino on serial port)

# Required Software
- Raspberry Pi OS (64-bit recommended)
- Python 3.11+
- FFmpeg
- MediaMTX
- Piper TTS
```

### 2. **Installation**
```bash
# Clone the repository
cd /home/havatar
git clone <your-repo-url> Avatar-robot
cd Avatar-robot

# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg v4l-utils alsa-utils \
  libopus-dev python3-eventlet mpg123

# Install Python packages
pip3 install -r requirements.txt

# Install MediaMTX (if not already installed)
# Download from https://github.com/bluenviron/mediamtx
sudo cp mediamtx /usr/local/bin/
sudo chmod +x /usr/local/bin/mediamtx

# Install Piper TTS
# Follow instructions in piper/README.md

# Make scripts executable
chmod +x start_avatar_simple.sh
chmod +x piper/bin/piper
```

### 3. **Hardware Setup**
```bash
# Camera
- Connect USB camera → detected as /dev/video0
- Verify: ls -l /dev/video*

# Audio
- Connect USB microphone → typically plughw:3,0
- Connect USB speaker → typically plughw:2,0
- Verify: arecord -L && aplay -L

# Motor Controller
- Connect ESP32/Arduino → /dev/ttyACM0 or /dev/ttyUSB0
- Verify: ls -l /dev/tty*
```

### 4. **Configure Service**
```bash
# Copy service file to systemd
sudo cp avatar-tank.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable avatar-tank.service
sudo systemctl start avatar-tank.service

# Check status
systemctl status avatar-tank.service
```

### 5. **Access the Interface**
```bash
# Find your Raspberry Pi's IP address
hostname -I

# Access web interface
http://YOUR_IP:5000

# Streaming endpoints
- WebRTC: http://YOUR_IP:8889/stream
- HLS: http://YOUR_IP:8888/stream/
- RTSP: rtsp://YOUR_IP:8554/stream
```

## 📁 Project Structure

```
Avatar-robot/
├── README.md                    # This file - complete project documentation
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT License
├── requirements.txt             # Python dependencies
│
├── avatar-tank.service          # Systemd service (main app)
├── avatar-media.service         # Systemd service (MediaMTX)
├── start_avatar_simple.sh       # Startup script
│
├── config/                      # Configuration files
│   ├── mediamtx.yml            # MediaMTX streaming config
│   ├── avatar_state.json       # Persistent system state
│   └── wifi.json               # Wi-Fi configuration
│
├── modules/                     # Core Python modules
│   ├── mediamtx_main.py        # Main Flask application
│   ├── mediamtx_camera.py      # Camera & streaming control
│   ├── mediamtx_audio.py       # Audio management
│   ├── mediamtx_recorder.py    # Video recording
│   ├── device_detector.py      # Hardware auto-detection
│   ├── motor_controller.py     # Motor control interface
│   ├── tts.py                  # Text-to-speech (Piper)
│   ├── predictor.py            # Word prediction for TTS
│   ├── avatar_state.py         # State persistence
│   ├── audio_utils.py          # Audio utilities
│   ├── esp32_communicator.py   # ESP32 communication
│   └── wifi_manager.py        # Wi-Fi management
│
├── static/                      # Web interface
│   ├── index.html              # Single-page application
│   └── js/                     # JavaScript modules
│
├── templates/                   # HTML templates
│   └── control.html            # Control interface template
│
├── piper/                       # TTS engine
│   ├── bin/piper               # Piper TTS binary
│   ├── models/                 # Voice models (EN, RO, DE)
│   └── words.txt              # Dictionary
│
├── sounds/                      # Sound effects (20+ slots)
│   └── sound*.mp3              # Custom sound files
│
├── snapshots/                   # Captured images
├── recordings/                  # Video recordings
├── dicts/                       # Word dictionaries
├── esp32_firmware/              # Motor controller firmware
│   └── flash_esp32.sh          # Firmware flashing script
│
├── scripts/                     # Utility scripts
│   ├── check_services.sh       # Service health check
│   └── *.sh                    # Other utility scripts
│
└── docs/                        # Additional documentation
    ├── PREREQUISITES.md        # Detailed setup requirements
    ├── FEATURES_AND_PURPOSE.md # Complete feature list
    ├── WIFI_SETUP.md           # Wi-Fi configuration guide
    ├── MOTOR_SAFETY.md         # Motor safety documentation
    └── archive/                # Historical documentation
```

## 🎛️ API Endpoints

### **System Control**
- `GET /api/status` - System status (streaming, camera, audio, recording)
- `GET /api/system_status` - Complete system state with motor info
- `POST /system/reboot` - Safely reboot the Raspberry Pi

### **Streaming Control**
- `POST /api/stream/start` - Start video/audio stream
- `POST /api/stream/stop` - Stop stream
- `POST /api/stream/refresh` - Refresh stream (full restart)
- `GET /api/stream/status` - Stream status

### **Camera Control**
- `POST /api/camera/resolution` - Change resolution (320p/480p/720p)
- `POST /api/camera/framerate` - Change FPS (10-25)
- `POST /api/snapshot` - Capture high-quality snapshot
- `GET /api/camera/status` - Camera device status

### **Recording**
- `POST /api/recording/start` - Start video recording
- `POST /api/recording/stop` - Stop recording
- `GET /api/recording/status` - Recording status

### **Motor Control**
- `POST /api/motor/forward` - Move forward
- `POST /api/motor/backward` - Move backward
- `POST /api/motor/left` - Turn left
- `POST /api/motor/right` - Turn right
- `POST /api/motor/stop` - Emergency stop
- `POST /api/motor/reconnect` - Reconnect motor controller
- `GET /api/motor/status` - Motor controller status

### **Audio & TTS**
- `POST /speak` - Text-to-speech (multi-language)
- `POST /set_language` - Change TTS language (en/ro/de)
- `POST /audio/set_volume` - Set volume level
- `POST /audio/test_mic` - Test microphone recording

### **Sound Effects**
- `POST /play_sound/<id>` - Play sound effect (0-19)
- `POST /generate_sound_from_tts` - Generate sound from TTS text
  - Parameters: `text`, `language`, `sound_id` (0-19)

## 🔧 Configuration

### **MediaMTX Settings** (`config/mediamtx.yml`)
```yaml
# Core streaming settings
logLevel: info
logDestinations: [file]
logFile: mediamtx.log

# Protocol settings
rtmpDisable: yes
hlsDisable: no
webrtcDisable: no
hlsVariant: mpegts

# Performance
readTimeout: 10s
writeTimeout: 10s
```

### **System State** (`config/avatar_state.json`)
Automatically managed - stores:
- Last used resolution and FPS
- Camera settings for each resolution
- Persistent preferences

### **Systemd Service** (`avatar-tank.service`)
- **Type**: Simple (Flask runs as main process)
- **Restart**: Always (5 second delay)
- **Auto-start**: Enabled (starts on boot)
- **User**: havatar
- **Logs**: journalctl -u avatar-tank.service

## 🛠️ Operation

### **Starting the System**
```bash
# Automatic (on boot)
# Service starts automatically - no action needed

# Manual start
sudo systemctl start avatar-tank.service

# Check status
systemctl status avatar-tank.service

# View logs
journalctl -u avatar-tank.service -f
```

### **Stopping the System**
```bash
# Stop service
sudo systemctl stop avatar-tank.service

# Disable auto-start
sudo systemctl disable avatar-tank.service
```

### **Restarting**
```bash
# Via command line
sudo systemctl restart avatar-tank.service

# Via web interface
# Click the "Reboot" button in System section
# System will safely reboot and auto-restart
```

### 📶 4G Mobility & ZeroTier Guide

This project is optimized for 4G mobility with ZeroTier providing a routable L3 overlay between laptop (UI) and the Raspberry Pi (rover).

- ZeroTier: install and join the same network on both devices; verify IPs (e.g., `172.25.x.x`).
- MediaMTX is configured to advertise the ZeroTier host in ICE via `webrtcAdditionalHosts` in `config/mediamtx.yml`.
- Preferred transport is WebRTC over the ZeroTier path; TURN is generally not required with ZeroTier.
- Ports in use: 5000 (Flask UI), 8554 (RTSP), 8888 (HLS), 8889 (WebRTC HTTP/WHEP), dynamic ICE/UDP.

WebRTC behavior (non‑intrusive):
- The page uses WebRTC as primary; it auto‑reconnects with exponential backoff and a stall watchdog.
- Press Shift+S to toggle the hidden WebRTC stats box (bitrate, RTT, jitter, FPS, lost).
- Prometheus metrics are available at `http://<pi>:5000/metrics` (basic stream gauges).

Bandwidth and quality:
- Video: H.264 with zerolatency tuning; ABR caps are applied internally.
- Audio: Opus mono, VOIP tuning, VBR+DTX, 20ms ptime; resilient on variable 4G bandwidth.
- If the carrier is constrained, prefer lower resolution/FPS in the UI; adaptation also occurs automatically.

Troubleshooting over 4G/ZeroTier:
- Verify ZeroTier link: `ping <pi-zerotier-ip>` from the laptop.
- Check MediaMTX listeners: `curl http://localhost:9997/v3/paths/list` on the Pi.
- ICE host advertisement: confirm `webrtcAdditionalHosts` contains the Pi’s ZeroTier IP.
- MTU issues: if you see freezes on some carriers, set a lower MTU on the ZeroTier interface (e.g., 1300) and retest.
- FPS mismatch: status shows detected FPS; ensure camera supports the selected FPS; we also set v4l2 framerate before streaming.

## 🔍 Monitoring & Diagnostics

### **Web Interface Diagnostics**
The web interface includes comprehensive diagnostics:
- System status display
- Real-time bandwidth monitoring
- Audio VU meter
- Stream health indicators
- Network latency display
- Hardware detection status

### **Log Files**
```bash
# Service logs (systemd journal)
journalctl -u avatar-tank.service --since today

# MediaMTX logs
tail -f /home/havatar/Avatar-robot/mediamtx.log

# Check process status
ps aux | grep -E "mediamtx|python3.*mediamtx_main"

# Check port usage
netstat -tlnp | grep -E "5000|8554|8888|8889"
```

### **Hardware Verification**
```bash
# Camera
v4l2-ctl --list-devices
ffmpeg -f v4l2 -list_formats all -i /dev/video0

# Audio
arecord -l  # List microphones
aplay -l    # List speakers
speaker-test -t wav -c 2  # Test speakers

# Serial ports (motor controller)
ls -l /dev/tty*
```

## 🚨 Troubleshooting

### **Service Won't Start**
```bash
# Check service status
systemctl status avatar-tank.service

# View detailed logs
journalctl -u avatar-tank.service -n 50

# Verify script is executable
ls -l /home/havatar/Avatar-robot/start_avatar_simple.sh

# Test MediaMTX manually
/usr/local/bin/mediamtx /home/havatar/Avatar-robot/config/mediamtx.yml
```

### **Stream Not Working**
```bash
# Check if FFmpeg is running
ps aux | grep ffmpeg

# Check MediaMTX
curl http://localhost:9997/v3/paths/list

# Verify camera
ls -l /dev/video0
v4l2-ctl --list-formats-ext -d /dev/video0

# Test stream manually
ffmpeg -f v4l2 -i /dev/video0 -f alsa -i plughw:3,0 -t 5 test.mp4
```

### **Audio Issues**
```bash
# Check microphone
arecord -D plughw:3,0 -f cd -d 5 test.wav
aplay test.wav

# Check speaker
speaker-test -D plughw:2,0

# Verify TTS
ls -l /home/havatar/Avatar-robot/piper/bin/piper
echo "test" | /home/havatar/Avatar-robot/piper/bin/piper --model <model>
```

### **Motor Control Not Responding**
```bash
# Check serial port
ls -l /dev/ttyACM0 /dev/ttyUSB0

# Check permissions
sudo usermod -a -G dialout havatar

# Test serial communication
screen /dev/ttyACM0 115200
```

## 🔧 Service Management

### **Service Audit & Health Check**

Run the automated service audit script to check for configuration issues:

```bash
bash /home/havatar/Avatar-robot/scripts/check_services.sh
```

This script checks:
- ✅ Only `avatar-tank.service` is enabled and running
- ✅ No duplicate MediaMTX services (`mediamtx.service`, `avatar-mediamtx.service`)
- ✅ Single MediaMTX instance with correct parent process
- ✅ All required ports are accessible (5000, 8554, 8888, 8889)
- ✅ Memory usage is healthy (< 85%)
- ✅ No recent OOM (Out of Memory) kills

**Example output (healthy system):**
```
🔍 Avatar Tank Service Audit
============================

📋 Checking enabled services...
  ✓ avatar-tank.service is ENABLED (correct)
  ✓ avatar-mediamtx.service is disabled (correct)
  ✓ mediamtx.service is disabled (correct)

📊 Checking running services...
  ✓ avatar-tank.service is running
  
🔢 Checking MediaMTX instance count...
  Found: 1 MediaMTX binary process(es)
  ✓ Correct! Only 1 MediaMTX instance
  ✓ MediaMTX is correctly launched by avatar-tank

💾 Checking memory usage...
  ✓ Memory usage is healthy (15%)
  
✅ ALL CHECKS PASSED!
```

### **Common Service Commands**

```bash
# Check service status
sudo systemctl status avatar-tank.service

# Restart service
sudo systemctl restart avatar-tank.service

# View live logs
sudo journalctl -u avatar-tank.service -f

# View recent logs
sudo journalctl -u avatar-tank.service -n 100

# Check for errors
sudo journalctl -u avatar-tank.service | grep -i error

# Disable duplicate services (if found)
sudo systemctl stop mediamtx.service avatar-mediamtx.service
sudo systemctl disable mediamtx.service avatar-mediamtx.service
```

### **CRITICAL: Preventing OOM Crashes**

⚠️ **Never run multiple MediaMTX services simultaneously!** This causes:
- Port conflicts
- Memory pressure
- OOM (Out of Memory) killer terminating processes
- System crashes and SSH failures

**Only `avatar-tank.service` should be enabled.** This service internally manages:
- Python Flask application (port 5000)
- MediaMTX streaming server (ports 8554, 8888, 8889)
- All child processes

If you experience crashes, run the service audit script:
```bash
bash /home/havatar/Avatar-robot/scripts/check_services.sh
```

See `docs/archive/` for historical incident reports and troubleshooting notes.

## 🔒 Security

### **Network Security**
```bash
# Restrict access (example)
sudo ufw allow from 192.168.1.0/24 to any port 5000
sudo ufw allow from 192.168.1.0/24 to any port 8888
sudo ufw allow from 192.168.1.0/24 to any port 8889
sudo ufw enable
```

### **Sudo Permissions**
The system requires these sudo permissions (configured):
```bash
# /etc/sudoers.d/avatar-reboot
havatar ALL=(ALL) NOPASSWD: /sbin/reboot, /usr/sbin/reboot
```

## 📊 Performance

### **Typical Resource Usage**
- **CPU**: 20-40% (depending on resolution/FPS)
- **Memory**: ~300MB (Flask + MediaMTX + FFmpeg)
- **Network**: 500KB/s - 2MB/s (depending on quality)
- **Storage**: ~100MB base + recordings/snapshots

### **Optimization Tips**
- Use 320p or 480p for better performance
- Lower FPS (10-15) for bandwidth savings
- Enable bandwidth management in web interface
- Regularly clean up old recordings/snapshots

## 🆕 Recent Features (2025)

- ✅ **TTS-to-Sound Generator** - Convert text to custom sound effects
- ✅ **Remote Reboot** - Safe system reboot from web interface
- ✅ **Auto-start on Boot** - Systemd integration with automatic startup
- ✅ **Socket.IO Improvements** - Better connection stability
- ✅ **UI Cleanup** - Removed unused battery monitor and debug panels
- ✅ **Process Cleanup Fix** - Eliminated self-killing service issues
- ✅ **Stream Lock Mechanism** - Prevents concurrent stream operations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaMTX** - Professional RTSP/HLS/WebRTC streaming server
- **FFmpeg** - Powerful video and audio processing
- **Piper TTS** - High-quality text-to-speech engine
- **Flask** - Lightweight web framework
- **Flask-SocketIO** - Real-time bidirectional communication
- **Eventlet** - Concurrent networking library

## 📞 Support & Contact

For issues, questions, or contributions, please use the GitHub repository's issue tracker.

---

**Built with ❤️ for remote presence and telepresence applications**

**Status**: Production Ready | **Last Updated**: October 2025
