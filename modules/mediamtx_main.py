#!/usr/bin/env python3
"""
Main MediaMTX application for Avatar Tank system.
Coordinates all MediaMTX-compatible modules and provides the web interface.
"""

import os
import sys
import json
import time
import threading
import subprocess
import datetime
from pathlib import Path
from flask import Flask, Response, request, jsonify, send_file, render_template_string
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()


# Ensure all modules can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import all MediaMTX-compatible modules with error handling
print("[MediaMTX Main] Loading Avatar Tank MediaMTX modules...")

try:
    from modules.device_detector import device_detector, device_config, CAMERA_DEVICE, MIC_PLUG, SPK_PLUG, MOTOR_PORT
    print("[MediaMTX Main] ✓ Device detector loaded")
except ImportError as e:
    print(f"[MediaMTX Main] ✗ Device detector failed: {e}")
    # Fallback values
    CAMERA_DEVICE = '/dev/video0'
    MIC_PLUG = 'plughw:3,0'
    SPK_PLUG = 'default'
    MOTOR_PORT = '/dev/ttyUSB0'

try:
    from modules.mediamtx_camera import (
        camera_manager, camera_settings, current_resolution, current_framerate,
        get_camera_status, set_camera_resolution, set_camera_framerate, 
        take_snapshot, start_streaming, stop_streaming, get_streaming_status
    )
    print("[MediaMTX Main] ✓ MediaMTX Camera module loaded")
except ImportError as e:
    print(f"[MediaMTX Main] ✗ MediaMTX Camera module failed: {e}")

try:
    from modules.mediamtx_audio import (
        get_audio_status, set_audio_bitrate, set_audio_sample_rate, 
        set_audio_channels, test_audio_playback, test_audio_recording
    )
    print("[MediaMTX Main] ✓ MediaMTX Audio module loaded")
except ImportError as e:
    print(f"[MediaMTX Main] ✗ MediaMTX Audio module failed: {e}")

try:
    from modules.mediamtx_recorder import (
        get_recording_status, start_recording, stop_recording, is_recording
    )
    print("[MediaMTX Main] ✓ MediaMTX Recorder module loaded")
except ImportError as e:
    print(f"[MediaMTX Main] ✗ MediaMTX Recorder module failed: {e}")

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'avatar_tank_mediamtx_secret_key'
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1000000
)

# Simple bearer token auth for control endpoints
# Auth disabled for simplicity
def _require_token():
    return True

# Global state
running = False
recording = False

# Global lock for stream operations to prevent concurrent FFmpeg spawning
stream_operation_lock = threading.Lock()
print("[MediaMTX Main] Stream operation lock initialized")

# Motor safety watchdog system
motor_watchdog_active = False
motor_last_heartbeat = time.time()
motor_heartbeat_timeout = 1.5  # Stop motors if no heartbeat for 1.5 seconds
motor_watchdog_lock = threading.Lock()
motor_clients_connected = set()  # Track connected clients that control motors

def motor_safety_watchdog():
    """
    Motor safety watchdog thread.
    Automatically stops motors if:
    1. No heartbeat received within timeout period
    2. All WebSocket clients disconnect
    3. USB serial link fails (handled in motor_controller.py)
    """
    global motor_watchdog_active, motor_last_heartbeat
    
    print("[Motor Safety] Watchdog thread started")
    motor_watchdog_active = True
    
    while motor_watchdog_active:
        try:
            with motor_watchdog_lock:
                time_since_heartbeat = time.time() - motor_last_heartbeat
                clients_count = len(motor_clients_connected)
                
                # Stop motors if no heartbeat for too long
                if time_since_heartbeat > motor_heartbeat_timeout:
                    # Only log and stop if we think motors might be moving
                    if time_since_heartbeat < motor_heartbeat_timeout + 2:  # Log once
                        print(f"[Motor Safety] ⚠️  No heartbeat for {time_since_heartbeat:.1f}s - STOPPING MOTORS")
                        try:
                            from modules.motor_controller import motors
                            motors.stop()
                        except Exception as e:
                            print(f"[Motor Safety] Error stopping motors: {e}")
                
                # Stop motors if no clients connected
                if clients_count == 0 and time_since_heartbeat < 5:  # Only if recently had clients
                    print("[Motor Safety] ⚠️  No clients connected - STOPPING MOTORS")
                    try:
                        from modules.motor_controller import motors
                        motors.stop()
                    except Exception as e:
                        print(f"[Motor Safety] Error stopping motors: {e}")
            
            time.sleep(0.5)  # Check every 500ms
            
        except Exception as e:
            print(f"[Motor Safety] Watchdog error: {e}")
            time.sleep(1)
    
    print("[Motor Safety] Watchdog thread stopped")


# ============== Web Interface ==============

def create_templates():
    """Create HTML templates for the web interface"""
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Avatar Tank - MediaMTX Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #fafafa;
        }
        .section h3 {
            margin-top: 0;
            color: #555;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .control-group {
            margin-bottom: 15px;
        }
        .control-group label {
            display: inline-block;
            width: 120px;
            font-weight: bold;
            color: #333;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
            margin-bottom: 10px;
            font-size: 14px;
        }
        button:hover {
            background-color: #0056b3;
        }
        button.danger {
            background-color: #dc3545;
        }
        button.danger:hover {
            background-color: #c82333;
        }
        button.success {
            background-color: #28a745;
        }
        button.success:hover {
            background-color: #218838;
        }
        .status {
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
        }
        .status.running {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.stopped {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        input[type="text"], input[type="range"], select {
            padding: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-left: 10px;
        }
        input[type="range"] {
            width: 200px;
        }
        .snapshots, .recordings {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 4px;
        }
        .file-item {
            padding: 5px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }
        .file-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Avatar Tank - MediaMTX Control</h1>
        
        <!-- Live Stream -->
        <div class="section">
            <h3>Live Stream</h3>
            <div id="stream-container" style="text-align: center; margin-bottom: 15px;">
                <video id="stream-player" width="640" height="360" controls style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;">
                    <source id="hls-source" src="" type="application/x-mpegURL">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div class="control-group">
                <button onclick="startStream()">Start Stream</button>
                <button onclick="stopStream()" class="danger">Stop Stream</button>
                <button onclick="refreshStream()">Refresh Stream</button>
            </div>
        </div>
        
        <!-- Status Section -->
        <div class="section">
            <h3>Stream Status</h3>
            <div id="status" class="status stopped">Loading...</div>
        </div>
        
        <!-- Stream URLs -->
        <div class="section">
            <h3>Stream URLs</h3>
            <div class="control-group">
                <label>HLS Stream:</label>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="text" id="hls-url" value="" readonly style="flex: 1; padding: 5px;">
                    <button onclick="copyToClipboard('hls-url')">Copy</button>
                </div>
            </div>
            <div class="control-group">
                <label>RTSP Stream:</label>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="text" id="rtsp-url" value="rtsp://192.168.68.107:8554/stream" readonly style="flex: 1; padding: 5px;">
                    <button onclick="copyToClipboard('rtsp-url')">Copy</button>
                </div>
            </div>
            <div class="control-group">
                <label>WebRTC Stream:</label>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="text" id="webrtc-url" value="" readonly style="flex: 1; padding: 5px;">
                    <button onclick="copyToClipboard('webrtc-url')">Copy</button>
                </div>
            </div>
        </div>
        
        <!-- Stream Settings -->
        <div class="section">
            <h3>Stream Settings</h3>
            <div class="control-group">
                <label for="resolution">Resolution:</label>
                <select id="resolution" onchange="setResolution()">
                    <option value="320p">320p (640x360)</option>
                    <option value="480p" selected>480p (854x480)</option>
                    <option value="720p">720p (1280x720)</option>
                </select>
            </div>
            <div class="control-group">
                <label for="framerate">Framerate:</label>
                <input type="range" id="framerate" min="10" max="25" value="10" onchange="setFramerate()">
                <span id="fps-display">10 fps</span>
            </div>
        </div>
        
        <!-- Recording Control -->
        <div class="section">
            <h3>Recording Control</h3>
            <div class="control-group">
                <button onclick="startRecording()">Start Recording</button>
                <button onclick="stopRecording()" class="danger">Stop Recording</button>
            </div>
        </div>
        
        <!-- Snapshot Control -->
        <div class="section">
            <h3>Snapshots</h3>
            <button onclick="takeSnapshot()">Take Snapshot</button>
            <button onclick="loadSnapshots()">Refresh Snapshots</button>
            <div id="snapshots" class="snapshots"></div>
        </div>
        
        <!-- Recordings -->
        <div class="section">
            <h3>Recordings</h3>
            <button onclick="loadRecordings()">Refresh Recordings</button>
            <div id="recordings" class="recordings"></div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        // Load initial status
        loadStatus();
        loadSnapshots();
        loadRecordings();

        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    const wasRunning = statusDiv.className.includes('running');
                    const isRunning = data.running;
                    
                    if (isRunning) {
                        statusDiv.className = 'status running';
                        statusDiv.textContent = `Stream Running - ${data.resolution} @ ${data.framerate}fps`;
                        
                        // Only update video player if stream just started or if not already playing
                        const video = document.getElementById('stream-player');
                        if (!wasRunning || !video.hls) {
                            updateStreamPlayer();
                        }
                    } else {
                        statusDiv.className = 'status stopped';
                        statusDiv.textContent = 'Stream Stopped';
                        
                        // Stop video player when stream stops
                        const video = document.getElementById('stream-player');
                        if (video.hls) {
                            video.hls.destroy();
                            video.hls = null;
                        }
                        video.src = '';
                    }
                    
                    // Update UI controls
                    const resolutionSelect = document.getElementById('resolution');
                    const framerateSlider = document.getElementById('framerate');
                    const fpsDisplay = document.getElementById('fps-display');
                    
                    // Set resolution
                    for (let option of resolutionSelect.options) {
                        if (data.resolution === data.available_resolutions.find(r => r === option.value)) {
                            option.selected = true;
                            break;
                        }
                    }
                    
                    // Set framerate
                    framerateSlider.value = data.framerate;
                    fpsDisplay.textContent = data.framerate + ' fps';
                })
                .catch(error => console.error('Error loading status:', error));
        }

        function startStream() {
            fetch('/api/stream/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadStatus();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => console.error('Error starting stream:', error));
        }

        function stopStream() {
            fetch('/api/stream/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadStatus();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => console.error('Error stopping stream:', error));
        }

        function startRecording() {
            fetch('/api/recording/start', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Recording started: ' + data.message);
                        loadStatus();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => console.error('Error starting recording:', error));
        }

        function stopRecording() {
            fetch('/api/recording/stop', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Recording stopped: ' + data.message);
                        loadStatus();
                        loadRecordings();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => console.error('Error stopping recording:', error));
        }

        function takeSnapshot() {
            fetch('/api/snapshot', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadSnapshots();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => console.error('Error taking snapshot:', error));
        }

        function setResolution() {
            const resolution = document.getElementById('resolution').value;
            fetch('/api/resolution', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({resolution: resolution})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => console.error('Error setting resolution:', error));
        }

        function setFramerate() {
            const framerate = document.getElementById('framerate').value;
            document.getElementById('fps-display').textContent = framerate + ' fps';
            fetch('/api/framerate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({framerate: parseInt(framerate)})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => console.error('Error setting framerate:', error));
        }

        function loadSnapshots() {
            fetch('/api/snapshots')
                .then(response => response.json())
                .then(data => {
                    const snapshotsDiv = document.getElementById('snapshots');
                    snapshotsDiv.innerHTML = '';
                    data.forEach(snapshot => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        div.innerHTML = `
                            <span>${snapshot.name}</span>
                            <span>${(snapshot.size / 1024).toFixed(1)} KB</span>
                        `;
                        snapshotsDiv.appendChild(div);
                    });
                })
                .catch(error => console.error('Error loading snapshots:', error));
        }

        function loadRecordings() {
            fetch('/api/recordings')
                .then(response => response.json())
                .then(data => {
                    const recordingsDiv = document.getElementById('recordings');
                    recordingsDiv.innerHTML = '';
                    data.forEach(recording => {
                        const div = document.createElement('div');
                        div.className = 'file-item';
                        div.innerHTML = `
                            <span>${recording.name}</span>
                            <span>${(recording.size / 1024 / 1024).toFixed(1)} MB</span>
                        `;
                        recordingsDiv.appendChild(div);
                    });
                })
                .catch(error => console.error('Error loading recordings:', error));
        }

        function refreshStream() {
            const video = document.getElementById('stream-player');
            const source = document.getElementById('hls-source');
            const currentTime = video.currentTime;
            
            // Reload the video source
            source.src = source.src + '?t=' + new Date().getTime();
            video.load();
            video.currentTime = currentTime;
            video.play().catch(e => console.log('Video play failed:', e));
        }

        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            element.select();
            element.setSelectionRange(0, 99999); // For mobile devices
            document.execCommand('copy');
            
            // Show feedback
            const button = element.nextElementSibling;
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        }

        function updateStreamPlayer() {
            const video = document.getElementById('stream-player');
            const host = window.location.hostname;
            const hlsUrl = `http://${host}:8888/stream/index.m3u8`;
            
            if (Hls.isSupported()) {
                // Use HLS.js for better browser compatibility
                if (video.hls) {
                    video.hls.destroy();
                }
                const hls = new Hls({
                    debug: false,
                    enableWorker: true,
                    lowLatencyMode: true,
                    backBufferLength: 90
                });
                hls.loadSource(hlsUrl);
                hls.attachMedia(video);
                video.hls = hls;
                
                hls.on(Hls.Events.MANIFEST_PARSED, function() {
                    console.log('HLS manifest parsed, starting playback');
                    video.play().catch(e => console.log('Video play failed:', e));
                });
                
                hls.on(Hls.Events.ERROR, function(event, data) {
                    console.error('HLS error:', data);
                    if (data.fatal) {
                        switch(data.type) {
                            case Hls.ErrorTypes.NETWORK_ERROR:
                                console.log('Fatal network error, retrying in 5 seconds...');
                                setTimeout(updateStreamPlayer, 5000);
                                break;
                            case Hls.ErrorTypes.MEDIA_ERROR:
                                console.log('Fatal media error, recovering...');
                                hls.recoverMediaError();
                                break;
                            default:
                                console.log('Fatal error, destroying HLS...');
                                hls.destroy();
                                break;
                        }
                    }
                });
            } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
                // Native HLS support (Safari)
                video.src = hlsUrl;
                video.addEventListener('loadedmetadata', function() {
                    video.play().catch(e => console.log('Video play failed:', e));
                });
            } else {
                console.error('HLS is not supported in this browser');
            }
        }

        // Auto-refresh status every 5 seconds
        function setDynamicUrls() {
            const host = window.location.hostname;
            const hls = document.getElementById('hls-url');
            const rtsp = document.getElementById('rtsp-url');
            const webrtc = document.getElementById('webrtc-url');
            if (hls) hls.value = `http://${host}:8888/stream/index.m3u8`;
            if (rtsp) rtsp.value = `rtsp://${host}:8554/stream`;
            if (webrtc) webrtc.value = `http://${host}:8889/stream`;
        }

        setDynamicUrls();
        setInterval(loadStatus, 5000);
    </script>
</body>
</html>"""
    
    with open(templates_dir / "control.html", 'w') as f:
        f.write(html_content)


# ============== API Routes ==============

@app.route('/')
def index():
    """Main control interface"""
    return send_file('../static/index.html')

# ============== TTS Routes ==============

@app.route('/speak', methods=['POST'])
def speak():
    """Text-to-speech endpoint"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({"ok": False, "msg": "No text provided"})
        
        print(f"[TTS] Speaking ({language}): {text}")
        
        # Use TTS module with word learning
        try:
            from modules.tts import tts
            result = tts.speak(text, language)
            
            # Learn words from spoken text (both written and spoken words)
            if result.get('ok'):
                try:
                    from modules.predictor import _predict
                    # Learn from the text that was spoken
                    learned_count = _predict.add_words_from_text(text)
                    if learned_count > 0:
                        print(f"[TTS] Learned {learned_count} new words from spoken text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
                except Exception as e:
                    print(f"[TTS] Word learning error: {e}")
            
            return jsonify(result)
        except ImportError as e:
            return jsonify({"ok": False, "msg": f"TTS module not available: {e}"})
        except Exception as e:
            return jsonify({"ok": False, "msg": f"TTS error: {e}"})
        
    except Exception as e:
        return jsonify({"ok": False, "msg": f"TTS error: {e}"})

@app.route('/set_language', methods=['POST'])
def set_language():
    """Set TTS language"""
    try:
        data = request.get_json()
        language = data.get('language', 'en')
        
        print(f"[TTS] Language set to: {language}")
        return jsonify({"ok": True, "msg": f"Language set to {language}"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Language error: {e}"})

# Global word learning storage
learned_words = {
    'en': {},
    'ro': {},
    'de': {}
}

@app.route('/predict')
def predict():
    """Text prediction endpoint with word learning"""
    try:
        query = request.args.get('q', '')
        language = request.args.get('lang', 'en')
        limit = int(request.args.get('limit', 3))
        
        predictions = []
        if len(query) > 0:
            # Use the enhanced predictor with language-specific suggestions
            try:
                predictions = _predict.suggest_language(query, language, limit)
            except Exception as e:
                print(f"[Predict] Error getting language-specific suggestions: {e}")
                # Fallback to regular suggestions
                predictions = _predict.suggest(query, limit)
            
            # If no language-specific suggestions, try regular suggestions
            if not predictions:
                predictions = _predict.suggest(query, limit)
        
        return jsonify({
            "ok": True,
            "items": predictions,
            "language": language,
            "query": query
        })
        
    except Exception as e:
        print(f"[Predict] Error: {e}")
        return jsonify({
            "ok": False,
            "msg": str(e),
            "items": []
        })
@app.route('/learn_word', methods=['POST'])
def learn_word():
    """Learn a new word for prediction"""
    try:
        data = request.get_json()
        word = data.get('word', '').strip().lower()
        language = data.get('language', 'en')
        
        if not word or len(word) < 2:
            return jsonify({"ok": False, "msg": "Word too short"})
        
        # Add word to learned words
        first_char = word[0]
        if language not in learned_words:
            learned_words[language] = {}
        if first_char not in learned_words[language]:
            learned_words[language][first_char] = []
        
        # Add word if not already present
        if word not in learned_words[language][first_char]:
            learned_words[language][first_char].append(word)
            print(f"[Word Learning] Learned '{word}' for language '{language}'")
        
        return jsonify({"ok": True, "msg": f"Learned word: {word}"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Learning error: {e}"})

@app.route('/play_word', methods=['POST'])
def play_word():
    """Play a learned word using TTS"""
    try:
        data = request.get_json()
        word = data.get('word', '').strip()
        language = data.get('language', 'en')
        
        if not word:
            return jsonify({"ok": False, "msg": "No word provided"})
        
        # Use TTS module for word playback
        print(f"[Word Playback] Playing word: {word} ({language})")
        
        try:
            from modules.tts import tts
            result = tts.speak(word, language)
            
            # Learn the word that was played
            if result.get('ok'):
                try:
                    from modules.predictor import _predict
                    learned_count = _predict.add_words_from_text(word)
                    if learned_count > 0:
                        print(f"[Word Playback] Learned new word: '{word}'")
                except Exception as e:
                    print(f"[Word Playback] Word learning error: {e}")
            
            return jsonify(result)
        except ImportError as e:
            return jsonify({"ok": False, "msg": f"TTS module not available: {e}"})
        except Exception as e:
            return jsonify({"ok": False, "msg": f"Word playback error: {e}"})
            
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Playback error: {e}"})

# ============== Motor Control Routes ==============

@app.route('/motor/<direction>', methods=['POST'])
def motor_control(direction):
    """Motor control endpoint with safety heartbeat"""
    global motor_last_heartbeat
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        
        # Update heartbeat timestamp for watchdog
        with motor_watchdog_lock:
            motor_last_heartbeat = time.time()
        
        data = request.get_json() or {}
        speed = int(data.get('speed', 150))
        print(f"[Motor] {direction} at speed {speed}")
        from modules.motor_controller import motors
        if direction == 'forward':
            result = motors.move(speed, speed)
        elif direction == 'backward':
            result = motors.move(-speed, -speed)
        elif direction == 'left':
            result = motors.move(-speed, speed)
        elif direction == 'right':
            result = motors.move(speed, -speed)
        elif direction == 'stop':
            result = motors.stop()
        else:
            return jsonify({"ok": False, "msg": "Unknown direction"}), 400
        return jsonify(result)
    except Exception as e:
        # On any error, try to stop motors
        try:
            from modules.motor_controller import motors
            motors.stop()
        except:
            pass
        return jsonify({"ok": False, "msg": f"Motor error: {e}"})

@app.route('/motor/test', methods=['POST'])
def motor_test():
    """Motor test endpoint"""
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        print("[Motor] Running motor test")
        from modules.motor_controller import motors
        result = motors.test_motors()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Motor test error: {e}"})

@app.route('/motor/reconnect', methods=['POST'])
def motor_reconnect():
    """Motor reconnect endpoint"""
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        print("[Motor] Reconnecting motors")
        from modules.motor_controller import reconnect_motor_controller
        ok = reconnect_motor_controller()
        return jsonify({"ok": bool(ok), "msg": "Motors reconnected" if ok else "Reconnect failed"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Motor reconnect error: {e}"})

@app.route('/lights/<position>/<state>', methods=['POST'])
def lights_control(position, state):
    """Lights control endpoint for front/back lights via SSR
    
    Args:
        position: 'front' or 'back'
        state: 'on' or 'off'
    """
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        
        # Validate inputs
        if position.lower() not in ['front', 'back']:
            return jsonify({"ok": False, "msg": "Invalid position. Use 'front' or 'back'"}), 400
        
        if state.lower() not in ['on', 'off']:
            return jsonify({"ok": False, "msg": "Invalid state. Use 'on' or 'off'"}), 400
        
        # Update heartbeat timestamp for watchdog (lights are part of vehicle control)
        with motor_watchdog_lock:
            motor_last_heartbeat = time.time()
        
        from modules.motor_controller import motors
        lights_state = (state.lower() == 'on')
        result = motors.set_lights(position.lower(), lights_state)
        
        print(f"[Lights] {position.capitalize()} lights: {state.upper()}")
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Lights control error: {e}"})

# ============== Sound Effects Routes ==============

@app.route('/play_sound/<int:sound_id>', methods=['POST'])
def play_sound(sound_id):
    """Play sound effect endpoint"""
    try:
        from modules.device_detector import SPK_PLUG
        print(f"[Sound] Playing sound effect {sound_id}")
        print(f"[Sound] Using speaker device: {SPK_PLUG}")
        
        # Map sound_id to actual sound files (1-10)
        # Get the directory where this module is located
        module_dir = Path(__file__).parent
        sound_file = module_dir / ".." / "sounds" / f"sound{sound_id + 1}.mp3"
        sound_path = sound_file.resolve()
        
        # Debug: print the actual path being checked
        print(f"[Sound] Looking for sound file: {sound_path}")
        print(f"[Sound] File exists: {sound_path.exists()}")
        
        if not sound_path.exists():
            # For sound IDs 10-19, use a default sound or create a beep
            if sound_id >= 10:
                # Use sound1.mp3 as default for extended sound IDs
                default_sound_file = module_dir / ".." / "sounds" / "sound1.mp3"
                if default_sound_file.exists():
                    sound_path = default_sound_file.resolve()
                    print(f"[Sound] Using default sound for ID {sound_id}: {sound_path}")
                else:
                    # Create a simple beep sound using system beep
                    try:
                        subprocess.run(['beep', '-f', '800', '-l', '200'], check=False, capture_output=True)
                        return jsonify({"ok": True, "msg": f"System beep played for sound {sound_id + 1}"})
                    except:
                        return jsonify({"ok": False, "msg": f"Sound file not found and no system beep available"})
            else:
                return jsonify({"ok": False, "msg": f"Sound file not found: {sound_file}"})
        
        # Convert MP3 to WAV and play through the correct audio device
        try:
            # Get audio duration first to set appropriate timeout
            duration = 10.0  # Default timeout
            try:
                probe_result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                     '-of', 'default=noprint_wrappers=1:nokey=1', str(sound_path)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if probe_result.returncode == 0:
                    duration = float(probe_result.stdout.strip())
                    print(f"[Sound] Detected duration: {duration:.1f}s")
            except (ValueError, subprocess.TimeoutExpired):
                print(f"[Sound] Could not detect duration, using default timeout")
            
            # Set timeout to duration + 5 seconds buffer, minimum 10s, maximum 60s
            playback_timeout = max(10, min(60, duration + 5))
            print(f"[Sound] Using timeout: {playback_timeout:.1f}s")
            
            # Convert to temporary WAV file first (more reliable than piping)
            temp_wav = "/tmp/sound_playback.wav"
            
            # Convert MP3 to WAV (timeout = 2x expected duration)
            convert_result = subprocess.run(
                ['ffmpeg', '-y', '-i', str(sound_path), '-ar', '44100', '-ac', '2', temp_wav],
                capture_output=True,
                timeout=max(10, duration * 2)
            )
            
            if convert_result.returncode != 0 or not os.path.exists(temp_wav):
                print(f"[Sound] FFmpeg conversion failed: {convert_result.stderr.decode('utf-8', 'ignore')}")
                return jsonify({"ok": False, "msg": "MP3 to WAV conversion failed"})
            
            # Play the WAV file through the detected speaker device with dynamic timeout
            play_result = subprocess.run(
                ['aplay', '-q', '-D', SPK_PLUG, temp_wav],
                capture_output=True,
                timeout=playback_timeout
            )
            
            # Clean up temp file
            try:
                os.unlink(temp_wav)
            except:
                pass
            
            if play_result.returncode == 0:
                print(f"[Sound] Successfully played sound {sound_id + 1} on {SPK_PLUG}")
                return jsonify({"ok": True, "msg": f"Playing sound {sound_id + 1}"})
            else:
                error_msg = play_result.stderr.decode('utf-8', 'ignore').strip() if play_result.stderr else "Unknown error"
                print(f"[Sound] Playback error: {error_msg}")
                return jsonify({"ok": False, "msg": f"Sound playback failed: {error_msg}"})
                    
        except subprocess.TimeoutExpired:
            return jsonify({"ok": False, "msg": "Sound timeout"})
        except FileNotFoundError as e:
            return jsonify({"ok": False, "msg": f"Required tool not found: {e}"})
            
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Sound error: {e}"})

@app.route('/generate_sound_from_tts', methods=['POST'])
def generate_sound_from_tts():
    """Generate TTS audio and save it as a sound effect using Edge-TTS for Romanian"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'en')
        sound_id = data.get('sound_id', 0)  # 0-109 for 110 slots
        
        if not text:
            return jsonify({"ok": False, "msg": "No text provided"})
        
        if not 0 <= sound_id <= 109:
            return jsonify({"ok": False, "msg": "Invalid sound ID (must be 0-109)"})
        
        print(f"[Sound TTS] Generating sound {sound_id + 1} from text: '{text}' ({language})")
        
        # Generate TTS audio using the updated TTS module
        try:
            from modules.tts import tts as tts_module
            import asyncio
            import edge_tts
            from pathlib import Path
            
            # Check if language is supported
            if language not in tts_module.languages:
                return jsonify({"ok": False, "msg": f"Unsupported language: {language}"})
            
            # Try Edge-TTS for all supported languages if internet is available
            if language in tts_module.edge_voices and tts_module.internet_available():
                try:
                    lang_name = tts_module.languages[language]['name']
                    print(f"[Sound TTS] Using Edge-TTS for {lang_name}: {text}")
                    
                    # Generate with Edge-TTS
                    voice = tts_module.edge_voices[language]
                    temp_mp3 = f"/tmp/edge_tts_sound_{language}_{sound_id}_{int(time.time())}.mp3"
                    
                    communicate = edge_tts.Communicate(text, voice)
                    asyncio.run(communicate.save(temp_mp3))
                    
                    if os.path.exists(temp_mp3):
                        # Copy to sounds directory
                        module_dir = Path(__file__).parent
                        sound_dir = module_dir / ".." / "sounds"
                        sound_dir.mkdir(exist_ok=True)
                        output_mp3 = sound_dir / f"sound{sound_id + 1}.mp3"
                        
                        # Copy the Edge-TTS MP3 file
                        import shutil
                        shutil.copy2(temp_mp3, output_mp3)
                        os.remove(temp_mp3)  # Clean up temp file
                        
                        print(f"[Sound TTS] Generated with Edge-TTS ({lang_name}): {output_mp3}")
                        return jsonify({
                            "ok": True, 
                            "msg": f"Sound {sound_id + 1} generated with Edge-TTS ({lang_name})",
                            "file": f"sound{sound_id + 1}.mp3",
                            "text": text,
                            "language": language
                        })
                    else:
                        print("[Sound TTS] Edge-TTS generation failed, falling back to Piper")
                        
                except Exception as e:
                    print(f"[Sound TTS] Edge-TTS error: {e}, falling back to Piper")
            
            # Fallback to Piper for other languages or when Edge-TTS fails
            print(f"[Sound TTS] Using Piper for {language}: {text}")
            
            lang_dir = tts_module.languages[language]['dir']
            temp_wav = "/tmp/tts_sound_gen.wav"
            
            # Use Piper to generate audio
            if tts_module.bin and tts_module.kind == "cli":
                # Piper CLI mode
                model, cfg = tts_module._find_model_pair(lang_dir)
                if not model or not cfg:
                    return jsonify({"ok": False, "msg": f"No Piper model found for {language}"})
                
                p = subprocess.run(
                    [tts_module.bin, "--model", model, "--config", cfg, "--output_file", temp_wav],
                    input=(text + "\n"), 
                    text=True,
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.PIPE, 
                    check=False
                )
                
                if p.returncode != 0 or not os.path.exists(temp_wav):
                    return jsonify({"ok": False, "msg": "TTS generation failed"})
                    
            elif tts_module.bin and tts_module.kind == "piper":
                # Piper mode
                model = tts_module._find_model_single(lang_dir)
                if not model:
                    return jsonify({"ok": False, "msg": f"No Piper model found for {language}"})
                
                p = subprocess.run(
                    [tts_module.bin, "--model", model, "--output_file", temp_wav],
                    input=(text + "\n"),
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=False
                )
                
                if p.returncode != 0 or not os.path.exists(temp_wav):
                    return jsonify({"ok": False, "msg": "TTS generation failed"})
            else:
                return jsonify({"ok": False, "msg": "No TTS engine available"})
            
            # Convert WAV to MP3 using ffmpeg
            module_dir = Path(__file__).parent
            sound_dir = module_dir / ".." / "sounds"
            sound_dir.mkdir(exist_ok=True)
            
            output_mp3 = sound_dir / f"sound{sound_id + 1}.mp3"
            
            # Convert with ffmpeg
            conv_result = subprocess.run(
                ['ffmpeg', '-y', '-i', temp_wav, '-codec:a', 'libmp3lame', '-qscale:a', '2', str(output_mp3)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temp WAV file
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            
            if conv_result.returncode != 0:
                return jsonify({"ok": False, "msg": f"Audio conversion failed: {conv_result.stderr}"})
            
            print(f"[Sound TTS] Generated with Piper: {output_mp3}")
            return jsonify({
                "ok": True, 
                "msg": f"Sound {sound_id + 1} generated with Piper",
                "file": f"sound{sound_id + 1}.mp3",
                "text": text,
                "language": language
            })
            
        except Exception as e:
            return jsonify({"ok": False, "msg": f"TTS generation error: {e}"})
        
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Sound generation error: {e}"})

# ============== Audio Control Routes ==============

@app.route('/audio/set_volume', methods=['POST'])
def set_volume():
    """Set audio volume endpoint with smart card/control detection"""
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        data = request.get_json()
        volume = data.get('volume', 70)
        mute = data.get('mute', False)
        
        print(f"[Audio] Volume request: {volume}%, Mute: {mute}")
        
        # Smart volume control: Try different cards and control names
        # Cards to try (USB audio devices first, then fallback to default)
        cards_to_try = [
            ('2', 'PCM'),      # USB Audio card 2 (UACDemoV1.0)
            ('3', 'PCM'),      # USB Audio card 3 (USB PnP Sound Device)
            ('0', 'PCM'),      # HDMI 0
            ('1', 'PCM'),      # HDMI 1
            (None, 'Master'),  # Default card with Master control
            (None, 'PCM'),     # Default card with PCM control
        ]
        
        success = False
        last_error = ""
        
        for card, control in cards_to_try:
            try:
                # Build amixer command
                if mute:
                    if card:
                        cmd = ['amixer', '-c', card, 'set', control, 'mute']
                    else:
                        cmd = ['amixer', 'set', control, 'mute']
                else:
                    if card:
                        cmd = ['amixer', '-c', card, 'set', control, f'{volume}%', 'unmute']
                    else:
                        cmd = ['amixer', 'set', control, f'{volume}%', 'unmute']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                
                if result.returncode == 0:
                    card_str = f"card {card}" if card else "default card"
                    print(f"[Audio] ✓ Volume set to {volume}% on {card_str} using '{control}' control")
                    success = True
                    return jsonify({"ok": True, "msg": f"Volume set to {volume}% on {card_str}"})
                else:
                    last_error = result.stderr.strip()
                    
            except subprocess.TimeoutExpired:
                last_error = "Timeout"
                continue
            except Exception as e:
                last_error = str(e)
                continue
        
        # If we get here, none of the cards worked
        if not success:
            print(f"[Audio] ✗ Failed to set volume on all cards. Last error: {last_error}")
            return jsonify({"ok": False, "msg": f"Volume control failed. Last error: {last_error}"})
                
    except FileNotFoundError:
        return jsonify({"ok": False, "msg": "amixer not available on system"})
    except Exception as e:
        print(f"[Audio] Volume error: {e}")
        return jsonify({"ok": False, "msg": f"Volume error: {e}"})

@app.route('/mic_test')
def mic_test():
    """Microphone test endpoint"""
    try:
        print("[Audio] Running microphone test")
        
        # Create a simple test file
        test_file = "mic_test.wav"
        with open(test_file, 'wb') as f:
            f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
        
        return send_file(test_file, as_attachment=True, download_name='mic_test.wav')
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Mic test error: {e}"})

# ============== System Control Routes ==============

@app.route('/system/reboot', methods=['POST'])
def system_reboot():
    """System reboot endpoint"""
    try:
        if not _require_token():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        print("[System] ⚠️  REBOOT REQUESTED - System will reboot in 3 seconds")
        
        # Schedule reboot in a separate thread to allow response to be sent
        def execute_reboot():
            import time
            time.sleep(3)  # Give time for response to be sent
            print("[System] Executing reboot command...")
            subprocess.run(['sudo', 'reboot'], check=False)
        
        import threading
        reboot_thread = threading.Thread(target=execute_reboot, daemon=True)
        reboot_thread.start()
        
        return jsonify({"ok": True, "msg": "System will reboot in 3 seconds"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Reboot error: {e}"})

@app.route('/system_status')
def system_status():
    """System status endpoint (for backward compatibility)"""
    try:
        # Return a basic system status
        status = {
            "camera": {"ok": True, "device": "/dev/video0", "resolution": "480p", "is_dummy": False},
            "motors": {"ok": True, "connected": True},
            "tts": {"ok": True}
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)})

# ============== WebSocket Events ==============

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection with motor safety tracking"""
    global motor_clients_connected, motor_last_heartbeat
    print(f"[WebSocket] Client connected: {request.sid}")
    
    # Track client for motor safety
    with motor_watchdog_lock:
        motor_clients_connected.add(request.sid)
        motor_last_heartbeat = time.time()  # Reset heartbeat on new connection
    
    emit('audio_status', {'status': 'connected'})
    print(f"[Motor Safety] Client {request.sid} added. Total clients: {len(motor_clients_connected)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection with emergency motor stop and stream cleanup"""
    global motor_clients_connected
    print(f"[WebSocket] Client disconnected: {request.sid}")
    
    # Remove client from tracking
    with motor_watchdog_lock:
        motor_clients_connected.discard(request.sid)
    
    # SAFETY: Stop motors when client disconnects (internet loss, tab closed, etc.)
    try:
        from modules.motor_controller import motors
        motors.stop()
        print(f"[Motor Safety] ⚠️  Client {request.sid} disconnected - MOTORS STOPPED")
    except Exception as e:
        print(f"[Motor Safety] Error stopping motors on disconnect: {e}")
    
    # DATA SAVING: Stop stream when last client disconnects to save bandwidth (4G data)
    try:
        if len(motor_clients_connected) == 0:
            # No more clients - stop the stream to save 4G data
            print(f"[Stream Safety] 💾 No clients connected - STOPPING STREAM to save bandwidth")
            stop_streaming()
            print(f"[Stream Safety] Stream stopped to prevent data waste on 4G connection")
    except Exception as e:
        print(f"[Stream Safety] Error stopping stream on disconnect: {e}")
    
    print(f"[Motor Safety] Client {request.sid} removed. Total clients: {len(motor_clients_connected)}")

@socketio.on('start_simple_audio')
def handle_start_audio():
    """Handle start audio streaming request"""
    try:
        print("[WebSocket] Starting audio streaming")
        emit('audio_status', {'status': 'started'})
        
        # For now, just send a test audio chunk
        # In a real implementation, you would capture audio and send it
        test_audio_data = b'\x00' * 1024  # Dummy audio data
        import base64
        encoded_data = base64.b64encode(test_audio_data).decode('utf-8')
        emit('audio_data', {'data': encoded_data})
        
    except Exception as e:
        print(f"[WebSocket] Audio start error: {e}")
        emit('audio_status', {'status': 'error', 'message': str(e)})

@socketio.on('stop_simple_audio')
def handle_stop_audio():
    """Handle stop audio streaming request"""
    try:
        print("[WebSocket] Stopping audio streaming")
        emit('audio_status', {'status': 'stopped'})
    except Exception as e:
        print(f"[WebSocket] Audio stop error: {e}")
        emit('audio_status', {'status': 'error', 'message': str(e)})

@socketio.on('test_audio_tone')
def handle_test_tone():
    """Handle test audio tone request"""
    try:
        print("[WebSocket] Playing test tone")
        emit('audio_status', {'status': 'test_tone'})
    except Exception as e:
        print(f"[WebSocket] Test tone error: {e}")
        emit('audio_status', {'status': 'error', 'message': str(e)})

@app.route('/api/status')
def get_status():
    """Get current system status"""
    try:
        camera_status = get_camera_status()
        audio_status = get_audio_status()
        recording_status = _get_recording_status_internal()
        streaming_status = get_streaming_status()
        
        # Check if FFmpeg is actually running AND if MediaMTX stream is active
        import subprocess
        import requests
        ffmpeg_running = False
        mediamtx_stream_active = False
        
        try:
            result = subprocess.run(['pgrep', '-f', 'ffmpeg.*rtsp://localhost:8554/stream'], capture_output=True, text=True)
            ffmpeg_running = result.returncode == 0 and len(result.stdout.strip()) > 0
            
            # Also check MediaMTX API to see if stream is actually active
            try:
                mediamtx_response = requests.get('http://localhost:9997/v3/paths/list', timeout=2)
                if mediamtx_response.status_code == 200:
                    mediamtx_data = mediamtx_response.json()
                    items = mediamtx_data.get('items', [])
                    if items and items[0].get('ready', False) and len(items[0].get('tracks', [])) > 0:
                        mediamtx_stream_active = True
                        print(f"[Status API] MediaMTX stream detected as active: {items[0].get('name')}")
            except Exception as e:
                print(f"[Status API] MediaMTX API check failed: {e}")
                pass  # MediaMTX API check failed, continue with FFmpeg check
            
            # Sync the state manager with actual process status
            try:
                if ffmpeg_running:
                    # Update the state manager if process is running but state is wrong
                    from modules import mediamtx_camera
                    current_state = mediamtx_camera.stream_state_manager.get_state()
                    if current_state.value == "stopped":
                        # Proper state transition: stopped -> starting -> active
                        mediamtx_camera.stream_state_manager.set_state(mediamtx_camera.StreamState.STARTING)
                        mediamtx_camera.stream_state_manager.set_state(
                            mediamtx_camera.StreamState.ACTIVE, 
                            process_id=int(result.stdout.strip())
                        )
                        mediamtx_camera.streaming_active = True
            except:
                pass
        except:
            pass
        
        # Consider streaming active if FFmpeg is running OR MediaMTX stream is active OR if streaming_status reports it
        is_streaming = streaming_status.get('active', False) or ffmpeg_running or mediamtx_stream_active
        print(f"[Status API] Streaming status: FFmpeg={ffmpeg_running}, MediaMTX={mediamtx_stream_active}, Internal={streaming_status.get('active', False)}, Final={is_streaming}")
        
        # Get framerate from the actual global variable (updated by FPS changes)
        try:
            from modules import mediamtx_camera
            actual_framerate = mediamtx_camera.current_framerate
        except:
            actual_framerate = camera_status.get('framerate', 10)
        
        return jsonify({
            'running': is_streaming,
            'resolution': camera_status.get('resolution', '480p'),
            'framerate': actual_framerate,
            'camera_device': camera_status.get('device', '/dev/video0'),
            'mic_device': audio_status.get('mic_device', 'plughw:3,0'),
            'available_resolutions': list(camera_settings.keys()),
            'fps_range': [10, 25],
            'recording': recording_status.get('recording', False),
            'streaming': is_streaming
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/start', methods=['POST'])
def start_stream_api():
    """Start MediaMTX streaming"""
    try:
        # Use refresh to ensure FFmpeg is actually started and MediaMTX sees tracks
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        return refresh_stream_api()
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/stream/refresh', methods=['POST'])
def refresh_stream_api():
    """Complete stream refresh - stop all FFmpeg processes and restart with audio"""
    # Try to acquire lock, return immediately if already in progress
    if not stream_operation_lock.acquire(blocking=False):
        print("[Stream Refresh] Another stream operation in progress, skipping...")
        return jsonify({'success': False, 'message': 'Stream operation already in progress'}), 409
    
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        import subprocess
        import time
        
        print("[Stream Refresh] Starting complete stream refresh...")
        
        # Kill all FFmpeg processes
        print("[Stream Refresh] Stopping all FFmpeg processes...")
        subprocess.run(['pkill', '-9', 'ffmpeg'], capture_output=True)
        time.sleep(2)
        
        # Wait for camera device to be free
        print("[Stream Refresh] Waiting for camera device to be free...")
        time.sleep(1)
        
        # Get current resolution settings from state manager
        from modules.avatar_state import get_last_resolution, get_resolution_settings
        resolution = get_last_resolution()
        settings = get_resolution_settings(resolution)
        if not settings:
            # Fallback to default
            resolution = '480p'
            settings = get_resolution_settings(resolution)
        width = settings['width']
        height = settings['height']
        fps = settings['fps']
        
        # Resolution-specific bitrate mapping for proper bandwidth control
        bitrate_map = {
            "320p": ("500k", "700k"),   # 640x360 - low bandwidth (target, max)
            "480p": ("1200k", "1500k"), # 854x480 - medium bandwidth
            "720p": ("2500k", "3000k")  # 1280x720 - high bandwidth
        }
        video_bitrate, max_bitrate = bitrate_map.get(resolution, ("1200k", "1500k"))
        
        print(f"[Stream Refresh] Starting new FFmpeg process with {resolution} ({width}x{height}@{fps}fps, {video_bitrate} bitrate)...")
        cmd = [
            'ffmpeg', '-nostdin',
            '-f', 'v4l2', '-i', '/dev/video0',
            '-f', 'alsa', '-i', 'plughw:3,0',
            '-vf', f'scale={width}:{height},fps={fps},format=yuv420p',
            '-c:v', 'libx264', '-preset', 'ultrafast', 
            '-b:v', video_bitrate,      # Target bitrate (resolution-specific)
            '-maxrate', max_bitrate,    # Maximum bitrate
            '-bufsize', f'{int(max_bitrate[:-1])*2}k',  # Buffer size = 2x maxrate
            '-g', str(fps), 
            '-sc_threshold', '0', '-profile:v', 'main', '-level', '3.0',
            '-c:a', 'libopus', '-b:a', '32k',
            '-rtsp_transport', 'tcp',
            '-reconnect', '1', '-reconnect_at_eof', '1', 
            '-reconnect_streamed', '1', '-reconnect_delay_max', '2',
            '-f', 'rtsp', 'rtsp://127.0.0.1:8554/stream'
        ]
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for stream to initialize
        time.sleep(3)
        
        # Check if stream is working
        import requests
        try:
            response = requests.get('http://localhost:9997/v3/paths/list', timeout=2)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if items and items[0].get('ready', False):
                    tracks = items[0].get('tracks', [])
                    has_video = 'H264' in tracks
                    has_audio = 'Opus' in tracks
                    print(f"[Stream Refresh] Stream ready - Video: {has_video}, Audio: {has_audio}")
                    return jsonify({
                        'success': True, 
                        'message': f'Stream refreshed successfully - Video: {has_video}, Audio: {has_audio}',
                        'tracks': tracks
                    })
        except:
            pass
        
        return jsonify({'success': True, 'message': 'Stream refresh initiated'})
        
    except Exception as e:
        print(f"[Stream Refresh] Error: {e}")
        return jsonify({'success': False, 'message': f"Refresh error: {str(e)}"}), 500
    finally:
        # Always release the lock
        stream_operation_lock.release()
        print("[Stream Refresh] Lock released")

@app.route('/api/stream/restart', methods=['POST'])
def restart_stream_api():
    """Restart streaming for reliability"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        # Import time module
        import time
        
        # Stop existing stream
        stop_result = stop_streaming()
        time.sleep(2)
        
        # Start new stream
        start_result = start_streaming()
        return jsonify({
            'success': start_result.get('ok', False), 
            'message': f"Restarted: {start_result.get('msg', 'Unknown')}"
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f"Restart error: {str(e)}"}), 500

@app.route('/api/stream/framerate-smooth', methods=['POST'])
def update_framerate_smooth():
    """Update framerate smoothly without interrupting stream"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        data = request.get_json()
        if not data or 'framerate' not in data:
            return jsonify({'success': False, 'message': 'Framerate not specified'}), 400
        
        new_framerate = int(data['framerate'])
        
        print(f"[Smooth FPS] Updating framerate to {new_framerate}")
        
        # Update the global framerate variable in the camera module
        try:
            from modules import mediamtx_camera
            mediamtx_camera.current_framerate = new_framerate
            print(f"[Smooth FPS] Updated camera module framerate to {new_framerate}")
        except Exception as e:
            print(f"[Smooth FPS] Failed to update camera module framerate: {e}")
        
        # For now, we still need to restart, but let's make it faster
        import time
        stop_result = stop_streaming()
        if stop_result.get('ok'):
            time.sleep(1)  # Reduced delay for smoother transition
            start_result = start_streaming()
            if start_result.get('ok'):
                return jsonify({
                    'success': True, 
                    'message': f'Framerate updated smoothly to {new_framerate}',
                    'framerate': new_framerate
                })
            else:
                return jsonify({'success': False, 'message': f'Failed to restart stream: {start_result.get("msg", "Unknown")}'})
        else:
            return jsonify({'success': False, 'message': f'Failed to stop stream: {stop_result.get("msg", "Unknown")}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Smooth framerate update error: {str(e)}'}), 500

@app.route('/api/stream/stop', methods=['POST'])
def stop_stream_api():
    """Stop MediaMTX streaming"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        result = stop_streaming()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Global recording process tracking
recording_process = None
recording_start_time = None
recording_filename = None

@app.route('/api/recording/start', methods=['POST'])
def start_recording_api():
    """Start reliable recording without breaking the stream"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        global recording_process, recording_start_time, recording_filename
        
        # First, check for any orphaned FFmpeg recording processes
        import subprocess
        try:
            # Check for FFmpeg processes that are recording
            result = subprocess.run(['pgrep', '-f', 'ffmpeg.*record'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                orphaned_pids = result.stdout.strip().split('\n')
                print(f"[Recording Start] Found orphaned recording processes: {orphaned_pids}")
                # Kill orphaned processes
                for pid in orphaned_pids:
                    try:
                        subprocess.run(['kill', '-TERM', pid], check=False)
                        print(f"[Recording Start] Killed orphaned FFmpeg process {pid}")
                    except:
                        pass
                time.sleep(1)  # Give time for processes to terminate
        except Exception as e:
            print(f"[Recording Start] Error checking orphaned processes: {e}")
        
        # Check if already recording - improved state detection
        if recording_process:
            # Check if process is actually running or just a stale reference
            try:
                poll_result = recording_process.poll()
                if poll_result is None:
                    # Process is actually running
                    return jsonify({'success': False, 'message': 'Recording already in progress'})
                else:
                    # Process has terminated, clear the stale reference
                    print(f"[Recording Start] Clearing stale recording process reference (exit code: {poll_result})")
                    recording_process = None
                    recording_start_time = None
                    recording_filename = None
            except Exception as e:
                # Invalid process object, clear it
                print(f"[Recording Start] Clearing invalid recording process reference: {e}")
                recording_process = None
                recording_start_time = None
                recording_filename = None
        
        result = _start_reliable_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording_api():
    """Stop reliable recording"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        global recording_process, recording_start_time, recording_filename
        
        if recording_process is None or recording_process.poll() is not None:
            return jsonify({'success': False, 'message': 'No recording in progress'})
        
        result = _stop_reliable_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/snapshot', methods=['POST'])
def take_snapshot_api():
    """Take a reliable snapshot without breaking the stream"""
    try:
        if not _require_token():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        result = _take_reliable_snapshot()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/resolution', methods=['POST'])
def set_resolution_api():
    """Set stream resolution"""
    try:
        data = request.get_json()
        if not data or 'resolution' not in data:
            return jsonify({'success': False, 'message': 'Resolution not specified'}), 400
        
        success = set_camera_resolution(data['resolution'])
        if success:
            # Trigger stream refresh to apply new resolution
            print(f"[Resolution API] Resolution changed to {data['resolution']}, triggering stream refresh...")
            try:
                refresh_stream_api()
                # Add a small delay to ensure the stream is ready
                import time
                time.sleep(2)
                return jsonify({'success': True, 'message': f'Resolution updated to {data["resolution"]} and stream refreshed'})
            except Exception as e:
                print(f"[Resolution API] Stream refresh failed: {e}")
                return jsonify({'success': True, 'message': f'Resolution updated to {data["resolution"]} but stream refresh failed'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update resolution'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/framerate', methods=['POST'])
def set_framerate_api():
    """Set stream framerate - use smooth approach"""
    try:
        data = request.get_json()
        if not data or 'framerate' not in data:
            return jsonify({'success': False, 'message': 'Framerate not specified'}), 400
        
        new_framerate = int(data['framerate'])
        
        # Update the global framerate variable in the camera module
        try:
            import modules.mediamtx_camera
            modules.mediamtx_camera.current_framerate = new_framerate
            print(f"[Framerate API] Updated camera module framerate to {new_framerate}")
        except Exception as e:
            print(f"[Framerate API] Failed to update camera module framerate: {e}")
        
        success = set_camera_framerate(new_framerate)
        return jsonify({'success': success, 'message': 'Framerate updated' if success else 'Failed to update framerate'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/state', methods=['GET'])
def get_system_state():
    """Get complete system state"""
    try:
        from modules.avatar_state import get_full_state, get_stream_status
        import subprocess
        
        state = get_full_state()
        
        # Add real-time stream status
        try:
            result = subprocess.run(['pgrep', '-f', 'ffmpeg.*rtsp://localhost:8554/stream'], capture_output=True, text=True)
            ffmpeg_running = result.returncode == 0 and len(result.stdout.strip()) > 0
            if ffmpeg_running:
                state['stream_status']['active'] = True
                state['stream_status']['ffmpeg_pid'] = int(result.stdout.strip())
            else:
                state['stream_status']['active'] = False
                state['stream_status']['ffmpeg_pid'] = None
        except:
            pass
        
        return jsonify({
            'success': True,
            'state': state,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/state/reset', methods=['POST'])
def reset_system_state():
    """Reset system state to defaults"""
    try:
        from modules.avatar_state import reset_to_defaults
        
        success = reset_to_defaults()
        if success:
            return jsonify({'success': True, 'message': 'System state reset to defaults'})
        else:
            return jsonify({'success': False, 'message': 'Failed to reset system state'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/state/snapshot-count', methods=['GET'])
def get_snapshot_count():
    """Get total snapshot count"""
    try:
        from modules.avatar_state import get_snapshot_count
        
        count = get_snapshot_count()
        return jsonify({
            'success': True,
            'count': count,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def _take_reliable_snapshot():
    """Take a snapshot using a separate camera process - doesn't interfere with main stream"""
    try:
        # Create snapshots directory
        os.makedirs("snapshots", exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"snapshots/avatar_tank_{timestamp}.jpg"
        
        # Get current resolution settings from state manager for proper snapshot size
        from modules.avatar_state import get_last_resolution, get_resolution_settings
        resolution = get_last_resolution()
        settings = get_resolution_settings(resolution)
        if not settings:
            # Fallback to default
            resolution = '480p'
            settings = get_resolution_settings(resolution)
        width = settings['width']
        height = settings['height']
        
        print(f"[Reliable Snapshot] Taking snapshot at {resolution} ({width}x{height})")
        
        # Take snapshot from RTSP stream but ensure it's scaled to the correct resolution
        # This approach doesn't interfere with the main streaming process
        rtsp_url = 'rtsp://localhost:8554/stream'
        
        cmd = [
            'ffmpeg', '-y',  # Overwrite output file
            '-rtsp_transport', 'tcp',  # Use TCP for reliability
            '-i', rtsp_url,  # Capture from the stream
            '-vf', f'scale={width}:{height}',  # Scale to exact resolution
            '-frames:v', '1',  # Capture only 1 frame
            '-q:v', '2',       # High quality
            '-timeout', '5000000',  # 5 second timeout
            filename
        ]
        
        print(f"[Reliable Snapshot] Using command: {' '.join(cmd)}")
        
        # Run snapshot command with timeout
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"[Reliable Snapshot] ✓ Snapshot saved: {filename} ({file_size} bytes)")
            
            # Increment snapshot count in state manager
            try:
                from modules.avatar_state import increment_snapshot_count
                increment_snapshot_count()
            except Exception as e:
                print(f"[Reliable Snapshot] Error updating snapshot count: {e}")
            
            return {'success': True, 'filename': filename, 'size': file_size, 'message': f'Snapshot saved as {filename}'}
        else:
            error_msg = f"FFmpeg failed: {result.stderr}" if result.stderr else "Unknown error"
            print(f"[Reliable Snapshot] ✗ Snapshot failed: {error_msg}")
            return {'success': False, 'message': f'Snapshot failed: {error_msg}'}
            
    except subprocess.TimeoutExpired:
        error_msg = "Snapshot timeout - camera may be busy"
        print(f"[Reliable Snapshot] ✗ {error_msg}")
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f"Snapshot error: {str(e)}"
        print(f"[Reliable Snapshot] ✗ {error_msg}")
        return {'success': False, 'message': error_msg}

@app.route('/api/snapshots')
def get_snapshots():
    """Get list of snapshots"""
    try:
        snapshots_dir = Path("snapshots")
        if not snapshots_dir.exists():
            return jsonify([])
        
        snapshots = []
        for file_path in snapshots_dir.glob("*.jpg"):
            snapshots.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })
        
        # Sort by modification time (newest first)
        snapshots.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify(snapshots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recordings')
def get_recordings():
    """Get list of recordings"""
    try:
        recordings_dir = Path("recordings")
        if not recordings_dir.exists():
            return jsonify([])
        
        recordings = []
        for file_path in recordings_dir.glob("*.mp4"):
            recordings.append({
                'name': file_path.name,
                'size': file_path.stat().st_size,
                'modified': file_path.stat().st_mtime
            })
        
        # Sort by modification time (newest first)
        recordings.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify(recordings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============== MediaMTX API Endpoints ==============

@app.route('/api/mediamtx/status')
def mediamtx_status():
    """Get MediaMTX server status"""
    try:
        # Check if MediaMTX is running by checking if port 8889 is open
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8889))
        sock.close()
        
        if result == 0:
            return jsonify({
                'status': 'running',
                'webrtc_port': 8889,
                'rtsp_port': 8554,
                'api_port': 9997
            })
        else:
            return jsonify({
                'status': 'stopped',
                'webrtc_port': 8889,
                'rtsp_port': 8554,
                'api_port': 9997
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mediamtx/metrics')
def mediamtx_metrics():
    """Get MediaMTX metrics"""
    try:
        # Get basic system metrics
        import psutil
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return jsonify({
            'cpu_usage': cpu_percent,
            'memory_usage': memory.percent,
            'memory_total': memory.total,
            'memory_available': memory.available,
            'connections': 0,  # Placeholder
            'streams': 1 if get_streaming_status() else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mediamtx/config', methods=['POST'])
def mediamtx_config():
    """Update MediaMTX configuration"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        data = request.get_json()
        parameter = data.get('parameter')
        value = data.get('value')
        stream = data.get('stream', 'stream')
        
        if parameter == 'resolution':
            set_camera_resolution(value)
            return jsonify({'success': True, 'message': f'Resolution set to {value}'})
        elif parameter == 'framerate':
            set_camera_framerate(int(value))
            return jsonify({'success': True, 'message': f'Framerate set to {value}'})
        else:
            return jsonify({'error': f'Unknown parameter: {parameter}'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mediamtx/hooks', methods=['POST'])
def mediamtx_hooks():
    """Register MediaMTX hooks"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        data = request.get_json()
        hooks = data.get('hooks', [])
        
        # Log the hooks registration
        print(f"[MediaMTX] Hooks registered: {len(hooks)} hooks")
        for hook in hooks:
            print(f"[MediaMTX] - {hook.get('event', 'unknown')}: {hook.get('url', 'no URL')}")
        
        return jsonify({'success': True, 'message': f'Registered {len(hooks)} hooks'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== Main Application ==============

def main():
    """Main function"""
    # Create templates directory and HTML file
    create_templates()
    
    # Get RPi IP addresses
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            print(f"[MediaMTX Main] RPi IP addresses: {ips}")
    except Exception as e:
        print(f"[MediaMTX Main] Could not get IP addresses: {e}")
    
    print("[MediaMTX Main] Starting Avatar Tank MediaMTX control interface...")
    print("[MediaMTX Main] Access the control interface at:")
    print("  - http://localhost:5000")
    try:
        hostnames = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if hostnames.returncode == 0:
            for ip in hostnames.stdout.strip().split():
                print(f"  - http://{ip}:5000")
    except Exception:
        pass
    
    # Start the web server (disable reloader to avoid forking under systemd)
    print("[MediaMTX Main] Launching web server on 0.0.0.0:5000")
    
    # Check if port is already in use (detect duplicate service instances)
    import socket
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        test_sock.bind(('0.0.0.0', 5000))
        test_sock.close()
        print("[MediaMTX Main] Port 5000 is available")
    except OSError as e:
        print(f"[MediaMTX Main] ⚠️  ERROR: Port 5000 is already in use!")
        print(f"[MediaMTX Main] ⚠️  This indicates a duplicate service instance is running.")
        print(f"[MediaMTX Main] ⚠️  Check: sudo systemctl status avatar-tank avatar-mediamtx")
        print(f"[MediaMTX Main] ⚠️  Disable duplicates: sudo systemctl disable avatar-mediamtx")
        import sys
        sys.exit(1)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)


def _start_reliable_recording():
    """Start recording using separate processes - doesn't interfere with main stream"""
    global recording_process, recording_start_time, recording_filename
    
    try:
        # Create recordings directory
        os.makedirs("recordings", exist_ok=True)
        
        # Generate filename with timestamp
        recording_start_time = datetime.datetime.now()
        timestamp = recording_start_time.strftime("%Y%m%d_%H%M%S")
        recording_filename = f"recordings/avatar_tank_{timestamp}.mp4"
        
        # Get camera device (use same as main stream)
        camera_device = get_camera_device() if 'get_camera_device' in globals() else '/dev/video0'
        
        # Get audio device
        audio_device = 'plughw:3,0'  # Use same audio device as main stream
        
        # Create recording command using stream input instead of camera directly
        # This approach avoids camera device conflicts
        rtsp_url = 'rtsp://localhost:8554/stream'
        
        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',  # Use TCP for reliability
            '-i', rtsp_url,  # Use stream instead of camera
            '-c:v', 'libx264',
            '-preset', 'fast',  # Faster encoding for recording
            '-crf', '23',       # Good quality
            '-t', '300',        # Limit to 5 minutes to prevent huge files
            recording_filename
        ]
        
        print(f"[Reliable Recording] Starting recording: {recording_filename}")
        
        # Start recording process
        recording_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        # Wait a moment to check if it started successfully
        time.sleep(1)
        if recording_process.poll() is not None:
            error_msg = "Recording process failed to start"
            print(f"[Reliable Recording] ✗ {error_msg}")
            return {'success': False, 'message': error_msg}
        
        print(f"[Reliable Recording] ✓ Recording started with PID: {recording_process.pid}")
        return {
            'success': True, 
            'message': f'Recording started as {recording_filename}',
            'filename': recording_filename,
            'pid': recording_process.pid
        }
        
    except Exception as e:
        error_msg = f"Recording start error: {str(e)}"
        print(f"[Reliable Recording] ✗ {error_msg}")
        return {'success': False, 'message': error_msg}

def _stop_reliable_recording():
    """Stop reliable recording"""
    global recording_process, recording_start_time, recording_filename
    
    try:
        if recording_process is None:
            return {'success': False, 'message': 'No recording process to stop'}
        
        print(f"[Reliable Recording] Stopping recording process PID: {recording_process.pid}")
        
        # Send quit command to FFmpeg
        recording_process.stdin.write(b'q\n')
        recording_process.stdin.flush()
        
        # Wait for process to finish
        recording_process.wait(timeout=10)
        
        # Check if file was created and get size
        file_size = 0
        if recording_filename and os.path.exists(recording_filename):
            file_size = os.path.getsize(recording_filename)
        
        recording_duration = 0
        if recording_start_time:
            recording_duration = (datetime.datetime.now() - recording_start_time).total_seconds()
        
        result = {
            'success': True,
            'message': f'Recording stopped. Duration: {recording_duration:.1f}s, Size: {file_size / (1024*1024):.1f}MB',
            'filename': recording_filename,
            'duration': recording_duration,
            'size': file_size
        }
        
        print(f"[Reliable Recording] ✓ {result['message']}")
        
        # Reset global variables
        recording_process = None
        recording_start_time = None
        recording_filename = None
        
        return result
        
    except subprocess.TimeoutExpired:
        error_msg = "Recording stop timeout"
        print(f"[Reliable Recording] ⚠️ {error_msg}")
        # Force kill the process
        if recording_process:
            recording_process.kill()
            recording_process = None
        return {'success': False, 'message': error_msg}
    except Exception as e:
        error_msg = f"Recording stop error: {str(e)}"
        print(f"[Reliable Recording] ✗ {error_msg}")
        return {'success': False, 'message': error_msg}

# Global variables for bandwidth tracking
last_network_stats = {}
last_bandwidth_time = 0
last_stream_stats = {}
last_stream_time = 0

@app.route('/api/network/bandwidth', methods=['GET'])
def get_network_bandwidth():
    """Get real-time network bandwidth usage with proper rate calculation"""
    global last_network_stats, last_bandwidth_time
    
    try:
        import subprocess
        import time
        
        current_time = time.time()
        
        # Get network interface statistics
        result = subprocess.run(['cat', '/proc/net/dev'], capture_output=True, text=True)
        if result.returncode != 0:
            return jsonify({'bandwidth_kbps': 0, 'error': 'Failed to read network stats'})
        
        lines = result.stdout.strip().split('\n')
        current_stats = {}
        
        for line in lines[2:]:  # Skip header lines
            parts = line.split(':')
            if len(parts) >= 2:
                interface = parts[0].strip()
                stats = parts[1].split()
                if len(stats) >= 9:
                    # bytes received, bytes transmitted
                    rx_bytes = int(stats[0])
                    tx_bytes = int(stats[8])
                    current_stats[interface] = {'rx': rx_bytes, 'tx': tx_bytes}
        
        # Calculate bandwidth rate for active interfaces
        total_bandwidth_kbps = 0
        active_interfaces = []
        
        # Only calculate rate if we have previous data
        if last_network_stats and last_bandwidth_time > 0:
            time_diff = current_time - last_bandwidth_time
            
            for interface, current_stat in current_stats.items():
                if interface in ['wlan0', 'eth0', 'zt2lrsngy5'] and interface in last_network_stats:
                    last_stat = last_network_stats[interface]
                    
                    # Calculate bytes per second
                    rx_rate = (current_stat['rx'] - last_stat['rx']) / time_diff
                    tx_rate = (current_stat['tx'] - last_stat['tx']) / time_diff
                    total_rate = rx_rate + tx_rate
                    
                    # Convert to KB/s
                    bandwidth_kbps = total_rate / 1024
                    
                    if bandwidth_kbps > 0:
                        active_interfaces.append({
                            'name': interface,
                            'rx_kbps': rx_rate / 1024,
                            'tx_kbps': tx_rate / 1024,
                            'total_kbps': bandwidth_kbps
                        })
                        total_bandwidth_kbps += bandwidth_kbps
        
        # Update tracking variables
        last_network_stats = current_stats.copy()
        last_bandwidth_time = current_time
        
        # Cap bandwidth at reasonable limit for display
        total_bandwidth_kbps = min(total_bandwidth_kbps, 500)  # Cap at 500 KB/s
        
        return jsonify({
            'bandwidth_kbps': round(total_bandwidth_kbps, 1),
            'interfaces': active_interfaces,
            'timestamp': current_time
        })
        
    except Exception as e:
        return jsonify({'bandwidth_kbps': 0, 'error': str(e)})

@app.route('/api/stream/bandwidth', methods=['GET'])
def get_stream_bandwidth():
    """Get actual stream bandwidth usage by monitoring MediaMTX connections"""
    global last_stream_stats, last_stream_time
    
    try:
        import subprocess
        import time
        
        current_time = time.time()
        
        # Get MediaMTX API status to check active connections
        try:
            import requests
            mediamtx_response = requests.get('http://localhost:9997/v3/paths/list', timeout=2)
            if mediamtx_response.status_code == 200:
                paths_data = mediamtx_response.json()
                stream_active = False
                for path in paths_data.get('items', []):
                    if path.get('name') == 'stream' and path.get('ready'):
                        stream_active = True
                        break
                
                if not stream_active:
                    return jsonify({
                        'stream_bandwidth_kbps': 0,
                        'stream_active': False,
                        'message': 'No active stream'
                    })
        except:
            pass
        
        # Monitor specific ports used by the stream
        stream_ports = [8554, 8888, 8889]
        total_stream_bytes = 0
        
        # Get network connections for stream ports
        result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                for port in stream_ports:
                    if f':{port}' in line and 'ESTABLISHED' in line:
                        # Extract bytes from connection info if available
                        parts = line.split()
                        if len(parts) > 4:
                            # This is a simplified approach - in reality we'd need more detailed monitoring
                            pass
        
        # Alternative: Use netstat to get connection info
        netstat_result = subprocess.run(['netstat', '-i'], capture_output=True, text=True)
        if netstat_result.returncode == 0:
            lines = netstat_result.stdout.strip().split('\n')
            for line in lines:
                if 'wlan0' in line or 'eth0' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        # Extract RX/TX bytes from interface stats
                        rx_bytes = int(parts[2]) if parts[2].isdigit() else 0
                        tx_bytes = int(parts[9]) if parts[9].isdigit() else 0
                        total_stream_bytes = rx_bytes + tx_bytes
                        break
        
        # Calculate stream bandwidth rate
        stream_bandwidth_kbps = 0
        
        if last_stream_stats and last_stream_time > 0:
            time_diff = current_time - last_stream_time
            if time_diff > 0:
                bytes_diff = total_stream_bytes - last_stream_stats.get('total_bytes', 0)
                stream_bandwidth_kbps = (bytes_diff / time_diff) / 1024  # Convert to KB/s
        
        # Update tracking variables
        last_stream_stats = {'total_bytes': total_stream_bytes}
        last_stream_time = current_time
        
        # Get actual bandwidth from current stream settings
        actual_bandwidth = 0
        try:
            # Get current resolution and calculate actual bandwidth from FFmpeg settings
            from modules.mediamtx_camera import current_resolution, camera_settings
            if current_resolution in camera_settings:
                # Use the same bitrate mapping as in get_ffmpeg_command()
                bitrate_map = {
                    "320p": 120,   # video bitrate
                    "480p": 180,   
                    "720p": 300    
                }
                video_bitrate = bitrate_map.get(current_resolution, 180)
                audio_bitrate = 32  # Fixed audio bitrate
                actual_bandwidth = video_bitrate + audio_bitrate
        except:
            actual_bandwidth = 212  # Default estimate
        
        return jsonify({
            'stream_bandwidth_kbps': round(actual_bandwidth, 1),
            'theoretical_bandwidth_kbps': actual_bandwidth,
            'stream_active': True,
            'timestamp': current_time
        })
        
    except Exception as e:
        return jsonify({'stream_bandwidth_kbps': 0, 'error': str(e)})

@app.route('/api/reconnection/status', methods=['GET'])
def get_reconnection_status():
    """Get current reconnection status and statistics"""
    try:
        from modules.mediamtx_camera import reconnection_state
        
        return jsonify({
            'attempts': reconnection_state['attempts'],
            'max_attempts': reconnection_state['max_attempts'],
            'is_reconnecting': reconnection_state['is_reconnecting'],
            'consecutive_failures': reconnection_state['consecutive_failures'],
            'last_failure_time': reconnection_state['last_failure_time'],
            'next_delay': reconnection_state['backoff_delays'][min(reconnection_state['attempts'], len(reconnection_state['backoff_delays'])-1)] if reconnection_state['attempts'] > 0 else 0
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/bandwidth/status', methods=['GET'])
def get_bandwidth_status():
    """Get current bandwidth management status and network conditions"""
    try:
        from modules.mediamtx_camera import bandwidth_manager
        
        return jsonify({
            'current_resolution': bandwidth_manager['current_resolution'],
            'current_fps': bandwidth_manager['current_fps'],
            'current_bitrate': bandwidth_manager['current_bitrate'],
            'network_conditions': bandwidth_manager['network_conditions'],
            'adaptation_history': bandwidth_manager['adaptation_history'][-5:],  # Last 5 adaptations
            'last_adaptation_time': bandwidth_manager['last_adaptation_time']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/audio/quality', methods=['GET'])
def get_audio_quality():
    """Get current audio quality status and packet loss information"""
    try:
        from modules.mediamtx_camera import audio_quality_monitor, calculate_packet_loss
        
        current_packet_loss = calculate_packet_loss()
        
        return jsonify({
            'current_bitrate': audio_quality_monitor['current_bitrate'],
            'packet_loss_rate': round(current_packet_loss, 2),
            'packet_loss_history': audio_quality_monitor['packet_loss_history'],
            'last_adjustment_time': audio_quality_monitor['last_adjustment_time'],
            'quality_status': 'good' if current_packet_loss < 2.0 else 'degraded' if current_packet_loss < 5.0 else 'poor'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/cpu/status', methods=['GET'])
def get_cpu_status():
    """Get current CPU usage and optimization status"""
    try:
        from modules.mediamtx_camera import get_cpu_usage, check_cpu_throttling, check_hardware_encoding
        return jsonify({
            'cpu_usage_percent': get_cpu_usage(),
            'is_throttling': check_cpu_throttling(),
            'hardware_encoding_available': check_hardware_encoding(),
            'optimization_active': True
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/cpu/optimize', methods=['POST'])
def trigger_cpu_optimization():
    """Manually trigger CPU optimization"""
    try:
        from modules.mediamtx_camera import auto_reduce_quality
        auto_reduce_quality()
        return jsonify({'status': 'CPU optimization triggered'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/stream/state', methods=['GET'])
def get_stream_state():
    """Get detailed stream state information"""
    try:
        from modules.mediamtx_camera import stream_state_manager
        state_info = stream_state_manager.get_state_info()
        state_history = stream_state_manager.get_state_history()
        
        return jsonify({
            'current_state': state_info.state.value,
            'timestamp': state_info.timestamp,
            'process_id': state_info.process_id,
            'error_message': state_info.error_message,
            'retry_count': state_info.retry_count,
            'state_history': [
                {
                    'state': entry.state.value,
                    'timestamp': entry.timestamp
                } for entry in state_history
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/health/check', methods=['GET'])
def health_check():
    """Comprehensive health check that tests the full streaming pipeline"""
    health_status = {
        'overall_status': 'healthy',
        'timestamp': time.time(),
        'checks': {}
    }
    
    try:
        # 1. Check FFmpeg process
        ffmpeg_running = False
        ffmpeg_pid = None
        try:
            result = subprocess.run(['pgrep', '-f', 'ffmpeg.*rtsp://localhost:8554/stream'], 
                                  capture_output=True, text=True, timeout=5)
            ffmpeg_running = result.returncode == 0 and len(result.stdout.strip()) > 0
            if ffmpeg_running:
                ffmpeg_pid = int(result.stdout.strip())
        except Exception as e:
            health_status['checks']['ffmpeg'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['ffmpeg'] = {
            'status': 'healthy' if ffmpeg_running else 'unhealthy',
            'running': ffmpeg_running,
            'pid': ffmpeg_pid
        }
        
        # 2. Check MediaMTX service
        mediamtx_running = False
        mediamtx_pid = None
        try:
            result = subprocess.run(['pgrep', '-f', 'mediamtx.*config/mediamtx.yml'], 
                                  capture_output=True, text=True, timeout=5)
            mediamtx_running = result.returncode == 0 and len(result.stdout.strip()) > 0
            if mediamtx_running:
                mediamtx_pid = int(result.stdout.strip())
        except Exception as e:
            health_status['checks']['mediamtx'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['mediamtx'] = {
            'status': 'healthy' if mediamtx_running else 'unhealthy',
            'running': mediamtx_running,
            'pid': mediamtx_pid
        }
        
        # 3. Check camera device availability
        camera_available = False
        try:
            camera_device = "/dev/video0"  # Default
            result = subprocess.run(['fuser', camera_device], capture_output=True, timeout=5)
            camera_available = result.returncode != 0  # Available if no processes using it
        except Exception as e:
            health_status['checks']['camera'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['camera'] = {
            'status': 'healthy' if camera_available else 'unhealthy',
            'available': camera_available,
            'device': camera_device
        }
        
        # 4. Check WebRTC endpoint
        webrtc_accessible = False
        try:
            response = requests.get('http://localhost:8889/stream', timeout=5)
            webrtc_accessible = response.status_code == 200
        except Exception as e:
            health_status['checks']['webrtc'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['webrtc'] = {
            'status': 'healthy' if webrtc_accessible else 'unhealthy',
            'accessible': webrtc_accessible
        }
        
        # 5. Check HLS endpoint
        hls_accessible = False
        try:
            response = requests.get('http://localhost:8888/stream/index.m3u8', timeout=5)
            hls_accessible = response.status_code == 200
        except Exception as e:
            health_status['checks']['hls'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['hls'] = {
            'status': 'healthy' if hls_accessible else 'unhealthy',
            'accessible': hls_accessible
        }
        
        # 6. Check audio device
        audio_available = False
        try:
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True, timeout=5)
            audio_available = 'plughw:3,0' in result.stdout or 'USB Audio' in result.stdout
        except Exception as e:
            health_status['checks']['audio'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['audio'] = {
            'status': 'healthy' if audio_available else 'unhealthy',
            'available': audio_available
        }
        
        # 7. Check state manager
        state_healthy = False
        try:
            from modules.mediamtx_camera import stream_state_manager
            current_state = stream_state_manager.get_state()
            state_healthy = current_state.value in ['active', 'starting']
        except Exception as e:
            health_status['checks']['state_manager'] = {'status': 'error', 'error': str(e)}
        
        health_status['checks']['state_manager'] = {
            'status': 'healthy' if state_healthy else 'unhealthy',
            'current_state': current_state.value if 'current_state' in locals() else 'unknown'
        }
        
        # Determine overall status
        unhealthy_checks = [check for check in health_status['checks'].values() 
                           if check.get('status') == 'unhealthy']
        
        if unhealthy_checks:
            health_status['overall_status'] = 'unhealthy'
            health_status['unhealthy_checks'] = len(unhealthy_checks)
        
        return jsonify(health_status)
        
    except Exception as e:
        return jsonify({
            'overall_status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })

@app.route('/api/health/recovery', methods=['POST'])
def trigger_recovery():
    """Manually trigger error recovery"""
    try:
        from modules.mediamtx_camera import error_recovery_manager
        
        data = request.get_json() or {}
        error_type = data.get('error_type', 'network_timeout')
        
        success = error_recovery_manager.attempt_recovery(error_type)
        
        return jsonify({
            'success': success,
            'error_type': error_type,
            'message': f'Recovery {"succeeded" if success else "failed"} for {error_type}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/system/cleanup', methods=['POST'])
def system_cleanup():
    """Manually trigger system cleanup and recovery"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import cleanup_zombie_processes, validate_system_state
        
        # Clean up zombie processes
        cleanup_success = cleanup_zombie_processes()
        
        # Validate system state
        validation_success = validate_system_state()
        
        return jsonify({
            'cleanup_success': cleanup_success,
            'validation_success': validation_success,
            'message': 'System cleanup completed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/system/auto-recovery', methods=['POST'])
def trigger_auto_recovery():
    """Manually trigger automatic recovery"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import auto_recovery_on_startup
        
        success = auto_recovery_on_startup()
        
        return jsonify({
            'success': success,
            'message': 'Automatic recovery completed'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/stream/auto-start', methods=['POST'])
def auto_start_stream():
    """Automatically start stream if conditions are met"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import start_streaming, get_streaming_status
        
        # Check current status
        status = get_streaming_status()
        
        if not status.get('streaming', False):
            # Start streaming
            result = start_streaming()
            return jsonify({
                'auto_started': result.get('ok', False),
                'message': result.get('msg', 'Unknown error'),
                'previous_status': status
            })
        else:
            return jsonify({
                'auto_started': False,
                'message': 'Stream already active',
                'current_status': status
            })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/recording/start', methods=['POST'])
def start_recording():
    """Start robust recording directly from FFmpeg source"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import recording_manager
        result = recording_manager.start_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/recording/stop', methods=['POST'])
def stop_recording():
    """Stop recording gracefully"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import recording_manager
        result = recording_manager.stop_recording()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

def _get_recording_status_internal():
    """Get current recording status (internal function for status endpoint)"""
    try:
        from modules.mediamtx_camera import recording_manager
        status = recording_manager.get_recording_status()
        return status  # Return dictionary, not jsonify
    except Exception as e:
        return {'error': str(e)}  # Return dictionary, not jsonify

@app.route('/api/recording/status', methods=['GET'])
def get_recording_status():
    """Get current recording status"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import recording_manager
        status = recording_manager.get_recording_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/recording/list', methods=['GET'])
def list_recordings():
    """List all recording files"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import recording_manager
        recordings = recording_manager.list_recordings()
        return jsonify({'recordings': recordings})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/recording/resume', methods=['POST'])
def resume_recording():
    """Manually trigger recording resume"""
    try:
        if not _require_token():
            return jsonify({'error': 'Unauthorized'}), 401
        from modules.mediamtx_camera import recording_manager
        recording_manager.auto_resume_recording()
        return jsonify({'status': 'Recording resume triggered'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/metrics')
def metrics():
    try:
        from modules.mediamtx_camera import get_streaming_status
        status = get_streaming_status()
        lines = [
            f"avatar_stream_active {1 if status.get('active') else 0}",
        ]
        return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; version=0.0.4"}
    except Exception as e:
        return f"avatar_metrics_error 1\n# {e}\n", 200, {"Content-Type": "text/plain; version=0.0.4"}

# Background bandwidth management thread
def bandwidth_management_thread():
    """Background thread to monitor and adapt stream quality"""
    import time
    from modules.mediamtx_camera import adapt_stream_quality, streaming_active
    
    while True:
        try:
            if streaming_active:
                # Check and adapt stream quality
                adaptation_applied = adapt_stream_quality()
                
                if adaptation_applied:
                    print("[Bandwidth Manager] Stream quality adaptation applied")
            
            time.sleep(15)  # Check every 15 seconds
            
        except Exception as e:
            print(f"[Bandwidth Manager] Error in monitoring thread: {e}")
            time.sleep(30)  # Wait longer on error

# Background CPU monitoring thread
def cpu_monitoring_thread():
    """Background thread to monitor CPU usage and trigger optimizations"""
    import time
    from modules.mediamtx_camera import auto_reduce_quality, streaming_active, get_cpu_usage
    
    while True:
        try:
            if streaming_active:
                cpu_usage = get_cpu_usage()
                if cpu_usage > 80:  # High CPU usage
                    print(f"[CPU Monitor] High CPU usage detected: {cpu_usage:.1f}%")
                    auto_reduce_quality()
            
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"[CPU Monitor] Error in monitoring thread: {e}")
            time.sleep(30)  # Wait longer on error

def stream_health_monitor_thread():
    """Background thread to monitor stream health and fix state synchronization issues"""
    import time
    import requests
    from modules.mediamtx_camera import stream_state_manager, StreamState, start_streaming, get_streaming_status
    
    while True:
        try:
            # Check every 15 seconds (more frequent)
            time.sleep(15)
            
            current_state = stream_state_manager.get_state()
            
            if current_state == StreamState.ACTIVE:
                # Verify the stream is actually working
                state_info = stream_state_manager.get_state_info()
                
                if state_info.process_id:
                    try:
                        # Check if process exists
                        import subprocess
                        subprocess.run(['kill', '-0', str(state_info.process_id)], 
                                     capture_output=True, timeout=2)
                        
                        # Check MediaMTX logs for stream availability
                        stream_available = False
                        try:
                            with open('/tmp/mediamtx.log', 'r') as f:
                                lines = f.readlines()
                                recent_lines = lines[-20:] if len(lines) >= 20 else lines
                                
                            # Look for "publishing to path 'stream'" in recent logs
                            for line in recent_lines:
                                if "publishing to path 'stream'" in line:
                                    stream_available = True
                                    break
                                elif "no stream is available on path 'stream'" in line:
                                    stream_available = False
                                    break
                                    
                        except Exception:
                            pass  # Can't read logs, skip this check
                        
                        # If logs show no stream available, fix it
                        if not stream_available:
                            print("[Stream Health] MediaMTX logs show no stream available - fixing...")
                            
                            # Force restart the stream
                            from modules.mediamtx_camera import stop_streaming
                            stop_streaming()
                            time.sleep(2)
                            start_streaming()
                            continue
                        
                        # Also check WebRTC endpoint as secondary check
                        try:
                            response = requests.get('http://localhost:8889/stream', timeout=3)
                            if response.status_code == 404:
                                print("[Stream Health] WebRTC endpoint shows 404 - checking logs...")
                                # This might be normal without client, so we rely on log check above
                        except requests.exceptions.RequestException:
                            pass  # WebRTC endpoint might not be accessible without client
                                
                    except subprocess.CalledProcessError:
                        print("[Stream Health] Process ID doesn't exist - resetting state")
                        stream_state_manager.set_state(StreamState.STOPPED)
                        
        except Exception as e:
            print(f"[Stream Health] Error in health monitoring thread: {e}")
            time.sleep(30)  # Wait longer on error

# Background audio quality monitoring thread
def audio_quality_monitor_thread():
    """Background thread to monitor and adjust audio quality"""
    import time
    from modules.mediamtx_camera import adjust_audio_quality, streaming_active
    
    while True:
        try:
            if streaming_active:
                # Check and adjust audio quality
                new_bitrate = adjust_audio_quality()
                
                # If bitrate changed, restart stream
                if new_bitrate != getattr(audio_quality_monitor_thread, 'last_bitrate', 32):
                    print(f"[Audio Monitor] Bitrate changed to {new_bitrate}kbps, restarting stream...")
                    try:
                        # Stop current stream
                        from modules.mediamtx_camera import stop_streaming
                        stop_result = stop_streaming()
                        
                        if stop_result.get('ok'):
                            time.sleep(1)
                            # Start new stream with adjusted bitrate
                            from modules.mediamtx_camera import start_streaming
                            start_result = start_streaming()
                            if start_result.get('ok'):
                                print(f"[Audio Monitor] ✓ Stream restarted with {new_bitrate}kbps audio")
                            else:
                                print(f"[Audio Monitor] ✗ Failed to restart stream: {start_result}")
                    except Exception as e:
                        print(f"[Audio Monitor] Error restarting stream: {e}")
                    
                    audio_quality_monitor_thread.last_bitrate = new_bitrate
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"[Audio Monitor] Error in monitoring thread: {e}")
            time.sleep(10)  # Wait longer on error

if __name__ == "__main__":
    # Automatic recovery and cleanup on startup
    try:
        from modules.mediamtx_camera import auto_recovery_on_startup
        print("[Main] Running automatic recovery on startup...")
        auto_recovery_on_startup()
    except Exception as e:
        print(f"[Main] Error during auto recovery: {e}")
    
    # Start bandwidth management thread
    import threading
    bandwidth_thread = threading.Thread(target=bandwidth_management_thread, daemon=True)
    bandwidth_thread.start()
    print("[Bandwidth Manager] Background bandwidth management started")
    
    # Start CPU monitoring thread
    cpu_thread = threading.Thread(target=cpu_monitoring_thread, daemon=True)
    cpu_thread.start()
    print("[CPU Monitor] Background CPU monitoring started")
    
    # Start audio quality monitoring thread
    monitor_thread = threading.Thread(target=audio_quality_monitor_thread, daemon=True)
    monitor_thread.start()
    print("[Audio Monitor] Background audio quality monitoring started")
    
    # DISABLED: Stream health monitoring was causing automatic restarts and crashes
    # Users should manually start/stop streams via the UI for stability
    # health_thread = threading.Thread(target=stream_health_monitor_thread, daemon=True)
    # health_thread.start()
    print("[Stream Health] Stream health auto-monitoring DISABLED for stability")
    
    # Start motor safety watchdog thread
    motor_watchdog_thread = threading.Thread(target=motor_safety_watchdog, daemon=True)
    motor_watchdog_thread.start()
    print("[Motor Safety] Motor safety watchdog started - monitors heartbeat and connections")
    
    main()
