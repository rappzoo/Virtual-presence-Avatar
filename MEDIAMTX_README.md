# Avatar Tank - MediaMTX Integration

This is the MediaMTX-compatible version of the Avatar Tank system, integrating the existing modular structure with MediaMTX streaming capabilities.

## Overview

The MediaMTX integration provides:
- **Real-time streaming** via RTSP, HLS, and WebRTC
- **Low-latency, low-bandwidth** streaming optimized for 250kbps total
- **Integrated web control interface** with live video player
- **Compatible with existing Avatar Tank modules**

## Architecture

### MediaMTX-Compatible Modules

- **`mediamtx_camera.py`** - Camera management with MediaMTX streaming
- **`mediamtx_audio.py`** - Audio device management and configuration
- **`mediamtx_recorder.py`** - Recording with MediaMTX-compatible codecs
- **`mediamtx_main.py`** - Main application coordinating all modules

### Key Features

1. **Streaming Integration**
   - FFmpeg-based streaming to MediaMTX
   - Opus audio codec for WebRTC compatibility
   - H.264 video with low-latency settings
   - Automatic stream management

2. **Web Interface**
   - Embedded HLS video player
   - Real-time stream controls
   - Copyable stream URLs
   - Resolution and framerate adjustment

3. **Device Management**
   - Automatic camera detection
   - Audio device configuration
   - Resource conflict prevention
   - Graceful error handling

## Installation

### Prerequisites

1. **MediaMTX Server** (already running)
2. **Python Dependencies**:
   ```bash
   pip install flask flask-socketio opencv-python numpy
   ```

### Setup

1. **Copy the service file**:
   ```bash
   sudo cp avatar-mediamtx.service /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Enable and start the service**:
   ```bash
   sudo systemctl enable avatar-mediamtx.service
   sudo systemctl start avatar-mediamtx.service
   ```

3. **Check status**:
   ```bash
   sudo systemctl status avatar-mediamtx.service
   ```

## Usage

### Web Interface

Access the control interface at:
- **Local**: `http://localhost:5000`
- **Network**: `http://192.168.68.107:5000`

### Stream URLs

Once streaming is active, use these URLs:

- **HLS**: `http://192.168.68.107:8888/stream/index.m3u8`
- **RTSP**: `rtsp://192.168.68.107:8554/stream`
- **WebRTC**: `http://192.168.68.107:8889/stream`

### API Endpoints

- `GET /api/status` - Get system status
- `POST /api/stream/start` - Start streaming
- `POST /api/stream/stop` - Stop streaming
- `POST /api/recording/start` - Start recording
- `POST /api/recording/stop` - Stop recording
- `POST /api/snapshot` - Take snapshot
- `POST /api/resolution` - Set resolution
- `POST /api/framerate` - Set framerate

## Configuration

### Stream Settings

- **Resolution**: 320p, 480p, 720p
- **Framerate**: 10-25 fps
- **Video Bitrate**: 200kbps
- **Audio Bitrate**: 48kbps
- **Total Bandwidth**: ~250kbps

### Audio Settings

- **Codec**: Opus (WebRTC compatible)
- **Sample Rate**: 24kHz
- **Channels**: Mono
- **Filters**: High-pass (100Hz), Low-pass (7kHz)

### Video Settings

- **Codec**: H.264
- **Preset**: ultrafast
- **Tune**: zerolatency
- **GOP**: 20 frames
- **Buffer**: 400k

## Troubleshooting

### Common Issues

1. **Stream not starting**:
   - Check MediaMTX service: `sudo systemctl status mediamtx`
   - Check camera device: `ls /dev/video*`
   - Check audio device: `arecord -l`

2. **Video player not working**:
   - Ensure HLS.js is loaded
   - Check browser console for errors
   - Verify HLS stream URL is accessible

3. **Audio issues**:
   - Test microphone: `arecord -D plughw:3,0 -f cd -d 2 test.wav`
   - Check audio device permissions
   - Verify Opus codec support

### Logs

- **Service logs**: `sudo journalctl -u avatar-mediamtx -f`
- **MediaMTX logs**: `sudo journalctl -u mediamtx -f`
- **FFmpeg processes**: `ps aux | grep ffmpeg`

## Integration with Existing Modules

The MediaMTX modules are designed to work alongside existing Avatar Tank modules:

- **Device Detection**: Uses existing `device_detector.py`
- **Motor Control**: Compatible with `motor_controller.py`
- **TTS**: Works with `tts.py`
- **Predictor**: Integrates with `predictor.py`

## Performance Optimization

### Low Latency Settings

- **HLS**: 7 segments, 1s duration, 200ms parts
- **WebRTC**: Low-latency mode enabled
- **FFmpeg**: Zero-latency tuning
- **Buffer**: Minimal buffering

### Bandwidth Optimization

- **Video**: 200kbps max
- **Audio**: 48kbps Opus
- **Filters**: Noise reduction
- **Compression**: Efficient encoding

## Security

- **Service isolation**: Private tmp, protected system
- **User permissions**: Runs as `havatar` user
- **Network access**: Local network only
- **File access**: Restricted to necessary directories

## Development

### Module Structure

```
modules/
├── mediamtx_camera.py      # Camera + streaming
├── mediamtx_audio.py       # Audio management
├── mediamtx_recorder.py    # Recording
├── mediamtx_main.py        # Main application
└── device_detector.py      # Device detection (existing)
```

### Adding Features

1. **New streaming protocol**: Extend `mediamtx_camera.py`
2. **Audio processing**: Modify `mediamtx_audio.py`
3. **Recording formats**: Update `mediamtx_recorder.py`
4. **Web interface**: Edit `mediamtx_main.py`

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify MediaMTX service is running
3. Test individual components
4. Check network connectivity
5. Verify device permissions

The MediaMTX integration maintains full compatibility with the existing Avatar Tank system while adding professional streaming capabilities.












