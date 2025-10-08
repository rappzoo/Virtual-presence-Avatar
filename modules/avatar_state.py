#!/usr/bin/env python3
"""
Avatar Tank State Management Module
Handles persistent storage of system state including resolution, FPS, and other settings.
"""

import json
import os
import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class AvatarStateManager:
    """Manages persistent state for Avatar Tank system"""
    
    def __init__(self, state_file: str = "/home/havatar/Avatar-robot/config/avatar_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file or create default state"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    print(f"[Avatar State] Loaded state from {self.state_file}")
                    return state
            else:
                print(f"[Avatar State] State file not found, creating default state")
                return self._get_default_state()
        except Exception as e:
            print(f"[Avatar State] Error loading state: {e}, using defaults")
            return self._get_default_state()
    
    def _get_default_state(self) -> Dict[str, Any]:
        """Get default state configuration"""
        return {
            "last_resolution": "480p",
            "last_fps": 10,
            "last_updated": datetime.datetime.now().isoformat(),
            "camera_settings": {
                "320p": {"width": 640, "height": 360, "fps": 10},
                "480p": {"width": 854, "height": 480, "fps": 10},
                "720p": {"width": 1280, "height": 720, "fps": 10}
            },
            "stream_status": {
                "active": False,
                "last_started": None,
                "ffmpeg_pid": None
            },
            "system_info": {
                "version": "1.0",
                "last_restart": None,
                "total_snapshots": 0
            }
        }
    
    def _save_state(self) -> bool:
        """Save current state to file"""
        try:
            self._state["last_updated"] = datetime.datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=4)
            print(f"[Avatar State] State saved to {self.state_file}")
            return True
        except Exception as e:
            print(f"[Avatar State] Error saving state: {e}")
            return False
    
    def get_last_resolution(self) -> str:
        """Get the last used resolution"""
        return self._state.get("last_resolution", "480p")
    
    def set_last_resolution(self, resolution: str) -> bool:
        """Set the last used resolution"""
        if resolution in self._state.get("camera_settings", {}):
            self._state["last_resolution"] = resolution
            return self._save_state()
        return False
    
    def get_last_fps(self) -> int:
        """Get the last used FPS"""
        return self._state.get("last_fps", 10)
    
    def set_last_fps(self, fps: int) -> bool:
        """Set the last used FPS"""
        if 1 <= fps <= 30:  # Reasonable FPS range
            self._state["last_fps"] = fps
            return self._save_state()
        return False
    
    def get_camera_settings(self) -> Dict[str, Dict[str, Any]]:
        """Get camera settings for all resolutions"""
        return self._state.get("camera_settings", {})
    
    def get_resolution_settings(self, resolution: str) -> Optional[Dict[str, Any]]:
        """Get settings for a specific resolution"""
        return self._state.get("camera_settings", {}).get(resolution)
    
    def set_stream_status(self, active: bool, ffmpeg_pid: Optional[int] = None) -> bool:
        """Update stream status"""
        self._state["stream_status"]["active"] = active
        if active:
            self._state["stream_status"]["last_started"] = datetime.datetime.now().isoformat()
            self._state["stream_status"]["ffmpeg_pid"] = ffmpeg_pid
        else:
            self._state["stream_status"]["ffmpeg_pid"] = None
        return self._save_state()
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get current stream status"""
        return self._state.get("stream_status", {})
    
    def increment_snapshot_count(self) -> bool:
        """Increment total snapshot count"""
        self._state["system_info"]["total_snapshots"] = self._state["system_info"].get("total_snapshots", 0) + 1
        return self._save_state()
    
    def get_snapshot_count(self) -> int:
        """Get total snapshot count"""
        return self._state["system_info"].get("total_snapshots", 0)
    
    def set_system_restart(self) -> bool:
        """Mark system restart time"""
        self._state["system_info"]["last_restart"] = datetime.datetime.now().isoformat()
        return self._save_state()
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete state for debugging"""
        return self._state.copy()
    
    def reset_to_defaults(self) -> bool:
        """Reset state to defaults"""
        self._state = self._get_default_state()
        return self._save_state()

# Global state manager instance
_state_manager = None

def get_state_manager() -> AvatarStateManager:
    """Get the global state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = AvatarStateManager()
    return _state_manager

def get_last_resolution() -> str:
    """Get the last used resolution"""
    return get_state_manager().get_last_resolution()

def set_last_resolution(resolution: str) -> bool:
    """Set the last used resolution"""
    return get_state_manager().set_last_resolution(resolution)

def get_last_fps() -> int:
    """Get the last used FPS"""
    return get_state_manager().get_last_fps()

def set_last_fps(fps: int) -> bool:
    """Set the last used FPS"""
    return get_state_manager().set_last_fps(fps)

def get_camera_settings() -> Dict[str, Dict[str, Any]]:
    """Get camera settings for all resolutions"""
    return get_state_manager().get_camera_settings()

def get_resolution_settings(resolution: str) -> Optional[Dict[str, Any]]:
    """Get settings for a specific resolution"""
    return get_state_manager().get_resolution_settings(resolution)

def set_stream_status(active: bool, ffmpeg_pid: Optional[int] = None) -> bool:
    """Update stream status"""
    return get_state_manager().set_stream_status(active, ffmpeg_pid)

def get_stream_status() -> Dict[str, Any]:
    """Get current stream status"""
    return get_state_manager().get_stream_status()

def increment_snapshot_count() -> bool:
    """Increment total snapshot count"""
    return get_state_manager().increment_snapshot_count()

def get_snapshot_count() -> int:
    """Get total snapshot count"""
    return get_state_manager().get_snapshot_count()

def set_system_restart() -> bool:
    """Mark system restart time"""
    return get_state_manager().set_system_restart()

def get_full_state() -> Dict[str, Any]:
    """Get complete state for debugging"""
    return get_state_manager().get_full_state()

def reset_to_defaults() -> bool:
    """Reset state to defaults"""
    return get_state_manager().reset_to_defaults()

if __name__ == "__main__":
    # Test the state manager
    print("Testing Avatar State Manager...")
    
    # Test basic functionality
    print(f"Last resolution: {get_last_resolution()}")
    print(f"Last FPS: {get_last_fps()}")
    
    # Test setting values
    set_last_resolution("720p")
    set_last_fps(15)
    
    print(f"Updated resolution: {get_last_resolution()}")
    print(f"Updated FPS: {get_last_fps()}")
    
    # Test camera settings
    settings = get_camera_settings()
    print(f"Available resolutions: {list(settings.keys())}")
    
    # Test stream status
    set_stream_status(True, 12345)
    status = get_stream_status()
    print(f"Stream status: {status}")
    
    # Test snapshot count
    increment_snapshot_count()
    print(f"Snapshot count: {get_snapshot_count()}")
    
    print("State manager test completed!")

