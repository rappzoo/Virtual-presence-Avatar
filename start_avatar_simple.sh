#!/bin/bash
# Avatar Tank Simple Startup

cd /home/havatar/Avatar-robot

# Kill any existing processes
pkill -f mediamtx_main.py || true
pkill -f mediamtx || true
sleep 3

# Start MediaMTX
/usr/local/bin/mediamtx config/mediamtx.yml > mediamtx.log 2>&1 &
sleep 3

# Start Flask
python3 modules/mediamtx_main.py > flask.log 2>&1 &
sleep 5

echo "Avatar Tank started at $(date)"
