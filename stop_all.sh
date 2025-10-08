#!/bin/bash
# Stop all Avatar Tank processes completely

echo "Stopping all Avatar Tank processes..."

# Kill all processes
pkill -f "modules/mediamtx_main.py" 2>/dev/null
pkill -f "mediamtx" 2>/dev/null
pkill -f "ffmpeg" 2>/dev/null
pkill -f "enhanced_web_app.py" 2>/dev/null
pkill -f "start_" 2>/dev/null
pkill -f "stable_" 2>/dev/null
pkill -f "clean_" 2>/dev/null
pkill -f "simple_" 2>/dev/null
pkill -f "final_" 2>/dev/null

# Remove PID files
rm -f /tmp/avatar_*.pid
rm -f /tmp/avatar_stable.pid
rm -f /tmp/avatar_clean.pid

# Wait for processes to die
sleep 3

# Check if anything is still running
REMAINING=$(ps aux | grep -E '(mediamtx|ffmpeg|python.*enhanced|modules/mediamtx_main)' | grep -v grep | wc -l)

if [ "$REMAINING" -gt 0 ]; then
    echo "Force killing remaining processes..."
    ps aux | grep -E '(mediamtx|ffmpeg|python.*enhanced|modules/mediamtx_main)' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null
    sleep 2
fi

echo "All processes stopped"
ps aux | grep -E '(mediamtx|ffmpeg|python.*enhanced|modules/mediamtx_main)' | grep -v grep || echo "No processes running"


