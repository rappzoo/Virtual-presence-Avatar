#!/bin/bash

# Avatar Tank Stream Monitor
# Monitors and maintains the video stream to prevent disconnections

LOG_FILE="stream_monitor.log"
API_URL="http://localhost:9997/v3/paths/list"

echo "$(date): Starting stream monitor..." | tee -a "$LOG_FILE"

while true; do
    # Check if stream is ready and has tracks
    STREAM_STATUS=$(curl -s "$API_URL" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    items = data.get('items', [])
    if items:
        item = items[0]
        ready = item.get('ready', False)
        tracks = item.get('tracks', [])
        readers = item.get('readers', [])
        print(f'READY:{ready},TRACKS:{len(tracks)},READERS:{len(readers)}')
    else:
        print('NO_STREAM')
except:
    print('ERROR')
" 2>/dev/null)
    
    echo "$(date): Stream status: $STREAM_STATUS" | tee -a "$LOG_FILE"
    
    # Check if FFmpeg is running (kill multiple processes)
    FFMPEG_COUNT=$(pgrep ffmpeg | wc -l)
    if [ "$FFMPEG_COUNT" -eq 0 ]; then
        echo "$(date): FFmpeg not running, restarting..." | tee -a "$LOG_FILE"
        ffmpeg -nostdin -f v4l2 -i /dev/video0 -vf "scale=640:480,fps=15,format=yuv420p" -c:v libx264 -preset ultrafast -crf 23 -g 15 -sc_threshold 0 -profile:v main -level 3.0 -rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2 -f rtsp rtsp://127.0.0.1:8554/stream > ffmpeg_monitor.log 2>&1 &
        sleep 5
    elif [ "$FFMPEG_COUNT" -gt 1 ]; then
        echo "$(date): Multiple FFmpeg processes detected ($FFMPEG_COUNT), killing all..." | tee -a "$LOG_FILE"
        pkill -9 ffmpeg
        sleep 2
        echo "$(date): Restarting single FFmpeg process..." | tee -a "$LOG_FILE"
        ffmpeg -nostdin -f v4l2 -i /dev/video0 -vf "scale=640:480,fps=15,format=yuv420p" -c:v libx264 -preset ultrafast -crf 23 -g 15 -sc_threshold 0 -profile:v main -level 3.0 -rtsp_transport tcp -reconnect 1 -reconnect_at_eof 1 -reconnect_streamed 1 -reconnect_delay_max 2 -f rtsp rtsp://127.0.0.1:8554/stream > ffmpeg_monitor.log 2>&1 &
        sleep 5
    fi
    
    # Check if MediaMTX is running
    if ! pgrep mediamtx > /dev/null; then
        echo "$(date): MediaMTX not running, restarting..." | tee -a "$LOG_FILE"
        /usr/local/bin/mediamtx config/mediamtx.yml > mediamtx_monitor.log 2>&1 &
        sleep 5
    fi
    
    # Check if Avatar app is running
    if ! pgrep -f "python.*mediamtx_main" > /dev/null; then
        echo "$(date): Avatar app not running, restarting..." | tee -a "$LOG_FILE"
        python3 modules/mediamtx_main.py > avatar_monitor.log 2>&1 &
        sleep 5
    fi
    
    sleep 30
done
