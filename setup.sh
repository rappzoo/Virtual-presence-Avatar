#!/bin/bash
# Avatar Tank - Setup Script
# Automated setup and installation script

set -e  # Exit on any error

echo "🤖 Avatar Tank Setup Script"
echo "=========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_status "Starting Avatar Tank setup..."
print_status "Working directory: $SCRIPT_DIR"

# Check system requirements
print_status "Checking system requirements..."

# Check if running on Raspberry Pi
if [[ $(uname -m) == "armv7l" ]] || [[ $(uname -m) == "aarch64" ]]; then
    print_success "Running on ARM architecture (Raspberry Pi compatible)"
else
    print_warning "Not running on ARM architecture - some features may not work"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
print_status "Python version: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION 3.8" | awk '{print ($1 >= $2)}') == 1 ]]; then
    print_success "Python version is compatible"
else
    print_error "Python 3.8+ is required"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    wget \
    unzip \
    ffmpeg \
    v4l-utils \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    net-tools \
    htop \
    vim \
    nano

print_success "System dependencies installed"

# Create virtual environment
print_status "Creating Python virtual environment..."
if [[ ! -d "avatar-env" ]]; then
    python3 -m venv avatar-env
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source avatar-env/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x *.sh
chmod +x scripts/*.sh 2>/dev/null || true

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p snapshots
mkdir -p recordings
mkdir -p sounds
mkdir -p config
mkdir -p logs

# Set up permissions
print_status "Setting up permissions..."
sudo usermod -a -G video,audio,dialout $USER

# Create default configuration if it doesn't exist
if [[ ! -f "config/avatar_state.json" ]]; then
    print_status "Creating default configuration..."
    cat > config/avatar_state.json << EOF
{
    "last_resolution": "480p",
    "last_fps": 10,
    "last_updated": "$(date -Iseconds)",
    "camera_settings": {
        "320p": {"width": 640, "height": 360, "fps": 10},
        "480p": {"width": 854, "height": 480, "fps": 10},
        "720p": {"width": 1280, "height": 720, "fps": 10}
    },
    "stream_status": {
        "active": false,
        "last_started": null,
        "ffmpeg_pid": null
    },
    "system_info": {
        "version": "1.0",
        "last_restart": null,
        "total_snapshots": 0
    }
}
EOF
    print_success "Default configuration created"
fi

# Check hardware
print_status "Checking hardware..."

# Check camera
if [[ -e "/dev/video0" ]]; then
    print_success "Camera detected at /dev/video0"
else
    print_warning "No camera detected at /dev/video0"
fi

# Check audio devices
if arecord -l | grep -q "card"; then
    print_success "Audio input devices detected"
else
    print_warning "No audio input devices detected"
fi

if aplay -l | grep -q "card"; then
    print_success "Audio output devices detected"
else
    print_warning "No audio output devices detected"
fi

# Check serial devices
if ls /dev/ttyACM* 1> /dev/null 2>&1; then
    print_success "Serial devices detected"
else
    print_warning "No serial devices detected (motor controller)"
fi

# Test basic functionality
print_status "Testing basic functionality..."

# Test Python imports
python3 -c "
import sys
try:
    import cv2
    import numpy as np
    import flask
    import serial
    print('✅ Core Python modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

# Test FFmpeg
if command -v ffmpeg &> /dev/null; then
    print_success "FFmpeg is available"
else
    print_error "FFmpeg is not available"
fi

# Test v4l2
if command -v v4l2-ctl &> /dev/null; then
    print_success "v4l2-utils is available"
else
    print_error "v4l2-utils is not available"
fi

# Create startup script
print_status "Creating startup script..."
cat > start_avatar.sh << 'EOF'
#!/bin/bash
# Avatar Tank - Startup Script

cd "$(dirname "$0")"

# Activate virtual environment
source avatar-env/bin/activate

# Start the system
python3 modules/mediamtx_main.py
EOF

chmod +x start_avatar.sh

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee /etc/systemd/system/avatar-tank.service > /dev/null << EOF
[Unit]
Description=Avatar Tank Remote Presence Robot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment=PATH=$SCRIPT_DIR/avatar-env/bin
ExecStart=$SCRIPT_DIR/avatar-env/bin/python modules/mediamtx_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created"

# Setup complete
echo ""
print_success "🎉 Avatar Tank setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Connect your hardware (camera, microphone, motor controller)"
echo "2. Configure your network settings"
echo "3. Edit config/mediamtx.yml if needed"
echo "4. Start the system: ./start_avatar.sh"
echo ""
echo "🌐 Access points:"
echo "   Web Interface: http://$(hostname -I | awk '{print $1}'):5000"
echo "   Video Stream: http://$(hostname -I | awk '{print $1}'):8888/stream/"
echo ""
echo "📚 Documentation:"
echo "   README.md - Main documentation"
echo "   PREREQUISITES.md - Detailed setup guide"
echo ""
echo "⚠️  Important:"
echo "   - Logout and login again for group permissions to take effect"
echo "   - Check hardware connections before starting"
echo "   - Review firewall settings for network access"
echo ""
print_success "Setup complete! 🚀"

