#!/bin/bash

# Avatar Tank FFmpeg Service
# Dedicated service to maintain FFmpeg stream with automatic restart

LOG_FILE="ffmpeg_service.log"
FFMPEG_LOG="ffmpeg_service_output.log"

echo "$(date): Starting FFmpeg service..." | tee -a "$LOG_FILE"

# Function to start FFmpeg
start_ffmpeg() {
    echo "$(date): Starting FFmpeg stream..." | tee -a "$LOG_FILE"
    ffmpeg -nostdin -f v4l2 -i /dev/video0 -vf "scale=640:480,fps=15,format=yuv420p" -c:v libx264 -preset ultrafast -crf 23 -g 15 -sc_threshold 0 -profile:v main -level 3.0 -rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2 -f rtsp rtsp://127.0.0.1:8554/stream > "$FFMPEG_LOG" 2>&1 &
    FFMPEG_PID=$!
    echo "$(date): FFmpeg started with PID $FFMPEG_PID" | tee -a "$LOG_FILE"
    return $FFMPEG_PID
}

# Function to check if FFmpeg is healthy
check_ffmpeg_health() {
    local pid=$1
    if ! kill -0 $pid 2>/dev/null; then
        echo "$(date): FFmpeg process $pid is dead" | tee -a "$LOG_FILE"
        return 1
    fi
    
    # Check if it's actually streaming by looking at MediaMTX API
    local stream_status=$(curl -s http://localhost:9997/v3/paths/list | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    if items and items[0].get('ready', False) and len(items[0].get('tracks', [])) > 0:
        print('HEALTHY')
    else:
        print('UNHEALTHY')
except:
    print('ERROR')
" 2>/dev/null)
    
    if [ "$stream_status" = "HEALTHY" ]; then
        return 0
    else
        echo "$(date): FFmpeg process $pid is running but stream is unhealthy" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Main service loop
FFMPEG_PID=""
while true; do
    if [ -z "$FFMPEG_PID" ] || ! check_ffmpeg_health $FFMPEG_PID; then
        # Kill any existing FFmpeg processes
        pkill -9 ffmpeg 2>/dev/null
        sleep 2
        
        # Start new FFmpeg process
        start_ffmpeg
        FFMPEG_PID=$?
        
        # Wait for it to establish connection
        sleep 5
        
        # Verify it's working
        if check_ffmpeg_health $FFMPEG_PID; then
            echo "$(date): FFmpeg service is healthy" | tee -a "$LOG_FILE"
        else
            echo "$(date): FFmpeg service failed to start properly" | tee -a "$LOG_FILE"
        fi
    fi
    
    # Check every 10 seconds
    sleep 10
done


