#!/bin/bash

# Avatar Tank Stable Final Startup Script
# Ensures clean single-process environment for maximum stability

LOG_FILE="startup_stable_final.log"
PROJECT_DIR="/home/havatar/Avatar-robot"

echo "$(date): === Avatar Tank Stable Final Startup ===" | tee -a "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Complete cleanup - kill ALL processes
echo "$(date): Performing complete cleanup..." | tee -a "$LOG_FILE"
./stop_all.sh | tee -a "$LOG_FILE"
pkill -9 ffmpeg 2>/dev/null
pkill -9 mediamtx 2>/dev/null
pkill -9 python 2>/dev/null
sleep 5

# Verify cleanup
if pgrep -f "ffmpeg|mediamtx|python.*mediamtx_main" > /dev/null; then
    echo "$(date): ⚠️ Some processes still running, force killing..." | tee -a "$LOG_FILE"
    pkill -9 -f "ffmpeg|mediamtx|python.*mediamtx_main" 2>/dev/null
    sleep 3
fi

# Start MediaMTX server
echo "$(date): Starting MediaMTX server..." | tee -a "$LOG_FILE"
/usr/local/bin/mediamtx config/mediamtx.yml > mediamtx_final.log 2>&1 &
MEDIAMTX_PID=$!
echo "$(date): MediaMTX started with PID $MEDIAMTX_PID" | tee -a "$LOG_FILE"
sleep 5

# Verify MediaMTX is running
if ! pgrep -F "$MEDIAMTX_PID" > /dev/null; then
    echo "$(date): ❌ MediaMTX failed to start, check mediamtx_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Start single FFmpeg process with reconnection
echo "$(date): Starting FFmpeg stream..." | tee -a "$LOG_FILE"
ffmpeg -nostdin -f v4l2 -i /dev/video0 -vf "scale=640:480,fps=15,format=yuv420p" -c:v libx264 -preset ultrafast -crf 23 -g 15 -sc_threshold 0 -profile:v main -level 3.0 -rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2 -f rtsp rtsp://127.0.0.1:8554/stream > ffmpeg_final.log 2>&1 &
FFMPEG_PID=$!
echo "$(date): FFmpeg started with PID $FFMPEG_PID" | tee -a "$LOG_FILE"
sleep 8

# Verify FFmpeg is running
if ! pgrep -F "$FFMPEG_PID" > /dev/null; then
    echo "$(date): ❌ FFmpeg failed to start, check ffmpeg_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Start Avatar Tank Advanced system
echo "$(date): Starting Avatar Tank Advanced system..." | tee -a "$LOG_FILE"
python3 modules/mediamtx_main.py > avatar_final.log 2>&1 &
AVATAR_PID=$!
echo "$(date): Avatar Tank Advanced started with PID $AVATAR_PID" | tee -a "$LOG_FILE"
sleep 5

# Verify Avatar system is running
if ! pgrep -F "$AVATAR_PID" > /dev/null; then
    echo "$(date): ❌ Avatar Tank Advanced failed to start, check avatar_final.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Start stream monitor
echo "$(date): Starting stream monitor..." | tee -a "$LOG_FILE"
./monitor_stream.sh > stream_monitor_final.log 2>&1 &
MONITOR_PID=$!
echo "$(date): Stream monitor started with PID $MONITOR_PID" | tee -a "$LOG_FILE"

# Wait for stream to be ready
echo "$(date): Waiting for stream to be ready..." | tee -a "$LOG_FILE"
for i in {1..10}; do
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
        echo "$(date): ✅ Stream is ready!" | tee -a "$LOG_FILE"
        break
    else
        echo "$(date): Waiting for stream... ($i/10)" | tee -a "$LOG_FILE"
        sleep 3
    fi
done

echo "$(date): === Avatar Tank Stable Final System Ready ===" | tee -a "$LOG_FILE"
echo "$(date): Web Interface: http://172.25.216.108:5000/" | tee -a "$LOG_FILE"
echo "$(date): WebRTC Stream: http://172.25.216.108:8889/stream" | tee -a "$LOG_FILE"
echo "$(date): HLS Stream: http://172.25.216.108:8888/stream/index.m3u8" | tee -a "$LOG_FILE"
echo "$(date): MediaMTX API: http://172.25.216.108:9997/v3/paths/list" | tee -a "$LOG_FILE"
echo "$(date): Process PIDs: MediaMTX=$MEDIAMTX_PID, FFmpeg=$FFMPEG_PID, Avatar=$AVATAR_PID, Monitor=$MONITOR_PID" | tee -a "$LOG_FILE"

# Keep the script running to monitor processes
wait $MEDIAMTX_PID $FFMPEG_PID $AVATAR_PID $MONITOR_PID


