#!/bin/bash
# Avatar Tank Simple Startup

cd /home/havatar/Avatar-robot

# Kill any existing processes quickly
pkill -9 -f mediamtx_main.py 2>/dev/null || true
pkill -9 -f mediamtx 2>/dev/null || true
sleep 1

# Start MediaMTX in background
/usr/local/bin/mediamtx config/mediamtx.yml > mediamtx.log 2>&1 &
sleep 2

# Start Flask in foreground (becomes main process for systemd)
exec python3 -u modules/mediamtx_main.py

