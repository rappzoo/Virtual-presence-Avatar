#!/bin/bash

# Avatar Tank Final Stable Startup Script
# This script starts all components in the correct order with proper monitoring

LOG_FILE="startup_final_stable.log"
MEDIA_MTX_CONFIG="config/mediamtx.yml"

echo "$(date): === Avatar Tank Final Stable Startup ===" | tee -a "$LOG_FILE"

# Step 1: Complete cleanup
echo "$(date): Performing complete cleanup..." | tee -a "$LOG_FILE"
./stop_all.sh | tee -a "$LOG_FILE"
sleep 3

# Step 2: Start MediaMTX server
echo "$(date): Starting MediaMTX server..." | tee -a "$LOG_FILE"
/usr/local/bin/mediamtx "$MEDIA_MTX_CONFIG" > mediamtx_final.log 2>&1 &
MEDIAMTX_PID=$!
echo "$(date): MediaMTX started with PID $MEDIAMTX_PID" | tee -a "$LOG_FILE"
sleep 5

# Verify MediaMTX is running
if ! pgrep -F "$MEDIAMTX_PID" > /dev/null; then
    echo "$(date): ❌ MediaMTX failed to start, check mediamtx_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Step 3: Start FFmpeg stream
echo "$(date): Starting FFmpeg stream..." | tee -a "$LOG_FILE"
# Use default 480p resolution for initial startup (will be updated by resolution API)
ffmpeg -nostdin -f v4l2 -i /dev/video0 -f alsa -i plughw:3,0 -vf "scale=854:480,fps=10,format=yuv420p" -c:v libx264 -preset ultrafast -crf 23 -g 10 -sc_threshold 0 -profile:v main -level 3.0 -c:a libopus -b:a 32k -rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2 -f rtsp rtsp://127.0.0.1:8554/stream > ffmpeg_final.log 2>&1 &
FFMPEG_PID=$!
echo "$(date): FFmpeg started with PID $FFMPEG_PID" | tee -a "$LOG_FILE"
sleep 5

# Verify FFmpeg is running
if ! pgrep -F "$FFMPEG_PID" > /dev/null; then
    echo "$(date): ❌ FFmpeg failed to start, check ffmpeg_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Step 4: Start Avatar Tank Advanced application
echo "$(date): Starting Avatar Tank Advanced application..." | tee -a "$LOG_FILE"
python3 modules/mediamtx_main.py > avatar_final.log 2>&1 &
AVATAR_PID=$!
echo "$(date): Avatar Tank Advanced started with PID $AVATAR_PID" | tee -a "$LOG_FILE"
sleep 5

# Verify Avatar app is running
if ! pgrep -F "$AVATAR_PID" > /dev/null; then
    echo "$(date): ❌ Avatar Tank Advanced failed to start, check avatar_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Step 5: Start stream monitor
echo "$(date): Starting stream monitor..." | tee -a "$LOG_FILE"
./monitor_stream.sh > stream_monitor_final.log 2>&1 &
MONITOR_PID=$!
echo "$(date): Stream monitor started with PID $MONITOR_PID" | tee -a "$LOG_FILE"

# Step 6: Verify everything is working
echo "$(date): Verifying system status..." | tee -a "$LOG_FILE"
sleep 5

# Check MediaMTX API
STREAM_STATUS=$(curl -s http://localhost:9997/v3/paths/list | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    if items and items[0].get('ready', False) and len(items[0].get('tracks', [])) > 0:
        print('READY')
    else:
        print('NOT_READY')
except:
    print('ERROR')
" 2>/dev/null)

if [ "$STREAM_STATUS" = "READY" ]; then
    echo "$(date): ✅ Stream is ready and active" | tee -a "$LOG_FILE"
else
    echo "$(date): ❌ Stream is not ready" | tee -a "$LOG_FILE"
fi

# Check web interface
if curl -s http://172.25.216.108:5000/ | grep -q "Avatar Tank"; then
    echo "$(date): ✅ Web interface is accessible" | tee -a "$LOG_FILE"
else
    echo "$(date): ❌ Web interface is not accessible" | tee -a "$LOG_FILE"
fi

echo "$(date): === Avatar Tank Final Stable System Ready ===" | tee -a "$LOG_FILE"
echo "$(date): Web Interface: http://172.25.216.108:5000/" | tee -a "$LOG_FILE"
echo "$(date): HLS Stream: http://172.25.216.108:8888/stream/index.m3u8" | tee -a "$LOG_FILE"
echo "$(date): WebRTC Stream: http://172.25.216.108:8889/stream" | tee -a "$LOG_FILE"
echo "$(date): MediaMTX API: http://172.25.216.108:9997/v3/paths/list" | tee -a "$LOG_FILE"

# Keep the script running to monitor the processes
wait $MEDIAMTX_PID $FFMPEG_PID $AVATAR_PID $MONITOR_PID
