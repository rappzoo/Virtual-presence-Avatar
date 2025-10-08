#!/usr/bin/env python3
"""
MediaMTX-compatible recording module for Avatar Tank system.
Handles video and audio recording with MediaMTX integration.
"""

import subprocess
import threading
import os
import datetime
import time
import sys
from subprocess import PIPE
from pathlib import Path
from typing import Optional, Dict, Any


# Try to get required imports - handle gracefully
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from modules.device_detector import device_detector, MIC_PLUG
    from modules.mediamtx_camera import camera_settings, current_resolution, current_framerate
    from modules.mediamtx_audio import current_audio_bitrate, current_audio_sample_rate, current_audio_channels, set_audio_device_busy, is_audio_device_busy
    print(f"[MediaMTX Recorder] Using detected microphone: {MIC_PLUG}")
except ImportError as e:
    print(f"[MediaMTX Recorder] Warning: Could not import modules ({e}), using fallbacks")
    MIC_PLUG = 'plughw:3,0'
    camera_settings = {
        "320p": {"width": 640, "height": 360, "fps": 10},
        "480p": {"width": 854, "height": 480, "fps": 10},
        "720p": {"width": 1280, "height": 720, "fps": 10}
    }
    current_resolution = "480p"
    current_framerate = 10
    current_audio_bitrate = "48k"
    current_audio_sample_rate = 24000
    current_audio_channels = 1
    
    def set_audio_device_busy(busy):
        pass
    
    def is_audio_device_busy():
        return False


# Ensure directories exist
Path("snapshots").mkdir(exist_ok=True)
Path("recordings").mkdir(exist_ok=True)
Path("sounds").mkdir(exist_ok=True)


class MediaMTXRecordingManager:
    """MediaMTX-compatible recording manager"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.writer_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
        self.last_file: Optional[str] = None
        self.recording_mode = 'full'  # 'full', 'video_only', 'failed'
        
        # Recording statistics
        self.recording_stats = {
            'start_time': None,
            'frames_written': 0,
            'bytes_written': 0,
            'errors': 0
        }
        
        print("[MediaMTX Recorder] Initialized")
    
    def _test_audio_setup(self):
        """Test audio device availability and compatibility"""
        print(f"[MediaMTX Recorder] Testing audio device: {MIC_PLUG}")
        
        try:
            # Quick test with arecord
            test_cmd = ["arecord", "-D", MIC_PLUG, "-f", "cd", "-d", "1", "-q"]
            result = subprocess.run(test_cmd, capture_output=True, timeout=3)
            
            if result.returncode == 0:
                print("[MediaMTX Recorder] Audio device test successful")
                return True
            else:
                print(f"[MediaMTX Recorder] Audio device test failed: {result.stderr.decode()[:100]}...")
                return False
                
        except subprocess.TimeoutExpired:
            print("[MediaMTX Recorder] Audio device test timed out")
            return False
        except Exception as e:
            print(f"[MediaMTX Recorder] Audio device test error: {e}")
            return False

    def _kill_conflicting_processes(self):
        """Kill any processes that might be using the camera or audio device"""
        try:
            # DISABLED: External FFmpeg management is handled by monitor_stream.sh
            # subprocess.run(['pkill', '-f', 'ffmpeg'], capture_output=True)
            
            # Kill any existing arecord processes
            subprocess.run(['pkill', '-f', 'arecord'], capture_output=True)
            
            # Wait a moment for processes to terminate
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[MediaMTX Recorder] Warning: Could not kill conflicting processes: {e}")

    def start(self, a_bitrate=None):
        """Start recording with MediaMTX-compatible settings"""
        with self.lock:
            if self.running:
                return {"ok": False, "msg": "Already recording"}
            
            # Check if audio device is busy
            if is_audio_device_busy():
                return {"ok": False, "msg": "Audio device is busy"}
            
            print("[MediaMTX Recorder] Starting recording...")
            
            # Kill any conflicting processes first
            self._kill_conflicting_processes()
            
            # Mark audio device as busy
            set_audio_device_busy(True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"recordings/recording_{timestamp}.mp4"
            self.last_file = output_file
            
            # Get current camera settings
            resolution = camera_settings.get(current_resolution, camera_settings["480p"])
            width, height = resolution["width"], resolution["height"]
            fps = current_framerate
            
            # Use provided bitrate or current setting
            audio_bitrate = a_bitrate or current_audio_bitrate
            
            # Build ffmpeg command with MediaMTX-compatible settings
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-f", "v4l2",
                "-framerate", str(fps),
                "-video_size", f"{width}x{height}",
                "-i", "/dev/video0",
            ]
            
            # Add audio if available and working
            audio_available = self._test_audio_setup()
            if audio_available:
                print("[MediaMTX Recorder] Adding audio to recording")
                cmd.extend([
                    "-f", "alsa",
                    "-ar", str(current_audio_sample_rate),
                    "-ac", str(current_audio_channels),
                    "-i", MIC_PLUG,
                    "-c:a", "libopus",  # Use Opus codec for MediaMTX compatibility
                    "-b:a", audio_bitrate,
                    "-ac", str(current_audio_channels)
                ])
                self.recording_mode = 'full'
            else:
                print("[MediaMTX Recorder] No audio available, recording video only")
                self.recording_mode = 'video_only'
            
            # Video encoding options with MediaMTX-compatible settings
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-g", "20",
                "-keyint_min", "10",
                "-sc_threshold", "0",
                "-b:v", "200k",
                "-maxrate", "200k",
                "-bufsize", "400k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-y", output_file
            ])
            
            print(f"[MediaMTX Recorder] Command: {' '.join(cmd)}")
            
            try:
                # Start recording process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
                
                self.running = True
                self.recording_stats['start_time'] = time.time()
                self.recording_stats['frames_written'] = 0
                self.recording_stats['bytes_written'] = 0
                
                # Start monitoring thread
                self.writer_thread = threading.Thread(
                    target=self._monitor_recording,
                    daemon=True
                )
                self.writer_thread.start()
                
                mode_text = "with audio" if audio_available else "video only"
                return {
                    "ok": True,
                    "msg": f"Started recording {mode_text}",
                    "file": output_file,
                    "audio": audio_available,
                    "mode": self.recording_mode
                }
                
            except Exception as e:
                self.running = False
                set_audio_device_busy(False)
                print(f"[MediaMTX Recorder] Failed to start recording: {e}")
                return {"ok": False, "msg": f"Recording failed: {str(e)}"}

    def _monitor_recording(self):
        """Monitor recording process in background thread"""
        if not self.process:
            return
            
        try:
            # Wait for process to complete
            stdout, stderr = self.process.communicate()
            
            if self.process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                print(f"[MediaMTX Recorder] Recording process error: {error_msg}")
                self.recording_stats['errors'] += 1
            else:
                # Try to get file size
                try:
                    if os.path.exists(self.last_file):
                        size = os.path.getsize(self.last_file)
                        self.recording_stats['bytes_written'] = size
                        print(f"[MediaMTX Recorder] Recording completed, file size: {size} bytes")
                except:
                    pass
                    
        except Exception as e:
            print(f"[MediaMTX Recorder] Monitoring error: {e}")
            self.recording_stats['errors'] += 1
        finally:
            with self.lock:
                self.running = False
                set_audio_device_busy(False)
                if self.process:
                    self.process = None

    def stop(self):
        """Stop recording with proper cleanup"""
        with self.lock:
            if not self.running or not self.process:
                return {"ok": False, "msg": "Not recording"}
            
            print("[MediaMTX Recorder] Stopping recording...")
            
            try:
                # Send quit signal to ffmpeg
                if self.process and self.process.stdin:
                    self.process.stdin.write(b'q')
                    self.process.stdin.flush()
                
                # Wait for process to finish (with timeout)
                timeout = 5
                start_time = time.time()
                
                while self.process.poll() is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                # If still running, terminate forcefully
                if self.process.poll() is None:
                    print("[MediaMTX Recorder] Force terminating recording process")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                
                self.running = False
                set_audio_device_busy(False)
                
                final_file = self.last_file
                self.last_file = None
                
                return {
                    "ok": True,
                    "msg": "Recording stopped",
                    "file": final_file,
                    "stats": self.recording_stats.copy()
                }
                
            except Exception as e:
                print(f"[MediaMTX Recorder] Error stopping recording: {e}")
                self.running = False
                set_audio_device_busy(False)
                return {"ok": False, "msg": f"Stop failed: {str(e)}"}

    def status(self):
        """Get current recording status"""
        return {
            "ok": True,
            "recording": self.running,
            "mode": self.recording_mode,
            "file": self.last_file if self.running else None,
            "stats": self.recording_stats.copy() if self.running else {},
            "audio_device_busy": is_audio_device_busy()
        }


# Create global recorder instance
rec = MediaMTXRecordingManager()


def get_recording_status():
    """Get recording status (for API)"""
    return rec.status()

def start_recording(bitrate=None):
    """Start recording"""
    return rec.start(bitrate)

def stop_recording():
    """Stop recording"""
    return rec.stop()

def is_recording():
    """Check if currently recording"""
    return rec.running

print("[MediaMTX Recorder] Module loaded successfully")


