# 📋 Avatar Tank - Prerequisites & Setup Guide

This document outlines all the hardware, software, and system requirements needed to run the Avatar Tank remote presence robot system.

## 🖥️ **System Requirements**

### **Minimum Hardware**
- **Raspberry Pi 4** (4GB RAM recommended)
- **32GB+ MicroSD Card** (Class 10 or better)
- **USB Camera** (compatible with v4l2)
- **USB Microphone** (or built-in audio)
- **Motor Controller** (Arduino-based or compatible)
- **Network Connection** (WiFi or Ethernet)

### **Recommended Hardware**
- **Raspberry Pi 4** (8GB RAM)
- **64GB+ MicroSD Card** (Class 10, U3)
- **High-quality USB Camera** (1080p capable)
- **External USB Microphone** (for better audio quality)
- **Dedicated Motor Controller Board**
- **Gigabit Ethernet** (for stable streaming)

## 🐧 **Operating System**

### **Raspberry Pi OS**
```bash
# Recommended: Raspberry Pi OS (64-bit)
# Download from: https://www.raspberrypi.org/software/

# Update system
sudo apt update && sudo apt upgrade -y
```

### **Alternative OS**
- **Ubuntu Server 22.04 LTS**
- **Debian 11+**
- **Other Linux distributions** (with Python 3.11+)

## 📦 **Software Dependencies**

### **System Packages**
```bash
# Essential packages
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    unzip

# Media and streaming
sudo apt install -y \
    ffmpeg \
    v4l-utils \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils

# Network and communication
sudo apt install -y \
    net-tools \
    iptables \
    ufw

# Development tools (optional)
sudo apt install -y \
    htop \
    vim \
    nano \
    screen \
    tmux
```

### **Python Packages**
```bash
# Create virtual environment (recommended)
python3 -m venv avatar-env
source avatar-env/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **Required Python Packages**
```
Flask==2.3.3
Flask-SocketIO==5.3.6
python-socketio==5.9.0
eventlet==0.33.3
opencv-python==4.8.1.78
numpy==1.24.3
requests==2.31.0
pyserial==3.5
pygame==2.5.2
```

## 🎥 **Hardware Setup**

### **Camera Configuration**
```bash
# Check camera detection
v4l2-ctl --list-devices

# Test camera
ffplay /dev/video0

# Configure camera (if needed)
v4l2-ctl --device=/dev/video0 --set-fmt-video=width=1280,height=720,pixelformat=YUYV
```

### **Audio Configuration**
```bash
# Check audio devices
arecord -l
aplay -l

# Test microphone
arecord -D plughw:3,0 -f cd -t wav test.wav

# Test speaker
aplay -D plughw:2,0 test.wav
```

### **Motor Controller Setup**
```bash
# Check serial devices
ls -la /dev/tty*

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Test serial communication
python3 -c "import serial; print(serial.Serial('/dev/ttyACM0', 9600))"
```

## 🌐 **Network Configuration**

### **Static IP Setup (Recommended)**
```bash
# Edit network configuration
sudo nano /etc/dhcpcd.conf

# Add static IP configuration
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4
```

### **Firewall Configuration**
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22

# Allow web interface
sudo ufw allow 5000

# Allow streaming ports
sudo ufw allow 8888
sudo ufw allow 8889
sudo ufw allow 8554
```

### **Port Requirements**
| **Port** | **Service** | **Protocol** | **Description** |
|----------|-------------|--------------|-----------------|
| 5000 | Flask Web | HTTP | Web interface |
| 8888 | HLS Stream | HTTP | Video streaming |
| 8889 | WebRTC | HTTP | Low-latency streaming |
| 8554 | RTSP | TCP | Internal streaming |
| 9997 | MediaMTX API | HTTP | Stream management |

## 🔧 **System Configuration**

### **User Permissions**
```bash
# Add user to required groups
sudo usermod -a -G video,audio,dialout $USER

# Logout and login again for changes to take effect
```

### **Service Configuration**
```bash
# Create systemd service (optional)
sudo nano /etc/systemd/system/avatar-tank.service

[Unit]
Description=Avatar Tank Remote Presence Robot
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/avatar-tank
ExecStart=/usr/bin/python3 modules/mediamtx_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable service
sudo systemctl enable avatar-tank.service
sudo systemctl start avatar-tank.service
```

### **Auto-start Configuration**
```bash
# Add to crontab for auto-start
crontab -e

# Add this line to start on boot
@reboot cd /home/pi/avatar-tank && ./start_final_stable.sh
```

## 🧪 **Testing & Verification**

### **Hardware Tests**
```bash
# Test camera
ffmpeg -f v4l2 -i /dev/video0 -t 10 -f null -

# Test microphone
arecord -D plughw:3,0 -f cd -t wav -d 5 test.wav && aplay test.wav

# Test motor controller
python3 -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.write(b'STATUS\\n')
response = ser.readline()
print('Motor response:', response)
ser.close()
"
```

### **Network Tests**
```bash
# Test local connectivity
curl -I http://localhost:5000

# Test streaming endpoints
curl -I http://localhost:8888/stream/index.m3u8
curl -I http://localhost:8889/stream
```

### **System Tests**
```bash
# Run system diagnostics
python3 -c "
from modules.device_detector import DeviceDetector
detector = DeviceDetector()
detector.scan_devices()
detector.print_summary()
"
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Camera Not Detected**
```bash
# Check USB connections
lsusb

# Check video devices
ls -la /dev/video*

# Test with different camera
v4l2-ctl --list-devices
```

#### **Audio Issues**
```bash
# Check audio devices
arecord -l
aplay -l

# Test ALSA configuration
alsamixer

# Reset audio system
sudo alsa force-reload
```

#### **Network Problems**
```bash
# Check network configuration
ip addr show
ip route show

# Test connectivity
ping -c 4 8.8.8.8

# Check firewall
sudo ufw status
```

#### **Permission Issues**
```bash
# Check user groups
groups $USER

# Fix permissions
sudo chmod 666 /dev/ttyACM0
sudo chmod 666 /dev/video0
```

### **Performance Optimization**

#### **Memory Management**
```bash
# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### **CPU Optimization**
```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## 📚 **Additional Resources**

### **Documentation**
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [MediaMTX Documentation](https://github.com/bluenviron/mediamtx)
- [WebRTC Documentation](https://webrtc.org/)

### **Community Support**
- [Raspberry Pi Forums](https://forums.raspberrypi.org/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/raspberry-pi)
- [GitHub Issues](https://github.com/yourusername/avatar-tank/issues)

### **Hardware Recommendations**
- **Cameras**: Logitech C920, C922, C930e
- **Microphones**: Blue Yeti, Audio-Technica ATR2100x-USB
- **Motor Controllers**: Arduino Uno, ESP32, Raspberry Pi Pico
- **Power**: Official Raspberry Pi 4 Power Supply (5V 3A)

---

**Need help?** Check the [README.md](README.md) or open an issue on GitHub!

