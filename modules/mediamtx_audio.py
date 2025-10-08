#!/usr/bin/env python3
"""
MediaMTX-compatible audio module for Avatar Tank system.
Handles audio device management and MediaMTX streaming integration.
"""

import subprocess
import threading
import time
import os
import sys
import json
from typing import Optional, Dict, Any


# Try to get device detector - handle import gracefully
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from modules.device_detector import device_detector, MIC_PLUG, SPK_PLUG
    print(f"[MediaMTX Audio] Using detected microphone: {MIC_PLUG}")
    print(f"[MediaMTX Audio] Using detected speaker: {SPK_PLUG}")
except ImportError as e:
    print(f"[MediaMTX Audio] Warning: Could not import device detector ({e}), using fallbacks")
    MIC_PLUG = 'plughw:3,0'
    SPK_PLUG = 'default'


# ============== AUDIO SETTINGS ==============
current_audio_bitrate = "48k"
current_audio_sample_rate = 24000
current_audio_channels = 1

# Audio device management
audio_device_busy = False
audio_device_lock = threading.Lock()


class MediaMTXAudioManager:
    """MediaMTX-compatible audio manager"""
    
    def __init__(self):
        self.mic_device = MIC_PLUG
        self.spk_device = SPK_PLUG
        self.lock = threading.Lock()
        self._initialized = False
        
    def _ensure_initialized(self):
        """Ensure audio is initialized before use"""
        if not self._initialized:
            print("[MediaMTX Audio] Performing delayed initialization...")
            self.init_audio()
            self._initialized = True
    
    def init_audio(self):
        """Initialize audio devices"""
        try:
            print(f"[MediaMTX Audio] Initializing audio devices...")
            print(f"[MediaMTX Audio] Microphone: {self.mic_device}")
            print(f"[MediaMTX Audio] Speaker: {self.spk_device}")
            
            # Test microphone device
            if self._test_microphone_device():
                print("[MediaMTX Audio] ✓ Microphone device working")
            else:
                print("[MediaMTX Audio] ✗ Microphone device test failed")
            
            # Test speaker device
            if self._test_speaker_device():
                print("[MediaMTX Audio] ✓ Speaker device working")
            else:
                print("[MediaMTX Audio] ✗ Speaker device test failed")
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"[MediaMTX Audio] Initialization error: {e}")
            return False
    
    def _test_microphone_device(self):
        """Test if the microphone device is accessible"""
        try:
            # Quick test with arecord
            test_cmd = ["arecord", "-D", self.mic_device, "-f", "cd", "-d", "1", "-q", "/dev/null"]
            result = subprocess.run(test_cmd, capture_output=True, timeout=3)
            return result.returncode == 0
        except Exception as e:
            print(f"[MediaMTX Audio] Microphone test failed: {e}")
            return False
    
    def _test_speaker_device(self):
        """Test if the speaker device is accessible"""
        try:
            # Quick test with aplay
            test_cmd = ["aplay", "-D", self.spk_device, "-f", "cd", "-d", "1", "-q", "/dev/null"]
            result = subprocess.run(test_cmd, capture_output=True, timeout=3)
            return result.returncode == 0
        except Exception as e:
            print(f"[MediaMTX Audio] Speaker test failed: {e}")
            return False
    
    def set_audio_bitrate(self, bitrate):
        """Set audio bitrate"""
        global current_audio_bitrate
        print(f"[MediaMTX Audio] Changing audio bitrate from {current_audio_bitrate} to {bitrate}")
        current_audio_bitrate = bitrate
        return True
    
    def set_audio_sample_rate(self, sample_rate):
        """Set audio sample rate"""
        global current_audio_sample_rate
        print(f"[MediaMTX Audio] Changing audio sample rate from {current_audio_sample_rate} to {sample_rate}")
        current_audio_sample_rate = sample_rate
        return True
    
    def set_audio_channels(self, channels):
        """Set audio channels"""
        global current_audio_channels
        print(f"[MediaMTX Audio] Changing audio channels from {current_audio_channels} to {channels}")
        current_audio_channels = channels
        return True
    
    def get_status(self):
        """Get audio status information"""
        try:
            self._ensure_initialized()
            return {
                "ok": True,
                "mic_device": self.mic_device,
                "spk_device": self.spk_device,
                "bitrate": current_audio_bitrate,
                "sample_rate": current_audio_sample_rate,
                "channels": current_audio_channels,
                "initialized": self._initialized,
                "device_busy": audio_device_busy
            }
        except Exception as e:
            return {
                "ok": False,
                "msg": f"Audio status error: {e}",
                "mic_device": self.mic_device,
                "spk_device": self.spk_device,
                "bitrate": current_audio_bitrate,
                "sample_rate": current_audio_sample_rate,
                "channels": current_audio_channels,
                "initialized": False,
                "device_busy": False
            }
    
    def test_audio_playback(self, duration=2):
        """Test audio playback with a test tone"""
        try:
            print(f"[MediaMTX Audio] Testing audio playback for {duration} seconds...")
            
            # Generate test tone with sox
            test_cmd = [
                "sox", "-n", "-t", "wav", "-",
                "synth", str(duration), "sine", "440",
                "rate", "44100"
            ]
            
            # Play test tone
            play_cmd = [
                "aplay", "-D", self.spk_device, "-f", "cd", "-q"
            ]
            
            # Pipe sox output to aplay
            sox_process = subprocess.Popen(test_cmd, stdout=subprocess.PIPE)
            aplay_process = subprocess.Popen(play_cmd, stdin=sox_process.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            sox_process.stdout.close()
            aplay_process.wait()
            sox_process.wait()
            
            if aplay_process.returncode == 0:
                print("[MediaMTX Audio] ✓ Audio playback test successful")
                return {"ok": True, "msg": "Audio playback test successful"}
            else:
                print("[MediaMTX Audio] ✗ Audio playback test failed")
                return {"ok": False, "msg": "Audio playback test failed"}
                
        except Exception as e:
            print(f"[MediaMTX Audio] Audio playback test error: {e}")
            return {"ok": False, "msg": f"Audio playback test error: {e}"}
    
    def test_audio_recording(self, duration=2):
        """Test audio recording"""
        try:
            print(f"[MediaMTX Audio] Testing audio recording for {duration} seconds...")
            
            # Record audio
            test_file = "/tmp/audio_test.wav"
            record_cmd = [
                "arecord", "-D", self.mic_device, "-f", "cd", "-d", str(duration), "-q", test_file
            ]
            
            result = subprocess.run(record_cmd, capture_output=True, timeout=duration + 2)
            
            if result.returncode == 0 and os.path.exists(test_file):
                # Check file size
                file_size = os.path.getsize(test_file)
                os.remove(test_file)  # Clean up
                
                if file_size > 0:
                    print("[MediaMTX Audio] ✓ Audio recording test successful")
                    return {"ok": True, "msg": "Audio recording test successful"}
                else:
                    print("[MediaMTX Audio] ✗ Audio recording test failed - empty file")
                    return {"ok": False, "msg": "Audio recording test failed - empty file"}
            else:
                print("[MediaMTX Audio] ✗ Audio recording test failed")
                return {"ok": False, "msg": "Audio recording test failed"}
                
        except Exception as e:
            print(f"[MediaMTX Audio] Audio recording test error: {e}")
            return {"ok": False, "msg": f"Audio recording test error: {e}"}


# ============== Audio Device Management ==============

def set_audio_device_busy(busy):
    """Set audio device busy state"""
    global audio_device_busy
    with audio_device_lock:
        audio_device_busy = busy
        print(f"[MediaMTX Audio] Audio device busy state: {busy}")

def is_audio_device_busy():
    """Check if audio device is busy"""
    with audio_device_lock:
        return audio_device_busy

def get_audio_device_info():
    """Get audio device information"""
    try:
        # Get ALSA device list
        result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            devices = []
            for line in result.stdout.split('\n'):
                if 'card' in line and 'device' in line:
                    devices.append(line.strip())
            return {"ok": True, "devices": devices}
        else:
            return {"ok": False, "msg": "Failed to get audio devices"}
    except Exception as e:
        return {"ok": False, "msg": f"Audio device info error: {e}"}


# ============== Module-level lazy initialization ==============

print("[MediaMTX Audio] Audio manager ready for lazy initialization")
audio_manager = None

def get_audio_manager():
    """Get audio manager instance with lazy initialization"""
    global audio_manager
    if audio_manager is None:
        print("[MediaMTX Audio] Lazy initializing audio manager...")
        try:
            audio_manager = MediaMTXAudioManager()
        except Exception as e:
            print(f"[MediaMTX Audio] Failed to initialize audio manager: {e}")
            return None
    return audio_manager

# Export compatibility functions
def init_audio():
    """Compatibility function for old interface"""
    try:
        return get_audio_manager().init_audio()
    except Exception as e:
        print(f"[MediaMTX Audio] Init failed: {e}")
        return False

def get_audio_status():
    """Get audio status"""
    try:
        return get_audio_manager().get_status()
    except Exception as e:
        return {"ok": False, "msg": f"Audio status failed: {e}"}

def set_audio_bitrate(bitrate):
    """Set audio bitrate"""
    try:
        return get_audio_manager().set_audio_bitrate(bitrate)
    except Exception as e:
        print(f"[MediaMTX Audio] Bitrate change failed: {e}")
        return False

def set_audio_sample_rate(sample_rate):
    """Set audio sample rate"""
    try:
        return get_audio_manager().set_audio_sample_rate(sample_rate)
    except Exception as e:
        print(f"[MediaMTX Audio] Sample rate change failed: {e}")
        return False

def set_audio_channels(channels):
    """Set audio channels"""
    try:
        return get_audio_manager().set_audio_channels(channels)
    except Exception as e:
        print(f"[MediaMTX Audio] Channels change failed: {e}")
        return False

def test_audio_playback(duration=2):
    """Test audio playback"""
    try:
        return get_audio_manager().test_audio_playback(duration)
    except Exception as e:
        return {"ok": False, "msg": f"Audio playback test failed: {e}"}

def test_audio_recording(duration=2):
    """Test audio recording"""
    try:
        return get_audio_manager().test_audio_recording(duration)
    except Exception as e:
        return {"ok": False, "msg": f"Audio recording test failed: {e}"}

def get_mic_device():
    """Get microphone device"""
    try:
        return get_audio_manager().mic_device
    except:
        return MIC_PLUG

def get_spk_device():
    """Get speaker device"""
    try:
        return get_audio_manager().spk_device
    except:
        return SPK_PLUG

print("[MediaMTX Audio] Module loaded successfully (lazy initialization)")







