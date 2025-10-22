#!/bin/bash
"""
ESP32 Firmware Setup Script
Automates the setup process for ESP32 crawler motor control
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ESP32_PORT="/dev/ttyUSB0"
ARDUINO_CLI_VERSION="0.35.0"
ESP32_BOARD_PACKAGE="esp32:esp32"

echo -e "${BLUE}ESP32 Crawler Motor Control Setup${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
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

# Check if ESP32 is connected
check_esp32_connection() {
    print_status "Checking ESP32 connection..."
    
    if ls /dev/ttyUSB* 1> /dev/null 2>&1; then
        ESP32_PORT=$(ls /dev/ttyUSB* | head -n1)
        print_status "ESP32 found on $ESP32_PORT"
        return 0
    else
        print_error "ESP32 not found. Please connect ESP32 via USB"
        return 1
    fi
}

# Install Arduino CLI
install_arduino_cli() {
    print_status "Installing Arduino CLI..."
    
    if command -v arduino-cli &> /dev/null; then
        print_status "Arduino CLI already installed"
        return 0
    fi
    
    # Download Arduino CLI
    cd /tmp
    wget -q "https://github.com/arduino/arduino-cli/releases/download/${ARDUINO_CLI_VERSION}/arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz"
    
    # Extract and install
    tar -xzf "arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz"
    sudo mv arduino-cli /usr/local/bin/
    
    # Cleanup
    rm "arduino-cli_${ARDUINO_CLI_VERSION}_Linux_64bit.tar.gz"
    
    print_status "Arduino CLI installed successfully"
}

# Install ESP32 board support
install_esp32_support() {
    print_status "Installing ESP32 board support..."
    
    # Initialize Arduino CLI
    arduino-cli config init
    
    # Add ESP32 board package
    arduino-cli core update-index --additional-urls "https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json"
    arduino-cli core install "$ESP32_BOARD_PACKAGE"
    
    print_status "ESP32 board support installed"
}

# Install required libraries
install_libraries() {
    print_status "Installing required libraries..."
    
    # Install ESP32Servo library
    arduino-cli lib install "ESP32Servo"
    
    print_status "Libraries installed successfully"
}

# Set up serial port permissions
setup_serial_permissions() {
    print_status "Setting up serial port permissions..."
    
    # Add user to dialout group
    sudo usermod -a -G dialout "$USER"
    
    # Set permissions for ESP32 port
    if [[ -e "$ESP32_PORT" ]]; then
        sudo chmod 666 "$ESP32_PORT"
        print_status "Serial port permissions set"
    else
        print_warning "ESP32 port not found, permissions will be set when connected"
    fi
}

# Compile firmware
compile_firmware() {
    print_status "Compiling firmware..."
    
    # Change to firmware directory
    cd "$(dirname "$0")"
    
    # Compile the firmware
    arduino-cli compile --fqbn "$ESP32_BOARD_PACKAGE:esp32:esp32" crawler_motor_control.ino
    
    if [[ $? -eq 0 ]]; then
        print_status "Firmware compiled successfully"
        return 0
    else
        print_error "Firmware compilation failed"
        return 1
    fi
}

# Upload firmware
upload_firmware() {
    print_status "Uploading firmware to ESP32..."
    
    # Check if ESP32 is connected
    if ! check_esp32_connection; then
        return 1
    fi
    
    # Upload firmware
    arduino-cli upload -p "$ESP32_PORT" --fqbn "$ESP32_BOARD_PACKAGE:esp32:esp32" crawler_motor_control.ino
    
    if [[ $? -eq 0 ]]; then
        print_status "Firmware uploaded successfully"
        return 0
    else
        print_error "Firmware upload failed"
        return 1
    fi
}

# Test ESP32 communication
test_communication() {
    print_status "Testing ESP32 communication..."
    
    # Wait for ESP32 to initialize
    sleep 3
    
    # Run test script
    if [[ -f "test_esp32_communication.py" ]]; then
        python3 test_esp32_communication.py --port "$ESP32_PORT" --test connection
    else
        print_warning "Test script not found, skipping communication test"
    fi
}

# Main setup function
main() {
    print_status "Starting ESP32 setup..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    print_status "Installing required packages..."
    sudo apt install -y python3 python3-pip python3-serial wget
    
    # Install Arduino CLI
    install_arduino_cli
    
    # Install ESP32 support
    install_esp32_support
    
    # Install libraries
    install_libraries
    
    # Setup serial permissions
    setup_serial_permissions
    
    # Compile firmware
    if ! compile_firmware; then
        print_error "Setup failed at compilation step"
        exit 1
    fi
    
    # Upload firmware
    if ! upload_firmware; then
        print_error "Setup failed at upload step"
        exit 1
    fi
    
    # Test communication
    test_communication
    
    print_status "ESP32 setup completed successfully!"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo "1. Connect ESCs to GPIO 18 (left) and GPIO 19 (right)"
    echo "2. Power on ESCs and wait for calibration"
    echo "3. Test with: python3 test_esp32_communication.py"
    echo "4. Start the Avatar Tank system"
    echo ""
    echo -e "${YELLOW}Note:${NC} You may need to log out and back in for serial permissions to take effect"
}

# Handle command line arguments
case "${1:-}" in
    "compile")
        compile_firmware
        ;;
    "upload")
        upload_firmware
        ;;
    "test")
        test_communication
        ;;
    "permissions")
        setup_serial_permissions
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  compile     - Compile firmware only"
        echo "  upload      - Upload firmware only"
        echo "  test        - Test communication only"
        echo "  permissions - Setup serial permissions only"
        echo "  help        - Show this help"
        echo ""
        echo "Default: Run complete setup"
        ;;
    *)
        main
        ;;
esac
