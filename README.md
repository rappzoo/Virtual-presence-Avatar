# 🤖 Avatar Tank - Remote Presence Robot

A comprehensive remote presence robot system with live video streaming, audio communication, motor control, and text-to-speech capabilities. Built for Raspberry Pi with professional-grade streaming and control interfaces.

![Avatar Tank](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🎥 **Live Video Streaming**
- **WebRTC & HLS Support** - Low-latency streaming with fallback options
- **Dynamic Resolution** - 320p, 480p, 720p with real-time switching
- **Audio + Video** - Synchronized audio and video streaming
- **Snapshot Capture** - High-quality still images at selected resolution

### 🎮 **Motor Control**
- **Serial Communication** - Direct motor controller interface
- **Movement Commands** - Forward, backward, left, right, stop
- **Real-time Control** - Responsive movement with status feedback

### 🔊 **Audio System**
- **Text-to-Speech** - Multi-language TTS with voice synthesis
- **Audio Streaming** - Live microphone input with VU meter
- **Sound Effects** - System sounds and audio feedback
- **Volume Control** - Adjustable audio levels

### 🌐 **Web Interface**
- **Modern UI** - Responsive design with real-time updates
- **WebSocket Communication** - Live status and control updates
- **Mobile Friendly** - Works on phones, tablets, and desktops
- **System Diagnostics** - Comprehensive health monitoring

### ⚙️ **System Management**
- **Persistent State** - Remembers settings across restarts
- **Auto-Recovery** - Automatic stream and connection recovery
- **Process Monitoring** - Health checks and automatic restarts
- **Log Management** - Clean logging with automatic cleanup

## 🚀 Quick Start

### 1. **Prerequisites**
See [PREREQUISITES.md](PREREQUISITES.md) for detailed setup requirements.

### 2. **Installation**
```bash
# Clone the repository
git clone https://github.com/yourusername/avatar-tank.git
cd avatar-tank

# Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv ffmpeg v4l-utils alsa-utils

# Install Python packages
pip3 install -r requirements.txt

# Make scripts executable
chmod +x *.sh
```

### 3. **Hardware Setup**
- Connect USB camera to `/dev/video0`
- Connect USB microphone to system
- Connect motor controller to `/dev/ttyACM0`
- Ensure network connectivity

### 4. **Configuration**
```bash
# Edit configuration files
nano config/mediamtx.yml
nano config/avatar_state.json
```

### 5. **Start the System**
```bash
# Start all services
./start_final_stable.sh

# Or start manually
python3 modules/mediamtx_main.py
```

### 6. **Access the Interface**
- **Web Interface**: http://your-ip:5000
- **Video Stream**: http://your-ip:8888/stream/
- **WebRTC Stream**: http://your-ip:8889/stream

## 📁 Project Structure

```
avatar-tank/
├── README.md                 # This file
├── PREREQUISITES.md          # Setup requirements
├── requirements.txt          # Python dependencies
├── config/                   # Configuration files
│   ├── mediamtx.yml         # MediaMTX server config
│   └── avatar_state.json    # Persistent state
├── modules/                  # Core system modules
│   ├── mediamtx_main.py     # Main Flask application
│   ├── mediamtx_camera.py   # Camera and streaming
│   ├── mediamtx_audio.py    # Audio management
│   ├── mediamtx_recorder.py # Recording functionality
│   ├── avatar_state.py      # State management
│   ├── device_detector.py   # Hardware detection
│   ├── motor.py             # Motor control
│   ├── tts.py               # Text-to-speech
│   └── predictor.py         # TTS prediction
├── static/                   # Web interface files
│   ├── index.html           # Main web interface
│   ├── css/                 # Stylesheets
│   ├── js/                  # JavaScript files
│   └── sounds/              # Audio files
├── piper/                    # TTS engine
│   ├── models/              # Voice models
│   └── bin/                 # TTS binaries
├── snapshots/               # Captured images
├── recordings/              # Video recordings
├── sounds/                  # System sounds
└── scripts/                 # Utility scripts
    ├── start_final_stable.sh
    ├── cleanup_logs.sh
    └── check_disk_usage.sh
```

## 🎛️ API Endpoints

### **System Control**
- `GET /api/status` - System status and health
- `GET /api/state` - Complete system state
- `POST /api/state/reset` - Reset system state

### **Streaming**
- `POST /api/stream/start` - Start video stream
- `POST /api/stream/stop` - Stop video stream
- `POST /api/stream/refresh` - Refresh stream
- `POST /api/snapshot` - Capture snapshot

### **Camera Control**
- `POST /api/resolution` - Change resolution
- `POST /api/framerate` - Change framerate
- `GET /api/camera/status` - Camera status

### **Motor Control**
- `POST /api/motor/forward` - Move forward
- `POST /api/motor/backward` - Move backward
- `POST /api/motor/left` - Turn left
- `POST /api/motor/right` - Turn right
- `POST /api/motor/stop` - Stop movement

### **Audio Control**
- `POST /api/tts/speak` - Text-to-speech
- `POST /api/audio/volume` - Set volume
- `POST /api/audio/mute` - Toggle mute

## 🔧 Configuration

### **MediaMTX Configuration**
Edit `config/mediamtx.yml` to customize streaming settings:
```yaml
rtmpDisable: yes
hlsDisable: no
webrtcDisable: no
```

### **System State**
The system automatically saves state in `config/avatar_state.json`:
```json
{
  "last_resolution": "720p",
  "last_fps": 15,
  "camera_settings": {
    "320p": {"width": 640, "height": 360, "fps": 10},
    "480p": {"width": 854, "height": 480, "fps": 10},
    "720p": {"width": 1280, "height": 720, "fps": 10}
  }
}
```

## 🛠️ Maintenance

### **Log Management**
```bash
# Clean up old log files
./cleanup_logs.sh

# Check disk usage
./check_disk_usage.sh
```

### **System Monitoring**
- **Process Status**: Check running processes
- **Stream Health**: Monitor WebRTC/HLS connections
- **Hardware Status**: Camera, microphone, motor controller
- **Network Status**: Latency and connectivity

### **Troubleshooting**
- **Stream Issues**: Check FFmpeg and MediaMTX logs
- **Audio Problems**: Verify ALSA device configuration
- **Motor Control**: Check serial port permissions
- **Web Interface**: Check Flask application logs

## 🔒 Security Considerations

- **Network Access**: Configure firewall rules
- **Authentication**: Add user authentication if needed
- **HTTPS**: Use SSL/TLS for production deployment
- **Access Control**: Restrict network access to trusted devices

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MediaMTX** - Professional streaming server
- **FFmpeg** - Video and audio processing
- **Piper TTS** - Text-to-speech engine
- **Flask** - Web framework
- **WebRTC** - Real-time communication

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/avatar-tank/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/avatar-tank/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/avatar-tank/wiki)

---

**Built with ❤️ for the robotics community**