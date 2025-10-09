#!/usr/bin/env python3
"""
MediaMTX-compatible camera module for Avatar Tank system.
Handles camera initialization, configuration, and MediaMTX streaming integration.
"""

import cv2
import numpy as np
import datetime
import os
import threading
import time
import sys
import subprocess
import json
from typing import Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass


# Stream State Management
class StreamState(Enum):
    """Enumeration of possible stream states"""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class StreamStateInfo:
    """Information about current stream state"""
    state: StreamState
    timestamp: float
    process_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class StreamStateManager:
    """Centralized stream state management with event emitters"""
    
    def __init__(self):
        self._state = StreamState.STOPPED
        self._state_info = StreamStateInfo(
            state=StreamState.STOPPED,
            timestamp=time.time()
        )
        self._lock = threading.RLock()
        self._event_callbacks = []
        self._state_history = []
    
    def get_state(self) -> StreamState:
        """Get current stream state"""
        with self._lock:
            return self._state
    
    def get_state_info(self) -> StreamStateInfo:
        """Get detailed state information"""
        with self._lock:
            return StreamStateInfo(
                state=self._state,
                timestamp=self._state_info.timestamp,
                process_id=self._state_info.process_id,
                error_message=self._state_info.error_message,
                retry_count=self._state_info.retry_count
            )
    
    def set_state(self, new_state: StreamState, process_id: Optional[int] = None, error_message: Optional[str] = None):
        """Set new stream state with validation and event emission"""
        with self._lock:
            old_state = self._state
            
            # Validate state transition
            if not self._is_valid_transition(old_state, new_state):
                print(f"[State Manager] Invalid state transition: {old_state.value} -> {new_state.value}")
                return False
            
            # Update state
            self._state = new_state
            self._state_info = StreamStateInfo(
                state=new_state,
                timestamp=time.time(),
                process_id=process_id,
                error_message=error_message,
                retry_count=self._state_info.retry_count
            )
            
            # Add to history
            self._state_history.append(StreamStateInfo(
                state=old_state,
                timestamp=self._state_info.timestamp - 0.001  # Slightly before new state
            ))
            
            # Keep only last 10 state changes
            if len(self._state_history) > 10:
                self._state_history.pop(0)
            
            print(f"[State Manager] State transition: {old_state.value} -> {new_state.value}")
            
            # Emit state change event
            self._emit_state_change(old_state, new_state, process_id, error_message)
            
            return True
    
    def _is_valid_transition(self, from_state: StreamState, to_state: StreamState) -> bool:
        """Validate if state transition is allowed"""
        valid_transitions = {
            StreamState.STOPPED: [StreamState.STARTING, StreamState.ERROR],
            StreamState.STARTING: [StreamState.ACTIVE, StreamState.ERROR, StreamState.STOPPING],
            StreamState.ACTIVE: [StreamState.STOPPING, StreamState.ERROR],
            StreamState.STOPPING: [StreamState.STOPPED, StreamState.ERROR],
            StreamState.ERROR: [StreamState.STOPPED, StreamState.STARTING]
        }
        return to_state in valid_transitions.get(from_state, [])
    
    def add_event_callback(self, callback):
        """Add callback for state change events"""
        with self._lock:
            self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback):
        """Remove callback for state change events"""
        with self._lock:
            if callback in self._event_callbacks:
                self._event_callbacks.remove(callback)
    
    def _emit_state_change(self, old_state: StreamState, new_state: StreamState, process_id: Optional[int], error_message: Optional[str]):
        """Emit state change event to all registered callbacks"""
        for callback in self._event_callbacks:
            try:
                callback(old_state, new_state, process_id, error_message)
            except Exception as e:
                print(f"[State Manager] Error in state change callback: {e}")
    
    def increment_retry_count(self):
        """Increment retry count for error states"""
        with self._lock:
            self._state_info.retry_count += 1
    
    def reset_retry_count(self):
        """Reset retry count"""
        with self._lock:
            self._state_info.retry_count = 0
    
    def get_state_history(self) -> list:
        """Get state change history"""
        with self._lock:
            return self._state_history.copy()

# Error Recovery System
class ErrorRecoveryManager:
    """Manages automatic error recovery for common streaming issues"""
    
    def __init__(self):
        self.recovery_attempts = {}
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 30  # seconds
        self.last_recovery_time = {}
    
    def handle_camera_busy_error(self):
        """Handle camera device busy errors by killing conflicting processes"""
        try:
            print("[Error Recovery] Camera busy detected, killing conflicting processes...")
            
            # Kill any processes using the camera device
            camera_device = get_camera_device() or "/dev/video0"
            result = subprocess.run(['fuser', '-k', camera_device], capture_output=True, text=True)
            
            # DISABLED: External FFmpeg management is handled by monitor_stream.sh
            # subprocess.run(['pkill', '-f', 'ffmpeg.*v4l2'], capture_output=True)
            
            # Wait a moment for processes to terminate
            time.sleep(2)
            
            print("[Error Recovery] Camera device cleared")
            return True
            
        except Exception as e:
            print(f"[Error Recovery] Failed to clear camera device: {e}")
            return False
    
    def handle_network_timeout_error(self):
        """Handle network timeout by reducing quality and retrying"""
        try:
            print("[Error Recovery] Network timeout detected, reducing quality...")
            
            global current_resolution, current_framerate
            
            # Reduce resolution first
            if current_resolution == "720p":
                set_resolution("480p")
                print("[Error Recovery] Reduced resolution to 480p")
            elif current_resolution == "480p":
                set_resolution("320p")
                print("[Error Recovery] Reduced resolution to 320p")
            
            # Reduce framerate
            if current_framerate > 10:
                set_framerate(10)
                print("[Error Recovery] Reduced framerate to 10fps")
            
            return True
            
        except Exception as e:
            print(f"[Error Recovery] Failed to reduce quality: {e}")
            return False
    
    def handle_mediamtx_crash(self):
        """Handle MediaMTX service crash by restarting it"""
        try:
            print("[Error Recovery] MediaMTX crash detected, restarting service...")
            
            # Kill existing MediaMTX processes
            subprocess.run(['pkill', '-f', 'mediamtx'], capture_output=True)
            time.sleep(2)
            
            # Restart MediaMTX
            import os
            mediamtx_cmd = ['/usr/local/bin/mediamtx', 'config/mediamtx.yml']
            subprocess.Popen(mediamtx_cmd, stdout=open('/tmp/mediamtx.log', 'w'), 
                           stderr=subprocess.STDOUT, cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Wait for MediaMTX to start
            time.sleep(3)
            
            print("[Error Recovery] MediaMTX service restarted")
            return True
            
        except Exception as e:
            print(f"[Error Recovery] Failed to restart MediaMTX: {e}")
            return False
    
    def should_attempt_recovery(self, error_type: str) -> bool:
        """Check if recovery should be attempted for this error type"""
        current_time = time.time()
        
        # Check cooldown period
        if error_type in self.last_recovery_time:
            if current_time - self.last_recovery_time[error_type] < self.recovery_cooldown:
                return False
        
        # Check max attempts
        if self.recovery_attempts.get(error_type, 0) >= self.max_recovery_attempts:
            print(f"[Error Recovery] Max recovery attempts reached for {error_type}")
            return False
        
        return True
    
    def attempt_recovery(self, error_type: str) -> bool:
        """Attempt recovery for a specific error type"""
        if not self.should_attempt_recovery(error_type):
            return False
        
        self.recovery_attempts[error_type] = self.recovery_attempts.get(error_type, 0) + 1
        self.last_recovery_time[error_type] = time.time()
        
        print(f"[Error Recovery] Attempting recovery for {error_type} (attempt {self.recovery_attempts[error_type]})")
        
        if error_type == "camera_busy":
            return self.handle_camera_busy_error()
        elif error_type == "network_timeout":
            return self.handle_network_timeout_error()
        elif error_type == "mediamtx_crash":
            return self.handle_mediamtx_crash()
        
        return False
    
    def reset_recovery_attempts(self, error_type: str = None):
        """Reset recovery attempts for successful recovery"""
        if error_type:
            self.recovery_attempts[error_type] = 0
        else:
            self.recovery_attempts.clear()

# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()

# Watchdog Timer for Frame Monitoring
class FrameWatchdog:
    """Monitors frame reception and triggers recovery if no frames received"""
    
    def __init__(self):
        self.last_frame_time = 0
        self.watchdog_timeout = 10  # seconds
        self.watchdog_active = False
        self.watchdog_thread = None
    
    def start_watchdog(self):
        """Start the watchdog monitoring thread"""
        if self.watchdog_active:
            return
        
        self.watchdog_active = True
        self.last_frame_time = time.time()
        
        def watchdog_loop():
            while self.watchdog_active:
                try:
                    current_time = time.time()
                    
                    # Check if we've received frames recently
                    if current_time - self.last_frame_time > self.watchdog_timeout:
                        print(f"[Watchdog] No frames received for {self.watchdog_timeout}s, triggering recovery")
                        
                        # Trigger recovery
                        error_recovery_manager.attempt_recovery("network_timeout")
                        
                        # Reset frame time to prevent immediate retrigger
                        self.last_frame_time = current_time
                    
                    time.sleep(1)  # Check every second
                    
                except Exception as e:
                    print(f"[Watchdog] Error in watchdog loop: {e}")
                    time.sleep(5)
        
        self.watchdog_thread = threading.Thread(target=watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        print("[Watchdog] Frame watchdog started")
    
    def stop_watchdog(self):
        """Stop the watchdog monitoring thread"""
        self.watchdog_active = False
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=2)
        print("[Watchdog] Frame watchdog stopped")
    
    def update_frame_time(self):
        """Update the last frame received time"""
        self.last_frame_time = time.time()

# Global instances
frame_watchdog = FrameWatchdog()
stream_state_manager = StreamStateManager()

# Process Management and Cleanup
def cleanup_zombie_processes():
    """Clean up any zombie or conflicting processes on startup"""
    try:
        print("[Process Cleanup] Starting cleanup of zombie processes...")
        
        # DISABLED: External FFmpeg management is handled by monitor_stream.sh
        # subprocess.run(['pkill', '-f', 'ffmpeg.*rtsp://localhost:8554/stream'], 
        #               capture_output=True, timeout=5)
        
        # Kill any existing Python processes (except current one)
        current_pid = os.getpid()
        result = subprocess.run(['pgrep', '-f', 'python.*mediamtx_main'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            for pid_line in result.stdout.strip().split('\n'):
                if pid_line.strip():
                    pid = int(pid_line.strip())
                    if pid != current_pid:
                        try:
                            os.kill(pid, 9)
                            print(f"[Process Cleanup] Killed conflicting Python process: {pid}")
                        except ProcessLookupError:
                            pass  # Process already dead
        
        # Wait for processes to terminate
        time.sleep(2)
        
        # Check for zombie processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        zombie_count = result.stdout.count('<defunct>')
        if zombie_count > 0:
            print(f"[Process Cleanup] Found {zombie_count} zombie processes")
            # DISABLED: External FFmpeg management is handled by monitor_stream.sh
            # subprocess.run(['killall', '-9', 'ffmpeg'], capture_output=True, timeout=5)
        
        print("[Process Cleanup] Process cleanup completed")
        return True
        
    except Exception as e:
        print(f"[Process Cleanup] Error during cleanup: {e}")
        return False

def validate_system_state():
    """Validate that the system is in a clean state before starting"""
    try:
        print("[System Validation] Validating system state...")
        
        # Check if camera device is available
        camera_device = get_camera_device() or "/dev/video0"
        result = subprocess.run(['fuser', camera_device], capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"[System Validation] Camera device {camera_device} is busy, clearing...")
            subprocess.run(['fuser', '-k', camera_device], capture_output=True, timeout=5)
            time.sleep(1)
        
        # Check if MediaMTX is running
        result = subprocess.run(['pgrep', '-f', 'mediamtx.*config/mediamtx.yml'], 
                              capture_output=True, timeout=5)
        if result.returncode != 0:
            print("[System Validation] MediaMTX not running, this may cause issues")
        
        # Check for state synchronization issues
        current_state = stream_state_manager.get_state()
        if current_state == StreamState.ACTIVE:
            # Verify the process is actually running and connected to MediaMTX
            state_info = stream_state_manager.get_state_info()
            if state_info.process_id:
                try:
                    # Check if process exists
                    subprocess.run(['kill', '-0', str(state_info.process_id)], 
                                 capture_output=True, timeout=2)
                    
                    # Check if MediaMTX is receiving the stream
                    import requests
                    try:
                        response = requests.get('http://localhost:8889/stream', timeout=2)
                        if response.status_code == 404:
                            print("[System Validation] State shows active but MediaMTX not receiving stream - fixing...")
                            stream_state_manager.set_state(StreamState.STOPPED)
                            return False
                    except:
                        pass  # WebRTC endpoint might not be accessible without client
                        
                except subprocess.CalledProcessError:
                    print("[System Validation] Process ID in state manager doesn't exist - resetting state")
                    stream_state_manager.set_state(StreamState.STOPPED)
        
        # Reset state manager to clean state if needed
        if current_state not in [StreamState.STOPPED, StreamState.ERROR]:
            print("[System Validation] Resetting state manager to clean state")
            stream_state_manager.set_state(StreamState.STOPPED)
        
        stream_state_manager.reset_retry_count()
        
        print("[System Validation] System validation completed")
        return True
        
    except Exception as e:
        print(f"[System Validation] Error during validation: {e}")
        return False

def auto_recovery_on_startup():
    """Automatic recovery and cleanup when the system starts"""
    try:
        print("[Auto Recovery] Starting automatic recovery...")
        
        # Step 1: Clean up zombie processes
        cleanup_zombie_processes()
        
        # Step 2: Validate system state
        validate_system_state()
        
        # Step 3: Check if stream should be auto-started
        # This will be determined by the main application
        
        print("[Auto Recovery] Automatic recovery completed")
        return True
        
    except Exception as e:
        print(f"[Auto Recovery] Error during auto recovery: {e}")
        return False

# Recording Robustness System
class RecordingManager:
    """Manages robust recording with automatic resume and segment management"""
    
    def __init__(self):
        self.recording_process = None
        self.recording_active = False
        self.recording_lock = threading.Lock()
        self.recording_directory = "/home/havatar/recordings"
        self.current_segment = None
        self.segment_duration = 300  # 5 minutes per segment
        self.last_segment_time = 0
        
        # Ensure recording directory exists
        os.makedirs(self.recording_directory, exist_ok=True)
    
    def start_recording(self):
        """Start recording directly from FFmpeg source (not RTSP loopback)"""
        with self.recording_lock:
            if self.recording_active:
                return {"ok": False, "msg": "Recording already active"}
            
            try:
                print("[Recording Manager] Starting direct FFmpeg recording...")
                
                # Get camera and audio devices
                camera_device = get_camera_device() or "/dev/video0"
                # Use different audio device to avoid conflict with WebRTC stream
                audio_device = "default"  # Use default device instead of plughw:3,0
                
                # Generate timestamped filename
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_segment = f"recording_{timestamp}.mp4"
                recording_path = os.path.join(self.recording_directory, self.current_segment)
                
                # FFmpeg command for direct recording (simplified, single file)
                cmd = [
                    'ffmpeg',
                    '-f', 'v4l2',
                    '-i', camera_device,
                    '-f', 'alsa',
                    '-i', audio_device,
                    
                    # Video encoding
                    '-c:v', 'libx264',
                    '-preset', 'fast',
                    '-crf', '23',  # Good quality for recording
                    '-pix_fmt', 'yuv420p',
                    
                    # Audio encoding
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    
                    # Recording-specific settings
                    '-movflags', '+faststart',  # Optimize for streaming
                    '-f', 'mp4',
                    
                    # Single output file
                    recording_path
                ]
                
                print(f"[Recording Manager] Recording command: {' '.join(cmd)}")
                
                # Start recording process
                self.recording_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                
                # Wait a moment to ensure it starts
                time.sleep(1)
                if self.recording_process.poll() is not None:
                    stderr_output = self.recording_process.stderr.read().decode('utf-8')
                    print(f"[Recording Manager] Recording failed to start: {stderr_output}")
                    return {"ok": False, "msg": f"Recording failed: {stderr_output}"}
                
                self.recording_active = True
                self.last_segment_time = time.time()
                
                print(f"[Recording Manager] Recording started: {recording_path}")
                return {"ok": True, "msg": f"Recording started: {self.current_segment}"}
                
            except Exception as e:
                print(f"[Recording Manager] Failed to start recording: {e}")
                return {"ok": False, "msg": f"Recording failed: {str(e)}"}
    
    def stop_recording(self):
        """Stop recording gracefully"""
        with self.recording_lock:
            if not self.recording_active:
                return {"ok": False, "msg": "Recording not active"}
            
            try:
                print("[Recording Manager] Stopping recording...")
                
                if self.recording_process:
                    # Send quit signal (Ctrl+C equivalent)
                    if self.recording_process.stdin:
                        self.recording_process.stdin.write(b'q\n')
                        self.recording_process.stdin.flush()
                        self.recording_process.stdin.close()
                    
                    # Wait for process to finish gracefully
                    timeout = 15
                    start_time = time.time()
                    
                    while self.recording_process.poll() is None and (time.time() - start_time) < timeout:
                        time.sleep(0.2)
                    
                    # Force terminate if still running
                    if self.recording_process.poll() is None:
                        print("[Recording Manager] Force terminating recording process")
                        self.recording_process.terminate()
                        try:
                            self.recording_process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            print("[Recording Manager] Force killing recording process")
                            self.recording_process.kill()
                            self.recording_process.wait(timeout=1)
                    
                    # Clean up any zombie processes
                    try:
                        self.recording_process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        pass
                
                self.recording_active = False
                self.recording_process = None
                self.current_segment = None
                
                print("[Recording Manager] Recording stopped")
                return {"ok": True, "msg": "Recording stopped"}
                
            except Exception as e:
                print(f"[Recording Manager] Error stopping recording: {e}")
                return {"ok": False, "msg": f"Stop failed: {str(e)}"}
    
    def get_recording_status(self):
        """Get current recording status"""
        with self.recording_lock:
            return {
                "active": self.recording_active,
                "current_segment": self.current_segment,
                "recording_directory": self.recording_directory,
                "segment_duration": self.segment_duration
            }
    
    def list_recordings(self):
        """List all recording files"""
        try:
            recordings = []
            for filename in os.listdir(self.recording_directory):
                if filename.startswith("recording_") and filename.endswith(".mp4"):
                    filepath = os.path.join(self.recording_directory, filename)
                    stat = os.stat(filepath)
                    recordings.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created": stat.st_ctime,
                        "modified": stat.st_mtime
                    })
            
            # Sort by creation time (newest first)
            recordings.sort(key=lambda x: x["created"], reverse=True)
            return recordings
            
        except Exception as e:
            print(f"[Recording Manager] Error listing recordings: {e}")
            return []
    
    def auto_resume_recording(self):
        """Automatically resume recording if stream restarts"""
        if not self.recording_active:
            return
        
        try:
            print("[Recording Manager] Auto-resuming recording after stream restart...")
            
            # Stop current recording
            self.stop_recording()
            
            # Wait a moment
            time.sleep(2)
            
            # Start new recording
            result = self.start_recording()
            if result["ok"]:
                print("[Recording Manager] Recording auto-resumed successfully")
            else:
                print(f"[Recording Manager] Failed to auto-resume recording: {result['msg']}")
                
        except Exception as e:
            print(f"[Recording Manager] Error in auto-resume: {e}")

# Global recording manager
recording_manager = RecordingManager()

# Try to get device detector - handle import gracefully
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from modules.device_detector import device_detector, CAMERA_DEVICE
    print(f"[MediaMTX Camera] Using detected camera device: {CAMERA_DEVICE}")
except ImportError as e:
    print(f"[MediaMTX Camera] Warning: Could not import device detector ({e}), using fallback")
    CAMERA_DEVICE = '/dev/video0'


# ============== CAMERA SETTINGS ==============
# Load saved settings or use defaults
def load_camera_settings():
    """Load camera settings from persistent state or use defaults"""
    global current_resolution, current_framerate
    
    try:
        # Use the new state manager for persistent settings
        from modules.avatar_state import get_last_resolution, get_last_fps, get_camera_settings
        
        # Load from persistent state
        current_resolution = get_last_resolution()
        current_framerate = get_last_fps()
        
        # Update camera_settings with state manager settings
        global camera_settings
        state_settings = get_camera_settings()
        if state_settings:
            camera_settings.update(state_settings)
        
        print(f"[MediaMTX Camera] Loaded persistent settings: {current_resolution}@{current_framerate}fps")
        
    except Exception as e:
        print(f"[MediaMTX Camera] Error loading persistent settings: {e}, using defaults")
        current_resolution = "480p"
        current_framerate = 10

def save_camera_settings():
    """Save camera settings to persistent state"""
    global current_resolution, current_framerate
    
    try:
        # Use the new state manager for persistent settings
        from modules.avatar_state import set_last_resolution, set_last_fps
        
        # Save to persistent state
        set_last_resolution(current_resolution)
        set_last_fps(current_framerate)
        
        print(f"[MediaMTX Camera] Saved persistent settings: {current_resolution}@{current_framerate}fps")
        
    except Exception as e:
        print(f"[MediaMTX Camera] Error saving persistent settings: {e}")

camera_settings = {
    "320p": {"width": 640, "height": 360, "fps": 10},
    "480p": {"width": 854, "height": 480, "fps": 10},
    "720p": {"width": 1280, "height": 720, "fps": 10}
}

# Global camera state variables (declared before loading settings)
current_resolution = "480p"
current_framerate = 10

# Initialize settings (this will update the global variables)
load_camera_settings()

# MediaMTX streaming settings
streaming_process: Optional[subprocess.Popen] = None
streaming_lock = threading.Lock()
streaming_active = False

# CPU optimization: FFmpeg process cache
ffmpeg_process_cache = {}
cache_lock = threading.Lock()


class MediaMTXCameraManager:
    """MediaMTX-compatible camera manager with streaming capabilities"""
    
    def __init__(self):
        self.camera = None
        self.camera_device = None
        self.lock = threading.Lock()
        self._last_bgr = None
        self._last_sz = (0, 0)
        self._last_lock = threading.Lock()
        self._frame_counter = 0
        self._error_count = 0
        self._max_errors = 5
        self._initialized = False
        
    def _ensure_initialized(self):
        """Ensure camera is initialized before use"""
        if not self._initialized:
            print("[MediaMTX Camera] Performing delayed initialization...")
            # Don't auto-initialize camera - let streaming handle it
            # self.init_camera()
            self._initialized = True
    
    def _kill_processes_using_device(self, device):
        """Kill any processes that might be using the camera device"""
        try:
            result = subprocess.run(['lsof', device], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            os.kill(int(pid), 9)
                            print(f"[MediaMTX Camera] Killed process {pid} using {device}")
                        except (ValueError, ProcessLookupError):
                            pass
            return True
        except Exception as e:
            print(f"[MediaMTX Camera] Warning: Could not kill processes using {device}: {e}")
            return False
    
    def _check_camera_device(self, device):
        """Check if camera device exists and is accessible (no OpenCV access)"""
        try:
            import os
            if os.path.exists(device):
                # Check if device is accessible
                with open(device, 'rb') as f:
                    pass  # Just test if we can open it
                print(f"[MediaMTX Camera] ✓ {device} - Device accessible")
                return True
            else:
                print(f"[MediaMTX Camera] ✗ {device} - Device not found")
                return False
        except Exception as e:
            print(f"[MediaMTX Camera] ✗ {device} - Error: {e}")
            return False
    
    def find_working_camera(self):
        """Find a working camera device"""
        devices_to_try = []
        
        # First try the detected device
        if CAMERA_DEVICE and isinstance(CAMERA_DEVICE, str):
            devices_to_try.append(CAMERA_DEVICE)
        
        # Add common device paths
        common_devices = ['/dev/video0', '/dev/video1', '/dev/video2', '/dev/video3']
        for dev in common_devices:
            if dev not in devices_to_try:
                devices_to_try.append(dev)
        
        # Check each device (no OpenCV access)
        for dev in devices_to_try:
            if isinstance(dev, str) and not os.path.exists(dev):
                continue
                
            print(f"[MediaMTX Camera] Testing device: {dev}")
            
            if self._check_camera_device(dev):
                return dev
        
        print("[MediaMTX Camera] ✗ No working camera device found")
        return None
    
    def init_camera(self):
        """Initialize camera device checking (no OpenCV access)"""
        with self.lock:
            print(f"[MediaMTX Camera] Checking camera device for resolution: {current_resolution}")
            
            # Clean up existing camera reference
            self.camera = None
            
            try:
                # Find working camera device
                device = self.find_working_camera()
                
                if not new_cam and CAMERA_DEVICE:
                    print(f"[MediaMTX Camera] Attempting to free device {CAMERA_DEVICE} and retry...")
                    self._kill_processes_using_device(CAMERA_DEVICE)
                    time.sleep(1)
                    new_cam, dev = self.find_working_camera()
                
                if not new_cam:
                    print("[MediaMTX Camera] No camera available")
                    self._error_count = 0
                    return False
                
                self.camera = new_cam
                self.camera_device = dev
                self._error_count = 0
                
                # Configure camera settings
                try:
                    settings = camera_settings[current_resolution]
                    print(f"[MediaMTX Camera] Setting resolution to {settings['width']}x{settings['height']}@{current_framerate}fps")
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
                    self.camera.set(cv2.CAP_PROP_FPS, current_framerate)
                    self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                    
                    # Verify settings
                    actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                    actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
                    
                    print(f"[MediaMTX Camera] Configured: {actual_width}x{actual_height}@{actual_fps:.1f}fps")
                    return True
                    
                except Exception as e:
                    print(f"[MediaMTX Camera] Configuration error: {e}")
                    return False
                    
            except Exception as e:
                print(f"[MediaMTX Camera] Initialization error: {e}")
                return False
    
    def read_frame(self):
        """Read a frame from the camera with error handling"""
        self._ensure_initialized()
        
        with self.lock:
            if self.camera is None:
                return False, None
            
            try:
                ret, frame = self.camera.read()
                
                if not ret or frame is None:
                    self._error_count += 1
                    print(f"[MediaMTX Camera] Frame read failed (error count: {self._error_count})")
                    
                    if self._error_count >= self._max_errors:
                        print("[MediaMTX Camera] Too many errors, reinitializing...")
                        threading.Thread(target=self._reinit_camera, daemon=True).start()
                    
                    return False, None
                
                # Reset error count on success
                self._error_count = 0
                self._frame_counter += 1
                
                # Update shared frame buffer
                h, w = frame.shape[:2]
                with self._last_lock:
                    self._last_bgr = frame.copy()
                    self._last_sz = (w, h)
                
                return True, frame
                
            except Exception as e:
                self._error_count += 1
                print(f"[MediaMTX Camera] Read exception: {e} (error count: {self._error_count})")
                
                if self._error_count >= self._max_errors:
                    print("[MediaMTX Camera] Too many errors, reinitializing...")
                    threading.Thread(target=self._reinit_camera, daemon=True).start()
                
                return False, None
    
    def _reinit_camera(self):
        """Reinitialize camera in separate thread"""
        time.sleep(1)
        self.init_camera()
    
    def get_shared_frame_data(self):
        """Get the shared frame data"""
        try:
            self._ensure_initialized()
            with self._last_lock:
                frame = self._last_bgr.copy() if self._last_bgr is not None else None
                size = self._last_sz
            return frame, size
        except Exception as e:
            print(f"[MediaMTX Camera] Shared frame data error: {e}")
            return None, (854, 480)
    
    def set_resolution(self, resolution):
        """Change camera resolution with graceful restart"""
        global current_resolution
        
        print(f"[MediaMTX Camera] Changing resolution from {current_resolution} to {resolution}")
        
        if resolution in camera_settings:
            old_resolution = current_resolution
            current_resolution = resolution
            
            # Save settings immediately
            save_camera_settings()
            print(f"[MediaMTX Camera] Resolution updated to {current_resolution}")
            
            # If streaming is active, restart gracefully
            if streaming_active:
                print(f"[MediaMTX Camera] Gracefully restarting stream for resolution change: {old_resolution} -> {resolution}")
                
                # Use state manager for coordinated restart
                try:
                    # Stop streaming gracefully
                    stop_result = stop_streaming()
                    if not stop_result.get('ok'):
                        print(f"[MediaMTX Camera] Failed to stop stream for resolution change: {stop_result}")
                        # Revert resolution on failure
                        current_resolution = old_resolution
                        save_camera_settings()
                        return False
                    
                    # Wait for clean shutdown
                    time.sleep(2)
                    
                    # Start streaming with new resolution
                    start_result = start_streaming()
                    if start_result.get('ok'):
                        print(f"[MediaMTX Camera] Stream restarted successfully with resolution {resolution}")
                        return True
                    else:
                        print(f"[MediaMTX Camera] Failed to restart stream: {start_result}")
                        # Revert resolution on failure
                        current_resolution = old_resolution
                        save_camera_settings()
                        return False
                        
                except Exception as e:
                    print(f"[MediaMTX Camera] Error during resolution change: {e}")
                    # Revert resolution on error
                    current_resolution = old_resolution
                    save_camera_settings()
                    return False
            else:
                print(f"[MediaMTX Camera] Resolution updated to {current_resolution} (stream not active)")
                return True
        return False
    
    def set_framerate(self, framerate):
        """Change camera framerate with graceful restart"""
        global current_framerate
        
        print(f"[MediaMTX Camera] Changing framerate from {current_framerate} to {framerate}")
        
        old_framerate = current_framerate
        current_framerate = framerate
        
        # Save settings immediately
        save_camera_settings()
        print(f"[MediaMTX Camera] Global framerate updated to {current_framerate}")
        
        # If streaming is active, restart gracefully
        if streaming_active:
            print(f"[MediaMTX Camera] Gracefully restarting stream for framerate change: {old_framerate} -> {framerate}")
            
            try:
                # Stop streaming gracefully
                stop_result = stop_streaming()
                if not stop_result.get('ok'):
                    print(f"[MediaMTX Camera] Failed to stop stream for framerate change: {stop_result}")
                    # Revert framerate on failure
                    current_framerate = old_framerate
                    save_camera_settings()
                    return False
                
                # Wait for clean shutdown
                time.sleep(2)
                
                # Start streaming with new framerate
                start_result = start_streaming()
                if start_result.get('ok'):
                    print(f"[MediaMTX Camera] Stream restarted successfully with framerate {framerate}")
                    return True
                else:
                    print(f"[MediaMTX Camera] Failed to restart stream: {start_result}")
                    # Revert framerate on failure
                    current_framerate = old_framerate
                    save_camera_settings()
                    return False
                    
            except Exception as e:
                print(f"[MediaMTX Camera] Error during framerate change: {e}")
                # Revert framerate on error
                current_framerate = old_framerate
                save_camera_settings()
                return False
        else:
            print(f"[MediaMTX Camera] Framerate updated to {current_framerate} (stream not active)")
            return True
    
    def get_status(self):
        """Get camera status information"""
        try:
            # Don't auto-initialize camera for status check
            with self.lock:
                return {
                    "ok": self.camera is not None and not isinstance(self.camera, DummyCamera),
                    "device": self.camera_device,
                    "resolution": current_resolution,
                    "framerate": current_framerate,
                    "frame_counter": self._frame_counter,
                    "error_count": self._error_count,
                    "initialized": self._initialized,
                    "streaming": streaming_active
                }
        except Exception as e:
            return {
                "ok": False,
                "msg": f"Camera status error: {e}",
                "device": "unknown",
                "resolution": current_resolution,
                "framerate": current_framerate,
                "frame_counter": 0,
                "error_count": 0,
                "initialized": False,
                "streaming": False
            }
    
    def take_snapshot(self, filename=None):
        """Take a snapshot and save it"""
        try:
            # Try to read frame from camera first
            ret, frame = self.read_frame()
            
            if not ret or frame is None:
                # If camera is busy, try to capture from FFmpeg stream
                return self._capture_from_stream(filename)
            
            if filename is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshots/avatar_tank_{timestamp}.jpg"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Save image
            success = cv2.imwrite(filename, frame)
            
            if success:
                return {"ok": True, "filename": filename}
            else:
                return {"ok": False, "msg": "Failed to save image"}
                
        except Exception as e:
            return {"ok": False, "msg": str(e)}
    
    def _capture_from_stream(self, filename=None):
        """Capture snapshot from HLS stream when camera is busy"""
        try:
            if filename is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshots/avatar_tank_{timestamp}.jpg"
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Use ffmpeg to capture a single frame from the HLS stream
            cmd = [
                'ffmpeg', '-y', '-i', 'http://localhost:8888/stream/index.m3u8',
                '-vframes', '1', '-q:v', '2', filename
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists(filename):
                return {"ok": True, "filename": filename}
            else:
                return {"ok": False, "msg": f"HLS capture failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"ok": False, "msg": "Snapshot timeout - stream busy"}
        except Exception as e:
            return {"ok": False, "msg": f"Stream capture error: {str(e)}"}
    
    def cleanup(self):
        """Clean up camera resources"""
        with self.lock:
            if self.camera:
                try:
                    self.camera.release()
                except:
                    pass
            self.camera = None


# ============== MediaMTX Streaming Functions ==============

def check_device_available(device):
    """Check if camera device is available and not in use by other processes"""
    try:
        import subprocess
        
        # Use fuser to check if device is in use
        result = subprocess.run(['fuser', device], capture_output=True, text=True)
        if result.returncode == 0:
            # Device is in use, get the PIDs
            pids = result.stdout.strip().split()
            print(f"[MediaMTX Camera] Device {device} is in use by PIDs: {pids}")
            return False
        
        # Device is available
        print(f"[MediaMTX Camera] Device {device} is available")
        return True
        
    except Exception as e:
        print(f"[MediaMTX Camera] Error checking device {device}: {e}")
        return False

def lock_device(device):
    """Lock camera device by killing conflicting processes"""
    try:
        import subprocess
        
        print(f"[MediaMTX Camera] Locking device {device}...")
        
        # Kill any processes using the device
        subprocess.run(['fuser', '-k', device], capture_output=True)
        time.sleep(1)
        
        # Verify device is now free
        result = subprocess.run(['fuser', device], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[MediaMTX Camera] Warning: Device {device} still in use after kill")
            return False
        
        print(f"[MediaMTX Camera] ✓ Device {device} locked successfully")
        return True
        
    except Exception as e:
        print(f"[MediaMTX Camera] Error locking device {device}: {e}")
        return False

# Reconnection state machine
reconnection_state = {
    'attempts': 0,
    'max_attempts': 5,
    'backoff_delays': [1, 2, 4, 8, 10],  # Exponential backoff in seconds
    'is_reconnecting': False,
    'last_failure_time': 0,
    'consecutive_failures': 0
}

def get_reconnection_delay():
    """Get the next reconnection delay using exponential backoff"""
    global reconnection_state
    
    if reconnection_state['attempts'] >= len(reconnection_state['backoff_delays']):
        return reconnection_state['backoff_delays'][-1]  # Max delay
    
    return reconnection_state['backoff_delays'][reconnection_state['attempts']]

def reset_reconnection_state():
    """Reset reconnection state after successful connection"""
    global reconnection_state
    reconnection_state['attempts'] = 0
    reconnection_state['is_reconnecting'] = False
    reconnection_state['consecutive_failures'] = 0
    print("[Reconnection] State reset - connection successful")

def should_attempt_reconnection():
    """Check if we should attempt reconnection"""
    global reconnection_state
    
    if reconnection_state['is_reconnecting']:
        return False
    
    if reconnection_state['attempts'] >= reconnection_state['max_attempts']:
        print(f"[Reconnection] Max attempts ({reconnection_state['max_attempts']}) reached")
        return False
    
    return True

def start_reconnection_attempt():
    """Start a reconnection attempt with proper locking"""
    global reconnection_state
    
    if not should_attempt_reconnection():
        return False
    
    reconnection_state['is_reconnecting'] = True
    reconnection_state['attempts'] += 1
    reconnection_state['consecutive_failures'] += 1
    
    delay = get_reconnection_delay()
    print(f"[Reconnection] Attempt {reconnection_state['attempts']}/{reconnection_state['max_attempts']} in {delay}s")
    
    return True

def handle_stream_failure():
    """Handle stream failure and initiate reconnection if appropriate"""
    global reconnection_state
    
    reconnection_state['last_failure_time'] = time.time()
    
    if start_reconnection_attempt():
        delay = get_reconnection_delay()
        print(f"[Reconnection] Scheduling reconnection in {delay} seconds...")
        
        # Schedule reconnection attempt
        import threading
        def delayed_reconnection():
            time.sleep(delay)
            if reconnection_state['is_reconnecting']:
                print(f"[Reconnection] Executing attempt {reconnection_state['attempts']}")
                try:
                    # Stop any existing stream
                    stop_streaming()
                    time.sleep(1)
                    
                    # Attempt to restart
                    result = start_streaming()
                    if result.get('ok'):
                        print("[Reconnection] ✓ Stream reconnected successfully")
                        reset_reconnection_state()
                    else:
                        print(f"[Reconnection] ✗ Reconnection failed: {result.get('msg', 'Unknown error')}")
                        reconnection_state['is_reconnecting'] = False
                        # Will retry on next failure
                        
                except Exception as e:
                    print(f"[Reconnection] ✗ Reconnection error: {e}")
                    reconnection_state['is_reconnecting'] = False
        
        # Start reconnection thread
        reconnect_thread = threading.Thread(target=delayed_reconnection, daemon=True)
        reconnect_thread.start()
    else:
        print("[Reconnection] Max reconnection attempts reached or already reconnecting")

# Bandwidth management system
bandwidth_manager = {
    'current_resolution': '480p',
    'current_fps': 10,
    'current_bitrate': 32,
    'network_conditions': {
        'packet_loss_rate': 0.0,
        'rtt_ms': 0,
        'bandwidth_kbps': 0
    },
    'adaptation_history': [],
    'last_adaptation_time': 0,
    'adaptation_cooldown': 10  # Seconds between adaptations
}

def measure_network_conditions():
    """Measure current network conditions"""
    global bandwidth_manager
    
    try:
        import requests
        import time
        
        # Measure RTT to MediaMTX server
        start_time = time.time()
        try:
            response = requests.get('http://localhost:9997/v3/paths/list', timeout=2)
            rtt_ms = (time.time() - start_time) * 1000
        except:
            rtt_ms = 1000  # Default high RTT if unreachable
        
        # Get packet loss from WebRTC sessions
        packet_loss_rate = 0.0
        try:
            webrtc_response = requests.get('http://localhost:9997/v3/webrtc/sessions/list', timeout=2)
            if webrtc_response.status_code == 200:
                sessions = webrtc_response.json()
                total_packets = 0
                lost_packets = 0
                
                for session in sessions.get('items', []):
                    # Estimate packet loss (simplified)
                    bytes_sent = session.get('bytesSent', 0)
                    packets_sent = bytes_sent // 1024  # Rough estimate
                    packets_lost = max(0, packets_sent * 0.01)  # Estimate 1% loss
                    
                    total_packets += packets_sent
                    lost_packets += packets_lost
                
                if total_packets > 0:
                    packet_loss_rate = (lost_packets / total_packets) * 100
        except:
            pass
        
        # Update network conditions
        bandwidth_manager['network_conditions'] = {
            'packet_loss_rate': packet_loss_rate,
            'rtt_ms': rtt_ms,
            'bandwidth_kbps': bandwidth_manager['network_conditions']['bandwidth_kbps']  # Keep previous value
        }
        
        return True
        
    except Exception as e:
        print(f"[Bandwidth Manager] Error measuring network conditions: {e}")
        return False

def adapt_stream_quality():
    """Adapt stream quality based on network conditions"""
    global bandwidth_manager, current_resolution, current_framerate
    
    try:
        import time
        
        current_time = time.time()
        
        # Check cooldown period
        if current_time - bandwidth_manager['last_adaptation_time'] < bandwidth_manager['adaptation_cooldown']:
            return False
        
        # Measure current network conditions
        if not measure_network_conditions():
            return False
        
        conditions = bandwidth_manager['network_conditions']
        packet_loss = conditions['packet_loss_rate']
        rtt = conditions['rtt_ms']
        
        print(f"[Bandwidth Manager] Network conditions: PL={packet_loss:.1f}%, RTT={rtt:.0f}ms")
        
        # Determine if adaptation is needed
        adaptation_needed = False
        new_resolution = bandwidth_manager['current_resolution']
        new_fps = bandwidth_manager['current_fps']
        new_bitrate = bandwidth_manager['current_bitrate']
        
        # Packet loss adaptation
        if packet_loss > 10.0:  # High packet loss
            if bandwidth_manager['current_bitrate'] > 16:
                new_bitrate = 16
                adaptation_needed = True
                print(f"[Bandwidth Manager] High packet loss ({packet_loss:.1f}%), reducing bitrate to {new_bitrate}kbps")
        
        elif packet_loss < 2.0:  # Low packet loss
            if bandwidth_manager['current_bitrate'] < 32:
                new_bitrate = 32
                adaptation_needed = True
                print(f"[Bandwidth Manager] Low packet loss ({packet_loss:.1f}%), increasing bitrate to {new_bitrate}kbps")
        
        # RTT adaptation
        if rtt > 500:  # High latency
            if bandwidth_manager['current_fps'] > 5:
                new_fps = max(5, bandwidth_manager['current_fps'] - 2)
                adaptation_needed = True
                print(f"[Bandwidth Manager] High RTT ({rtt:.0f}ms), reducing FPS to {new_fps}")
        
        elif rtt < 100:  # Low latency
            if bandwidth_manager['current_fps'] < 25:
                new_fps = min(25, bandwidth_manager['current_fps'] + 2)
                adaptation_needed = True
                print(f"[Bandwidth Manager] Low RTT ({rtt:.0f}ms), increasing FPS to {new_fps}")
        
        # Resolution adaptation based on combined conditions
        if packet_loss > 15.0 or rtt > 800:  # Very poor conditions
            if bandwidth_manager['current_resolution'] != '320p':
                new_resolution = '320p'
                adaptation_needed = True
                print(f"[Bandwidth Manager] Poor conditions, downgrading to {new_resolution}")
        
        elif packet_loss < 5.0 and rtt < 200:  # Good conditions
            if bandwidth_manager['current_resolution'] == '320p':
                new_resolution = '480p'
                adaptation_needed = True
                print(f"[Bandwidth Manager] Good conditions, upgrading to {new_resolution}")
        
        # Apply adaptations if needed
        if adaptation_needed:
            bandwidth_manager['last_adaptation_time'] = current_time
            
            # Update global settings
            if new_resolution != bandwidth_manager['current_resolution']:
                set_resolution(new_resolution)
                bandwidth_manager['current_resolution'] = new_resolution
            
            if new_fps != bandwidth_manager['current_fps']:
                set_framerate(new_fps)
                bandwidth_manager['current_fps'] = new_fps
            
            if new_bitrate != bandwidth_manager['current_bitrate']:
                bandwidth_manager['current_bitrate'] = new_bitrate
                # Bitrate will be applied on next stream restart
            
            # Record adaptation
            adaptation_record = {
                'timestamp': current_time,
                'packet_loss': packet_loss,
                'rtt': rtt,
                'resolution': new_resolution,
                'fps': new_fps,
                'bitrate': new_bitrate
            }
            bandwidth_manager['adaptation_history'].append(adaptation_record)
            
            # Keep only last 20 adaptations
            if len(bandwidth_manager['adaptation_history']) > 20:
                bandwidth_manager['adaptation_history'].pop(0)
            
            print(f"[Bandwidth Manager] ✓ Adaptation applied: {new_resolution}@{new_fps}fps, {new_bitrate}kbps")
            return True
        
        return False
        
    except Exception as e:
        print(f"[Bandwidth Manager] Error in adaptation: {e}")
        return False

# Audio quality monitoring variables
audio_quality_monitor = {
    'current_bitrate': 32,  # Current audio bitrate in kbps
    'packet_loss_history': [],  # Last 10 packet loss measurements
    'last_adjustment_time': 0,  # Prevent too frequent adjustments
    'quality_check_interval': 5  # Check every 5 seconds
}

def calculate_packet_loss():
    """Calculate packet loss rate from MediaMTX statistics"""
    try:
        import requests
        
        # Get MediaMTX statistics
        response = requests.get('http://localhost:9997/v3/paths/list', timeout=2)
        if response.status_code == 200:
            paths_data = response.json()
            
            for path in paths_data.get('items', []):
                if path.get('name') == 'stream':
                    # Get WebRTC session statistics
                    webrtc_response = requests.get('http://localhost:9997/v3/webrtc/sessions/list', timeout=2)
                    if webrtc_response.status_code == 200:
                        sessions = webrtc_response.json()
                        
                        total_packets_sent = 0
                        total_packets_lost = 0
                        
                        for session in sessions.get('items', []):
                            # Extract packet statistics (simplified calculation)
                            # In a real implementation, you'd parse detailed WebRTC stats
                            packets_sent = session.get('bytesSent', 0) // 1024  # Rough estimate
                            packets_lost = max(0, packets_sent * 0.01)  # Estimate 1% loss
                            
                            total_packets_sent += packets_sent
                            total_packets_lost += packets_lost
                        
                        if total_packets_sent > 0:
                            packet_loss_rate = (total_packets_lost / total_packets_sent) * 100
                            return min(packet_loss_rate, 20)  # Cap at 20%
        
        return 0  # No data available
        
    except Exception as e:
        print(f"[Audio Quality] Error calculating packet loss: {e}")
        return 0

def adjust_audio_quality():
    """Adjust audio bitrate based on packet loss"""
    global audio_quality_monitor, bandwidth_manager
    
    try:
        import time
        
        current_time = time.time()
        
        # Check if enough time has passed since last adjustment
        if current_time - audio_quality_monitor['last_adjustment_time'] < audio_quality_monitor['quality_check_interval']:
            return bandwidth_manager['current_bitrate']
        
        # Use bandwidth manager's bitrate if available
        if bandwidth_manager['current_bitrate'] != audio_quality_monitor['current_bitrate']:
            audio_quality_monitor['current_bitrate'] = bandwidth_manager['current_bitrate']
            audio_quality_monitor['last_adjustment_time'] = current_time
            print(f"[Audio Quality] Using bandwidth manager bitrate: {bandwidth_manager['current_bitrate']}kbps")
            return bandwidth_manager['current_bitrate']
        
        # Calculate current packet loss
        packet_loss = calculate_packet_loss()
        
        # Add to history
        audio_quality_monitor['packet_loss_history'].append(packet_loss)
        if len(audio_quality_monitor['packet_loss_history']) > 10:
            audio_quality_monitor['packet_loss_history'].pop(0)
        
        # Calculate average packet loss
        avg_packet_loss = sum(audio_quality_monitor['packet_loss_history']) / len(audio_quality_monitor['packet_loss_history'])
        
        current_bitrate = audio_quality_monitor['current_bitrate']
        new_bitrate = current_bitrate
        
        # Adjust bitrate based on packet loss
        if avg_packet_loss > 5.0:  # High packet loss
            if current_bitrate > 16:
                new_bitrate = 16  # Reduce to minimum
                print(f"[Audio Quality] High packet loss ({avg_packet_loss:.1f}%), reducing bitrate to {new_bitrate}kbps")
        elif avg_packet_loss < 2.0:  # Low packet loss
            if current_bitrate < 32:
                new_bitrate = 32  # Increase to normal
                print(f"[Audio Quality] Low packet loss ({avg_packet_loss:.1f}%), increasing bitrate to {new_bitrate}kbps")
        
        # Update bitrate if changed
        if new_bitrate != current_bitrate:
            audio_quality_monitor['current_bitrate'] = new_bitrate
            bandwidth_manager['current_bitrate'] = new_bitrate  # Sync with bandwidth manager
            audio_quality_monitor['last_adjustment_time'] = current_time
            
            # Restart stream with new bitrate
            print(f"[Audio Quality] Restarting stream with {new_bitrate}kbps audio")
            return new_bitrate
        
        return current_bitrate
        
    except Exception as e:
        print(f"[Audio Quality] Error adjusting audio quality: {e}")
        return audio_quality_monitor['current_bitrate']

def check_hardware_encoding():
    """Check if hardware H264 encoding is available on RPi"""
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True, timeout=5)
        if 'h264_v4l2m2m' in result.stdout:
            print("[CPU Optimization] Hardware H264 encoding (h264_v4l2m2m) available")
            return True
        else:
            print("[CPU Optimization] Hardware H264 encoding not available, using software")
            return False
    except Exception as e:
        print(f"[CPU Optimization] Error checking hardware encoding: {e}")
        return False

def get_cpu_usage():
    """Get current CPU usage percentage"""
    try:
        with open('/proc/loadavg', 'r') as f:
            load_avg = float(f.read().split()[0])
        # Convert load average to percentage (assuming 4 cores)
        cpu_percent = min(100, (load_avg / 4) * 100)
        return cpu_percent
    except Exception as e:
        print(f"[CPU Optimization] Error getting CPU usage: {e}")
        return 0

def check_cpu_throttling():
    """Check if CPU is throttling due to thermal issues"""
    try:
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
            current_freq = int(f.read().strip())
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq', 'r') as f:
            max_freq = int(f.read().strip())
        
        # If current frequency is significantly below max, CPU is throttling
        if current_freq < max_freq * 0.8:
            print(f"[CPU Optimization] CPU throttling detected: {current_freq/1000:.0f}MHz < {max_freq/1000:.0f}MHz")
            return True
        return False
    except Exception as e:
        print(f"[CPU Optimization] Error checking CPU throttling: {e}")
        return False

def auto_reduce_quality():
    """Automatically reduce stream quality based on CPU usage and throttling"""
    global current_resolution, current_framerate
    
    cpu_usage = get_cpu_usage()
    is_throttling = check_cpu_throttling()
    
    if cpu_usage > 85 or is_throttling:
        # Reduce to lowest quality
        if current_resolution != "320p":
            print(f"[CPU Optimization] Auto-reducing resolution to 320p (CPU: {cpu_usage:.1f}%, Throttling: {is_throttling})")
            set_resolution("320p")
        if current_framerate > 10:
            print(f"[CPU Optimization] Auto-reducing FPS to 10 (CPU: {cpu_usage:.1f}%, Throttling: {is_throttling})")
            set_framerate(10)
    elif cpu_usage > 70:
        # Reduce to medium quality
        if current_resolution == "720p":
            print(f"[CPU Optimization] Auto-reducing resolution to 480p (CPU: {cpu_usage:.1f}%)")
            set_resolution("480p")
        if current_framerate > 15:
            print(f"[CPU Optimization] Auto-reducing FPS to 15 (CPU: {cpu_usage:.1f}%)")
            set_framerate(15)

def get_ffmpeg_command():
    """Generate optimized FFmpeg command for MediaMTX streaming with better codecs"""
    global current_resolution, current_framerate
    
    width, height = camera_settings[current_resolution]["width"], camera_settings[current_resolution]["height"]
    
    # Get the detected camera device
    camera_device = get_camera_device()
    if not camera_device or camera_device == "unknown":
        camera_device = "/dev/video0"  # Fallback
    
    # Dynamic bitrate calculation based on resolution
    # Lower resolutions = lower bitrate for bandwidth efficiency
    bitrate_map = {
        "320p": "120k",   # 640x360 - very low bandwidth
        "480p": "180k",   # 854x480 - low bandwidth  
        "720p": "300k"    # 1280x720 - medium bandwidth
    }
    video_bitrate = bitrate_map.get(current_resolution, "180k")
    
    # Check CPU usage and adjust settings accordingly
    cpu_usage = get_cpu_usage()
    if cpu_usage > 80:
        print(f"[CPU Optimization] High CPU usage ({cpu_usage:.1f}%), using conservative settings")
        preset = 'ultrafast'  # Fastest encoding
        crf = '32'  # Lower quality for speed
    elif cpu_usage > 60:
        print(f"[CPU Optimization] Moderate CPU usage ({cpu_usage:.1f}%), using balanced settings")
        preset = 'fast'
        crf = '30'
    else:
        preset = 'fast'
        crf = '28'
    
    # Use software encoding for reliability (hardware encoder has issues)
    use_hardware = False  # Disabled due to hardware encoder issues
    video_codec = 'libx264'
    
    # Software encoder supports all parameters
    video_params = ['-c:v', video_codec, '-preset', preset, '-tune', 'zerolatency', 
                   '-profile:v', 'main', '-level', '3.1', '-crf', crf]
    
    cmd = [
        'ffmpeg',
        '-f', 'v4l2',
        '-i', camera_device,
        '-f', 'alsa',
        '-i', 'default',  # Use default audio device to avoid conflict
        
        # Video encoding with optimized settings
        '-vf', f'fps={current_framerate},scale={width}:{height}:flags=lanczos,format=yuv420p',
    ] + video_params + [
        '-g', '30',  # Larger GOP for better compression
        '-keyint_min', '15',
        '-sc_threshold', '40',
        '-b:v', video_bitrate,
        '-maxrate', video_bitrate,
        '-bufsize', f'{int(video_bitrate[:-1]) * 1.5}k',  # Reduced from 2x to 1.5x for lower latency
        
        # Audio encoding - Simple Opus configuration
        '-c:a', 'libopus',
        '-b:a', '32k',
        
        # Network optimization for low latency
        '-fflags', '+nobuffer',
        '-flags', '+low_delay',
        '-strict', 'experimental',
        '-rtsp_transport', 'tcp',  # TCP for better reliability
        '-muxdelay', '0',  # No muxing delay
        '-muxpreload', '0',  # No preload delay
        '-f', 'rtsp',
        'rtsp://localhost:8554/stream'
    ]
    return cmd


def start_streaming():
    """Start MediaMTX streaming with robust error handling and state management"""
    global streaming_process, streaming_active
    
    # DISABLED: External FFmpeg management is handled by monitor_stream.sh
    # This prevents conflicts between Avatar app and external FFmpeg processes
    print("[MediaMTX Camera] FFmpeg management disabled - using external stream monitor")
    return {"ok": True, "msg": "Stream management handled externally"}
    
    # Check current state
    current_state = stream_state_manager.get_state()
    if current_state == StreamState.ACTIVE:
        return {"ok": False, "msg": "Streaming already active"}
    elif current_state == StreamState.STARTING:
        return {"ok": False, "msg": "Stream is currently starting"}
    
    # Set state to starting
    if not stream_state_manager.set_state(StreamState.STARTING):
        return {"ok": False, "msg": "Invalid state transition"}
    
    with streaming_lock:
        # Check if streaming is actually active by verifying the process
        if streaming_active and streaming_process:
            # Check if the process is still running
            if streaming_process.poll() is None:
                stream_state_manager.set_state(StreamState.ACTIVE, process_id=streaming_process.pid)
                return {"ok": False, "msg": "Streaming already active"}
            else:
                # Process died, reset the flag
                print("[MediaMTX Camera] Previous streaming process died, resetting status")
                streaming_active = False
                streaming_process = None
                stream_state_manager.set_state(StreamState.STOPPED)
        
        try:
            print("[MediaMTX Camera] Starting MediaMTX stream...")
            
            # Get camera device and lock it
            camera_device = get_camera_device()
            if not camera_device or camera_device == "unknown":
                camera_device = "/dev/video0"  # Fallback
            
            # Lock the camera device to prevent conflicts
            if not check_device_available(camera_device):
                print(f"[MediaMTX Camera] Device {camera_device} in use, attempting to lock...")
                if not lock_device(camera_device):
                    # Try error recovery for camera busy
                    if error_recovery_manager.attempt_recovery("camera_busy"):
                        # Retry after recovery
                        if not check_device_available(camera_device):
                            return {"ok": False, "msg": f"Could not lock camera device {camera_device} after recovery"}
                    else:
                        return {"ok": False, "msg": f"Could not lock camera device {camera_device}"}
            
            # DISABLED: External FFmpeg management is handled by monitor_stream.sh
            # This prevents conflicts between Avatar app and external FFmpeg processes
            print("[MediaMTX Camera] FFmpeg cleanup disabled - using external stream monitor")
            # subprocess.run(['pkill', '-f', 'ffmpeg.*rtsp://localhost:8554/stream'], capture_output=True)
            # time.sleep(2)
            
            # Simplified FFmpeg command for reliability
            cmd = get_ffmpeg_command()
            # Remove complex audio filters that might cause issues
            cmd = [c for c in cmd if not c.startswith('compand=')]
            print(f"[MediaMTX Camera] FFmpeg command: {' '.join(cmd)}")
            
            # Start streaming process with robust configuration
            streaming_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # Wait a moment to see if FFmpeg starts successfully
            time.sleep(1)
            if streaming_process.poll() is not None:
                stderr_output = streaming_process.stderr.read().decode('utf-8') if streaming_process.stderr else "No error output"
                print(f"[MediaMTX Camera] FFmpeg failed to start: {stderr_output}")
                stream_state_manager.set_state(StreamState.ERROR, error_message=f"FFmpeg failed to start: {stderr_output}")
                return {"ok": False, "msg": f"FFmpeg failed to start: {stderr_output}"}
            
            streaming_active = True
            print(f"[MediaMTX Camera] FFmpeg started with PID: {streaming_process.pid}")
            
            # Set state to active
            stream_state_manager.set_state(StreamState.ACTIVE, process_id=streaming_process.pid)
            
            # Reset reconnection state on successful start
            reset_reconnection_state()
            
            # Start monitoring thread after a brief delay to ensure process is stable
            def delayed_monitor():
                time.sleep(2)  # Wait 2 seconds for process to stabilize
                _monitor_streaming()
            
            threading.Thread(target=delayed_monitor, daemon=True).start()
            
            # Start frame watchdog for monitoring
            frame_watchdog.start_watchdog()
            
            # Reset recovery attempts on successful start
            error_recovery_manager.reset_recovery_attempts()
            
            return {"ok": True, "msg": f"Streaming started with PID {streaming_process.pid}"}
            
        except Exception as e:
            streaming_active = False
            print(f"[MediaMTX Camera] Failed to start streaming: {e}")
            
            # Set state to error
            stream_state_manager.set_state(StreamState.ERROR, error_message=str(e))
            
            # Handle stream failure for reconnection
            handle_stream_failure()
            
            return {"ok": False, "msg": f"Streaming failed: {str(e)}"}


def stop_streaming():
    """Stop MediaMTX streaming with state management"""
    global streaming_process, streaming_active
    
    # DISABLED: External FFmpeg management is handled by monitor_stream.sh
    # This prevents conflicts between Avatar app and external FFmpeg processes
    print("[MediaMTX Camera] FFmpeg management disabled - using external stream monitor")
    return {"ok": True, "msg": "Stream management handled externally"}
    
    # Check current state
    current_state = stream_state_manager.get_state()
    if current_state == StreamState.STOPPED:
        return {"ok": False, "msg": "Streaming not active"}
    elif current_state == StreamState.STOPPING:
        return {"ok": False, "msg": "Stream is currently stopping"}
    
    # Set state to stopping
    if not stream_state_manager.set_state(StreamState.STOPPING):
        return {"ok": False, "msg": "Invalid state transition"}
    
    with streaming_lock:
        if not streaming_active:
            stream_state_manager.set_state(StreamState.STOPPED)
            return {"ok": False, "msg": "Streaming not active"}
        
        try:
            print("[MediaMTX Camera] Stopping MediaMTX stream...")
            
            if streaming_process:
                # Send quit signal to ffmpeg
                if streaming_process.stdin:
                    streaming_process.stdin.write(b'q')
                    streaming_process.stdin.flush()
                
                # Wait for process to finish
                timeout = 5
                start_time = time.time()
                
                while streaming_process.poll() is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                # Force terminate if still running
                if streaming_process.poll() is None:
                    print("[MediaMTX Camera] Force terminating streaming process")
                    streaming_process.terminate()
                    try:
                        streaming_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        streaming_process.kill()
            
            streaming_active = False
            streaming_process = None
            
            # Stop frame watchdog
            frame_watchdog.stop_watchdog()
            
            # Set state to stopped
            stream_state_manager.set_state(StreamState.STOPPED)
            
            return {"ok": True, "msg": "Streaming stopped"}
            
        except Exception as e:
            print(f"[MediaMTX Camera] Error stopping streaming: {e}")
            streaming_active = False
            
            # Set state to error
            stream_state_manager.set_state(StreamState.ERROR, error_message=str(e))
            
            return {"ok": False, "msg": f"Stop failed: {str(e)}"}


def _monitor_streaming():
    """Monitor streaming process in background thread"""
    global streaming_process, streaming_active
    
    if not streaming_process:
        return
        
    try:
        # Monitor process without blocking
        while streaming_process and streaming_process.poll() is None:
            time.sleep(1)
        
        if streaming_process and streaming_process.returncode != 0:
            print(f"[MediaMTX Camera] Streaming process exited with code: {streaming_process.returncode}")
        else:
            print("[MediaMTX Camera] Streaming process completed normally")
            
    except Exception as e:
        print(f"[MediaMTX Camera] Streaming monitoring error: {e}")
    finally:
        with streaming_lock:
            streaming_active = False
            streaming_process = None
            # Update state manager when process ends
            stream_state_manager.set_state(StreamState.STOPPED)


def get_streaming_status():
    """Get streaming status with process health check and state management"""
    global streaming_process, streaming_active
    
    # Get current state from state manager
    current_state = stream_state_manager.get_state()
    state_info = stream_state_manager.get_state_info()
    
    with streaming_lock:
        # Check if process is actually running
        process_running = False
        if streaming_process:
            if streaming_process.poll() is None:
                process_running = True
            else:
                # Process died, reset the flag and state
                print("[MediaMTX Camera] Streaming process died, resetting status")
                streaming_active = False
                streaming_process = None
                stream_state_manager.set_state(StreamState.STOPPED)
        
        return {
            "active": streaming_active and process_running,
            "process_running": process_running,
            "pid": streaming_process.pid if streaming_process else None,
            "state": current_state.value,
            "state_info": {
                "timestamp": state_info.timestamp,
                "error_message": state_info.error_message,
                "retry_count": state_info.retry_count
            }
        }


# ============== Module-level lazy initialization ==============

print("[MediaMTX Camera] Camera manager ready for lazy initialization")
camera_manager = None

def get_camera_manager():
    """Get camera manager instance with lazy initialization"""
    global camera_manager
    if camera_manager is None:
        print("[MediaMTX Camera] Lazy initializing camera manager...")
        try:
            camera_manager = MediaMTXCameraManager()
        except Exception as e:
            print(f"[MediaMTX Camera] Failed to initialize camera manager: {e}")
            return None
    return camera_manager

# Export compatibility functions
def init_camera():
    """Compatibility function for old interface"""
    try:
        return get_camera_manager().init_camera()
    except Exception as e:
        print(f"[MediaMTX Camera] Init failed: {e}")
        return False

def get_camera_status():
    """Get camera status"""
    try:
        return get_camera_manager().get_status()
    except Exception as e:
        return {"ok": False, "msg": f"Camera status failed: {e}"}

def set_camera_resolution(resolution):
    """Set camera resolution"""
    try:
        return get_camera_manager().set_resolution(resolution)
    except Exception as e:
        print(f"[MediaMTX Camera] Resolution change failed: {e}")
        return False

def set_camera_framerate(framerate):
    """Set camera framerate"""
    try:
        return get_camera_manager().set_framerate(framerate)
    except Exception as e:
        print(f"[MediaMTX Camera] Framerate change failed: {e}")
        return False

def take_snapshot(filename=None):
    """Take a snapshot"""
    try:
        return get_camera_manager().take_snapshot(filename)
    except Exception as e:
        return {"ok": False, "msg": f"Snapshot failed: {e}"}

def get_shared_frame_data():
    """Get shared frame data"""
    try:
        return get_camera_manager().get_shared_frame_data()
    except Exception as e:
        print(f"[MediaMTX Camera] Shared frame data error: {e}")
        return None, (854, 480)

def get_camera():
    try:
        return get_camera_manager().camera
    except:
        return None

def get_camera_device():
    try:
        return get_camera_manager().camera_device
    except:
        return "unknown"

print("[MediaMTX Camera] Module loaded successfully (lazy initialization)")
