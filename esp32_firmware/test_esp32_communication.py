#!/usr/bin/env python3
"""
ESP32 Communication Test Script
Tests the crawler motor control firmware
"""

import serial
import time
import sys
import argparse

class ESP32Tester:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
    def connect(self):
        """Connect to ESP32"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            print(f"Connected to ESP32 on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Disconnected from ESP32")
    
    def send_command(self, command):
        """Send command to ESP32 and wait for response"""
        if not self.ser or not self.ser.is_open:
            print("Not connected to ESP32")
            return None
        
        try:
            # Send command
            self.ser.write(f"{command}\n".encode())
            self.ser.flush()
            
            # Wait for response
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print(f"Error sending command: {e}")
            return None
    
    def test_connection(self):
        """Test basic connection"""
        print("\n=== Testing Connection ===")
        response = self.send_command("STATUS")
        if response:
            print(f"Status response: {response}")
            return True
        else:
            print("No response from ESP32")
            return False
    
    def test_motor_control(self):
        """Test motor control commands"""
        print("\n=== Testing Motor Control ===")
        
        # Test forward
        print("Testing forward movement...")
        response = self.send_command("MOTOR:L:100:R:100")
        print(f"Forward response: {response}")
        time.sleep(2)
        
        # Test backward
        print("Testing backward movement...")
        response = self.send_command("MOTOR:L:-100:R:-100")
        print(f"Backward response: {response}")
        time.sleep(2)
        
        # Test left turn
        print("Testing left turn...")
        response = self.send_command("MOTOR:L:-100:R:100")
        print(f"Left turn response: {response}")
        time.sleep(2)
        
        # Test right turn
        print("Testing right turn...")
        response = self.send_command("MOTOR:L:100:R:-100")
        print(f"Right turn response: {response}")
        time.sleep(2)
        
        # Stop
        print("Stopping motors...")
        response = self.send_command("MOTOR:L:0:R:0")
        print(f"Stop response: {response}")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid speed
        print("Testing invalid speed...")
        response = self.send_command("MOTOR:L:300:R:100")
        print(f"Invalid speed response: {response}")
        
        # Test invalid format
        print("Testing invalid format...")
        response = self.send_command("MOTOR:INVALID")
        print(f"Invalid format response: {response}")
        
        # Test unknown command
        print("Testing unknown command...")
        response = self.send_command("UNKNOWN_COMMAND")
        print(f"Unknown command response: {response}")
    
    def test_emergency_stop(self):
        """Test emergency stop"""
        print("\n=== Testing Emergency Stop ===")
        
        # Start motors
        print("Starting motors...")
        response = self.send_command("MOTOR:L:150:R:150")
        print(f"Start response: {response}")
        time.sleep(1)
        
        # Emergency stop
        print("Emergency stop...")
        response = self.send_command("STOP")
        print(f"Stop response: {response}")
    
    def test_sequence(self):
        """Test complete sequence"""
        print("\n=== Testing Complete Sequence ===")
        
        # Test connection
        if not self.test_connection():
            print("Connection test failed")
            return False
        
        # Test motor control
        self.test_motor_control()
        
        # Test error handling
        self.test_error_handling()
        
        # Test emergency stop
        self.test_emergency_stop()
        
        print("\n=== All Tests Complete ===")
        return True
    
    def interactive_mode(self):
        """Interactive mode for manual testing"""
        print("\n=== Interactive Mode ===")
        print("Enter commands manually (type 'quit' to exit)")
        print("Available commands:")
        print("  STATUS - Get current status")
        print("  MOTOR:L:{speed}:R:{speed} - Control motors")
        print("  STOP - Emergency stop")
        print("  TEST - Run test sequence")
        
        while True:
            try:
                command = input("\nESP32> ").strip()
                if command.lower() == 'quit':
                    break
                
                if command:
                    response = self.send_command(command)
                    if response:
                        print(f"Response: {response}")
                    else:
                        print("No response")
            except KeyboardInterrupt:
                break
        
        print("Exiting interactive mode")

def main():
    parser = argparse.ArgumentParser(description='Test ESP32 crawler motor control')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baudrate', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--test', choices=['connection', 'motors', 'errors', 'stop', 'all'], 
                       default='all', help='Test to run')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Create tester
    tester = ESP32Tester(args.port, args.baudrate)
    
    try:
        # Connect to ESP32
        if not tester.connect():
            print("Failed to connect to ESP32")
            return 1
        
        # Wait for ESP32 to initialize
        print("Waiting for ESP32 to initialize...")
        time.sleep(2)
        
        # Run tests
        if args.interactive:
            tester.interactive_mode()
        else:
            if args.test == 'connection':
                tester.test_connection()
            elif args.test == 'motors':
                tester.test_motor_control()
            elif args.test == 'errors':
                tester.test_error_handling()
            elif args.test == 'stop':
                tester.test_emergency_stop()
            elif args.test == 'all':
                tester.test_sequence()
        
        return 0
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test failed: {e}")
        return 1
    finally:
        tester.disconnect()

if __name__ == "__main__":
    sys.exit(main())
