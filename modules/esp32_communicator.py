#!/usr/bin/env python3
"""
ESP32 Communication Module for Crawler Motor Control
Handles USB serial communication with ESP32 for motor control
"""

import serial
import time
import threading
import queue
from pathlib import Path

class ESP32Communicator:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.connected = False
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.communication_thread = None
        self.running = False
        
    def connect(self):
        """Establish connection to ESP32"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1,
                write_timeout=1
            )
            self.connected = True
            self.running = True
            
            # Start communication thread
            self.communication_thread = threading.Thread(target=self._communication_loop)
            self.communication_thread.daemon = True
            self.communication_thread.start()
            
            print(f"[ESP32] Connected to {self.port} at {self.baudrate} baud")
            return True
            
        except Exception as e:
            print(f"[ESP32] Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        if self.communication_thread:
            self.communication_thread.join(timeout=2)
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        
        self.connected = False
        print("[ESP32] Disconnected")
    
    def send_motor_command(self, left_speed, right_speed):
        """Send motor command to ESP32"""
        if not self.connected:
            print("[ESP32] Not connected, cannot send command")
            return False
        
        # Format: MOTOR:L:{left_speed}:R:{right_speed}
        command = f"MOTOR:L:{left_speed}:R:{right_speed}\n"
        
        try:
            self.command_queue.put(command)
            print(f"[ESP32] Command queued: {command.strip()}")
            return True
        except Exception as e:
            print(f"[ESP32] Failed to queue command: {e}")
            return False
    
    def _communication_loop(self):
        """Main communication loop"""
        while self.running:
            try:
                # Send queued commands
                if not self.command_queue.empty():
                    command = self.command_queue.get_nowait()
                    self.serial_connection.write(command.encode())
                    self.serial_connection.flush()
                
                # Read responses
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if response:
                        self.response_queue.put(response)
                        print(f"[ESP32] Response: {response}")
                
                time.sleep(0.01)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                print(f"[ESP32] Communication error: {e}")
                time.sleep(0.1)
    
    def get_response(self, timeout=1.0):
        """Get response from ESP32"""
        try:
            return self.response_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def is_connected(self):
        """Check if ESP32 is connected"""
        return self.connected and self.serial_connection and self.serial_connection.is_open

# Global ESP32 communicator instance
esp32_comm = ESP32Communicator()

def init_esp32():
    """Initialize ESP32 communication"""
    return esp32_comm.connect()

def send_crawler_command(direction, left_speed, right_speed):
    """Send crawler command to ESP32"""
    return esp32_comm.send_motor_command(left_speed, right_speed)

def get_esp32_status():
    """Get ESP32 connection status"""
    return {
        "connected": esp32_comm.is_connected(),
        "port": esp32_comm.port,
        "baudrate": esp32_comm.baudrate
    }

def cleanup_esp32():
    """Cleanup ESP32 communication"""
    esp32_comm.disconnect()
